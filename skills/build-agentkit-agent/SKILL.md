---
name: build-agentkit-agent
description: Build any custom agent in Python on the Databricks Agent Server — the AgentKit Python SDK's DurableAgentServer (package databricks-agentbricks, module databricks_agentkit) — hosted on Databricks Apps and deployed WITHOUT the Beta Agent Bricks CLI (Apps REST API or DABs). Covers the invoke/recover handlers, streaming events, durable runs and reconnect, sessions, calling Foundation Model API models and tools, wiring several Genie spaces together as parallel domain-expert tools (Agent mode or Chat mode / AgentKit GenieAgent), on-behalf-of-user auth, MLflow tracing to Unity Catalog, deployment and evaluation. Use when someone wants a new custom agent, wants to move a custom FastAPI / MLflow AgentServer / ResponsesAgent / Model Serving agent onto the Agent Server, or asks how to use DurableAgentServer. For a full worked supervisor over Genie spaces (spaces as code, notes by priority), also load build-custom-supervisor.
---

# Build a custom agent on the Agent Server (AgentKit `DurableAgentServer`)

You are helping a Databricks user build a **custom agent**: their own Python agent loop, hosted on the **Agent Server**
(AgentKit's `DurableAgentServer`) as a Databricks App. This skill is domain-neutral. A complete worked example is
`04_supervisor_agent/agent/server.py` + `foreman.py` in the KK's Parts demo repo (a supervisor over Genie spaces).

## 0 · Platform facts (as of 2026-11; re-check release stages before you start)
| Piece | What it is | Status |
|---|---|---|
| **AgentKit Python SDK** | PyPI `databricks-agentbricks` (≥ 0.8), imported as `databricks_agentkit`. Contains the runtime (`DurableAgentServer`, `InvocationContext`, `workspace_client`, tracing helpers) **and** clients for managed session/memory stores (`AgentKitClient`, `SessionStore`, `MemoryStore`). | Runtime / Agent Server: **GA** (product-confirmed) |
| Agent Bricks CLI (`agentbricks init/dev/deploy`) | Scaffolds, runs and deploys AgentKit projects; provisions the Runtime Store for you. | **Beta** — don't depend on it for a GA build |
| Agent sessions / agent memory (`client.session_stores`, `client.memory_stores`) | Managed short-term history / long-term memory in Lakebase. | **Beta** (admin enables "Agent Memory Sessions") |
| Legacy hosts | Custom FastAPI orchestrators, MLflow `AgentServer` + `ResponsesAgent`, `databricks_ai_bridge` `LongRunningAgentServer`, Model Serving agents. | Legacy for new agents |

**GA-only route = the GA Agent Server, deployed without the CLI.** If the user's rule is "GA / Public Preview only",
keep sessions and memory in your own Lakebase tables (GA) instead of the Beta managed stores.

Docs: <https://docs.databricks.com/aws/en/agents/deploy/agent-server> (Agent Server) ·
`/agents/deploy/agent-runtime` · `/agents/agent-memory/managed-sessions` · `/agents/agent-memory/managed-memory` ·
`/dev-tools/databricks-apps/auth` · `/mlflow3/genai/tracing/trace-unity-catalog`. The SDK ships its own design notes:
`databricks_agentkit/runtime/README.md` and `ARCHITECTURE.md` in the installed package — read them when the docs are thin.

## 1 · Project layout (one Databricks App)
```
agent/
  app.yaml            command + env (rendered by the deploy step from config; IDs via valueFrom)
  requirements.txt    databricks-agentbricks>=0.8, fastapi>=0.129, uvicorn[standard], mlflow[databricks]>=3.14,
                      databricks-sdk, databricks-openai, psycopg[binary] (if you use Lakebase yourself)
  server.py           the HOST: DurableAgentServer + handlers + any extra routes — no agent logic
  agent.py            the AGENT: a plain Python loop that yields events (testable without a server)
```
Keep the agent framework-free (or LangGraph / OpenAI Agents SDK if the team prefers; AgentKit has
`databricks_agentkit.langgraph` and `.openai` helpers). One implementation of the loop; hosts and eval wrap it.

## 2 · The server — minimal, correct
```python
# server.py
import asyncio, os
import mlflow
from databricks_agentkit import DurableAgentServer, InvocationContext
from agent import MyAgent                                  # your loop: run(question, ...) -> Iterator[dict]

mlflow.set_tracking_uri("databricks")
if os.getenv("MLFLOW_EXPERIMENT_ID"):
    mlflow.set_experiment(experiment_id=os.environ["MLFLOW_EXPERIMENT_ID"])
mlflow.openai.autolog()                                    # a span per model call

AGENT = MyAgent(...)
app = DurableAgentServer()            # a FastAPI app; Runtime Store chosen from the environment (section 4)

@app.invoke                           # REQUIRED — the server won't start without it
async def invoke(input: dict, context: InvocationContext) -> dict:
    # input = whatever the client sent as "input" (persisted! never put credentials in it)
    loop, q, DONE = asyncio.get_running_loop(), asyncio.Queue(), object()

    def work():                       # blocking agent code runs on a thread, events bridged to the loop
        try:
            for ev in AGENT.run(input["question"], session_id=context.session_id):
                loop.call_soon_threadsafe(q.put_nowait, ev)
        finally:
            loop.call_soon_threadsafe(q.put_nowait, DONE)

    task = asyncio.create_task(asyncio.to_thread(work))
    answer = ""
    while (ev := await q.get()) is not DONE:
        if ev["type"] == "answer":
            answer = ev["text"]
        await context.emit(ev)        # persisted + streamed; returns the replay cursor
    await task
    return {"answer": answer}         # the invocation's output (GET /api/invocations/{id})

@app.recover                          # optional; without it automatic recovery is off
async def recover(input: dict, context: InvocationContext) -> dict:
    # a worker died mid-run (redeploy, crash). context.is_recovery is True, context.attempt > 1.
    # Re-run if the work is safe to repeat; otherwise tell the client to ask again.
    await context.emit({"type": "error", "message": "Interrupted — please ask again."})
    return {"interrupted": True}

@app.get("/api/health")               # ordinary FastAPI routes live on the same app
def health():
    return {"ok": True}
```
`app.yaml`: `command: [uvicorn, server:app, --host, 0.0.0.0, --port, "8000"]`.

**Event design.** `context.emit` takes any JSON object; design a small vocabulary and keep it stable (e.g. `step`,
`step_update`, `step_done`, `token`, `answer`, `error`, `done`). Every emit is a Runtime Store write, so **batch
tokens** (flush every ~250 ms) instead of emitting per token. Send a `heartbeat` while a slow tool works so proxies
don't close an idle stream.

`InvocationContext`: `invocation_id`, `session_id`, `attempt` (first = 1), `is_recovery`, `emit(event)`,
`request_auth` (only populated on the CLI-managed request-user path, see section 5).

## 3 · The protocol clients use
| Call | Meaning |
|---|---|
| `POST /api/invocations` `{"id": <uuid>, "session_id": "...", "input": {...}, "stream": true}` | Start a run. `stream` → SSE of your events (plus `run.started` / `run.completed` / `run.failed`). `background: true` → returns at once. Neither → waits for the result. Unknown body fields are rejected. |
| `GET /api/invocations/{id}` | Status + final output. |
| `GET /api/invocations/{id}/events?after=N` | Replay stored events after cursor N — **reconnect** after a dropped connection. SSE `id:` lines carry the cursor. |

* `id` is the **idempotency key**: retrying the same body never runs twice; reusing an id with a different body →
  409. Generate it client-side, once per question.
* Same `session_id` ⇒ invocations run **one at a time, in order** (a conversation). No session id ⇒ sessionless.
* Client pattern: POST with `stream: true`, remember the last `id:`; on a network error, GET `.../events?after=<last>`
  until `run.completed` / `run.failed`. Example: `05_app/backend/core/foreman_client.py`.

## 4 · Runtime Store (what makes runs durable)
* **Local** (no env set) → in-memory store: same API, state lost on exit. Good for development.
* **CLI deploy** → the CLI provisions a managed Lakebase database (you can't bring your own on that path).
* **No-CLI deploy on Apps** → give the app a `postgres` resource (Lakebase Autoscaling, `CAN_CONNECT_AND_CREATE`)
  and set both:
  ```yaml
  env:
  - name: DATABRICKS_AGENTBRICKS_RUNTIME_STORE_LAKEBASE_ENDPOINT
    value: projects/<project>/branches/<branch>/endpoints/<endpoint>
  - name: DATABRICKS_AGENTBRICKS_RUNTIME_STORE_SCHEMA
    value: <agent>_runtime              # a schema the app's SP creates and owns
  ```
  `runtime_store_from_environment()` (SDK `runtime/store.py`) then uses `LakebaseDurableRuntimeStore.from_app_resource`,
  with the `PG*` values the postgres resource injects. **Caveat:** the SDK calls this the "legacy Apps resource" path,
  and the public docs only describe the CLI-provisioned store. It works (verified on SDK 0.8.0) but isn't documented,
  so pin the SDK version, re-test on upgrades, and tell the user. Setting only one of the two variables is an error.
* The Runtime Store is **not** conversation memory. It holds runs, events and results. Keep history and memory
  separately (your own Lakebase tables, or the Beta managed stores).

## 5 · Identity — who the agent calls Databricks as
* **App identity (default):** `WorkspaceClient()` (or `databricks_agentkit.workspace_client()`) authenticates as the
  app's service principal. Grant it exactly what the agent needs through app resources (section 7) and UC grants.
* **On behalf of the user (Apps user authorization, GA):** declare `user_api_scopes` on the app (e.g. `["genie"]`,
  least privilege). The platform then forwards each signed-in person's token as `x-forwarded-access-token`.
  * **Users call the agent app directly:** read the header per request.
  * **Another app calls the agent** (a UI app's backend): the forwarded token on the agent is the *calling app's*.
    The UI app must pass the person's token in its own header, and the agent keeps it in memory keyed by invocation id.
    Use ASGI middleware that reads the body's `id`; see `_CaptureUserToken` in the worked example.
  * Never put a token in `input` (persisted), logs or traces. Build a per-call client:
    `WorkspaceClient(host=cfg.host, token=user_token, auth_type="pat")`. `auth_type` pins the user token even
    though SP credentials are in the environment.
  * OBO runs **can't be recovered** after a crash: the token is gone. `@app.recover` should ask the user to retry
    (AgentKit's own request-user path fails recovery the same way).
  * Stale consent (scope added later): the user revokes consent or clears cookies, then signs in again.
* AgentKit's built-in request-user auth (`context.request_auth.client_for("user")`) is wired by the CLI's agent
  manifest. Without the CLI, use the pattern above.

## 6 · Models, tools, tracing
* **Models:** Foundation Model API through the OpenAI protocol — `DatabricksOpenAI(workspace_client=w)` from
  `databricks-openai`. Split the models: a fast one for routing and tool choice, a strong one for the answer.
  Reasoning models spend tokens thinking, so keep `max_tokens` ≥ 1000 even for short replies, or they return no text.
* **Tools:** plain function-calling. Run independent tool calls **in parallel** (thread pool). Copy the
  `contextvars` context per task so MLflow spans nest under the run. Bound the rounds (`max_tool_rounds`). Turn a
  tool error into evidence ("no access to X"), never a crash.
* **Tracing (crucial):** one MLflow trace per invocation. Use a root span (`span_type=AGENT`) and a span per tool,
  and tag the session and user:
  `mlflow.update_current_trace(metadata={"mlflow.trace.session": sid, "mlflow.trace.user": user})`.
  Bind the experiment to **Unity Catalog** tables at creation:
  `mlflow.set_experiment(name, trace_location=UnityCatalog(catalog_name=..., schema_name=..., table_prefix=...))`
  (MLflow ≥ 3.14). The binding can't change later. Then grant the app SP `USE SCHEMA, MODIFY, SELECT` on that
  schema, and set `MLFLOW_TRACING_SQL_WAREHOUSE_ID` (a `sql_warehouse` resource) so traces can be read back.
  `MLFLOW_ENABLE_ASYNC_LOGGING=true` and `atexit.register(mlflow.flush_trace_async_logging)` keep the user from
  waiting on trace upload.
* Return the trace id in a final `done` event so the UI can deep-link: `<host>/ml/experiments/<id>/traces?traceId=<trace id>`.

## 6b · Wiring Genie spaces together (one agent, many domain experts)
The most common Databricks agent: each **Genie space is one tool** (a domain expert), and the agent decides which to
ask, asks them **in parallel**, and combines the answers. The same shape works with other tools added alongside.

**1. A registry, not hard-coded IDs.** Keep one row per space: `domain_key, title, space_id, description`. A UC table
written when the spaces are created, or a config file. The agent builds its tools from it at startup, so adding a
domain means adding a space plus a redeploy, with no code change.

**2. One function tool per space. The description is the routing rule.** The model only sees name + description,
so reuse the space's own description and say what it does **not** own:
```python
tools = [{"type": "function", "function": {
            "name": f"ask_{s['domain_key']}_genie",
            "description": f"Ask the {s['title']} expert. {s['description']}",
            "parameters": {"type": "object", "required": ["question"], "properties": {"question": {
                "type": "string", "description": "A complete, self-contained question: IDs, time period, "
                                                 "and say so if documents are needed."}}}}}
         for s in registry]
```
Genie spaces don't see the conversation, and each tool call is a fresh Genie conversation. The router must rewrite
follow-ups ("what about last month?") into self-contained questions. Put that rule in the system prompt.

**3. Call a space: pick the API.**
| | Genie **Agent mode** — `POST /api/2.0/genie/agents/{space_id}/responses` (SSE) | Genie **Chat mode** — Conversation API |
|---|---|---|
| Does | Plans, runs several SQL queries, searches files in volumes attached to the space, answers | One SQL query + answer per question |
| Use when | Spaces have documents or notes, or questions need more than one query | Pure data questions; simplest |
| Streams | Each step (`reasoning`, `function_call` = `execute_sql` / `search_context_files`, `function_call_output` = result as a markdown table, `message`) | Poll for status |
| Helper | Write a small SSE reader (below) | SDK `w.genie.start_conversation_and_wait(space_id, q)`, or AgentKit's `GenieAgent` |

Agent mode, the core of the reader:
```python
body = {"input": [{"type": "message", "role": "user", "content": [{"type": "input_text", "text": q}]}]}
with requests.post(f"{host}/api/2.0/genie/agents/{space_id}/responses", json=body, stream=True,
                   headers={**w.config.authenticate(), "Accept": "text/event-stream"}, timeout=(10, 300)) as r:
    for line in r.iter_lines(decode_unicode=True):
        if not line.startswith("data:"): continue
        ev = json.loads(line[5:]); item = ev.get("item") or {}
        if ev["type"] == "response.output_item.added" and item.get("type") == "function_call":
            emit_status(json.loads(item["arguments"]).get("title", item["name"]))   # "querying: OEE by line"
        elif ev["type"] == "response.output_item.done" and item.get("type") == "function_call_output":
            evidence.append(item["output"])                                       # markdown table
        elif ev["type"] == "response.output_item.done" and item.get("type") == "message":
            answer += "".join(c["text"] for c in item["content"] if c["type"] == "output_text")
        elif ev["type"] in ("response.completed", "response.failed"): break
```
Chat mode via AgentKit, which works without the CLI if you construct it yourself. Its `genie_tools()` factory reads
the CLI's `agent.toml`, so call the class directly:
```python
from databricks_agentkit.runtime.genie import GenieAgent
expert = GenieAgent(space_id, auth="user", workspace_client_for=lambda mode: user_client)  # or auth="app"
result = await expert.ask(question)          # starts a conversation and waits; .poll() / .query_result() also exist
```

**4. Ask in parallel, keep the trace intact.** Run the chosen tool calls with a thread pool. Submit each task with
`contextvars.copy_context().run` so every Genie span nests under the run's trace. Emit a status event per
space as it works. Truncate each space's evidence (e.g. 20 kB) before handing it to the answer model. Bound the rounds
(e.g. 2): after that, the model must answer with what it has.

**5. Identity and grants (per space).**
* App resource per space: `{"genie_space": {"space_id": ..., "permission": "CAN_RUN"}}`, plus the space's SQL warehouse
  (`CAN_USE`).
* **As the user** (recommended: answers respect each person's permissions): the app declares `user_api_scopes:
  ["genie"]`, and Genie calls use the person's token (section 5). The *person* then needs CAN_RUN on the space,
  CAN_USE on its warehouse, SELECT on its tables and READ VOLUME on attached volumes, usually granted to groups.
* **As the app:** the SP needs those same UC grants. Simpler, but everyone sees the same data.

**6. Make errors evidence, not crashes.** Map a permission error to "you don't have access to <domain>" and let the
answer model work with the other spaces' evidence. A NULL from a column mask means *confidential*: tell the model
so in the system prompt, so it never reports it as zero.

**7. Files in spaces** ("Analyze files in volumes", Public Preview): attach volumes via
`serialized_space.data_sources.volumes` (**sorted by path**). A volume is indexed when attached and when Sync is pressed.
It does not pick up new files by itself, so anything that writes files must trigger the index sync and wait for it.
Space instructions should say the files are attached and must be searched, otherwise a space may answer "I can only
query SQL".

**8. Test both layers.** Benchmark each Genie space on its own questions. Then evaluate the agent on **routing**
(did it call the right spaces?) and **correctness** (expected facts). When a regression appears, you know which layer
caused it. For a full worked example (spaces as YAML, registry, routing prompt, notes by priority), load the
`build-custom-supervisor` skill.

## 7 · Deploy without the CLI (Apps REST from a notebook, or DABs)
```python
w = WorkspaceClient()
resources = [
  {"name": "experiment", "experiment": {"experiment_id": exp_id, "permission": "CAN_EDIT"}},
  {"name": "sql-warehouse", "sql_warehouse": {"id": wh_id, "permission": "CAN_USE"}},
  {"name": "postgres", "postgres": {"branch": f"projects/{p}/branches/{b}",
                                    "database": f"projects/{p}/branches/{b}/databases/{db}",
                                    "permission": "CAN_CONNECT_AND_CREATE"}},
  # + one per tool resource, e.g. {"name": "genie-x", "genie_space": {"space_id": ..., "permission": "CAN_RUN"}}
]
spec = {"name": APP, "resources": resources}                 # + "user_api_scopes": [...] for OBO
try:
    w.api_client.do("GET", f"/api/2.0/apps/{APP}")
    w.api_client.do("POST", f"/api/2.0/apps/{APP}/update",
                    body={"app": spec, "update_mask": "resources"})   # replaces the whole list: send all of them
except NotFound:
    w.api_client.do("POST", "/api/2.0/apps", body=spec)
# wait for compute ACTIVE and any update to finish, then:
w.api_client.do("POST", f"/api/2.0/apps/{APP}/deployments", body={"source_code_path": AGENT_DIR})
```
* Each resource **grants** the app's SP and **injects** a value into `app.yaml` (`valueFrom: experiment`). No IDs or
  secrets in code. Render `app.yaml` from config in the deploy step. Don't hand-edit it.
* Deploy the app **before** running it locally against Lakebase, so the SP creates and owns its schemas (otherwise
  `permission denied` for the SP).
* DABs: the same app, resources and source path as a `resources.apps` entry. Run `databricks bundle validate` first.
* End the deploy with a **smoke test**: stream one real invocation and print each event.
* Callers need `CAN_USE` on the agent app. An app calling it uses its own SP's OAuth token
  (`Config().authenticate()`).

## 8 · Evaluate (the regression test)
Run the **same loop in-process** (import `agent.py`, no server) over an eval set with known answers using
`mlflow.genai.evaluate`. Score tool choice and correctness, and make expectations identity-aware when data is
masked by permissions. Re-run after every prompt, model or tool change. Install the agent's own
`requirements.txt` in the eval notebook (`%pip install -r ./agent/requirements.txt`): a loose `%pip` can resolve
for a very long time on serverless.

## 9 · Checklist before you hand it over
- [ ] `@app.invoke` handles bad input with a clear error, and the loop never blocks the event loop (use `to_thread`)
- [ ] Tokens are batched, and a heartbeat goes out during long tool calls
- [ ] Runtime Store env set as a pair (or consciously in-memory), and the SDK version pinned
- [ ] No credentials in `input`, logs, traces or the Runtime Store
- [ ] `@app.recover` is decided: re-run if safe, otherwise tell the user to ask again
- [ ] One trace per run, with session and user metadata, in UC tables the SP can write
- [ ] Client reconnects with `events?after=` and uses a fresh `id` per question
- [ ] Deploy renders `app.yaml`, declares every resource, runs a smoke test
- [ ] An eval set exists and passes
