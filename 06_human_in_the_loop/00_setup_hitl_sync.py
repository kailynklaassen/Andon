# Databricks notebook source
# MAGIC %md
# MAGIC # Step 6a · Human-in-the-loop: wire the app's Lakebase ledger back into the lakehouse
# MAGIC
# MAGIC The app (05_app) writes every human action to **Lakebase** — fast, transactional, read-your-own-writes. Approved
# MAGIC actions have to come back to the lakehouse so the pipelines, metric views and Genie spaces learn from them:
# MAGIC
# MAGIC ```
# MAGIC  app ─submit─► Lakebase hitl.actions ─approve─► hitl.approved_actions (outbox) ─┐
# MAGIC                                     hitl.action_events (audit trail)          │ job kkparts-hitl-sync (schedule)
# MAGIC                                                                               ▼
# MAGIC   value change → <landing>.app_corrections_<table> → append flow → bronze_<table> → silver → gold
# MAGIC   note         → routed to 1-2 domains → app_notes_<domain>/NOTE-….md → that Genie space's attached files
# MAGIC   everything   → Delta mirror <app schema>.hitl_* (+ sync status back in Lakebase)
# MAGIC ```
# MAGIC
# MAGIC This notebook is idempotent. It:
# MAGIC 1. checks the Lakebase project exists (Step 0 creates it; the app's service principal owns its schema);
# MAGIC 2. creates one **correction table** per correctable bronze table — same columns as the bronze table, so the
# MAGIC    pipeline's append flow (`02_medallion_pipeline/transformations/bronze_app_corrections.py`) can feed it in;
# MAGIC 3. makes sure every Genie space has its approved-notes volume (`app_notes_<domain>`, also created in Step 2a);
# MAGIC 4. grants the app's service principal read access to gold (if the app is deployed);
# MAGIC 5. creates / updates the scheduled sync job: sync → (if corrections landed) refresh the medallion pipeline.
# MAGIC
# MAGIC **Run after Step 2a** — the bronze tables need the app-lineage columns (`_altered_in_app`, `_app_action_id`, …).

# COMMAND ----------

# MAGIC %md
# MAGIC ### Why this step matters
# MAGIC An agentic framework is a loop, not a chatbot: insight → recommendation → **human decision** → back into the data. Without this step, people's corrections and context die in the app.
# MAGIC
# MAGIC **Crucial**
# MAGIC * Approval before anything reaches the lakehouse (the outbox table).
# MAGIC * Traceability: the action id on every bronze row and note it produces.
# MAGIC
# MAGIC **Optional**
# MAGIC * The schedule (default every 30 min) and the `Sync now` button.

# COMMAND ----------

# MAGIC %pip install "databricks-sdk>=0.81" --quiet
# MAGIC %restart_python

# COMMAND ----------

# MAGIC %run ../config/config

# COMMAND ----------

import os
from databricks.sdk import WorkspaceClient
from databricks.sdk.errors import NotFound

w = WorkspaceClient()
H = CFG["hitl"]
LB = H["lakebase"]
ensure_uc_objects()                                   # includes the app schema (workspace.schemas.app)
LINEAGE = ["_altered_in_app", "_app_action_id", "_app_approved_by", "_app_approved_ts"]

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1 · Lakebase project (created by Step 0 — `00_lakebase`)

# COMMAND ----------

try:
    w.postgres.get_project(name=f"projects/{LB['project']}")
except NotFound:
    raise RuntimeError(f"Lakebase project {LB['project']} doesn't exist — run 00_lakebase/00_setup_lakebase first")
