"""
Sessions and long-term memory for Foreman, in Lakebase (Postgres) — GA building blocks only.
=========================================================================================

Databricks also offers *managed* agent sessions and memory (AgentKit, also Lakebase-backed). They are Beta as of
2026-11, and this accelerator uses GA / Public Preview only, so we build the same two stores directly on Lakebase.
The shapes match the managed feature, so moving later is a storage swap, not a redesign.

    SESSIONS  (short-term)  foreman.sessions + foreman.turns
              One row per conversation and one per turn. The server loads the last turns of a session, so a
              client only sends `session_id` — the conversation survives page reloads, devices and restarts.
    MEMORY    (long-term)   foreman.memories
              Durable facts a USER told Foreman ("I run the Greenville plant", "send me numbers in metric").
              After each turn a fast model distills 0-2 such facts off the hot path; the next conversation recalls
              the relevant ones with Postgres full-text search (no embedding endpoint needed).

WHAT MEMORY IS NOT FOR (crucial): data. "WC01 vibration is 8.75 mm/s" must never be remembered — it would go stale
and bypass Unity Catalog. Data always comes from Genie at answer time. The distill prompt enforces this.

The app's service principal creates and owns schema `foreman` on first use (Lakebase resource on the app,
CAN_CONNECT_AND_CREATE). Every row carries the trace id, so a memory can be traced to the conversation it came from.
"""
from __future__ import annotations

import json
import os
import re
import threading
import time

SCHEMA = os.getenv("FOREMAN_SCHEMA", "foreman")

DDL = """
CREATE SCHEMA IF NOT EXISTS {s};
CREATE TABLE IF NOT EXISTS {s}.sessions (
  session_id  text PRIMARY KEY,
  user_email  text,
  title       text,                                  -- the first question, for a session list
  created_ts  timestamptz NOT NULL DEFAULT now(),
  updated_ts  timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS {s}.turns (
  turn_id     bigserial PRIMARY KEY,
  session_id  text NOT NULL REFERENCES {s}.sessions (session_id),
  role        text NOT NULL CHECK (role IN ('user', 'assistant')),
  content     text NOT NULL,
  trace_id    text,                                  -- the MLflow trace of the run that produced this turn
  created_ts  timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS turns_session ON {s}.turns (session_id, turn_id);
CREATE TABLE IF NOT EXISTS {s}.memories (
  memory_id   bigserial PRIMARY KEY,
  user_email  text NOT NULL,
  fact        text NOT NULL,
  session_id  text,                                  -- where it was learned
  trace_id    text,
  created_ts  timestamptz NOT NULL DEFAULT now(),
  tsv         tsvector GENERATED ALWAYS AS (to_tsvector('english', fact)) STORED,
  UNIQUE (user_email, fact)
);
CREATE INDEX IF NOT EXISTS memories_tsv ON {s}.memories USING gin (tsv);
"""

DISTILL_PROMPT = """You maintain an assistant's long-term memory about ONE user of a manufacturing operations app.
From the user's message below, extract at most 2 durable facts ABOUT THE USER: their role, the plant/line/supplier
they own, preferences for how answers are written, standing instructions.
Never extract data values, metrics, statuses or anything that could change in the data (those come from the data
platform at answer time). Most messages contain nothing worth remembering.
Reply with only a JSON list of short third-person sentences, e.g. ["Runs the Greenville plant."] or [].

User message:
{message}"""


