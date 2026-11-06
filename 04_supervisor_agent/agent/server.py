"""
Foreman agent server — AgentKit DurableAgentServer on Databricks Apps (app: kkparts-foreman).
==============================================================================================

The host Databricks recommends for new agents is the Agent Server: AgentKit's `DurableAgentServer`
(package `databricks-agentbricks`, GA). This file is the host only — the agent itself is foreman.py, sessions/memory are
memory.py, the health page's run log is runlog.py. (Custom FastAPI orchestrators and the MLflow/ai-bridge servers are
the legacy path.)

    POST /api/invocations               run one question. Body: {id: <uuid>, session_id, stream: true,
                                        input: {question, context?, user?}} → Server-Sent Events, each a Foreman event:
                                        step · step_update · step_done · token · answer · heartbeat · done | error
    GET  /api/invocations/{id}          status / final output        GET .../{id}/events?after=N   reconnect a stream
    GET  /api/sessions                  this user's conversations    GET /api/sessions/{id}   its turns
    GET  /api/memories                  what Foreman remembers       DELETE /api/memories/{id}  forget one
    GET  /api/info · /api/runs · /api/runs/summary · /api/health

WHAT THE AGENT SERVER ADDS (vs. a plain FastAPI streaming endpoint)
* Durable runs. Every invocation, its events and its result live in a Runtime Store — here a Lakebase schema
  (`foreman_runtime`) in this app's own `postgres` resource. A client that loses its connection (closed tab, proxy
  timeout, redeploy) reconnects to GET .../events?after=<last id> and gets the rest; the answer isn't lost.
* Idempotency: the client's `id` is the key, so a retried request never runs the question twice.
* Sessions: invocations with the same `session_id` run one at a time, in order (that's the conversation).
* The same protocol for every agent on Databricks, so clients and tooling don't need a custom contract.

THE GA ROUTE: the GA Agent Server, deployed WITHOUT the Agent Bricks CLI (the CLI is Beta). The Runtime Store comes from
this app's own Postgres resource: DATABRICKS_AGENTBRICKS_RUNTIME_STORE_LAKEBASE_ENDPOINT + DATABRICKS_AGENTBRICKS_RUNTIME_STORE_SCHEMA
(app.yaml, rendered by 02_deploy_agent_app). The SDK supports this pair in code (runtime/store.py, from_app_resource,
which it labels the "legacy Apps resource" path); the public docs describe only the store the CLI provisions, so
databricks-agentbricks is pinned and re-tested on upgrade. With neither set (local runs) it uses an in-memory store.

WHO IS THE USER / WHO GENIE RUNS AS (supervisor.genie_auth = on_behalf_of_user)
Requests come from the Andon app's backend (its service principal), which passes the signed-in person's email as
input.user and their Genie-scoped token in the X-Foreman-User-Token header. The token is held IN MEMORY for that one
invocation (never written to the Runtime Store) and used only for that question's Genie calls; models, Lakebase and
traces run as this app's service principal. Only identities with CAN_USE on this app can reach it. (AgentKit's own
request-user auth reads the CALLER's x-forwarded-access-token — that would be the Andon app, not the person — so the
person's token is forwarded explicitly.) An interrupted run can't be recovered on the person's behalf: recovery tells
the client to ask again, exactly as AgentKit does for request-user runs.

"""
from __future__ import annotations

import asyncio
import atexit
import json
import os
import threading
import time
from pathlib import Path

import mlflow
import yaml
from databricks_agentkit import DurableAgentServer, InvocationContext
from fastapi import HTTPException, Request

from foreman import Foreman

HERE = Path(__file__).parent
CONFIG = yaml.safe_load((HERE / "supervisor_config.yaml").read_text())   # written by build_config.py (02_deploy_agent_app)
CONFIG["router_llm"] = os.getenv("FOREMAN_ROUTER_LLM") or CONFIG.get("router_llm")
CONFIG["answer_llm"] = os.getenv("FOREMAN_ANSWER_LLM") or CONFIG.get("answer_llm")
CONFIG["genie_auth"] = os.getenv("FOREMAN_GENIE_AUTH") or CONFIG.get("genie_auth") or "service_principal"
CONFIG["genie_mode"] = os.getenv("FOREMAN_GENIE_MODE") or CONFIG.get("genie_mode") or "agent"

