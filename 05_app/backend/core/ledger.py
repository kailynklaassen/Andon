"""Human-in-the-loop action ledger — every human decision in the app becomes a row in Lakebase (Postgres).

Issues come from the data (insights.py); people respond with actions: raise a work order, propose a
threshold change, escalate a SCAR, correct a value, add context to a data point. The loop:

    app ──submit──► hitl.actions            the inbox: one row per action, its current status
        ──approve─► hitl.approved_actions   the outbox: a frozen copy of what was approved, by whom, and where it goes
                    hitl.action_events      the audit trail: every transition (submitted, approved, synced ...)
                          │
                          ▼  scheduled job (06_human_in_the_loop/01_sync_approved_actions)
        value changes → mfg_landing.app_corrections_<bronze table> → pipeline append flow → bronze_<table>
                        (flagged _altered_in_app = true, _app_action_id = <action_id>) → silver → gold
        notes         → routed to 1-2 Genie spaces → NOTE-<id>.md in each one's app_notes_<domain> volume → Genie
        both          → Delta mirror of the three tables in mfg_app, and sync_status / sync_ref written back here

Why Lakebase: the app does many small, concurrent writes and reads its own writes immediately — OLTP work.
The lakehouse gets the approved records on a schedule, with the action_id carried all the way to the bronze row.

Storage
  * lakebase: the app has a Lakebase `postgres` resource (PGHOST / PGDATABASE / PGUSER are injected). The app's
              service principal creates and owns schema `hitl` on first use.
  * local (no PGHOST): data/actions.jsonl — an append-only event log, zero setup, for laptop runs.

Every function takes the acting person (`user`) explicitly: the API layer reads it from the request
(X-Forwarded-Email on Databricks Apps), so nothing here depends on a web framework.
"""
from __future__ import annotations

import json
import os
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

LOCAL_LEDGER = Path(__file__).resolve().parents[2] / "data" / "actions.jsonl"
SCHEMA = os.getenv("KK_HITL_SCHEMA", "hitl")
# Postgres roles that run the lakehouse sync job: they read the outbox and write back sync status.
SYNC_ROLES = [r.strip() for r in os.getenv("KK_HITL_SYNC_ROLES", "databricks_superuser").split(",") if r.strip()]

# The three tables. One action table typed by action_type; payload (jsonb) holds the type-specific fields,
# so new action types never need a schema change.
DDL = """
CREATE SCHEMA IF NOT EXISTS {s};

CREATE TABLE IF NOT EXISTS {s}.actions (
  action_id    uuid PRIMARY KEY,
  created_ts   timestamptz NOT NULL DEFAULT now(),   -- when the human submitted it
  created_by   text NOT NULL,                        -- app user email (X-Forwarded-Email)
  action_type  text NOT NULL,                        -- work_order | threshold_change | data_correction | comment | ...
  entity_type  text NOT NULL,                        -- plant | line | machine | supplier | carrier | customer | capa | defect
  entity_id    text NOT NULL,                        -- e.g. GVL-L3-WC01, SUP-1007
  title        text NOT NULL,
  details      text,                                 -- free-text context the human added
  priority     text,                                 -- P1 | P2 | P3
  status       text NOT NULL DEFAULT 'Submitted' CHECK (status IN ('Submitted', 'Approved', 'Rejected', 'Done')),
  source       text,                                 -- human | agent_suggested
  insight_id   text,                                 -- the insight this responds to, if any
  payload      jsonb NOT NULL DEFAULT '{{}}',         -- type-specific fields; corrections name table · key · column
  reviewed_by  text,
  reviewed_ts  timestamptz
);
COMMENT ON TABLE {s}.actions IS 'KK''s Parts app: every submitted human action (the inbox).';

CREATE TABLE IF NOT EXISTS {s}.approved_actions (
  action_id    uuid PRIMARY KEY REFERENCES {s}.actions (action_id),
  approved_ts  timestamptz NOT NULL DEFAULT now(),
  approved_by  text NOT NULL,
  created_ts   timestamptz NOT NULL,
  created_by   text NOT NULL,
  action_type  text NOT NULL,
  entity_type  text NOT NULL,
  entity_id    text NOT NULL,
  title        text NOT NULL,
  details      text,
  priority     text,
  source       text,
  insight_id   text,
  payload      jsonb NOT NULL,
  kind         text NOT NULL CHECK (kind IN ('value_change', 'note')),
  target       text NOT NULL,                        -- value_change: bronze table · note: Genie domain
  sync_status  text NOT NULL DEFAULT 'pending' CHECK (sync_status IN ('pending', 'synced', 'failed')),
  synced_ts    timestamptz,
  sync_ref     text,                                 -- where it landed: correction table + row, or the note's file path
  sync_error   text,
  sync_run_id  text                                  -- the job run that moved it to the lakehouse
);
CREATE INDEX IF NOT EXISTS approved_actions_pending ON {s}.approved_actions (sync_status, approved_ts);
COMMENT ON TABLE {s}.approved_actions IS 'KK''s Parts app: approved actions waiting for / moved to the lakehouse (the outbox).';

CREATE TABLE IF NOT EXISTS {s}.action_events (
  event_id   bigserial PRIMARY KEY,
  action_id  uuid NOT NULL REFERENCES {s}.actions (action_id),
  event_ts   timestamptz NOT NULL DEFAULT now(),
  actor      text NOT NULL,                          -- a person, or the sync job
  event      text NOT NULL,                          -- submitted | approved | rejected | done | synced | sync_failed | in_gold | searchable_in_genie
  detail     jsonb NOT NULL DEFAULT '{{}}'
);
CREATE INDEX IF NOT EXISTS action_events_action ON {s}.action_events (action_id, event_ts);
COMMENT ON TABLE {s}.action_events IS 'KK''s Parts app: audit trail of every action state change.';
"""

