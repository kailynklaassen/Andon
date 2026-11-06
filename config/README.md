# config/ — the one place this accelerator is configured

| File | What it is |
|---|---|
| [`demo_config.yml`](demo_config.yml) | **The only file you edit.** Company, data, governance, Genie, agent, apps, Lakebase, human loop. |
| [`config.py`](config.py) | The loader every notebook `%run`s: reads the YAML, exposes `CATALOG`, schemas, volume paths and helpers (`get_warehouse_id()`, `docs_path()`, `notes_path()`, …). Never edit values here. |
| [`00_preflight`](00_preflight.py) | Checks your workspace is ready (catalog, warehouse, models, admin, Lakebase) **before** anything is built. `99_run_all` runs it first; run it alone any time. |

Nothing is hard-coded anywhere else: notebooks, the Foreman agent and the Andon app all get their names from
`demo_config.yml` (the deploy notebooks render each app's `app.yaml` from it). To point the accelerator at another
workspace, catalog or company, change this file — not code.

## What you're building — an agentic framework on Databricks (GA / Public Preview only)
```
 0  lakebase    one Lakebase project: the app's human-in-the-loop ledger + Foreman's sessions, memory and run log
 1  data        raw source files + 40 PDFs ─► 2 medallion pipeline ─► gold facts ─► metric views (governed KPIs)
 2c govern      Unity Catalog groups, grants, ABAC column mask on confidential values
 3  experts     4 domain Genie spaces: metric views + tables + attached documents and approved-notes volumes
 4  agent       Foreman: a custom supervisor that routes questions to the experts (Genie Agent mode, as the asker)
                — on the Agent Server (AgentKit DurableAgentServer) on Apps, every run traced in Unity Catalog, evaluated against the narrative
 5  app         Andon (FastAPI + React on Apps): drill-down, impact web, Foreman chat with visible steps, actions,
                App & agent health
 6  loop        human actions → Lakebase → approved → bronze corrections + routed, priority-weighted Genie notes
```

## The settings — what's crucial, what's optional

| Setting (`demo_config.yml`) | | What it does |
|---|---|---|
| `workspace.catalog` | **crucial** | Where everything lands. Must exist; you need `USE`/`CREATE` on it. Not a default-storage catalog (UC traces can't be written there). |
| `workspace.schemas.*` | crucial | landing → bronze → silver → gold, plus `app` (the ledger's Delta mirror). Created if missing. |
| `workspace.warehouse_name` | crucial for speed | The SQL warehouse Genie, the agent and the app run on (`warehouse_id` pins one instead; both blank = the first serverless warehouse). **Size it for parallel questions** (see the latency note). |
| `company`, `story` | optional | The fictional manufacturer and its four planted problems. Change them and the data, documents and Genie follow. |
| `governance.*` | crucial | Who sees what: domain groups and the confidential columns the ABAC mask hides. With Genie on behalf of the user, every answer respects the asker's groups. |
| `genie.spaces[]` | **crucial** | One Genie space per domain = one tool for the agent. Their *descriptions* are the agent's routing rules (for questions **and** for approved notes). |
| `genie.attach_documents` / `attach_app_notes` | crucial | Attach each space's documents volume and approved-notes volume ("Analyze files in volumes", Public Preview), so Genie Agent mode searches the files. No search functions: the files are the knowledge. |
| `supervisor.router_llm` / `answer_llm` | crucial | Two models on purpose: a **fast** one decides which experts to ask (and routes notes), a **strong** one writes the answer. |
| `supervisor.genie_mode` | **crucial** | `agent` (Genie Agent-mode API, GA): plans several queries, searches attached files, never refuses document questions as "SQL only". `chat`: one SQL answer per question. |
| `supervisor.genie_auth` | **crucial for governance** | `on_behalf_of_user` (Apps user authorization, GA): Genie runs as the person asking, with their permissions. `service_principal`: Genie runs as the app for everyone. |
| `supervisor.max_tool_rounds` | crucial | How many rounds of Genie calls before the agent must answer. Default 2. |
| `supervisor.app_name` | crucial | The agent server on Databricks Apps (`kkparts-foreman`) — the recommended, GA host. |
| `supervisor.traces.*` | crucial | Where traces land: Unity Catalog tables `<catalog>.<schema>.<prefix>_otel_*` (GA) — queryable with SQL, governed by UC. |
| `supervisor.memory` | optional | Sessions + long-term memory in Lakebase. Off = the agent still answers, it just forgets. |
| `hitl.lakebase.*` | **crucial for the human loop** | The Lakebase project (Step 0, `00_lakebase`) that holds the ledger, sessions, memory and run log. `postgres_database` is the name jobs connect to. |
| `hitl.notes.*` | crucial for the human loop | Approved notes: one volume per Genie space (`volume_prefix`), routing (`supervisor` = Foreman's router model reads the note against the space descriptions) and `max_domains`. `index_wait_minutes`: how long the sync job waits for the Genie file index to re-sync after writing notes (the index does not pick up new files on its own). Each note states its priority (P1 decision · P2 context · P3 FYI) in its text; the space instructions say how to weigh it. |
| `hitl.corrections` | crucial for the human loop | Which bronze tables accept app corrections, and each one's record key. |
| `hitl.sync.cron` | optional | How often approved actions move to the lakehouse (default every 30 min; *Sync now* in the app). |
| `app.admins` | optional | Who sees the App & agent health page (errors and slow runs by user and session). `{admin}` = whoever deploys. |
| `app.dashboard_embed_url` | optional | A published AI/BI dashboard shown as a tab on the Andon Board. |

## Before you run
* Run as a **workspace admin** (Step 2c creates groups and users; Steps 4–5 create apps and service principals).
* Only GA and Public Preview features are used. Where Databricks has a newer **Beta** option (managed agent sessions
  and memory, Lakebase → Delta *Lakehouse Sync*, the Agent Bricks CLI), the notebooks say so and use a GA building
  block instead.
* Enable the workspace preview **Analyze Files in Volumes with Genie Agents** (Public Preview) for the attached volumes.
* **People authorize the Andon app once** (it asks for the `genie` scope so Genie can run as them). If you add a scope
  later, everyone must authorize again (revoke the old consent or clear browser cookies, then sign in).
* **Latency note:** the agent asks several Genie spaces at once. On a 1-cluster Small warehouse those queries queue
  ("waiting for the SQL warehouse" in the app). Use a dedicated serverless warehouse that can scale out
  (this demo: `kkparts-demo`, Large, 1-8 clusters).

## How notebooks load it
Every step notebook starts with `%run ../config/config` (root notebooks: `%run ./config/config`). Optional widget
overrides: a notebook that defines `catalog` or `warehouse_id` widgets (as `99_run_all` passes them) wins over the YAML.