endpoint = w.postgres.get_endpoint(name=f"projects/{LB['project']}/branches/{LB['branch']}/endpoints/{LB['endpoint']}")
print(f"Lakebase project {LB['project']} · endpoint {endpoint.name} → {endpoint.status.hosts.host}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2 · Correction tables (one per correctable bronze table)
# MAGIC `CREATE TABLE … AS SELECT * FROM bronze WHERE false` copies the bronze schema exactly, so a corrected record has
# MAGIC the same columns and types as a source-system record. Only the sync job writes here.

# COMMAND ----------

for bronze_table in H["corrections"]:
    src = f"{CATALOG}.{BRONZE_SCHEMA}.{bronze_table}"
    missing = [c for c in LINEAGE if c not in spark.table(src).columns]
    if missing:
        raise RuntimeError(f"{src} has no {missing} yet — run Step 2a (medallion pipeline) first")
    target = correction_table(bronze_table)
    spark.sql(f"CREATE TABLE IF NOT EXISTS {target} "
              f"COMMENT 'Approved app corrections for {bronze_table} (written by the HITL sync job, read by the pipeline append flow)' "
              f"AS SELECT * FROM {src} WHERE false")
    print(f"  {target}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3 · One approved-notes volume per Genie space

# COMMAND ----------

for s in CFG["genie"]["spaces"]:
    spark.sql(f"CREATE VOLUME IF NOT EXISTS `{CATALOG}`.`{LANDING_SCHEMA}`.`{notes_volume(s['key'])}` "
              f"COMMENT 'Approved comments and decisions from the app for the Genie space: {sql_str(s['title'])}'")
    print(f"  {notes_path(s['key'])}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4 · The app's service principal reads gold
# MAGIC The app's own resources (SQL warehouse, serving endpoint, Lakebase database) are granted through the app; table
# MAGIC access is Unity Catalog, like for any other identity. Skipped if the app isn't deployed yet — re-run after deploying.

# COMMAND ----------

try:
    app = w.apps.get(name=H["app_name"])
    sp = app.service_principal_client_id
    for stmt in (f"GRANT USE CATALOG ON CATALOG `{CATALOG}` TO `{sp}`",
                 f"GRANT USE SCHEMA, SELECT ON SCHEMA `{CATALOG}`.`{GOLD_SCHEMA}` TO `{sp}`"):
        spark.sql(stmt)
    print(f"App {app.name} (service principal {sp}): USE CATALOG, USE SCHEMA + SELECT on {GOLD_SCHEMA}")
except NotFound:
    print(f"App {H['app_name']} not deployed yet — deploy 05_app, then re-run this cell")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5 · The scheduled sync job
# MAGIC `sync_approved_actions` → `corrections_landed` (condition: did any value change land?) → `refresh_pipeline` →
# MAGIC `mark_in_gold` (an `in_gold` event per correction; the app refreshes its cached gold data when it sees one).
# MAGIC Notes need no refresh: the sync writes each note's file into its Genie space's `app_notes_<domain>` volume (Genie keeps
# MAGIC its file index in sync, usually within a minute).
# MAGIC Serverless, one run at a time. It also runs on demand (*Run now*) — handy right after approving in a demo.

# COMMAND ----------

pipeline_name = f"{CFG['supervisor']['name'].split('-')[0]}-mfg-medallion"
pipeline = next(p for p in w.pipelines.list_pipelines(filter=f"name LIKE '{pipeline_name}'") if p.name == pipeline_name)
notebook = f"{REPO_ROOT}/06_human_in_the_loop/01_sync_approved_actions".removeprefix("/Workspace")

tasks = [{"task_key": "sync_approved_actions",
          "notebook_task": {"notebook_path": notebook, "source": "WORKSPACE"},
          "timeout_seconds": 1800,
          "max_retries": 1, "min_retry_interval_millis": 60000}]   # the sync is idempotent, so a retry is safe
if H["sync"].get("refresh_pipeline", True):
    tasks += [{"task_key": "corrections_landed", "depends_on": [{"task_key": "sync_approved_actions"}],
               "condition_task": {"op": "GREATER_THAN", "right": "0",
                                  "left": "{{tasks.sync_approved_actions.values.value_changes}}"}},
              {"task_key": "refresh_pipeline", "depends_on": [{"task_key": "corrections_landed", "outcome": "true"}],
               "pipeline_task": {"pipeline_id": pipeline.pipeline_id, "full_refresh": False}},
              # the corrections are now in gold: record it (audit trail) and let the app refresh its cached gold data
              {"task_key": "mark_in_gold", "depends_on": [{"task_key": "refresh_pipeline"}],
               "notebook_task": {"notebook_path": notebook.replace("01_sync_approved_actions", "02_mark_in_gold"),
                                 "source": "WORKSPACE"}}]
settings = {
    "name": H["sync"]["job_name"],
    "description": f"{COMPANY}: move approved app actions from Lakebase into the lakehouse (bronze corrections, Genie notes, ledger mirror).",
    "schedule": {"quartz_cron_expression": H["sync"]["cron"], "timezone_id": H["sync"]["timezone"], "pause_status": "UNPAUSED"},
    "max_concurrent_runs": 1,
    "parameters": [{"name": "run_id", "default": "{{job.run_id}}"}],
    "tasks": tasks,
    "tags": {"demo": "kkparts", "component": "hitl"},
}
existing = [j for j in w.jobs.list(name=settings["name"])]
if existing:
    job_id = existing[0].job_id
    w.api_client.do("POST", "/api/2.2/jobs/reset", body={"job_id": job_id, "new_settings": settings})
    print(f"Updated job {settings['name']} ({job_id})")
else:
    job_id = w.api_client.do("POST", "/api/2.2/jobs/create", body=settings)["job_id"]
    print(f"Created job {settings['name']} ({job_id})")
print(f"  {w.config.host.rstrip('/')}/jobs/{job_id} · schedule {H['sync']['cron']} {H['sync']['timezone']}")
dbutils.notebook.exit(f"job {job_id}")
