# Databricks notebook source
# MAGIC %md
# MAGIC # 99 · Run all — build the whole KK's Parts agentic framework end to end
# MAGIC
# MAGIC **This is the only notebook you need to run.** It runs `config/00_preflight` (checks your workspace), then every step
# MAGIC in dependency order. Each step is also its own notebook that you can open and run alone — they all load the same
# MAGIC config — and every step is idempotent, so re-running is safe. Use the widgets to skip steps you've already built.
# MAGIC
# MAGIC | Step | Notebook | Builds | |
# MAGIC |---|---|---|---|
# MAGIC | 0 | `00_lakebase/00_setup_lakebase` | the Lakebase project: the app's ledger + Foreman's sessions, memory, run log | crucial |
# MAGIC | 1 | `01_data_generation/01_generate_raw_data`, `02_publish_documents` | raw source-system files + 40 domain PDFs | crucial |
# MAGIC | 2 | `02_medallion_pipeline/01_run_medallion_pipeline`, `02_create_metric_views` | bronze → silver → gold, 9 metric views | crucial |
# MAGIC | 2c | `02b_unity_catalog_governance/*` | groups, users, grants, ABAC column mask | crucial |
# MAGIC | 3b | `03_genie_spaces/01_create_genie_spaces`, `02_benchmark_genie_spaces` | 4 domain Genie spaces (the agent's tools) + benchmarks | crucial · benchmarks optional |
# MAGIC | 4b | `04_supervisor_agent/02_deploy_agent_app` | **Foreman** agent server on Databricks Apps (UC traces, sessions, memory, run log, Genie on behalf of the user) | crucial |
# MAGIC | 4c | `04_supervisor_agent/03_evaluate_supervisor` | MLflow evaluation: routing, correctness, citations, latency | crucial |
# MAGIC | 6a | `06_human_in_the_loop/00_setup_hitl_sync` | correction tables, notes volumes, the sync job | crucial for the human loop |
# MAGIC | 5 | `05_app/00_deploy_app` | **Andon** app (FastAPI + React) | crucial |
# MAGIC
# MAGIC **Why this order:** governance (2c) comes before the Genie spaces (3b) so every group can read its volumes; the human-in-the-loop setup (6a) comes before the app (5) because the app gets the sync job as a resource.
# MAGIC
# MAGIC **Prerequisites:** a workspace admin, a catalog you can create schemas in, and the models in `supervisor.*_llm`.
# MAGIC First run end to end: ~60-90 minutes (most of it the pipeline, document parsing and app builds).

# COMMAND ----------

dbutils.widgets.dropdown("run_data_generation", "true", ["true", "false"], "1. Generate data + documents")
dbutils.widgets.dropdown("run_pipeline", "true", ["true", "false"], "2. Medallion pipeline + metric views")
dbutils.widgets.dropdown("run_genie", "true", ["true", "false"], "3. Document search + Genie spaces")
dbutils.widgets.dropdown("run_governance", "true", ["true", "false"], "2c. UC governance (tags, grants, ABAC)")
dbutils.widgets.dropdown("run_supervisor", "true", ["true", "false"], "4. Foreman agent (build, deploy, evaluate)")
dbutils.widgets.dropdown("run_hitl", "true", ["true", "false"], "6. Human in the loop (Lakebase → lakehouse sync)")
dbutils.widgets.dropdown("run_app", "true", ["true", "false"], "5. Andon app")
dbutils.widgets.text("catalog", "", "Override catalog (optional)")
dbutils.widgets.text("warehouse_id", "", "Override warehouse id (optional)")

# COMMAND ----------

# MAGIC %run ./config/00_preflight

# COMMAND ----------

import time

ARGS = {"catalog": dbutils.widgets.get("catalog"), "warehouse_id": dbutils.widgets.get("warehouse_id")}
RUN = {k: dbutils.widgets.get(k) == "true" for k in
       ("run_data_generation", "run_pipeline", "run_governance", "run_genie", "run_supervisor", "run_hitl", "run_app")}
