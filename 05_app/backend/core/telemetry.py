"""App-side issues for the App & agent health page: what went wrong in THIS app, for whom, on which page.

Foreman logs its own runs (foreman.runs: every question, its Genie calls, errors, timings). This module covers the
other half — failures the agent never sees: an API route that crashed, Foreman unreachable, a stream cut off
mid-answer, an error the browser hit. One row each, keyed by user, so "who is having a bad time?" is one query.

    <hitl schema>.app_events   event_ts · user_email · kind · route · message · detail (jsonb)
    kinds: api_error | foreman_unreachable | client_error

Lakebase when the app has it (same connection as the ledger), otherwise data/app_events.jsonl for laptop runs.
Never stores tokens or request bodies beyond a short question preview.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

from backend.core import ledger as L

LOCAL_FILE = Path(__file__).resolve().parents[2] / "data" / "app_events.jsonl"
DDL = """
CREATE TABLE IF NOT EXISTS {s}.app_events (
  event_id   bigserial PRIMARY KEY,
  event_ts   timestamptz NOT NULL DEFAULT now(),
  user_email text,
  kind       text NOT NULL,                      -- api_error | foreman_unreachable | client_error
  route      text,
  message    text,
  detail     jsonb NOT NULL DEFAULT '{{}}'
);
CREATE INDEX IF NOT EXISTS app_events_ts ON {s}.app_events (event_ts DESC);
"""
_READY: list = []


def _ensure() -> None:
    if not _READY:
        L._ensure_schema()
        L._run(lambda cur: cur.execute(DDL.format(s=L.SCHEMA)))
        _READY.append(True)


def record(kind: str, user: str, route: str, message: str, detail: dict | None = None) -> None:
    """Best effort: logging an issue must never cause one."""
    try:
        if L.backend() == "lakebase":
            _ensure()
            L._run(lambda cur: cur.execute(
                f"INSERT INTO {L.SCHEMA}.app_events (user_email, kind, route, message, detail) VALUES (%s, %s, %s, %s, %s)",
                (user, kind, route, message[:2000], json.dumps(detail or {}, default=str))))
        else:
            LOCAL_FILE.parent.mkdir(parents=True, exist_ok=True)
            with LOCAL_FILE.open("a") as f:
                f.write(json.dumps({"event_ts": datetime.now(timezone.utc).isoformat(), "user": user, "kind": kind,
                                    "route": route, "message": message[:2000], "detail": detail or {}}) + "\n")
    except Exception as e:
        print(f"telemetry: {e}")


def events(hours: int = 168, limit: int = 300) -> list[dict]:
    if L.backend() == "lakebase":
        _ensure()
        def select(cur):
            cur.execute(f"SELECT event_ts, user_email, kind, route, message, detail::text FROM {L.SCHEMA}.app_events "
                        f"WHERE event_ts > now() - make_interval(hours => %s) ORDER BY event_ts DESC LIMIT %s", (hours, limit))
            return cur.fetchall()
        return [{"event_ts": t.isoformat(), "user": u, "kind": k, "route": r, "message": m, "detail": json.loads(d or "{}")}
                for t, u, k, r, m, d in L._run(select)]
    if not LOCAL_FILE.exists():
        return []
    cutoff = time.time() - hours * 3600
    rows = [json.loads(l) for l in LOCAL_FILE.read_text().splitlines() if l.strip()]
    rows = [r for r in rows if datetime.fromisoformat(r["event_ts"]).timestamp() >= cutoff]
    return list(reversed(rows))[:limit]
