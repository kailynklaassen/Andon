# Databricks notebook source
# MAGIC %md
# MAGIC # Step 6b · Sync approved human actions from Lakebase into the lakehouse
# MAGIC
# MAGIC Runs on a schedule (job `kkparts-hitl-sync`, created by `00_setup_hitl_sync`). Each run moves every approved,
# MAGIC not-yet-synced action out of the app's Lakebase outbox and into the right place in the lakehouse:
# MAGIC
# MAGIC ```
# MAGIC Lakebase hitl.approved_actions (sync_status = pending)
# MAGIC   ├─ kind = value_change → full corrected record appended to <landing>.app_corrections_<table>
# MAGIC   │                         → pipeline append flow → bronze_<table> (_altered_in_app = true, _app_action_id)
# MAGIC   │                         → silver keeps the latest version → gold → metric views, Genie, the app
# MAGIC   └─ kind = note         → routed by the supervisor's router model (Genie space descriptions) to 1-2 domains
# MAGIC                             → app_notes_<domain>/NOTE-<id>.md (one volume per Genie space, attached to it)
# MAGIC                             → Genie Agent mode searches the file; its priority (P1/P2/P3) is in the text
# MAGIC                             → the volume's Genie file index is re-synced (it does not pick up new files itself)
# MAGIC then: sync_status / sync_ref / sync_run_id written back to Lakebase + a 'synced' audit event,
# MAGIC       and the three Lakebase tables mirrored to Delta in <app schema> (hitl_actions, hitl_approved_actions,
# MAGIC       hitl_action_events) so every change is traceable in the lakehouse: bronze row → action → people → events.
# MAGIC ```
# MAGIC
# MAGIC **Why a job and not Lakehouse Sync:** Lakebase's native Postgres → Delta CDC is Beta; this accelerator uses GA and
# MAGIC Public Preview features only. The job is idempotent: a correction already appended for an action is not appended
# MAGIC twice, and a note file is simply rewritten.
# MAGIC
# MAGIC **Identity:** the job runs as its owner, who needs a Lakebase role in the project (the project owner has one) and
# MAGIC MODIFY on the correction tables, WRITE VOLUME on the `app_notes_<domain>` volumes and the app schema;
# MAGIC it also queries the router model (Foundation Model API) to route notes.

# COMMAND ----------

# MAGIC %md
# MAGIC ### Why this step matters
# MAGIC This is the reverse ETL that closes the loop: approved value changes become bronze rows (so they flow through the same pipeline and quality rules as source data), approved notes are routed to the Genie space(s) they are about, where their priority decides how much they change an answer.
# MAGIC
# MAGIC **Crucial**
# MAGIC * Idempotency (re-runs never double-apply)
# MAGIC * Writing the outcome back to Lakebase (the app shows where each action landed).
# MAGIC
# MAGIC **Optional**
# MAGIC * The Delta mirror of the ledger (`mfg_app.hitl_*`) — strongly recommended for audit, not required for the loop.

# COMMAND ----------

# MAGIC %pip install "psycopg[binary]>=3.2" "databricks-sdk>=0.81" "databricks-openai>=0.6" --quiet
# MAGIC %restart_python

# COMMAND ----------

# MAGIC %run ../config/config

# COMMAND ----------

import json
import os
from datetime import datetime, timezone

import psycopg
from databricks.sdk import WorkspaceClient
from delta.tables import DeltaTable
from pyspark.sql import Window
from pyspark.sql import functions as F

