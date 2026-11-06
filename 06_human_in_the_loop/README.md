# 06 — Human in the loop: Lakebase ledger → lakehouse

The app (`05_app`) is where people act on what the data and the agents surface. Every action is written to
**Lakebase** (Postgres — what's in it and who owns it: [`00_lakebase/README.md`](../00_lakebase/README.md)) — the app needs fast, concurrent, read-your-own-writes storage. Approved actions then come
back to the **lakehouse** on a schedule, into the place that makes them useful:

```
 app ─submit──► <schema>.actions            (inbox: every action, current status)
     ─approve─► <schema>.approved_actions   (outbox: frozen copy + kind + target + sync status)
                <schema>.action_events  (audit trail: submitted / approved / rejected / synced / sync_failed / done)
                      │
                      │  job kkparts-hitl-sync (every 30 min, or "Sync now" on the Action Ledger)
                      ▼
 kind = value_change  → mfg_landing.app_corrections_<table>   full corrected record, typed like bronze
                      → pipeline append flow                  02_medallion_pipeline/transformations/bronze_app_corrections.py
                      → bronze_<table>                        _altered_in_app = true, _app_action_id, _app_approved_by/_ts
                      → silver (latest version per record)    altered_in_app, app_action_id
                      → gold → metric views → Genie, the app  (the job refreshes the pipeline only when a value change landed)
                      → 'in_gold' event in Lakebase           → the app refreshes its cached gold data within a minute
 kind = note          → routed by the supervisor's router model to the 1-2 Genie spaces it is about
                        (it reads the note against the Genie space descriptions — the rule Foreman routes questions by)
                      → app_notes_<domain>/NOTE-<id>.md   one volume per Genie space, attached to it
                      → Genie Agent mode searches the file; the note states its priority in its text, and the space
                        instructions + Foreman's prompt say how to weigh P1 (decision: supersedes older
                        recommendations) / P2 (context) / P3 (FYI)
                      → the job re-syncs that volume's Genie file index (Genie does not pick up new files by
                        itself; ~2 min) and records a 'searchable_in_genie' event
 always               → mfg_app.hitl_actions / hitl_approved_actions / hitl_action_events (Delta mirror, MERGE)
                      → sync_status, sync_ref, sync_run_id written back to Lakebase + a 'synced' event
```

**Which actions are which:** a *Flag / correct a value* action names one cell (gold table · key · column, chosen from
dropdowns of real records and values — `05_app/backend/core/records.py`), so it's a **value change** written back to the bronze
table behind that cell. Every other action (work order request, MOC proposal, SCAR escalation, comment, …) is human
context — a **note**, routed to the Genie space(s) it is about and weighted by the priority the person gave it.
Re-route every note (after changing routing or volumes): run `01_sync_approved_actions` with `republish_notes=true`.

## Traceability

Every hop carries the action id:

```sql
-- which gold/silver values came from the app, and who decided them
SELECT w.machine_id, w.criticality, a.created_by, a.approved_by, a.approved_ts, a.sync_ref
FROM   <catalog>.mfg_silver.work_centers w
JOIN   <catalog>.mfg_app.hitl_approved_actions a ON a.action_id = w.app_action_id
WHERE  w.altered_in_app;

-- every version of one record in bronze: source-system file rows and app rows
SELECT _source_file, _altered_in_app, _app_action_id, _app_approved_by, failure_mode
FROM   <catalog>.mfg_bronze.bronze_maintenance_work_orders WHERE work_order_id = 'WO-900322';

-- the full story of one action
SELECT * FROM <catalog>.mfg_app.hitl_action_events WHERE action_id = '<id>' ORDER BY event_ts;
```

Nothing is updated in place: the source-system row stays in bronze next to the corrected one (`_source_file =
kkparts-app://hitl/actions/<id>`), so you can always see what the value was and why it changed.

## Files

| File | What it does |
|---|---|
| `00_setup_hitl_sync` | checks the Lakebase project (Step 0) · one correction table per correctable bronze table · one notes volume per Genie space · app SP grants on gold · the scheduled job |
| `01_sync_approved_actions` | The job: read the outbox → write corrections / notes → write the outcome back → mirror the ledger to Delta |
| `app_notes.py` | The note file format (header + text with the priority line) the sync writes |
| `02_mark_in_gold` | The job's last task, after the pipeline refresh: an `in_gold` event per correction (the app refreshes its cache on it) |

## What gets refreshed after an approval

| Approved | Refreshed | Why |
|---|---|---|
| value change | the medallion pipeline (job task `refresh_pipeline`, only when a value change landed) | bronze → silver → gold are pipeline tables |
| value change | the app's cached gold data (on the `in_gold` event) | pages are cached 10 minutes |
| value change | nothing in Genie | metric views are views; Genie's next query reads the new gold values |
| note | nothing | the note's file lands in its `app_notes_<domain>` volume; Genie re-indexes the attached volume automatically |

**Does Genie read the volume?** Yes — in Agent mode. Each Genie space has its documents volume (`genie_docs_<domain>`)
and its notes volume (`app_notes_<domain>`) attached ("Analyze files in volumes"), and Foreman asks Genie through the
Agent-mode API (`supervisor.genie_mode: agent`). No search functions are needed: each note states its priority in its
text and the space instructions say how to weigh it. People need `READ VOLUME` on their
domains' volumes (Step 2c grants it), because Agent mode reads the files as the person asking.

The correctable bronze tables and their record keys are listed under `hitl.corrections` in `config/demo_config.yml`.

## Why not Lakehouse Sync?

Lakebase can stream Postgres changes into Delta natively (Lakehouse Sync), but that is **Beta**; this accelerator
uses GA / Public Preview features only. The job is a plain Lakeflow Job over a Postgres connection: idempotent (an
action already in a correction table is skipped; a note file is rewritten), one run at a time, and a failed action
is marked `failed` with the error and retried on the next run without blocking the others.

## Order of operations (new workspace)

1. Steps 1–4 (`99_run_all`). Step 2a adds the app-lineage columns to bronze.
2. Step 0 (`00_lakebase`) creates the Lakebase project; Step 6a (`00_setup_hitl_sync`) the correction tables, notes volumes and the job.
3. Step 5 (`05_app/00_deploy_app`) deploys the app and grants its service principal SELECT on gold.
   Deploy before running the app locally against Lakebase: the app's service principal must create (and so own) its schema (`hitl.lakebase.schema`, `andon`).