# The sync job's roles read everything and may only touch the sync columns + append events.
GRANTS = """
GRANT USAGE ON SCHEMA {s} TO {r};
GRANT SELECT ON ALL TABLES IN SCHEMA {s} TO {r};
GRANT UPDATE (sync_status, synced_ts, sync_ref, sync_error, sync_run_id) ON {s}.approved_actions TO {r};
GRANT INSERT ON {s}.action_events TO {r};
GRANT USAGE ON SEQUENCE {s}.action_events_event_id_seq TO {r};
"""

# What a person can do. `fields` drive the form; every type writes the same ledger row.
# Field kinds: select / number / date / text, plus data-bound kinds whose choices come from the data itself
# (failure_mode, alt_supplier, materials, owner, record) so the payload always maps back to real ids.
# `domain` = the Genie space an approved note is published to ("any" → decided by the entity, see note_domain).
ACTION_TYPES: dict[str, dict] = {
    "work_order": {"label": "Create work order", "icon": ":material/build:", "domain": "maintenance",
                   "fields": [("work_order_type", "select", ["Corrective", "Emergency", "Preventive", "Inspection"]),
                              ("failure_mode", "failure_mode", None), ("needed_by", "date", None)]},
    "inspect": {"label": "Request inspection", "icon": ":material/search:", "domain": "maintenance",
                "fields": [("inspection_type", "select", ["Vibration route", "Thermography", "Oil analysis", "Visual"])]},
    "threshold_change": {"label": "Propose threshold change (MOC)", "icon": ":material/tune:", "domain": "maintenance",
                         "fields": [("parameter", "text", "PM-CNC-030 bearing replacement limit (mm/s)"),
                                    ("current_value", "number", 7.1), ("proposed_value", "number", 4.5),
                                    ("reference", "text", "Hartwell HMC-Series manual §7.4 · MOC-2026-031")]},
    "scar_escalation": {"label": "Escalate SCAR / supplier", "icon": ":material/campaign:", "domain": "quality",
                        "fields": [("escalation_level", "select", ["Level 2 — formal letter", "Level 3 — executive review",
                                                                    "Controlled shipping CS1", "New business hold"]),
                                   ("response_due", "date", None)]},
    "dual_source": {"label": "Start dual-source / PPAP", "icon": ":material/alt_route:", "domain": "supply_chain",
                    "fields": [("alternate_supplier", "alt_supplier", None), ("materials", "materials", None)]},
    "carrier_review": {"label": "Carrier action", "icon": ":material/local_shipping:", "domain": "supply_chain",
                       "fields": [("carrier_action", "select", ["Claim service credit", "Shift volume to alternate",
                                                                 "Schedule QBR", "Issue 60-day notice"]),
                                  ("volume_shift_pct", "number", 30)]},
    "customer_response": {"label": "Customer response", "icon": ":material/mail:", "domain": "supply_chain",
                          "fields": [("response_type", "select", ["Recovery plan letter", "Expedite open orders", "Call with account team"])]},
    "containment": {"label": "Containment / quality hold", "icon": ":material/block:", "domain": "quality",
                    "fields": [("scope", "text", "C-shift output since die change"), ("hold_qty", "number", 0)]},
    "work_instruction": {"label": "Fix work instruction", "icon": ":material/menu_book:", "domain": "quality",
                         "fields": [("document", "text", "WI-WRO-CR-07"), ("from_rev", "text", "Rev D"), ("to_rev", "text", "Rev E")]},
    "capa_update": {"label": "Update CAPA", "icon": ":material/task_alt:", "domain": "quality",
                    "fields": [("new_status", "select", ["In Progress", "Containment verified", "Root cause confirmed",
                                                          "Pending effectiveness check", "Closed"]),
                               ("new_due_date", "date", None)]},
    "assign_owner": {"label": "Assign / reassign owner", "icon": ":material/person:", "domain": "quality",
                     "fields": [("owner", "owner", None)]},
    "data_correction": {"label": "Flag / correct a value", "icon": ":material/edit:", "domain": "any",
                        "fields": [("record", "record", None)]},   # record → field → current → corrected (kk/records.py)
    "comment": {"label": "Add context / comment", "icon": ":material/chat:", "domain": "any", "fields": []},
}

