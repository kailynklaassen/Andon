# Databricks notebook source
# MAGIC %md
# MAGIC # Step 1 · Generate raw source-system data
# MAGIC
# MAGIC **What this does:** simulates one fiscal year (FY2026) of operations at *KK's Parts* —
# MAGIC 5 plants → 15 production lines → 70 work centers, 3 distribution centers, 24 suppliers, 48 customers —
# MAGIC and lands it as **raw files** in a Unity Catalog Volume, organized the way real extracts arrive:
# MAGIC
# MAGIC | Source system | What lands | Format |
# MAGIC |---|---|---|
# MAGIC | `erp` | plants, parts, BOM, suppliers, materials, customers, carriers, purchase orders, receipts, production orders, sales orders | CSV |
# MAGIC | `mes` | production lines, work centers, shift production results, downtime events | JSON |
# MAGIC | `cmms` | maintenance work orders (PM / corrective / emergency) | CSV |
# MAGIC | `qms` | inspections (with SPC measurements), nonconformances (NCRs), CAPAs | CSV |
# MAGIC | `wms` | daily inventory snapshots, outbound shipments | Parquet / CSV |
# MAGIC | `iot_historian` | hourly machine telemetry (vibration, temperature, load, power) | JSON (monthly files) |
# MAGIC | `hr` | employees | CSV |
# MAGIC
# MAGIC **Why raw files instead of tables?** Because that's what customers actually have. Step 2 (the medallion
# MAGIC pipeline) is where Auto Loader ingests these into bronze, cleans them in silver, and builds gold —
# MAGIC the same path a real implementation would take.
# MAGIC
# MAGIC **Why the data is *correlated*, not random:** the agents need something real to find. The generator
# MAGIC (`mfg_datagen.py`) plants four storylines from the `story:` block of `demo_config.yml`:
# MAGIC
# MAGIC 1. **Failing spindle** — `GVL-L3-WC01` vibration drifts past the OEM limit months before the internal PM limit → breakdowns, emergency work orders, OEE collapse on Greenville Gearbox Assembly.
# MAGIC 2. **Problem supplier** — Brightline Castings goes late and porous → material-shortage downtime, porosity NCRs, an overdue SCAR.
# MAGIC 3. **Problem carrier** — Ridgeway Freight misses its on-time SLA out of the Memphis DC.
# MAGIC 4. **Night-shift quality** — crimp-height defects on Wroclaw's crimp press, C shift only, after a die change.
# MAGIC
# MAGIC Runtime: ~2 minutes on serverless.

# COMMAND ----------

# MAGIC %md
# MAGIC ### Why this step matters
# MAGIC Agents are only as good as the data they reason over. Realistic source-system extracts (ERP, MES, CMMS, QMS, WMS, IoT, HR) with **planted, causally consistent problems** give the agent something true to find — and give the evaluation (4c) known right answers.
# MAGIC
# MAGIC **Crucial**
# MAGIC * Raw files that look like real source systems (messy codes, resends, late arrivals) — the pipeline's job is to clean them.
# MAGIC * A fixed `data.seed`: same data every run, so the documents, benchmarks and evaluation stay accurate.
# MAGIC
# MAGIC **Optional**
# MAGIC * Data volume (`data.*`) and the company/storylines — swap in your own domain.

# COMMAND ----------

# MAGIC %run ../config/config

# COMMAND ----------

# Make the generator module importable (it sits next to this notebook).
import os, sys, json
sys.path.insert(0, os.path.join(REPO_ROOT, "01_data_generation"))
import importlib, mfg_datagen
importlib.reload(mfg_datagen)

# Create schemas + volumes the demo needs (no-op if they exist).
ensure_uc_objects()
print(f"Raw files will land in {RAW_PATH}")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Run the simulation
# MAGIC Each phase builds on the previous one — purchasing creates late deliveries, which create material
# MAGIC shortages; maintenance creates breakdowns; both feed the shift production results (OEE), which feed
# MAGIC finished-goods availability and, finally, customer shipments.

# COMMAND ----------

gen = mfg_datagen.MfgGenerator(CFG)
tables = gen.run()

# COMMAND ----------

# MAGIC %md
# MAGIC ### Land the files
# MAGIC Writes `RAW_PATH/<source_system>/<entity>/…` plus `RAW_PATH/_story/story_anchors.json` — the exact
# MAGIC numbers behind each storyline. The Genie documents in `01_data_generation/documents/` are written
# MAGIC around those numbers, so a SQL answer and a document answer agree.

# COMMAND ----------

manifest = mfg_datagen.write_tables(tables, RAW_PATH, gen.anchors)
display(manifest)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Storyline check
# MAGIC Quick proof that the planted patterns are present before we build anything on top of them.

# COMMAND ----------

a = gen.anchors
fm, sp, cr, qi = a["failing_machine"], a["problem_supplier"], a["problem_carrier"], a["quality_shift_issue"]
checks = [
    ("Failing spindle: vibration crosses OEM limit", fm["first_month_above_oem_limit"] is not None, f"first month above {fm['oem_limit_mm_s']} mm/s = {fm['first_month_above_oem_limit']}"),
    ("Failing spindle: repeated breakdowns", fm["breakdowns_since_degradation"] >= 15, f"{fm['breakdowns_since_degradation']} breakdowns since {fm['degradation_start']}"),
    ("Problem supplier: PPM above contract", sp["ppm_after"] > sp["contract_ppm_limit"], f"{sp['ppm_after']:.0f} PPM vs {sp['contract_ppm_limit']} limit"),
    ("Problem supplier: on-time collapse", sp["on_time_after"] < 0.7, f"on-time {sp['on_time_before']:.0%} → {sp['on_time_after']:.0%}"),
    ("Problem carrier: below SLA", cr["on_time_all_lanes"] < cr["sla"] - 0.1, f"{cr['on_time_all_lanes']:.0%} vs {cr['sla']:.0%} SLA"),
    ("Night-shift crimp defects", qi["defect_rate_by_period_shift"]["after_C"] > 3 * qi["defect_rate_by_period_shift"]["after_A"],
     f"C shift {qi['defect_rate_by_period_shift']['after_C']:.1%} vs A shift {qi['defect_rate_by_period_shift']['after_A']:.1%}"),
]
for name, ok, detail in checks:
    print(f"{'✅' if ok else '❌'} {name:<48} {detail}")
assert all(ok for _, ok, _ in checks), "A storyline did not materialize — check the story: block in demo_config.yml"
