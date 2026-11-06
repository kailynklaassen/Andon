"""
The run log — one row per Foreman run, for the App & agent health page (Lakebase, next to sessions and memory).
=============================================================================================================

Why a table AND traces: the MLflow trace (in Unity Catalog) is the full record of a run — every span, prompt and
token — and is what you open to debug one answer. This log is the small, fast summary an operations page needs:
who asked, in which conversation, how long it took, which Genie spaces were asked (and how long each took), and
what went wrong. It answers "is the agent healthy, and who is hitting errors?" in milliseconds, links each row to
its trace, and keeps working even if trace ingestion lags.

    foreman.runs   run_id (= trace id) · session · user · question · status (ok | error | stopped)
                   · error · duration · genie_auth (on_behalf_of_user | service_principal) · steps (jsonb, one per
                   Genie call: space, seconds, status, error, rows)

Never logged: tokens, answers' data rows (the trace has them, governed by Unity Catalog).
"""
from __future__ import annotations

import json

from memory import SCHEMA

DDL = """
CREATE TABLE IF NOT EXISTS {s}.runs (
  run_id      text PRIMARY KEY,                       -- the MLflow trace id (or a uuid if tracing is off)
  session_id  text,
  user_email  text,
  question    text,
  status      text NOT NULL CHECK (status IN ('ok', 'error', 'stopped')),
  error       text,
  started_ts  timestamptz NOT NULL,
  duration_ms integer,
  genie_auth  text,                                   -- who Genie ran as for this run
  router_llm  text,
  answer_llm  text,
  steps       jsonb NOT NULL DEFAULT '[]'
);
CREATE INDEX IF NOT EXISTS runs_started ON {s}.runs (started_ts DESC);
CREATE INDEX IF NOT EXISTS runs_user ON {s}.runs (user_email, started_ts DESC);
"""


class RunLog:
    """Writes and reads foreman.runs over the Memory store's connection (one Lakebase connection per process)."""

    def __init__(self, store):
        self.store = store
        store._exec(DDL.format(s=SCHEMA))

    def record(self, run: dict) -> None:
        try:
            self.store._exec(
                f"""INSERT INTO {SCHEMA}.runs (run_id, session_id, user_email, question, status, error, started_ts,
                                               duration_ms, genie_auth, router_llm, answer_llm, steps)
                    VALUES (%s, %s, %s, %s, %s, %s, to_timestamp(%s), %s, %s, %s, %s, %s)
                    ON CONFLICT (run_id) DO UPDATE SET status = EXCLUDED.status, error = EXCLUDED.error,
                                                       duration_ms = EXCLUDED.duration_ms, steps = EXCLUDED.steps""",
                (run["run_id"], run.get("session_id"), run.get("user"), (run.get("question") or "")[:1000],
                 run["status"], (run.get("error") or None) and str(run["error"])[:2000], run["started"],
                 run.get("duration_ms"), run.get("genie_auth"), run.get("router_llm"), run.get("answer_llm"),
                 json.dumps(run.get("steps", []), default=str)))
        except Exception as e:                       # observability must never break a conversation
            print(f"run log: {e}")

    def runs(self, user: str = "", session_id: str = "", status: str = "", hours: int = 168, limit: int = 200) -> list[dict]:
        where, params = ["started_ts > now() - make_interval(hours => %s)"], [hours]
        for col, val in (("user_email", user), ("session_id", session_id), ("status", status)):
            if val:
                where.append(f"{col} = %s")
                params.append(val)
        rows = self.store._exec(
            f"""SELECT run_id, session_id, user_email, question, status, error, started_ts, duration_ms, genie_auth, steps
                FROM {SCHEMA}.runs WHERE {' AND '.join(where)} ORDER BY started_ts DESC LIMIT %s""",
            (*params, limit), fetch=True)
        keys = ["run_id", "session_id", "user", "question", "status", "error", "started_ts", "duration_ms", "genie_auth", "steps"]
        return [{**dict(zip(keys, r)), "started_ts": r[6].isoformat()} for r in rows]

    def summary(self, hours: int = 168) -> dict:
        """Headline health numbers, per-user and per-Genie-space breakdowns for the last `hours`."""
        q = lambda sql: self.store._exec(sql, (hours,), fetch=True)
        since = "started_ts > now() - make_interval(hours => %s)"
        issue = """(status = 'error' OR steps @> '[{"status": "error"}]')"""   # the run failed, or one of its Genie calls did
        total, errors, stopped, p50, p95 = q(f"""
            SELECT count(*), count(*) FILTER (WHERE {issue}), count(*) FILTER (WHERE status = 'stopped'),
                   percentile_cont(0.5) WITHIN GROUP (ORDER BY duration_ms), percentile_cont(0.95) WITHIN GROUP (ORDER BY duration_ms)
            FROM {SCHEMA}.runs WHERE {since}""")[0]
        users = q(f"""SELECT user_email, count(*), count(*) FILTER (WHERE {issue}), count(DISTINCT session_id),
                             avg(duration_ms), max(started_ts)
                      FROM {SCHEMA}.runs WHERE {since} GROUP BY user_email ORDER BY count(*) DESC""")
        spaces = q(f"""SELECT s->>'space', count(*), count(*) FILTER (WHERE s->>'status' = 'error'),
                              avg((s->>'seconds')::float), percentile_cont(0.95) WITHIN GROUP (ORDER BY (s->>'seconds')::float)
                       FROM {SCHEMA}.runs, jsonb_array_elements(steps) s WHERE {since} GROUP BY 1 ORDER BY 2 DESC""")
        return {
            "hours": hours, "runs": total, "errors": errors, "stopped": stopped,   # errors = runs with an issue
            "p50_s": round((p50 or 0) / 1000, 1), "p95_s": round((p95 or 0) / 1000, 1),
            "users": [{"user": u, "runs": n, "errors": e, "sessions": s, "avg_s": round((a or 0) / 1000, 1),
                       "last": t.isoformat()} for u, n, e, s, a, t in users],
            "genie_spaces": [{"space": sp, "calls": n, "errors": e, "avg_s": round(a or 0, 1), "p95_s": round(p or 0, 1)}
                             for sp, n, e, a, p in spaces],
        }