STATUSES = ["Submitted", "Approved", "Rejected", "Done"]
ENTITY_DOMAIN = {"plant": "production", "line": "production", "machine": "maintenance", "capa": "quality",
                 "defect": "quality", "supplier": "supply_chain", "material": "supply_chain", "carrier": "supply_chain",
                 "customer": "supply_chain", "dc": "supply_chain", "warehouse": "supply_chain"}


def note_domain(action_type: str, entity_type: str) -> str:
    d = ACTION_TYPES.get(action_type, {}).get("domain", "any")
    return d if d != "any" else ENTITY_DOMAIN.get(entity_type, "production")


def route(action_type: str, entity_type: str, payload: dict) -> tuple[str, str]:
    """Where an approved action goes in the lakehouse: (kind, target).

    A data correction names a cell → it's a value change, written back to the bronze table behind that cell.
    Everything else is human context (a decision, a note, a request) → a note document for that domain's Genie space.
    """
    if action_type == "data_correction" and payload.get("bronze_table"):
        return "value_change", payload["bronze_table"]
    return "note", note_domain(action_type, entity_type)


def backend() -> str:
    return "lakebase" if os.getenv("PGHOST") else "local"


# ----------------------------------------------------------------------------- Lakebase connection
# OAuth database credentials last one hour, so the connection is re-opened with a fresh token well before that.
_TOKEN_TTL_S = 45 * 60


def _password() -> str:
    if os.getenv("PGPASSWORD"):
        return os.environ["PGPASSWORD"]
    from databricks.sdk import WorkspaceClient
    endpoint = os.getenv("KK_LAKEBASE_ENDPOINT") or os.getenv("LAKEBASE_ENDPOINT")
    return WorkspaceClient().postgres.generate_database_credential(endpoint=endpoint).token


def _username() -> str:
    if os.getenv("PGUSER"):
        return os.environ["PGUSER"]
    from databricks.sdk import WorkspaceClient
    return WorkspaceClient().current_user.me().user_name


_HOLDER = {"conn": None, "opened": 0.0}
_LOCK = threading.Lock()


def _conn_holder() -> dict:
    return _HOLDER