w = WorkspaceClient()
import databricks.sdk
print(f"databricks-sdk {databricks.sdk.version.__version__}")      # what this run's %pip resolved (see pg_database)
H = CFG["hitl"]
LB = H["lakebase"]
PG_SCHEMA = LB["schema"]
BRANCH = f"projects/{LB['project']}/branches/{LB['branch']}"
ENDPOINT = f"{BRANCH}/endpoints/{LB['endpoint']}"
DOMAINS = {s["key"]: s["docs_folder"] for s in CFG["genie"]["spaces"]}
ACTOR = f"job:{H['sync']['job_name']}"
RUN_ID = _widget("run_id", "") or f"manual-{datetime.now(timezone.utc):%Y%m%dT%H%M%S}"
# republish_notes=true: route + rewrite every already-synced note too (after changing the routing or the volumes)
REPUBLISH = _widget("republish_notes", "false").lower() == "true"
spark.sql(f"CREATE SCHEMA IF NOT EXISTS `{CATALOG}`.`{APP_SCHEMA}` COMMENT 'KK''s Parts app: human-in-the-loop ledger mirrored from Lakebase'")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1 · Connect to Lakebase and read the outbox
# MAGIC OAuth database credential for the job's identity (valid one hour — a sync run takes seconds).

# COMMAND ----------

def pg_database() -> str:
    """The Postgres database name. From config, so the job doesn't depend on w.postgres.get_database — the SDK the
    job's %pip resolves can be older than the one that added it (that broke every scheduled sync after a new package)."""
    if LB.get("postgres_database"):
        return LB["postgres_database"]
    return w.postgres.get_database(name=f"{BRANCH}/databases/{LB['database']}").status.postgres_database


def pg():
    host = w.postgres.get_endpoint(name=ENDPOINT).status.hosts.host
    dbname = pg_database()
    token = w.postgres.generate_database_credential(endpoint=ENDPOINT).token
    return psycopg.connect(host=host, dbname=dbname, user=w.current_user.me().user_name, password=token,
                           sslmode="require")


def rows(cur) -> list[dict]:
    names = [d.name for d in cur.description]
    return [dict(zip(names, r)) for r in cur.fetchall()]


with pg() as conn, conn.cursor() as cur:
    cur.execute(f"""
        SELECT action_id::text, approved_ts, approved_by, created_ts, created_by, action_type, entity_type, entity_id,
               title, details, priority, source, insight_id, payload, kind, target, sync_status
        FROM {PG_SCHEMA}.approved_actions
        WHERE sync_status IN ('pending', 'failed') OR (%s AND kind = 'note')
        ORDER BY approved_ts""", (REPUBLISH,))   # oldest approval first, so a later correction of the same cell wins
    pending = rows(cur)
