# =============================================================================
# BRONZE · app corrections (the app is a source system too)
# =============================================================================
# A person corrects a value in the app (05_app, "Flag / correct a value"), a reviewer approves it, and the HITL
# sync job (06_human_in_the_loop/01_sync_approved_actions) appends the full corrected record to
#     <catalog>.<landing>.app_corrections_<table>          e.g. app_corrections_maintenance_work_orders
# with the lineage columns set: _altered_in_app = true, _app_action_id, _app_approved_by, _app_approved_ts.
#
# This file adds a second APPEND FLOW into each bronze streaming table that reads that correction table.
# So a bronze table has two writers: Auto Loader (the source system's files) and the app. Nothing is updated in
# place — the corrected record is a new bronze row, and silver keeps the latest version of each record (app
# corrections win over the source-system row; the latest approval wins between corrections).
#
# Tables come from hitl.corrections in demo_config.yml (passed in as the `app_corrections` pipeline setting).
# A correction table that doesn't exist yet (HITL setup not run) is skipped, so the pipeline runs either way.
# =============================================================================
from pyspark import pipelines as dp
from pyspark.sql import functions as F

catalog = spark.conf.get("catalog")                                   # noqa: F821 (spark is provided by the pipeline)
landing = spark.conf.get("landing_schema")                            # noqa: F821
tables = [t.strip() for t in spark.conf.get("app_corrections", "").split(",") if t.strip()]  # noqa: F821
# correction tables that exist (spark.catalog.tableExists isn't available inside a pipeline; SHOW TABLES is)
existing = {r.tableName for r in spark.sql(f"SHOW TABLES IN `{catalog}`.`{landing}` LIKE 'app_corrections_*'").collect()}  # noqa: F821


def add_correction_flow(bronze_table: str) -> None:
    name = f"app_corrections_{bronze_table.removeprefix('bronze_')}"
    source = f"{catalog}.{landing}.{name}"
    if name not in existing:
        return

    @dp.append_flow(target=bronze_table, name=f"app_corrections_to_{bronze_table}",
                    comment=f"Approved app corrections from {source} (rows flagged _altered_in_app = true)")
    def corrections():
        return (spark.readStream.table(source)                       # noqa: F821
                .withColumn("_ingested_at", F.current_timestamp()))


for t in tables:
    add_correction_flow(t)