def _pg():
    import psycopg
    h = _conn_holder()
    c = h["conn"]
    if c is None or c.closed or time.time() - h["opened"] > _TOKEN_TTL_S:
        if c is not None and not c.closed:
            c.close()
        c = psycopg.connect(host=os.environ["PGHOST"], port=int(os.getenv("PGPORT", "5432")),
                            dbname=os.getenv("PGDATABASE", "databricks_postgres"), user=_username(),
                            password=_password(), sslmode=os.getenv("PGSSLMODE", "require"), autocommit=False)
        h.update(conn=c, opened=time.time())
    return c


def _run(fn):
    """Run fn(cursor) in one transaction; reconnect once if the connection went stale (scale-to-zero, idle timeout).
    One connection per process, used by one request at a time (the lock) — plenty for a ledger."""
    import psycopg
    for attempt in (1, 2):
        with _LOCK:
            conn = _pg()
            try:
                with conn.transaction(), conn.cursor() as cur:
                    return fn(cur)
            except psycopg.OperationalError:
                _conn_holder()["conn"] = None
                if attempt == 2:
                    raise


_SCHEMA_READY = []


def _ensure_schema() -> bool:
    if _SCHEMA_READY:
        return True
    def create(cur):
        cur.execute(DDL.format(s=SCHEMA))
        for r in SYNC_ROLES:
            cur.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (r,))
            if cur.fetchone():
                cur.execute(GRANTS.format(s=SCHEMA, r=f'"{r}"'))
    _run(create)
    _SCHEMA_READY.append(True)
    return True


def _event(cur, action_id: str, event: str, actor: str, detail: dict | None = None) -> None:
    cur.execute(f"INSERT INTO {SCHEMA}.action_events (action_id, actor, event, detail) VALUES (%s, %s, %s, %s)",
                (action_id, actor, event, json.dumps(detail or {}, default=str)))


# ----------------------------------------------------------------------------- the API the pages use
def record(user: str, action_type: str, entity_type: str, entity_id: str, title: str, details: str = "",
           priority: str = "P2", payload: dict | None = None, source: str = "human", insight_id: str = "") -> dict:
    row = {"action_id": str(uuid.uuid4()), "created_ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "created_by": user, "action_type": action_type, "entity_type": entity_type, "entity_id": entity_id,
           "title": title, "details": details, "priority": priority, "status": "Submitted", "source": source,
           "insight_id": insight_id, "payload": json.dumps(payload or {}, default=str), "reviewed_by": "", "reviewed_ts": ""}
    if backend() == "lakebase" and _ensure_schema():
        def insert(cur):
            cols = [c for c in row if c not in ("reviewed_by", "reviewed_ts")]
            cur.execute(f"INSERT INTO {SCHEMA}.actions ({', '.join(cols)}) VALUES ({', '.join(['%s'] * len(cols))})",
                        [row[c] for c in cols])
            _event(cur, row["action_id"], "submitted", row["created_by"], {"action_type": action_type})
        _run(insert)
    else:
        LOCAL_LEDGER.parent.mkdir(parents=True, exist_ok=True)
        with LOCAL_LEDGER.open("a") as f:
            f.write(json.dumps(row) + "\n")
    return row


LEDGER_COLUMNS = ["action_id", "created_ts", "created_by", "action_type", "entity_type", "entity_id", "title",
                  "details", "priority", "status", "source", "insight_id", "payload", "reviewed_by", "reviewed_ts",
                  "kind", "target", "sync_status", "synced_ts", "sync_ref", "sync_error"]


