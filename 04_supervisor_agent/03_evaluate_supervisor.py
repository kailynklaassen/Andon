# Databricks notebook source
# MAGIC %md
# MAGIC # Step 4c · Evaluate the supervisor (the regression test for the agentic framework)
# MAGIC
# MAGIC **What this does:** runs the evaluation set in [`eval/eval_set.yml`](./eval/eval_set.yml) through **the same agent
# MAGIC code the app runs** ([`agent/foreman.py`](./agent/foreman.py), loaded here in the notebook against the live Genie
# MAGIC spaces) with `mlflow.genai.evaluate()`, and scores every answer on four things:
# MAGIC
# MAGIC | Scorer | Type | Question it answers |
# MAGIC |---|---|---|
# MAGIC | `routing` | code | Did the supervisor consult every domain the question needs? |
# MAGIC | `correctness` | LLM judge | Does the answer contain the expected facts (from the narrative bible)? |
# MAGIC | `cites_sources` | LLM judge (guidelines) | Does it cite the Genie space and/or document IDs it used? |
# MAGIC | `latency_seconds` | code | How long did the whole multi-agent answer take? |
# MAGIC
# MAGIC Results land in the MLflow experiment as an evaluation run — compare runs side by side every time you change the
# MAGIC system prompt, a model, or a Genie space. This is the regression test for the agentic framework.
# MAGIC
# MAGIC **Why in the notebook and not over HTTP:** the agent's behavior is the code + config, not the host. Running it
# MAGIC in-process scores exactly what the Agent Server serves (same loop), needs no OAuth hop, and gives one trace per case.
# MAGIC
# MAGIC **Crucial:** an evaluation set grounded in the data's real answers (here, the narrative bible) and a routing scorer —
# MAGIC wrong routing is the most common way a multi-agent system fails silently. **Optional:** the LLM judges' wording.
# MAGIC
# MAGIC The install below uses the agent's own `agent/requirements.txt`, so the evaluation scores exactly the stack the
# MAGIC deployed agent runs on (a loose `-U mlflow … databricks-openai` against the serverless base environment backtracked
# MAGIC for 49 minutes and failed).

# COMMAND ----------

# MAGIC %pip install -q -r ./agent/requirements.txt
# MAGIC %restart_python

# COMMAND ----------

# MAGIC %run ../config/config

# COMMAND ----------

import json, time, yaml
import mlflow
from mlflow.entities import Feedback
import os
from mlflow.genai.scorers import Correctness, Guidelines, scorer
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
SUP = CFG["supervisor"]
ME = w.current_user.me().user_name
mlflow.set_experiment(f"/Users/{ME}/{SUP['name']}/supervisor_experiment")

cases = yaml.safe_load(open(f"{REPO_ROOT}/04_supervisor_agent/eval/eval_set.yml"))["cases"]
# Genie answers as the identity running this notebook, so confidential values are visible or masked depending on its
# groups: governance cases carry both expectations and we score the one that applies to this identity.
cleared_groups = CFG["governance"]["confidential"]["visible_to"]
CLEARED = spark.sql("SELECT " + " OR ".join(f"is_account_group_member('{g}')" for g in cleared_groups) + " AS c").first().c
print(f"evaluating as {ME} — {'sees' if CLEARED else 'does not see'} confidential values ({', '.join(cleared_groups)})")
data = [{"inputs": {"question": c["question"]},
         "expectations": {"expected_facts": c.get("expected_facts_if_cleared", c["expected_facts"]) if CLEARED else c["expected_facts"],
                          "expected_tools": c["expected_tools"]}} for c in cases]
print(f"{len(data)} evaluation cases")

# COMMAND ----------

# MAGIC %md
# MAGIC ### The agent under test: Foreman, in-process
# MAGIC Same `foreman.py`, same `supervisor_config.yaml` (Step 4b writes it from the Genie registry), same models.

# COMMAND ----------

import sys
AGENT_DIR = f"{REPO_ROOT}/04_supervisor_agent/agent"
sys.path.insert(0, AGENT_DIR)
import build_config
from foreman import Foreman
registry = [r.asDict() for r in spark.table(f"{CATALOG}.{GOLD_SCHEMA}.genie_space_registry").collect()]
agent = Foreman(build_config.build(CFG, registry, COMPANY))      # no memory: every case starts fresh
mlflow.openai.autolog()

def predict_fn(question: str) -> dict:
    t0, tools, answer = time.time(), [], ""
    for ev in agent.run(question, user=ME):
        if ev["type"] == "step" and ev.get("kind") == "route":
            tools.append(f"ask_{ev['domain']}_genie")
        elif ev["type"] == "answer":
            answer = ev["text"]
    return {"response": answer, "tools_called": tools, "latency_seconds": round(time.time() - t0, 1)}

# COMMAND ----------

@scorer
def routing(outputs: dict, expectations: dict) -> Feedback:
    called = {t.removeprefix("ask_").removesuffix("_genie") for t in outputs["tools_called"]}
    missing = set(expectations["expected_tools"]) - called
    return Feedback(value=not missing,
                    rationale=f"called={sorted(called)} expected={expectations['expected_tools']} missing={sorted(missing)}")

@scorer
def latency_seconds(outputs: dict) -> float:
    return outputs["latency_seconds"]

cites_sources = Guidelines(
    name="cites_sources",
    guidelines=["The response cites where its facts came from: a domain/Genie space name in brackets such as "
                "[Production] or [Maintenance], and/or a document ID such as RCA-2026-GVL-007 or SOP-PRD-001."])

# Evaluate like real traffic, not a burst: 4 questions at a time. (23 at once queues every Genie call on one small
# warehouse and doubles the measured latency.)
os.environ["MLFLOW_GENAI_EVAL_MAX_WORKERS"] = "4"
results = mlflow.genai.evaluate(data=data, predict_fn=predict_fn,
                                scorers=[routing, Correctness(), cites_sources, latency_seconds])
print(json.dumps({k: round(v, 3) for k, v in results.metrics.items()}, indent=2))

# COMMAND ----------

# MAGIC %md
# MAGIC ### Per-question results
# MAGIC Open the evaluation run in the MLflow UI for full traces (every LLM turn and Genie call) behind each row.

# COMMAND ----------

df = results.tables["eval_results"]
cols = [c for c in df.columns if c.endswith("/value") or c in ("request", "inputs")]
display(df[cols] if cols else df)

dbutils.notebook.exit(json.dumps({k: round(v, 3) for k, v in results.metrics.items()}))
