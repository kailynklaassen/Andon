# Databricks notebook source
# MAGIC %md
# MAGIC # Step 2b · Metric views (the semantic layer Genie reasons over)
# MAGIC
# MAGIC **What this does:** deploys the 9 Unity Catalog **metric views** defined in [`metric_views/*.yaml`](./metric_views)
# MAGIC on top of the gold fact tables, then smoke-tests each one.
# MAGIC
# MAGIC | Genie space | Metric views |
# MAGIC |---|---|
# MAGIC | Production & OEE | `production_oee_metrics`, `production_downtime_metrics` |
# MAGIC | Quality & Compliance | `quality_inspection_metrics`, `quality_ncr_metrics` |
# MAGIC | Maintenance & Reliability | `maintenance_work_order_metrics`, `maintenance_asset_health_metrics` |
# MAGIC | Supply Chain & Warehousing | `supply_supplier_performance_metrics`, `supply_inventory_metrics`, `supply_shipment_metrics` |
# MAGIC
# MAGIC **Why metric views matter for agents:** a KPI like OEE is a *ratio of sums*
# MAGIC (`run/planned × ideal/run × good/total`). If an LLM writes `AVG(oee)` it gets a different, wrong number.
# MAGIC A metric view defines the KPI **once**, and Genie queries it with `MEASURE(\`OEE\`)` at any grain
# MAGIC (plant, line, shift, month) and always gets the governed answer. The `comment`, `display_name`, and
# MAGIC `synonyms` on every field are how Genie maps "first pass yield" or "uptime" to the right measure.
# MAGIC
# MAGIC Design rule we follow: **one fact table per metric view** (no fan-out joins), organized by domain.

# COMMAND ----------

# MAGIC %md
# MAGIC ### Why this step matters
# MAGIC LLMs are bad at inventing KPI formulas (OEE, PPM, PM compliance). Metric views define each KPI **once**, so Genie, dashboards and the app compute the same number — and the agent quotes it consistently.
# MAGIC
# MAGIC **Crucial**
# MAGIC * One governed definition per KPI the business argues about; Genie uses the measures instead of re-deriving them.
# MAGIC
# MAGIC **Optional**
# MAGIC * The number of metric views; extra dimensions.

# COMMAND ----------

# MAGIC %run ../config/config

# COMMAND ----------

import glob, os, re, yaml

MV_DIR = f"{REPO_ROOT}/02_medallion_pipeline/metric_views"
created = []
for path in sorted(glob.glob(f"{MV_DIR}/*.yaml")):
    name = os.path.basename(path)[:-5]
    body = open(path).read().format(catalog=CATALOG, gold_schema=GOLD_SCHEMA)
    body = "\n".join(l for l in body.splitlines() if not l.startswith("#"))   # drop file header comments
    yaml.safe_load(body)                                                     # fail fast on bad YAML
    spark.sql(f"CREATE OR REPLACE VIEW {fq(GOLD_SCHEMA, name)} WITH METRICS LANGUAGE YAML AS $$\n{body}\n$$")
    created.append(name)
    print(f"✅ {fq(GOLD_SCHEMA, name)}")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Smoke test — one governed KPI per metric view
# MAGIC Notice the query pattern Genie will use: `MEASURE(\`<measure>\`)` + `GROUP BY` the dimensions.

# COMMAND ----------

tests = {
    "production_oee_metrics":            ("`Plant Name`", "`OEE`"),
    "production_downtime_metrics":       ("`Reason Category`", "`Downtime Hours`"),
    "quality_inspection_metrics":        ("`Shift`", "`Defect Rate`"),
    "quality_ncr_metrics":               ("`Defect Code`", "`COPQ USD`"),
    "maintenance_work_order_metrics":    ("`Plant Name`", "`PM Compliance`"),
    "maintenance_asset_health_metrics":  ("`Machine ID`", "`Hours Above 4.5 mm/s`"),
    "supply_supplier_performance_metrics": ("`Supplier Name`", "`Supplier PPM`"),
    "supply_inventory_metrics":          ("`Warehouse ID`", "`Stockout Rate`"),
    "supply_shipment_metrics":           ("`Carrier Name`", "`Carrier On-Time Rate`"),
}
for mv, (dim, meas) in tests.items():
    df = spark.sql(f"SELECT {dim}, MEASURE({meas}) AS value FROM {fq(GOLD_SCHEMA, mv)} GROUP BY ALL ORDER BY value DESC LIMIT 3")
    print(f"\n{mv}: top {dim} by {meas}")
    for r in df.collect():
        print(f"   {r[0]!s:<40} {r[1]:,.4f}")
