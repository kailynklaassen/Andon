# 00_lakebase — the operational database (Lakebase Autoscaling Postgres)

Everything **transactional** lives in one Lakebase project; everything **analytical** stays in Delta / Unity Catalog.
Approved human actions move from here to the lakehouse on a schedule (`06_human_in_the_loop`).

| | Config (`hitl.lakebase.*`) | This demo |
|---|---|---|
| Project | `project` | `kkparts-hitl` |
| Branch · endpoint | `branch` · `endpoint` | `production` · `primary` (read-write, scale-to-zero) |
| Database | `database` (resource id) · `postgres_database` (Postgres name) | `databricks-postgres` · `databricks_postgres` |

## What's in it

| Schema | Owner (created on first start) | Table | What it holds | Written by | Read by |
|---|---|---|---|---|---|
| `andon` (`hitl.lakebase.schema`) | Andon app SP | `actions` | every action submitted in the app (the inbox) | Andon | Andon, sync job |
| | | `approved_actions` | approved actions + where each landed (the outbox) | Andon (approve), sync job (status) | sync job, Andon |
| | | `action_events` | audit trail: submitted · approved · synced · in_gold … | Andon, sync job | Andon (timeline), sync job |
| | | `app_events` | the app's own issues (API errors, Foreman unreachable, browser errors) | Andon | Health page |
| `foreman` (`supervisor.memory_schema`) | Foreman app SP | `sessions` · `turns` | conversations, by session id | Foreman | Foreman (history), Andon (Recent conversations) |
| | | `memories` | durable facts a user told Foreman (never data values) | Foreman | Foreman (recall) |
| | | `runs` | one row per question: user, session, status, time per Genie call, errors | Foreman | Health page |
| `foreman_runtime` (`supervisor.runtime_store_schema`) | Foreman app SP | AgentKit tables | the Agent Server's durable runs: every invocation, its streamed events, its result (lets a client reconnect after a drop) | Foreman (AgentKit `DurableAgentServer`) | Foreman (`/api/invocations/*`) |

## Where the code is
The code stays with the thing that uses it, because each Databricks App deploys its own folder:

| Code | Uses |
|---|---|
| `05_app/backend/core/ledger.py`, `telemetry.py` | schema `andon` (DDL in `ledger.py`) |
| `04_supervisor_agent/agent/memory.py`, `runlog.py` | schema `foreman` (DDL in each file) |
| `06_human_in_the_loop/01_sync_approved_actions`, `02_mark_in_gold` | reads the outbox, writes sync status + events (job identity: the project owner, via `databricks_superuser`) |
| `00_lakebase/00_setup_lakebase` | creates the project; read-only inventory of the schemas |

## Rules that matter
* **The project must exist before the apps deploy** — both attach it as a `postgres` resource (`CAN_CONNECT_AND_CREATE`). That's why this is Step 0.
* **Each app creates and owns its schema.** Deploy an app before running it locally against Lakebase; if you run locally
  first, *you* own the schema and the app gets `permission denied`. Renaming an app = a new schema.
* Credentials are OAuth database tokens (`w.postgres.generate_database_credential`), valid ~1 hour; the apps refresh them
  every 45 minutes and reconnect once after scale-to-zero.
* Jobs take the Postgres database name from config (`postgres_database`), not from an SDK lookup.
* Lakebase → Delta *Lakehouse Sync* (native CDC) is Beta, so the human loop uses a scheduled job instead.