def ledger() -> pd.DataFrame:
    """Every action with its review status and, once approved, where it went in the lakehouse."""
    if backend() == "lakebase" and _ensure_schema():
        def select(cur):
            cur.execute(f"""
                SELECT a.action_id::text, a.created_ts, a.created_by, a.action_type, a.entity_type, a.entity_id, a.title,
                       a.details, a.priority, a.status, a.source, a.insight_id, a.payload::text AS payload,
                       a.reviewed_by, a.reviewed_ts, p.kind, p.target, p.sync_status, p.synced_ts, p.sync_ref, p.sync_error
                FROM {SCHEMA}.actions a LEFT JOIN {SCHEMA}.approved_actions p USING (action_id)
                ORDER BY a.created_ts DESC""")
            return cur.fetchall()
        df = pd.DataFrame(_run(select), columns=LEDGER_COLUMNS)
        for c in ("created_ts", "reviewed_ts", "synced_ts"):
            df[c] = pd.to_datetime(df[c], utc=True)          # keep the UTC offset: the browser shows local time
    elif LOCAL_LEDGER.exists():
        df = pd.DataFrame([json.loads(l) for l in LOCAL_LEDGER.read_text().splitlines() if l.strip()])
        # the local ledger is an append-only event log: the last line per action_id (file order) is its state
        df = df.drop_duplicates("action_id", keep="last").reindex(columns=LEDGER_COLUMNS)
    else:
        df = pd.DataFrame(columns=LEDGER_COLUMNS)
    if len(df):
        df = df.sort_values("created_ts", ascending=False).reset_index(drop=True)
    return df


def review(user: str, action_id: str, status: str) -> None:
    """Approve / reject / complete. Approving copies the action into the outbox (approved_actions) with its route."""
    who, ts = user, datetime.now(timezone.utc).isoformat(timespec="seconds")
    if backend() == "lakebase" and _ensure_schema():
        def update(cur):
            cur.execute(f"UPDATE {SCHEMA}.actions SET status = %s, reviewed_by = %s, reviewed_ts = now() "
                        f"WHERE action_id = %s RETURNING action_type, entity_type, payload", (status, who, action_id))
            action_type, entity_type, payload = cur.fetchone()
            detail = {"status": status}
            if status == "Approved":
                kind, target = route(action_type, entity_type, payload or {})
                cur.execute(f"""
                    INSERT INTO {SCHEMA}.approved_actions
                      (action_id, approved_by, created_ts, created_by, action_type, entity_type, entity_id, title, details,
                       priority, source, insight_id, payload, kind, target)
                    SELECT action_id, %s, created_ts, created_by, action_type, entity_type, entity_id, title, details,
                           priority, source, insight_id, payload, %s, %s
                    FROM {SCHEMA}.actions WHERE action_id = %s
                    ON CONFLICT (action_id) DO NOTHING""", (who, kind, target, action_id))
                detail.update(kind=kind, target=target)
            _event(cur, action_id, status.lower(), who, detail)
        _run(update)
    else:
        row = ledger().set_index("action_id").loc[action_id].to_dict()
        row.update(action_id=action_id, status=status, reviewed_by=who, reviewed_ts=ts)
        if status == "Approved":
            kind, target = route(row["action_type"], row["entity_type"], json.loads(row.get("payload") or "{}"))
            row.update(kind=kind, target=target, sync_status="pending")
        with LOCAL_LEDGER.open("a") as f:
            f.write(json.dumps({k: (None if isinstance(v, float) and pd.isna(v) else v) for k, v in row.items()},
                               default=str) + "\n")


def events(action_id: str) -> pd.DataFrame:
    """The audit trail of one action (Lakebase only; the local ledger keeps its states as lines in the file)."""
    if backend() != "lakebase" or not _ensure_schema():
        return pd.DataFrame(columns=["event_ts", "actor", "event", "detail"])
    def select(cur):
        cur.execute(f"SELECT event_ts, actor, event, detail::text FROM {SCHEMA}.action_events "
                    f"WHERE action_id = %s ORDER BY event_ts", (action_id,))
        return cur.fetchall()
    return pd.DataFrame(_run(select), columns=["event_ts", "actor", "event", "detail"])


def last_in_gold():
    """When an approved correction last reached gold (the sync job's `in_gold` event, written after the pipeline
    refresh), or None. The app polls this to know when its cached gold data is out of date."""
    if backend() != "lakebase" or not _ensure_schema():
        return None
    def select(cur):
        cur.execute(f"SELECT max(event_ts) FROM {SCHEMA}.action_events WHERE event = 'in_gold'")
        return cur.fetchone()[0]
    return _run(select)


def for_entity(entity_id: str) -> pd.DataFrame:
    df = ledger()
    return df[df.entity_id == entity_id] if len(df) else df