print(f"{len(pending)} approved action(s) to sync — run {RUN_ID}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2 · Value changes → bronze (via the correction tables)
# MAGIC The correction is a **whole record**, not a patch: start from the latest version of the record (bronze, or an
# MAGIC earlier app correction that the pipeline hasn't picked up yet), change one column, stamp the lineage columns.
# MAGIC The value is cast to the bronze column's type, so it means exactly what a source-system value would.

# COMMAND ----------

LINEAGE = ["_altered_in_app", "_app_action_id", "_app_approved_by", "_app_approved_ts"]
INT_TYPES = ("tinyint", "smallint", "int", "bigint")


def typed(value, dtype: str):
    """The corrected value as a string Spark can CAST to the bronze column type (ANSI-safe for '12.0' → int)."""
    if value is None or str(value).strip() == "":
        return None
    if dtype in INT_TYPES:
        return str(int(float(value)))
    return str(value)


def apply_correction(a: dict) -> str:
    p = a["payload"]
    bronze_table, key, key_value = p["bronze_table"], p["bronze_key"], p["key_value"]
    column, new = p["bronze_column"], p["corrected_value"]
    target = correction_table(bronze_table.split(".")[-1])
    bronze = spark.table(bronze_table)
    missing = [c for c in [key, column, *LINEAGE] if c not in bronze.columns]
    if missing:
        raise ValueError(f"{bronze_table} has no column(s) {missing} — run Step 2a (pipeline) and 6a (setup) first")
    cols = bronze.columns
    if not spark.catalog.tableExists(target):
        raise ValueError(f"{target} does not exist — run 06_human_in_the_loop/00_setup_hitl_sync first")
    if spark.table(target).where(F.col("_app_action_id") == a["action_id"]).limit(1).count():
        return f"{target} · {key} = {key_value} · {column} (already synced)"        # idempotent re-run

    versions = (bronze.where(F.col(key) == key_value).select(cols)
                .unionByName(spark.table(target).where(F.col(key) == key_value).select(cols)))
    latest = Window.orderBy(F.col("_app_approved_ts").desc_nulls_last(), F.col("_ingested_at").desc())
    base = versions.withColumn("_v", F.row_number().over(latest)).where("_v = 1").drop("_v")
    current = base.collect()
    if not current:
        raise ValueError(f"{key} = {key_value} not found in {bronze_table}")
    prior = current[0][column]
    dtype = dict(bronze.dtypes)[column]
    corrected = (base
                 .withColumn(column, F.lit(typed(new, dtype)).cast(dtype))
                 .withColumn("_source_file", F.lit(f"kkparts-app://hitl/actions/{a['action_id']}"))
                 .withColumn("_source_file_ts", F.lit(a["approved_ts"]).cast("timestamp"))
                 .withColumn("_ingested_at", F.current_timestamp())
                 .withColumn("_altered_in_app", F.lit(True))
                 .withColumn("_app_action_id", F.lit(a["action_id"]))
                 .withColumn("_app_approved_by", F.lit(a["approved_by"]))
                 .withColumn("_app_approved_ts", F.lit(a["approved_ts"]).cast("timestamp"))
                 .select(cols))
    corrected.write.mode("append").saveAsTable(target)
    return f"{target} · {key} = {key_value} · {column}: {prior} → {typed(new, dtype)}"

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3 · Notes → the Genie space(s) they are about
# MAGIC Every other approved action (a decision, a request, a comment) is human context.
# MAGIC 1. **Route it** the way the supervisor routes a question: the fast router model reads the note against each Genie
# MAGIC    space's description — the same routing rule Foreman uses — and picks the 1-2 domains it is about. A comment on a
# MAGIC    *machine* about a *supplier's* castings belongs to Supply Chain and Quality, not Maintenance. If the model call
# MAGIC    fails, the rule (action type → entity type) decides, and the note says so.
# MAGIC 2. **Write it** to each chosen domain's notes volume (`app_notes_<domain>`) as markdown. That volume is attached to
# MAGIC    the domain's Genie space; Agent mode finds the note — and reads its priority (P1 / P2 / P3) from the text — once
# MAGIC    the volume's file index has re-synced (section 4b).

# COMMAND ----------

import sys

sys.path.insert(0, f"{REPO_ROOT}/06_human_in_the_loop")
import app_notes as AN

N = CFG["hitl"].get("notes", {})
PRIORITIES = ("P1", "P2", "P3")
REGISTRY = {r.domain_key: r.description for r in spark.table(f"{CATALOG}.{GOLD_SCHEMA}.genie_space_registry").collect()}
ROUTER = CFG["supervisor"]["router_llm"]
ROUTE_PROMPT = """You route an approved note from a manufacturing operations app to the domain expert(s) it is about, exactly
as you would route a question. Domains (key: what it owns):
{domains}

Pick the 1-{n} domains whose expert must know this note to answer future questions correctly — usually one; two only
when the note clearly matters to both (e.g. a supplier decision that changes quality containment). Judge by what the
note is ABOUT, not where it was written.
Reply with only JSON: {{"domains": ["<key>", ...], "reason": "<one short sentence>"}}

Note — {kind} on {entity_type} {entity_id}, priority {priority}
Title: {title}
{details}"""


def route_note(a: dict) -> tuple[list[str], str, str]:
    """(domains, routed_by, reason). Supervisor routing, falling back to the rule the app recorded (target)."""
    fallback = [a["target"] if a["target"] in DOMAINS else "production"]
    if N.get("routing", "supervisor") != "supervisor":
        return fallback, "rule", "routing set to rules (hitl.notes.routing)"
    try:
        from databricks_openai import DatabricksOpenAI      # the same client Foreman routes with
        llm = DatabricksOpenAI(workspace_client=w)
        prompt = ROUTE_PROMPT.format(domains="\n".join(f"- {k}: {v}" for k, v in REGISTRY.items()),
                                     n=int(N.get("max_domains", 2)), kind=a["action_type"].replace("_", " "),
                                     entity_type=a["entity_type"], entity_id=a["entity_id"], priority=a["priority"] or "P3",
                                     title=a["title"], details=(a["details"] or "")[:3000])
        out = llm.chat.completions.create(model=ROUTER, max_tokens=1000, messages=   # room for the model to reason first
                                         [{"role": "user", "content": prompt}])
        text = out.choices[0].message.content
        text = text if isinstance(text, str) else "".join(b.get("text", "") for b in text if isinstance(b, dict))
        r = json.loads(text[text.index("{"):text.rindex("}") + 1])
        domains = [d for d in r.get("domains", []) if d in DOMAINS][: int(N.get("max_domains", 2))]
        if domains:
            return domains, f"supervisor ({ROUTER})", str(r.get("reason", ""))[:300]
    except Exception as e:
        print(f"   routing fell back to the rule for {a['action_id']}: {str(e)[:200]}")
    return fallback, "rule", "router model unavailable; routed by action/entity type"


TOUCHED: set[str] = set()                                   # domains whose notes volume changed this run


def publish_note(a: dict) -> str:
    domains, routed_by, reason = route_note(a)
    note_id = f"NOTE-{a['action_id'][:8].upper()}"
    prio = a["priority"] if a["priority"] in PRIORITIES else "P3"
    fields = "\n".join(f"- {k.replace('_', ' ')}: {', '.join(map(str, v)) if isinstance(v, list) else v}"
                       for k, v in (a["payload"] or {}).items() if v not in (None, "", []))
    body = "\n".join([
        f"Approved {a['action_type'].replace('_', ' ')} from the {COMPANY} operations app, about {a['entity_type']} "
        f"{a['entity_id']}" + (f" (responds to insight {a['insight_id']})." if a["insight_id"] else "."),
        f"Submitted by {a['created_by']} on {a['created_ts']:%Y-%m-%d}; approved by {a['approved_by']} on {a['approved_ts']:%Y-%m-%d}. "
        f"{'Suggested by the Foreman agent, accepted by a person.' if a['source'] == 'agent_suggested' else 'Entered by a person.'}",
        "", "## What the person said", a["details"] or "(no free-text note)", "",
        *(["## Details", fields, ""] if fields else []),
        f"Routed to: {', '.join(domains)} — {reason}",
        f"Trace: Lakebase {PG_SCHEMA}.approved_actions action_id = {a['action_id']} · lakehouse {CATALOG}.{APP_SCHEMA}.hitl_approved_actions",
    ])
    meta = {"note_id": note_id, "action_id": a["action_id"], "priority": prio, "title": a["title"],
            "entity_type": a["entity_type"], "entity_id": a["entity_id"], "created_by": a["created_by"],
            "approved_by": a["approved_by"], "approved_ts": a["approved_ts"].isoformat(), "routed_by": routed_by,
            "routing_reason": reason}
    paths = []
    TOUCHED.update(domains)
    for d in domains:
        os.makedirs(notes_path(d), exist_ok=True)
        path = f"{notes_path(d)}/{note_id}.md"
        text = AN.render({**meta, "domain": d}, body)
        with open(path, "w") as f:
            f.write(text)
        paths.append(path)
    # re-routing may move a note: drop its file from domains it no longer belongs to
    for d in DOMAINS:
        old = f"{notes_path(d)}/{note_id}.md"
        if d not in domains and os.path.exists(old):
            os.remove(old)
            TOUCHED.add(d)
    return " · ".join(paths)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4 · Process the outbox and write the outcome back to Lakebase

# COMMAND ----------

results = []
for a in pending:
    try:
        ref = apply_correction(a) if a["kind"] == "value_change" else publish_note(a)
        results.append((a, "synced", ref, None))
    except Exception as e:                                   # one bad action must not block the rest
        results.append((a, "failed", None, str(e)[:2000]))

with pg() as conn, conn.cursor() as cur:
    for a, status, ref, err in results:
        cur.execute(f"""UPDATE {PG_SCHEMA}.approved_actions
                        SET sync_status = %s, synced_ts = now(), sync_ref = %s, sync_error = %s, sync_run_id = %s
                        WHERE action_id = %s""", (status, ref, err, RUN_ID, a["action_id"]))
        cur.execute(f"INSERT INTO {PG_SCHEMA}.action_events (action_id, actor, event, detail) VALUES (%s, %s, %s, %s)",
                    (a["action_id"], ACTOR, "synced" if status == "synced" else "sync_failed",
                     json.dumps({"kind": a["kind"], "ref": ref, "error": err, "run_id": RUN_ID})))

for a, status, ref, err in results:
    print(f"{'✅' if status == 'synced' else '❌'} {a['kind']:<12} {a['entity_id']:<14} {ref or err}")
value_changes = sum(1 for a, s, *_ in results if s == "synced" and a["kind"] == "value_change")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4b · Re-sync each changed notes volume's Genie file index
# MAGIC A volume attached to a Genie space ("Analyze files in volumes", Public Preview) is indexed when it is attached and
# MAGIC when someone presses **Sync** on the source in the space — it does **not** pick up new files by itself. So after
# MAGIC writing notes, the job triggers the same sync for every volume it changed, waits for the index watermark to pass
# MAGIC the write time, and records a `searchable_in_genie` event per note: the app shows when a note can change answers.
# MAGIC
# MAGIC The index lives on the volume (every space that attaches it shares it). The endpoints are the ones the Sync button
# MAGIC calls — `POST /api/2.0/volume-indexes/<volume id>/sync`, `GET /api/2.0/volume-indexes/<volume id>` — and are not in
# MAGIC the public API reference yet; if they change, notes still land and a person can press Sync in the space.

# COMMAND ----------

import time

WAIT_S = int(N.get("index_wait_minutes", 10)) * 60
written = datetime.now(timezone.utc)
indexes = {}                                                # domain -> volume id
for d in sorted(TOUCHED):
    try:
        vid = w.volumes.read(f"{CATALOG}.{LANDING_SCHEMA}.{notes_volume(d)}").volume_id
        w.api_client.do("POST", f"/api/2.0/volume-indexes/{vid}/sync", body={})
        indexes[d] = vid
        print(f"   index sync started: {notes_volume(d)}")
    except Exception as e:
        print(f"⚠️  could not start the index sync for {notes_volume(d)} (press Sync on the source in the space): {str(e)[:200]}")

index_state = {d: "triggered" for d in indexes}
deadline = time.time() + WAIT_S
while WAIT_S and indexes and time.time() < deadline:
    time.sleep(15)
    for d, vid in list(indexes.items()):
        st = w.api_client.do("GET", f"/api/2.0/volume-indexes/{vid}")
        mark = datetime.fromisoformat(st.get("index_watermark_time", "1970-01-01T00:00:00Z").replace("Z", "+00:00"))
        if st.get("state") == "SUCCEEDED" and mark >= written:
            index_state[d] = "searchable"
            indexes.pop(d)
        elif st.get("state") not in ("RUNNING", "PENDING", "SUCCEEDED"):
            index_state[d] = f"index {st.get('state', 'unknown').lower()}"
            indexes.pop(d)
for d, state in sorted(index_state.items()):
    print(f"{'✅' if state == 'searchable' else '⏳' if state == 'triggered' else '❌'} {notes_volume(d)}: {state}")

with pg() as conn, conn.cursor() as cur:
    for a, status, ref, _ in results:
        if status != "synced" or a["kind"] != "note":
            continue
        doms = [d for d in TOUCHED if f"/{notes_volume(d)}/" in (ref or "")]
        if doms and all(index_state.get(d) == "searchable" for d in doms):
            cur.execute(f"INSERT INTO {PG_SCHEMA}.action_events (action_id, actor, event, detail) VALUES (%s, %s, %s, %s)",
                        (a["action_id"], ACTOR, "searchable_in_genie",
                         json.dumps({"volumes": [notes_volume(d) for d in doms], "run_id": RUN_ID})))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5 · Mirror the ledger to Delta (traceability in the lakehouse)
# MAGIC MERGE on the primary key: rows are inserted or updated, never deleted, so the lakehouse copy keeps every action
# MAGIC even if the Lakebase project is reset. Join `bronze_*._app_action_id` to `hitl_approved_actions.action_id`.

# COMMAND ----------

# table → (primary key, Postgres query, Delta schema). Explicit schemas: a column that is NULL in every row
# (e.g. sync_error) must still get a type.
MIRROR = {
    "hitl_actions": ("action_id",
        f"SELECT action_id::text, created_ts, created_by, action_type, entity_type, entity_id, title, details, priority, "
        f"status, source, insight_id, payload::text, reviewed_by, reviewed_ts FROM {PG_SCHEMA}.actions",
        "action_id string, created_ts timestamp, created_by string, action_type string, entity_type string, "
        "entity_id string, title string, details string, priority string, status string, source string, "
        "insight_id string, payload string, reviewed_by string, reviewed_ts timestamp"),
    "hitl_approved_actions": ("action_id",
        f"SELECT action_id::text, approved_ts, approved_by, created_ts, created_by, action_type, entity_type, entity_id, "
        f"title, details, priority, source, insight_id, payload::text, kind, target, sync_status, synced_ts, sync_ref, "
        f"sync_error, sync_run_id FROM {PG_SCHEMA}.approved_actions",
        "action_id string, approved_ts timestamp, approved_by string, created_ts timestamp, created_by string, "
        "action_type string, entity_type string, entity_id string, title string, details string, priority string, "
        "source string, insight_id string, payload string, kind string, target string, sync_status string, "
        "synced_ts timestamp, sync_ref string, sync_error string, sync_run_id string"),
    "hitl_action_events": ("event_id",
        f"SELECT event_id, action_id::text, event_ts, actor, event, detail::text FROM {PG_SCHEMA}.action_events",
        "event_id bigint, action_id string, event_ts timestamp, actor string, event string, detail string"),
}
COMMENTS = {"hitl_actions": "Every action submitted in the app (mirror of Lakebase hitl.actions).",
            "hitl_approved_actions": "Approved actions and where each landed: sync_ref = correction table row or note file (mirror of hitl.approved_actions).",
            "hitl_action_events": "Audit trail of every action state change, including the sync (mirror of hitl.action_events)."}

with pg() as conn, conn.cursor() as cur:
    for table, (key, query, schema) in MIRROR.items():
        cur.execute(query)
        data = cur.fetchall()
        if not data:
            continue
        df = spark.createDataFrame(data, schema=schema)
        name = f"{CATALOG}.{APP_SCHEMA}.{table}"
        if spark.catalog.tableExists(name):
            (DeltaTable.forName(spark, name).alias("t").merge(df.alias("s"), f"t.{key} = s.{key}")
             .whenMatchedUpdateAll().whenNotMatchedInsertAll().execute())
        else:
            df.write.saveAsTable(name)
            spark.sql(f"COMMENT ON TABLE {name} IS '{sql_str(COMMENTS[table])}'")
        print(f"{name}: {spark.table(name).count()} rows")

# COMMAND ----------

# The job's next task refreshes the medallion pipeline only when corrections landed (condition task).
try:
    dbutils.jobs.taskValues.set(key="value_changes", value=value_changes)
except Exception:
    pass
print(f"value changes written: {value_changes} · notes published: "
      f"{sum(1 for a, s, *_ in results if s == 'synced' and a['kind'] == 'note')} · failed: "
      f"{sum(1 for _, s, *_ in results if s == 'failed')}")