# --- tracing (CRUCIAL): every request becomes one MLflow trace in the app's experiment ---------------------------
# The experiment is bound to Unity Catalog tables (<catalog>.<schema>.<prefix>_otel_*, GA): spans are exported to the
# workspace's OTel endpoint and land in Delta, queryable with SQL. MLFLOW_TRACING_SQL_WAREHOUSE_ID is the warehouse
# the MLflow UI and SDK use to read them back.
os.environ.setdefault("MLFLOW_ENABLE_ASYNC_LOGGING", "true")      # never make the user wait for trace upload
mlflow.set_tracking_uri("databricks")
if os.getenv("MLFLOW_EXPERIMENT_ID"):
    mlflow.set_experiment(experiment_id=os.environ["MLFLOW_EXPERIMENT_ID"])
mlflow.openai.autolog()                                                  # a span for every model call
atexit.register(mlflow.flush_trace_async_logging)                        # don't lose queued traces on shutdown

# --- sessions + memory (Lakebase) — optional: the agent works without them ------------------------------------------
memory = runlog = None
if os.getenv("PGHOST"):
    from memory import Memory, lakebase_connector
    from runlog import RunLog
    memory = Memory(lakebase_connector())
    runlog = RunLog(memory)                                              # the health page's run summaries

AGENT = Foreman(CONFIG, memory=memory, runlog=runlog)
app = DurableAgentServer()                     # Runtime Store from the environment (Lakebase on Apps, in-memory locally)

# --- the person's Genie token: in memory, per invocation, never persisted --------------------------------------------
_USER_TOKENS: dict[str, tuple[str, float]] = {}       # invocation id → (token, received at)
_TOKENS_LOCK = threading.Lock()
_TOKEN_TTL_S = 15 * 60


class _CaptureUserToken:
    """ASGI middleware: remember X-Foreman-User-Token for the invocation id in the request body.
    The body is buffered and replayed unchanged, so the Agent Server handles the request as usual."""

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] != "POST" or scope["path"] != "/api/invocations":
            return await self.inner(scope, receive, send)
        token = dict(scope["headers"]).get(b"x-foreman-user-token", b"").decode().strip()
        if not token:
            return await self.inner(scope, receive, send)
        chunks, more = [], True
        while more:
            message = await receive()
            chunks.append(message.get("body", b""))
            more = message.get("more_body", False)
        body = b"".join(chunks)
        try:
            invocation_id = str(json.loads(body or b"{}").get("id", ""))
        except ValueError:
            invocation_id = ""
        if invocation_id:
            with _TOKENS_LOCK:
                now = time.time()
                for k in [k for k, (_, t) in _USER_TOKENS.items() if now - t > _TOKEN_TTL_S]:
                    _USER_TOKENS.pop(k, None)
                _USER_TOKENS[invocation_id] = (token, now)
        sent = False

        async def replay():
            nonlocal sent
            if sent:
                return await receive()
            sent = True
            return {"type": "http.request", "body": body, "more_body": False}

        return await self.inner(scope, replay, send)


app.add_middleware(_CaptureUserToken)


def _take_user_token(invocation_id: str) -> str | None:
    with _TOKENS_LOCK:
        entry = _USER_TOKENS.pop(invocation_id, None)
    return entry[0] if entry else None


# --- the agent: one invocation = one Foreman run ---------------------------------------------------------------------
_TOKEN_FLUSH_S = 0.25          # stream tokens in small batches: each event is a Runtime Store write