if failed:                                                   # from config/00_preflight
    raise RuntimeError(f"Pre-flight checks failed: {failed}. Fix them (see the output above) and re-run.")


def step(label: str, notebook: str, timeout_min: int = 60) -> None:
    """Run one step notebook in its own context and report how long it took."""
    t0 = time.time()
    print(f"▶ {label} ...", flush=True)
    result = dbutils.notebook.run(f"{REPO_ROOT}/{notebook}", timeout_min * 60, ARGS)
    print(f"  ✓ {label} ({(time.time() - t0) / 60:.1f} min) {result or ''}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 0 · Lakebase (first: both apps attach it, and provisioning takes a few minutes)

# COMMAND ----------

if RUN["run_supervisor"] or RUN["run_hitl"] or RUN["run_app"]:
    step("0  Lakebase project (ledger, sessions, memory, run log)", "00_lakebase/00_setup_lakebase", 20)
else:
    print("⏭ skipped (nothing that uses Lakebase is selected)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1 · Data and documents

# COMMAND ----------

if RUN["run_data_generation"]:
    step("1a Generate raw source-system data", "01_data_generation/01_generate_raw_data")
    step("1b Publish domain documents (PDF) to the genie_docs volumes", "01_data_generation/02_publish_documents")
else:
    print("⏭ skipped")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2 · Medallion pipeline + metric views

# COMMAND ----------

if RUN["run_pipeline"]:
    step("2a Bronze → silver → gold pipeline", "02_medallion_pipeline/01_run_medallion_pipeline", 90)
    step("2b Metric views", "02_medallion_pipeline/02_create_metric_views")
else:
    print("⏭ skipped")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2c · Unity Catalog governance (tags, domain grants, ABAC)

# COMMAND ----------

if RUN["run_governance"]:
    step("2c-0 Account groups and demo users", "02b_unity_catalog_governance/00_create_groups_and_users")
    step("2c Tags, domain grants and ABAC column mask", "02b_unity_catalog_governance/01_tags_grants_abac")
else:
    print("⏭ skipped")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3b · Genie spaces (the agent's domain experts)

# COMMAND ----------

if RUN["run_genie"]:
    step("3b Create / update the four Genie spaces", "03_genie_spaces/01_create_genie_spaces")
    step("3c Benchmark the Genie spaces (narrative-grounded)", "03_genie_spaces/02_benchmark_genie_spaces", 60)
    for r in spark.table(f"{CATALOG}.{GOLD_SCHEMA}.genie_space_registry").collect():
        print(f"• {r.title}\n    {r.url}\n    {r.docs_status}")
else:
    print("⏭ skipped")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4 · Foreman, the supervisor agent
# MAGIC 4b deploys Foreman on the **Agent Server** (AgentKit `DurableAgentServer`) on Databricks Apps — the app calls it.
# MAGIC 4c evaluates the same agent loop in-process against the evaluation set, into MLflow.

# COMMAND ----------

if RUN["run_supervisor"]:
    step("4b Deploy Foreman on the Agent Server (Databricks Apps)", "04_supervisor_agent/02_deploy_agent_app", 45)
    step("4c Evaluate the agent", "04_supervisor_agent/03_evaluate_supervisor", 60)
else:
    print("⏭ skipped")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 6a · Human in the loop (before the app: the app gets the sync job as a resource)
# MAGIC The app writes human actions to Lakebase; approved ones come back on a schedule: value corrections into bronze
# MAGIC (flagged `_altered_in_app`), notes into the Genie document search.

# COMMAND ----------

if RUN["run_hitl"]:
    step("6a Correction tables, notes volumes, sync job", "06_human_in_the_loop/00_setup_hitl_sync", 30)
else:
    print("⏭ skipped")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 5 · The Andon app

# COMMAND ----------

if RUN["run_app"]:
    step("5  Deploy the Andon app (FastAPI + React)", "05_app/00_deploy_app", 30)
else:
    print("⏭ skipped")
