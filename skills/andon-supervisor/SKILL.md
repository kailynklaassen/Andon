---
name: andon-supervisor
description: ANDON SUPERVISOR skill — the custom supervisor agent (Foreman) behind the Andon demo, which routes questions across domain Genie spaces (each with its documents and approved human notes attached as volumes), hosted on the Agent Server (AgentKit DurableAgentServer) on Databricks Apps with durable runs, Genie on behalf of the asking user, MLflow traces in Unity Catalog, and Lakebase sessions/memory. Use it to update Andon, add another Genie space (domain) to Andon or change an existing one, or to build the same supervisor pattern for another business. For a generic custom agent that isn't this supervisor, use generic-agentkit-agent.
---

# Andon supervisor: Foreman over the domain Genie spaces

You are helping a Databricks user build a **custom supervisor agent**: plain Python they own, hosted on the
**Agent Server** and governed by Unity Catalog. Reference implementation: `04_supervisor_agent/` in the KK's Parts
demo repo (agent loop `agent/foreman.py`, host `agent/server.py`) — copy its structure.

**Platform choices (as of 2026-11 — re-check release stages before you start):**
| Choice | Use | Status / why |
|---|---|---|
| Agent host | **AgentKit `DurableAgentServer`** (`databricks-agentbricks`) on Databricks Apps | GA, and the server Databricks recommends for new agents. Custom FastAPI orchestrators, MLflow `AgentServer` + `ResponsesAgent`, `LongRunningAgentServer` and Model Serving agents are the **legacy** path. |
| Deploy | Apps REST API from a notebook (or a DABs bundle) — **not** the Agent Bricks CLI | The CLI is **Beta**. Without it, configure the Runtime Store from the app's own `postgres` resource (below). Switch to `agentbricks deploy` when the CLI reaches GA; agent code doesn't change. |
| Genie calls | **Genie Agent-mode API** (`POST /api/2.0/genie/agents/{space_id}/responses`, GA) | Plans several queries and searches files attached to the space. Chat mode (Conversation API) is one SQL answer and can't read files. |
| Documents + human notes | **Volumes attached to each space** ("Analyze files in volumes", Public Preview) | No search functions or chunk tables to maintain. |
| Identity | Genie **on behalf of the user** (Apps user authorization, GA, `genie` scope) | Every answer respects the asker's UC permissions; models/memory/traces run as the app SP. |
| Traces | MLflow experiment bound to **Unity Catalog** trace tables (GA) | Queryable with SQL; works from Apps (classic trace storage can't upload spans from an app). |
| Sessions / memory | Lakebase tables you own | Managed agent sessions/memory are Beta. |

**The GA route:** AgentKit's `DurableAgentServer` is GA; the Agent Bricks CLI that also ships in `databricks-agentbricks`
is Beta. So use the server, and deploy it **without the CLI** (Apps REST from a notebook, or DABs).

## Target architecture
```
browser ─► client app (e.g. Andon, Apps user auth: genie scope) ─► supervisor app (Agent Server, its own SP)
                passes the person's email + Genie token per question      POST /api/invocations (stream, durable)
                                                                             │ fast router LLM picks domains
                                                                             ├─► Genie Agent mode, AS THE USER ─┐
                                                                             │     metric views + gold tables   │ parallel
                                                                             │     documents volume (files)     │
                                                                             │     approved-notes volume (files)┘
                                                                             └─► strong answer LLM (streamed)
 Runtime Store (durable runs) + sessions + memory + run log → Lakebase · every run → MLflow trace in UC tables
```
Unity Catalog decides what each user sees: domain GRANTs, `READ VOLUME` on each domain's volumes, ABAC column masks.

## Add a Genie space to Andon, or change one
Everything is driven by config and the space YAML, so `foreman.py` and `server.py` don't change. Foreman reads its
tools from `genie_space_registry`, which Step 3b writes.

**Add a domain** (key `<key>`, e.g. `energy`):
1. `config/demo_config.yml` → `genie.spaces`: add `{ key: <key>, title: "...", docs_folder: <key> }`. This list drives
   the `genie_docs_<folder>` and `app_notes_<key>` volumes, the note router's domains and the Foreman app's volume grants.
2. `03_genie_spaces/spaces/<key>.yml`: copy an existing space. The **description is the routing rule** for questions
   and for notes, so say what it covers *and* what it doesn't. Then fill in `metric_views`, `tables`, `join_specs`,
   `sql_snippets`, `example_sqls`, `text_instructions`, `sample_questions` and `benchmarks`.
3. The gold tables and metric views it lists must exist (Step 2, `02_medallion_pipeline/`). Step 2c tags and grants
   them from the space YAML.
4. Documents: put markdown in `01_data_generation/documents/<docs_folder>/`, which Step 1b renders to PDF. You can
   also put your own PDFs in the `genie_docs_<docs_folder>` volume.
5. `governance.groups`: add `<key>` to the `domains` of every group that should use it (that sets the space's `CAN_RUN`
   and the UC grants).
6. `04_supervisor_agent/eval/eval_set.yml`: add a few cases with `expected_tools: [<key>]` and at least one
   cross-domain case.
7. Run, in order: 1b → 2c → 3b → 3c → 4b → 4c → 6a. Running `99_run_all` with the earlier steps skipped does the
   same. 4b re-renders `app.yaml`, which gives Foreman `CAN_RUN` on the new space and access to its volumes. 6a
   creates the notes volume.

**Change an existing space:** edit its `spaces/<key>.yml` and re-run 3b, which updates it in place with the same
`space_id`. Then re-run 4b, because Foreman's routing reads the descriptions from the registry when it is deployed.
Re-run 3c and 4c to catch regressions.

The Andon board pages (`05_app/backend/core/`, `frontend/src/pages/`) are dashboards written for the four KK's Parts
domains. A new space shows up in Foreman chat and in note routing without touching them. Add a board page only if
you want a dashboard for the new domain.

## Workflow for a new supervisor — do these in order, confirming with the user between steps

### 1. Inventory the domains
- List the Genie spaces (`GET /api/2.0/genie/spaces`). One space per business domain; a precise **description**
  per space (it is the routing rule — for questions and for notes) and metric views for governed KPIs.
- Write a **registry table** (`domain_key, title, space_id, description`). The agent reads tools from it; never
  hardcode space IDs in agent code.

### 2. Give each space its documents and its human notes (attached volumes)
- One UC **managed** volume per domain for its PDFs, clear file names (the document ID). Enable the workspace preview
  "Analyze Files in Volumes with Genie Agents".
- Attach via `serialized_space.data_sources.volumes = [{"path": "/Volumes/<cat>/<schema>/<vol>/"}, ...]` — **sorted by
  path** (template `03_genie_spaces/01_create_genie_spaces`). Genie indexes a volume when it is attached and when **Sync**
  is pressed on the source — it does **not** pick up new files by itself. Whatever writes files must trigger the sync:
  `POST /api/2.0/volume-indexes/<volume id>/sync`, then poll `GET /api/2.0/volume-indexes/<volume id>` until `state`
  is `SUCCEEDED` and `index_watermark_time` is after the write (~2 min for a small volume). These are the endpoints the
  Sync button calls and are not in the public API reference yet (template `01_sync_approved_actions` §4b). Volume descriptions are UI-only (Sources tab); put the same guidance in instructions.
- Approved human notes: a second volume per domain, one markdown file per note (`NOTE-<id>.md`) that **states its
  priority in the text** (P1 approved decision — supersedes older recommendations · P2 context · P3 FYI), what it is
  about, who approved it and when (template `06_human_in_the_loop/app_notes.py`). Route each note to 1-2 domains with
  the same router model + space descriptions the supervisor uses (template `01_sync_approved_actions`).
- Space instructions: documents and notes are attached files and must be searched — never "unavailable"; how to
  weigh P1/P2/P3; cite document and note IDs.

### 3. Govern once in Unity Catalog
- Account-level groups per domain (+ cross-domain groups). A **workspace admin** can create account groups/users with
  `/api/2.0/identity/{groups,users,workspace-assignments}` (template `02b_unity_catalog_governance/00_create_groups_and_users`).
- `GRANT SELECT` on each domain's objects, `USE SCHEMA` + `READ VOLUME` on its documents + notes volumes, `CAN_RUN` on
  its space, `CAN_USE` on the warehouse — Genie Agent mode runs the SQL **and reads the files as the person asking**.
- ABAC: governed tag on confidential columns, one masking function, one `CREATE POLICY ... COLUMN MASK` on the schema.
  Put policies on source tables/MVs; metric views inherit them.

### 4. Write the agent from the template
- `agent/foreman.py` = the whole loop, framework-free: memory recall → fast router LLM picks domains (one tool per
  registry row; tool description = space description) → Genie calls **in parallel**, each streaming Genie's live status
  (reasoning / querying: <title> / searching the attached files / writing its answer) → strong LLM writes the answer
  from the evidence (streamed) → done (trace id). Bounded rounds (`max_tool_rounds`), errors returned as tool output.
- `agent/server.py` = the host: `app = DurableAgentServer()`; `@app.invoke async def invoke(input, context)` runs the
  loop on a worker thread and `await context.emit(event)` for each event (batch tokens ~250 ms — every event is a
  Runtime Store write); `@app.recover` tells the client to ask again. Extra routes (sessions, memories, run log) are
  plain FastAPI routes on `app`.
- Per-user Genie token: AgentKit's request-user auth reads the **caller's** `x-forwarded-access-token`, which is the
  client app's SP when one app calls another. Have the client forward the person's token in a header, capture it in a
  small ASGI middleware keyed by the invocation `id`, use it only for that run's Genie calls, **never put it in
  `input`** (input is persisted). Interrupted runs can't be recovered on the person's behalf.

### 5. Configure (no code changes)
`build_config.py` writes `supervisor_config.yaml`: `system_prompt`, `genie_spaces[]`, `router_llm`, `answer_llm`,
`max_tool_rounds`, `genie_mode: agent`, `genie_auth: on_behalf_of_user`. Pick models from the live list
(`databricks serving-endpoints list`): a fast one to route, a strong one to answer.

### 6. Test locally and in a notebook before deploying
- Locally: `uvicorn server:app` (no Runtime Store env → in-memory store), then `POST /api/invocations`
  `{id: <uuid>, session_id, stream: true, input: {question, user}}` with your token in the user-token header. Then
  `GET /api/invocations/{id}` must return `completed` with the stored output.
- Questions: one single-domain number, one document question, one approved-note question (P1 must change the
  recommendation), one cross-domain "why". Read the MLflow trace for each.

### 7. Deploy on Databricks Apps (template `04_supervisor_agent/02_deploy_agent_app`)
- App resources (each grants the app SP and injects a value via `valueFrom`): the Genie spaces (`CAN_RUN`), the SQL
  warehouse (`CAN_USE`), the MLflow experiment (`CAN_EDIT`), the Lakebase `postgres` resource (`CAN_CONNECT_AND_CREATE`).
- `app.yaml` env, rendered from config: `DATABRICKS_AGENTBRICKS_RUNTIME_STORE_LAKEBASE_ENDPOINT=projects/<p>/branches/<b>/endpoints/<e>`
  and `DATABRICKS_AGENTBRICKS_RUNTIME_STORE_SCHEMA=<schema>` — the durable Runtime Store in the app's own Lakebase
  (the app SP creates and owns the schema). The SDK supports this pair in code (`runtime/store.py`,
  `from_app_resource` — its "legacy Apps resource" path) but the public docs only describe the CLI-provisioned store,
  so pin `databricks-agentbricks` and re-test on upgrade. Also `MLFLOW_EXPERIMENT_ID` (valueFrom),
  `MLFLOW_TRACING_SQL_WAREHOUSE_ID`. Generic AgentKit guidance: skill `generic-agentkit-agent`.
- Experiment bound to UC trace tables at creation (`mlflow.set_experiment(..., trace_location=UnityCatalog(...))`,
  MLflow ≥ 3.14); grant the SP `USE SCHEMA, MODIFY, SELECT` on the traces schema.
- The client app: `user_api_scopes: ["genie"]`, `CAN_USE` on the supervisor app, and it calls `POST /api/invocations`
  and reconnects with `GET /api/invocations/{id}/events?after=<last id>` if the stream drops.

### 8. Evaluate
`mlflow.genai.evaluate()` with a code routing scorer (expected domains ⊆ called), `Correctness()` with expected facts,
a `Guidelines` scorer for citations, and latency. Genie benchmarks: data questions in Chat mode (exact cells),
document/note questions in Agent mode. Test as users from different groups to prove governance flows through.

## Gotchas (each one cost real time)
| Symptom | Fix |
|---|---|
| Genie answers "only execute_sql_query is available" / refuses document questions | You're in Chat mode. Use the Agent-mode API; attach the volumes |
| `data_sources.volumes must be sorted by path` | Sort the volume list (and every list) in `serialized_space` |
| Token has no `genie` scope after adding the scope to the app | Each user re-consents: revoke `DELETE /api/2.0/oauth-app-integrations/<oauth2_app_client_id>/user-consent/me`, clear the app's cookies, reopen, Authorize |
| Trace list fine, traces empty when opened (from an app) | Classic trace storage uploads spans to cloud storage the app can't reach — bind the experiment to UC trace tables |
| Note routing silently falls back / memory stores nothing | Reasoning models spend the token budget thinking — `max_tokens≥1000` for small structured calls |
| Scheduled job fails after adding a `%pip` package | It resolved an older SDK — run the JOB itself (`jobs run-now`) after changing `%pip`; avoid newer SDK calls for values config knows |
| `PRINCIPAL_DOES_NOT_EXIST` on GRANT | Group is workspace-local — create it as an account group |
| `maximum number of tag policies ... reached` | Fall back to a system governed tag (e.g. `class.compensation`) |
| ABAC policy on a metric view fails | Put policies on the source tables/MVs |
| Reasoning model returns `content` as a list | Keep only `type == "text"` blocks |
| `tool_choice="none"` returns only reasoning (Claude) | For the forced answer, fold tool results into one evidence message and call without tools |
| Genie computes a KPI wrong (e.g. share of total = 100%) | Fix the space: governing metric view + a certified example SQL that shows the pattern (not the benchmark's answer) |
| Redeploy mid-answer | With the Agent Server the run continues; the client reconnects. Recovery after a crash can't reuse the user's token — ask again |