@app.invoke
async def invoke(input: dict, context: InvocationContext) -> dict:
    """Run Foreman on a worker thread and emit each of its events through the Agent Server (persisted + streamed)."""
    if not isinstance(input, dict) or not str(input.get("question", "")).strip():
        raise ValueError("input must be an object with a non-empty 'question'")
    loop = asyncio.get_running_loop()
    events: asyncio.Queue = asyncio.Queue()
    DONE = object()
    genie_token = _take_user_token(context.invocation_id)

    def work():
        try:
            for ev in AGENT.run(str(input["question"])[:4000], context=str(input.get("context", "")),
                                session_id=context.session_id, user=str(input.get("user", "")),
                                genie_token=genie_token):
                loop.call_soon_threadsafe(events.put_nowait, ev)
        finally:
            loop.call_soon_threadsafe(events.put_nowait, DONE)

    worker = asyncio.create_task(asyncio.to_thread(work))
    final: dict = {"answer": "", "session_id": context.session_id}
    pending_text, last_flush = "", time.monotonic()

    async def flush():
        nonlocal pending_text, last_flush
        if pending_text:
            await context.emit({"type": "token", "text": pending_text})
            pending_text = ""
        last_flush = time.monotonic()

    while True:
        ev = await events.get()
        if ev is DONE:
            break
        if ev.get("type") == "token":                      # batch tokens: fewer writes, same live feel
            pending_text += ev.get("text", "")
            if time.monotonic() - last_flush >= _TOKEN_FLUSH_S:
                await flush()
            continue
        await flush()
        if ev.get("type") == "answer":
            final["answer"] = ev.get("text", "")
        elif ev.get("type") == "done":
            final.update(session_id=ev.get("session_id"), trace_id=ev.get("trace_id"), elapsed_ms=ev.get("elapsed_ms"))
        await context.emit(ev)
    await flush()
    await worker
    return final


@app.recover
async def recover(input: dict, context: InvocationContext) -> dict:
    """A worker stopped mid-answer (restart, redeploy). The person's Genie token was never stored, so the question
    can't be re-run on their behalf: say so, durably, and let the client ask again."""
    message = "Foreman restarted while answering this question. Please ask it again."
    await context.emit({"type": "error", "message": message, "recoverable": False})
    return {"answer": "", "interrupted": True, "message": message}


# --- the rest of the API (plain FastAPI routes on the same app) -------------------------------------------------------
def _user(request: Request, claimed: str = "") -> str:
    return claimed or request.headers.get("X-Forwarded-Email") or ""


@app.get("/api/health")
def health():
    return {"ok": True, "memory": memory is not None, "server": "agentkit.DurableAgentServer"}


@app.get("/api/info")
def info():
    host = os.getenv("DATABRICKS_HOST", "").rstrip("/")
    host = host if host.startswith("http") else f"https://{host}" if host else ""
    exp = os.getenv("MLFLOW_EXPERIMENT_ID", "")
    return {"router_llm": AGENT.router_llm, "answer_llm": AGENT.answer_llm,
            "tools": [{"name": s["title"], "domain": s["domain_key"]} for s in AGENT.spaces],
            "experiment_id": exp, "traces_url": f"{host}/ml/experiments/{exp}/traces" if exp and host else "",
            "trace_tables": os.getenv("FOREMAN_TRACE_TABLES", ""), "genie_auth": AGENT.genie_auth,
            "genie_mode": AGENT.genie_mode, "server": "agentkit.DurableAgentServer",
            "protocol": "POST /api/invocations (stream)", "memory": memory is not None}


@app.get("/api/sessions")
def sessions(request: Request, user: str = ""):
    if not memory:
        return []
    return memory.sessions(_user(request, user))


@app.get("/api/sessions/{session_id}")
def session_turns(session_id: str):
    if not memory:
        raise HTTPException(404, "sessions are not enabled (no Lakebase resource)")
    return memory.turns(session_id)


@app.get("/api/memories")
def memories(request: Request, user: str = ""):
    if not memory:
        return []
    return memory.memories(_user(request, user))


@app.delete("/api/memories/{memory_id}")
def forget(memory_id: int, request: Request, user: str = ""):
    if not memory:
        raise HTTPException(404, "memory is not enabled (no Lakebase resource)")
    memory.forget(_user(request, user), memory_id)
    return {"ok": True}


@app.get("/api/runs")
def runs(user: str = "", session_id: str = "", status: str = "", hours: int = 168, limit: int = 200):
    """The run log. The calling app decides who may see it (Andon: admins only)."""
    return runlog.runs(user=user, session_id=session_id, status=status, hours=hours, limit=min(limit, 1000)) if runlog else []


@app.get("/api/runs/summary")
def runs_summary(hours: int = 168):
    if not runlog:
        raise HTTPException(404, "the run log needs the Lakebase resource")
    return runlog.summary(hours)
