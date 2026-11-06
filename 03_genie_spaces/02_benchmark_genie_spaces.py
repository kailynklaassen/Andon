# Databricks notebook source
# MAGIC %md
# MAGIC # Step 3c · Benchmark the Genie spaces
# MAGIC
# MAGIC **Why:** a Genie space is only as good as the answers it gives. Each space spec
# MAGIC (`spaces/<domain>.yml → benchmarks`) carries ~12 questions whose expected answers come straight from the
# MAGIC storylines in `NARRATIVE_BIBLE.md` — the spindle failure, Brightline Castings, Ridgeway Freight and the night-shift
# MAGIC crimp defects. This notebook asks every question, scores the answers and saves the run, so you can see whether a
# MAGIC change to a space (instructions, example SQL, column descriptions) made it better or worse.
# MAGIC
# MAGIC | Benchmark type | How it's scored |
# MAGIC |---|---|
# MAGIC | `sql` — the certified answer | We run the SQL ourselves; every expected value must appear in Genie's result (numbers within 1%). For "which is highest/lowest" questions the answer must be Genie's **first** row. |
# MAGIC | `expect_doc` — a document question | Genie must surface that document ID — asked in **Agent mode**, which searches the documents attached to the space. |
# MAGIC
# MAGIC The SQL-answer benchmarks are also loaded into each space's **Benchmarks** tab, so you can run them from the Genie UI.
# MAGIC This notebook uses the GA Conversation API (the benchmark-run API is Beta).
# MAGIC
# MAGIC Results land in `<gold>.genie_benchmark_results` (one row per question per run).

# COMMAND ----------

# MAGIC %md
# MAGIC ### Why this step matters
# MAGIC If an expert is wrong, the supervisor will be confidently wrong. Benchmarks per space catch that **before** you blame the agent.
# MAGIC
# MAGIC **Crucial**
# MAGIC * Benchmarks with exact expected values from the data.
# MAGIC
# MAGIC **Optional**
# MAGIC * Running it on every build (run it after changing a space's instructions).

# COMMAND ----------

# MAGIC %run ../config/config

# COMMAND ----------

import glob, sys, yaml
from datetime import datetime, timezone
from databricks.sdk import WorkspaceClient

sys.path.insert(0, f"{REPO_ROOT}/03_genie_spaces")
import genie_benchmark as gb

w = WorkspaceClient()
GOLD = f"`{CATALOG}`.`{GOLD_SCHEMA}`"
spaces = {r.domain_key: r.space_id for r in spark.table(f"{CATALOG}.{GOLD_SCHEMA}.genie_space_registry").collect()}
benchmarks = {}
for path in sorted(glob.glob(f"{REPO_ROOT}/03_genie_spaces/spaces/*.yml")):
    spec = yaml.safe_load(open(path))
    benchmarks[spec["key"]] = spec.get("benchmarks", [])
print({d: len(b) for d, b in benchmarks.items()})

def run_sql(sql: str) -> list:
    return [[None if v is None else str(v) for v in row] for row in spark.sql(sql).collect()]

# COMMAND ----------

# MAGIC %md
# MAGIC ## Run (the four spaces in parallel, questions within a space one at a time)

# COMMAND ----------

run_ts = datetime.now(timezone.utc)
results = gb.run_suite(w, spaces, benchmarks, run_sql, GOLD)
df = spark.createDataFrame([{**r, "run_ts": run_ts} for r in results])
df.write.mode("append").option("mergeSchema", "true").saveAsTable(f"{CATALOG}.{GOLD_SCHEMA}.genie_benchmark_results")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Scorecard and failures

# COMMAND ----------

display(spark.sql(f"""
  SELECT domain, count(*) AS questions, sum(CASE WHEN status = 'PASS' THEN 1 ELSE 0 END) AS passed,
         round(avg(CASE WHEN status = 'PASS' THEN 1.0 ELSE 0 END), 2) AS pass_rate, round(avg(seconds), 1) AS avg_seconds
  FROM {CATALOG}.{GOLD_SCHEMA}.genie_benchmark_results WHERE run_ts = '{run_ts.isoformat()}' GROUP BY domain ORDER BY domain"""))
display(df.filter("status != 'PASS'").select("domain", "question", "status", "reason", "expected", "genie_rows", "genie_sql"))

# COMMAND ----------

passed = sum(r["status"] == "PASS" for r in results)
dbutils.notebook.exit(f"{passed}/{len(results)} benchmark questions passed")