class Memory:
    """Sessions + memory over one Lakebase database. Connections refresh their OAuth token every 45 minutes."""

    TOKEN_TTL_S = 45 * 60

    def __init__(self, connect):
        self._connect = connect                         # () -> new psycopg connection (fresh credential)
        self._lock = threading.Lock()
        self._conn, self._opened = None, 0.0
        self._exec(DDL.format(s=SCHEMA))

    # -------------------------------------------------------------- plumbing
    def _exec(self, sql: str | list[tuple], params=None, fetch: bool = False):
        """Run one statement, or a list of (sql, params) in ONE transaction (psycopg binds one statement at a time)."""
        import psycopg
        stmts = sql if isinstance(sql, list) else [(sql, params)]
        for attempt in (1, 2):                          # reconnect once after scale-to-zero / idle timeout
            with self._lock:
                if self._conn is None or self._conn.closed or time.time() - self._opened > self.TOKEN_TTL_S:
                    self._conn, self._opened = self._connect(), time.time()
                try:
                    with self._conn.transaction(), self._conn.cursor() as cur:
                        for q, p in stmts:
                            cur.execute(q, p)
                        return cur.fetchall() if fetch else None
                except psycopg.OperationalError:
                    self._conn = None
                    if attempt == 2:
                        raise

    # -------------------------------------------------------------- sessions
    def history(self, session_id: str, limit: int = 8) -> list[dict]:
        rows = self._exec(f"SELECT role, content FROM (SELECT role, content, turn_id FROM {SCHEMA}.turns "
                          f"WHERE session_id = %s ORDER BY turn_id DESC LIMIT %s) t ORDER BY turn_id",
                          (session_id, limit), fetch=True)
        return [{"role": r, "content": c} for r, c in rows]

    def save_turn(self, session_id: str, user: str, question: str, answer: str, trace_id: str | None) -> None:
        self._exec([
            (f"INSERT INTO {SCHEMA}.sessions (session_id, user_email, title) VALUES (%s, %s, %s) "
             f"ON CONFLICT (session_id) DO UPDATE SET updated_ts = now()", (session_id, user, question[:200])),
            (f"INSERT INTO {SCHEMA}.turns (session_id, role, content, trace_id) VALUES (%s, 'user', %s, %s), "
             f"(%s, 'assistant', %s, %s)", (session_id, question, trace_id, session_id, answer, trace_id)),
        ])

    def sessions(self, user: str, limit: int = 20) -> list[dict]:
        rows = self._exec(f"SELECT session_id, title, updated_ts FROM {SCHEMA}.sessions WHERE user_email = %s "
                          f"ORDER BY updated_ts DESC LIMIT %s", (user, limit), fetch=True)
        return [{"session_id": s, "title": t, "updated_ts": u.isoformat()} for s, t, u in rows]

    def turns(self, session_id: str) -> list[dict]:
        rows = self._exec(f"SELECT role, content, trace_id, created_ts FROM {SCHEMA}.turns WHERE session_id = %s "
                          f"ORDER BY turn_id", (session_id,), fetch=True)
        return [{"role": r, "content": c, "trace_id": t, "created_ts": ts.isoformat()} for r, c, t, ts in rows]

    # -------------------------------------------------------------- long-term memory
    def recall(self, user: str, question: str, limit: int = 5) -> list[str]:
        """Facts about this user relevant to the question (full-text match, any word), newest first as tie-break."""
        words = [w for w in re.findall(r"[a-zA-Z0-9]{3,}", question.lower())][:20]
        if not user or not words:
            return []
        rows = self._exec(f"""
            SELECT fact FROM {SCHEMA}.memories
            WHERE user_email = %s AND tsv @@ to_tsquery('english', %s)
            ORDER BY ts_rank(tsv, to_tsquery('english', %s)) DESC, created_ts DESC LIMIT %s""",
                          (user, " | ".join(words), " | ".join(words), limit), fetch=True)
        return [r[0] for r in rows]

    def remember(self, llm, model: str, user: str, session_id: str, message: str, trace_id: str | None) -> None:
        """Distill durable facts about the user from their message (runs on a background thread)."""
        if not user:
            return
        import mlflow
        try:
            # runs after the answer, outside the run's trace: its own small trace, tagged with the same session and
            # user so it groups with the conversation instead of floating loose in the experiment
            with mlflow.start_span(name="foreman · remember") as span:
                mlflow.update_current_trace(metadata={"mlflow.trace.session": session_id, "mlflow.trace.user": user},
                                            tags={"kind": "memory"})
                span.set_inputs({"source_trace": trace_id})
                facts = self._distill(llm, model, message)
                span.set_outputs({"facts": facts})
            for f in facts[:2]:
                self._exec(f"INSERT INTO {SCHEMA}.memories (user_email, fact, session_id, trace_id) "
                           f"VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING", (user, str(f)[:300], session_id, trace_id))
        except Exception:
            pass                                        # memory is best-effort; never fail a conversation over it

    @staticmethod
    def _distill(llm, model: str, message: str) -> list:
        try:
            out = llm.chat.completions.create(model=model, max_tokens=1000, messages=[   # reasoning models think first
                {"role": "user", "content": DISTILL_PROMPT.format(message=message)}]).choices[0].message.content
            text = out if isinstance(out, str) else "".join(b.get("text", "") for b in out if isinstance(b, dict))
            return json.loads(re.search(r"\[.*\]", text, re.S).group(0)) if "[" in text else []
        except Exception:
            return []

    def memories(self, user: str) -> list[dict]:
        rows = self._exec(f"SELECT memory_id, fact, created_ts FROM {SCHEMA}.memories WHERE user_email = %s "
                          f"ORDER BY created_ts DESC", (user,), fetch=True)
        return [{"memory_id": i, "fact": f, "created_ts": t.isoformat()} for i, f, t in rows]

    def forget(self, user: str, memory_id: int) -> None:
        self._exec(f"DELETE FROM {SCHEMA}.memories WHERE user_email = %s AND memory_id = %s", (user, memory_id))


def lakebase_connector():
    """A connect() for Memory, from the Lakebase resource the platform injects on Databricks Apps
    (PGHOST/PGDATABASE/PGUSER) plus an OAuth database credential for the app's identity."""
    import psycopg
    from databricks.sdk import WorkspaceClient

    def connect():
        w = WorkspaceClient()
        token = w.postgres.generate_database_credential(endpoint=os.environ["LAKEBASE_ENDPOINT_PATH"]).token
        return psycopg.connect(host=os.environ["PGHOST"], port=int(os.getenv("PGPORT", "5432")),
                               dbname=os.getenv("PGDATABASE", "databricks_postgres"),
                               user=os.getenv("PGUSER") or w.current_user.me().user_name,
                               password=token, sslmode=os.getenv("PGSSLMODE", "require"))
    return connect
