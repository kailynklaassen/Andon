# Databricks notebook source
# MAGIC %md
# MAGIC # Step 2a · Medallion pipeline (bronze → silver → gold)
# MAGIC
# MAGIC **What this does:** creates (or updates) one **Lakeflow Spark Declarative Pipeline** from the SQL files in
# MAGIC [`transformations/`](./transformations), then runs it and waits.
# MAGIC
# MAGIC | Layer | Schema | Object type | What happens |
# MAGIC |---|---|---|---|
# MAGIC | Bronze | `mfg_bronze` | Streaming tables (Auto Loader) | Raw files ingested as-is + lineage columns. Only new files are read each run. |
# MAGIC | Silver | `mfg_silver` | Materialized views | Typed, de-duplicated, normalized; **expectations** drop bad rows and log them. |
# MAGIC | Gold | `mfg_gold` | Materialized views | Business-ready facts + dimensions, denormalized for Genie, with KPI components pre-computed. |
# MAGIC
# MAGIC **Why one declarative pipeline:** you declare *what* each table is; the pipeline works out the dependency graph,
# MAGIC orchestration, retries, incremental refresh, and data-quality metrics. Open the pipeline UI after this runs to see
# MAGIC the full lineage graph — it's a good demo moment.
# MAGIC
# MAGIC Everything the SQL needs (`${catalog}`, `${silver_schema}`, `${gold_schema}`, `${raw_path}`) is passed in as pipeline
# MAGIC configuration from `demo_config.yml` — the SQL files never hardcode a name.

# COMMAND ----------

# MAGIC %md
# MAGIC ### Why this step matters
# MAGIC The agent should read **business-ready, governed** data, never raw files. A declarative pipeline gives you the clean gold layer, data-quality expectations, lineage — and, here, a second writer into bronze: approved human corrections from the app (`bronze_app_corrections.py`).
# MAGIC
# MAGIC **Crucial**
# MAGIC * Gold tables with clear names and comments (Genie and the agent read them).
# MAGIC * Expectations in silver: bad rows are dropped *and counted*, so answers don't silently include them.
# MAGIC * The app-lineage columns (`_altered_in_app`, `_app_action_id`): every human change is traceable to its decision.
# MAGIC
# MAGIC **Optional**
# MAGIC * Serverless/Photon settings; scheduling the pipeline (it runs on demand and after app corrections).

# COMMAND ----------

# MAGIC %run ../config/config

# COMMAND ----------

import glob, time
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
ensure_uc_objects()

PIPELINE_NAME = f"{CFG['supervisor']['name'].split('-')[0]}-mfg-medallion"     # e.g. kkparts-mfg-medallion
# SQL files define bronze/silver/gold; bronze_app_corrections.py adds the app's write-back flows into bronze.
sql_files = sorted(glob.glob(f"{REPO_ROOT}/02_medallion_pipeline/transformations/*.sql")
                   + glob.glob(f"{REPO_ROOT}/02_medallion_pipeline/transformations/*.py"))
print("Pipeline source files:"); [print("  ", f.replace(REPO_ROOT, "")) for f in sql_files]

# The pipeline definition. We call the REST API directly (instead of typed SDK classes) so
# this works on any SDK version bundled with serverless compute.
spec = {
    "name": PIPELINE_NAME,
    "catalog": CATALOG,
    "schema": BRONZE_SCHEMA,                  # default target; silver/gold use fully-qualified names
    "serverless": True,
    "continuous": False,                      # triggered: run on demand / on a schedule
    "channel": "CURRENT",
    "photon": True,
    "libraries": [{"file": {"path": f}} for f in sql_files],
    "configuration": {                        # becomes ${catalog}, ${raw_path}, ... inside the SQL
        "catalog": CATALOG,
        "silver_schema": SILVER_SCHEMA,
        "gold_schema": GOLD_SCHEMA,
        "raw_path": RAW_PATH,
        "landing_schema": LANDING_SCHEMA,     # where the app's approved corrections land (app_corrections_<table>)
        "app_corrections": ",".join(CFG.get("hitl", {}).get("corrections", {})),   # bronze tables the app may correct
    },
}

existing = [p for p in w.pipelines.list_pipelines(filter=f"name LIKE '{PIPELINE_NAME}'") if p.name == PIPELINE_NAME]
if existing:
    pipeline_id = existing[0].pipeline_id
    w.api_client.do("PUT", f"/api/2.0/pipelines/{pipeline_id}", body={**spec, "id": pipeline_id})
    print(f"Updated pipeline {PIPELINE_NAME} ({pipeline_id})")
else:
    pipeline_id = w.api_client.do("POST", "/api/2.0/pipelines", body=spec)["pipeline_id"]
    print(f"Created pipeline {PIPELINE_NAME} ({pipeline_id})")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Run it and wait
# MAGIC First run on serverless: ~5-8 minutes (cold start + full build). Later runs only pick up new files.

# COMMAND ----------

update_id = w.pipelines.start_update(pipeline_id=pipeline_id, full_refresh=False).update_id
host = w.config.host.rstrip("/")
print(f"Update {update_id} started → {host}/pipelines/{pipeline_id}/updates/{update_id}")

while True:
    u = w.pipelines.get_update(pipeline_id=pipeline_id, update_id=update_id).update
    state = u.state.value if u.state else "UNKNOWN"
    if state in ("COMPLETED", "FAILED", "CANCELED"):
        break
    print(f"  {time.strftime('%H:%M:%S')}  {state}")
    time.sleep(30)

if state != "COMPLETED":
    errs = [e for e in w.pipelines.list_pipeline_events(pipeline_id=pipeline_id, max_results=200)
            if e.level and e.level.value == "ERROR"]
    for e in errs[:5]:
        print("ERROR:", e.message)
        if e.error and e.error.exceptions:
            print("   ", e.error.exceptions[0].message[:1500])
    raise RuntimeError(f"Pipeline update {update_id} ended {state}")
print(f"✅ Pipeline update {state}")

# COMMAND ----------

# MAGIC %md
# MAGIC ### What got built

# COMMAND ----------

for schema in (BRONZE_SCHEMA, SILVER_SCHEMA, GOLD_SCHEMA):
    rows = spark.sql(f"SHOW TABLES IN `{CATALOG}`.`{schema}`").collect()
    print(f"{schema:<12} {len(rows):>3} objects: {', '.join(sorted(r.tableName for r in rows))}")

# COMMAND ----------

# Data-quality results: rows dropped by each silver expectation (from the pipeline event log).
display(spark.sql(f"""
SELECT origin.flow_name AS dataset, exp.name AS expectation, SUM(exp.passed_records) AS passed, SUM(exp.failed_records) AS failed
FROM event_log('{pipeline_id}')
LATERAL VIEW EXPLODE(from_json(details:flow_progress:data_quality:expectations,
  'array<struct<name:string,dataset:string,passed_records:bigint,failed_records:bigint>>')) AS exp
WHERE event_type = 'flow_progress' AND details:flow_progress:data_quality IS NOT NULL
GROUP BY ALL ORDER BY failed DESC
"""))
