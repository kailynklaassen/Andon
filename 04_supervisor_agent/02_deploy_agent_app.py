# Databricks notebook source
# MAGIC %md
# MAGIC # Step 4b · Deploy Foreman on the Agent Server (AgentKit `DurableAgentServer`) on Databricks Apps
# MAGIC
# MAGIC **What this does:** deploys [`agent/`](./agent) as the Databricks App **`kkparts-foreman`**: the one agent loop in
# MAGIC [`agent/foreman.py`](./agent/foreman.py), hosted on the **Agent Server** — AgentKit's `DurableAgentServer`
# MAGIC (`databricks-agentbricks`, GA), the server Databricks recommends for new agents. The Andon app (Step 5) calls it.
# MAGIC
# MAGIC **Why the Agent Server:** custom FastAPI orchestrators and the MLflow / ai-bridge agent servers are now the *legacy*
# MAGIC path. The Agent Server gives every agent the same protocol (`POST /api/invocations`) and **durable runs**: each
# MAGIC question, its streamed events and its answer live in a Runtime Store, so a dropped connection or a redeploy doesn't
# MAGIC lose the answer — the client reconnects to `…/events?after=N`. Invocations in a session run in order.
# MAGIC
# MAGIC **The GA route — no Agent Bricks CLI** (the CLI is Beta): this notebook creates the app, its resources and grants over the
# MAGIC Apps REST API, and points the Runtime Store at the app's own Lakebase resource (schema
# MAGIC `supervisor.runtime_store_schema`) — the configuration AgentKit supports for an Apps `postgres` resource.
# MAGIC When the Agent Bricks CLI reaches GA, `agentbricks deploy` can replace this notebook; the agent code doesn't change.
# MAGIC
# MAGIC | | Model Serving (legacy) | Agent Server on Apps (this step) |
# MAGIC |---|---|---|
# MAGIC | First question after idle | ~2 min cold start (scale-to-zero) | warm — the app stays up |
# MAGIC | What the UI can show while it works | Responses items | any event: Genie's live status, SQL, rows, tokens |
# MAGIC | If the connection drops | the answer is lost | durable: reconnect and get the rest |
# MAGIC | Extra routes | none | sessions, memories, run log, info — it's FastAPI |
# MAGIC | Identity | an SP + OAuth secret in a secret scope | the app's own service principal, no secret to manage |
# MAGIC
# MAGIC **What is crucial vs optional here**
# MAGIC * **Crucial** — the Genie space + SQL warehouse resources (the agent's tools), the MLflow experiment resource (every
# MAGIC   request is traced there, into **Unity Catalog tables**), and Unity Catalog `SELECT`/`EXECUTE` on gold (with
# MAGIC   `genie_auth: service_principal`, Genie reads the data *as the app*).
# MAGIC * **Crucial for per-user governance** — `supervisor.genie_auth: on_behalf_of_user` (Apps user authorization, GA).
# MAGIC   Genie then runs as the person asking: the Andon app passes their Genie-scoped token with each question.
# MAGIC * **Optional** — the Lakebase `postgres` resource. It turns on sessions (conversation history by `session_id`) and
# MAGIC   long-term memory. Without it the agent still answers; it just forgets between questions.
# MAGIC
# MAGIC **Governance:** with `on_behalf_of_user`, each answer shows exactly what the asker may see — a procurement user sees
# MAGIC supplier prices, a production user sees them masked, a user without a domain's group gets "no access" for that
# MAGIC expert. With `service_principal`, everyone gets the app's view (not in the confidential groups → masked).

# COMMAND ----------

# MAGIC %pip install -q -U "databricks-sdk>=0.81" "mlflow[databricks]>=3.14" pyyaml
# MAGIC %restart_python

# COMMAND ----------

# MAGIC %run ../config/config

# COMMAND ----------

import json, os, sys, time
from databricks.sdk import WorkspaceClient
from databricks.sdk.errors import NotFound

w = WorkspaceClient()
SUP, H = CFG["supervisor"], CFG["hitl"]
APP = SUP["app_name"]
AGENT_DIR = f"{REPO_ROOT}/04_supervisor_agent/agent"
ME = w.current_user.me().user_name
WAREHOUSE_ID = get_warehouse_id()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1 · The agent's configuration
# MAGIC `supervisor_config.yaml` is the only place the agent learns about this company: the Genie spaces (from the registry
# MAGIC Step 3 wrote), the system prompt, and the two models. Written next to the code so it ships with the app.

# COMMAND ----------

sys.path.insert(0, AGENT_DIR)
import build_config
registry = [r.asDict() for r in spark.table(f"{CATALOG}.{GOLD_SCHEMA}.genie_space_registry").collect()]
agent_config = build_config.build(CFG, registry, COMPANY)
print(f"wrote {build_config.write(agent_config)}")
print(f"router: {agent_config['router_llm']}   answer: {agent_config['answer_llm']}   tools: {len(registry)} Genie spaces")

# COMMAND ----------

# `agent/app.yaml`: resource IDs arrive through `valueFrom`; the rest is rendered from config, so nobody edits it by hand.
import yaml
LB0 = H["lakebase"]
env = [{"name": "MLFLOW_EXPERIMENT_ID", "valueFrom": "experiment"},
       {"name": "LAKEBASE_ENDPOINT_PATH", "value": f"projects/{LB0['project']}/branches/{LB0['branch']}/endpoints/{LB0['endpoint']}"},
       {"name": "FOREMAN_SCHEMA", "value": SUP.get("memory_schema", "foreman")},
       {"name": "FOREMAN_ROUTER_LLM", "value": agent_config["router_llm"]},
       {"name": "FOREMAN_ANSWER_LLM", "value": agent_config["answer_llm"]},
       {"name": "FOREMAN_GENIE_AUTH", "value": SUP.get("genie_auth", "service_principal")},
       {"name": "FOREMAN_GENIE_MODE", "value": SUP.get("genie_mode", "agent")},
       # Agent Server Runtime Store (AgentKit DurableAgentServer): durable invocations in this app's own Lakebase
       # resource, no Agent Bricks CLI. Supported in the SDK (runtime/store.py: from_app_resource, which it calls the
       # "legacy Apps resource" path) but not in the public docs, which describe only the CLI-provisioned store: pin
       # databricks-agentbricks and re-test on upgrade
       {"name": "DATABRICKS_AGENTBRICKS_RUNTIME_STORE_LAKEBASE_ENDPOINT",
        "value": f"projects/{LB0['project']}/branches/{LB0['branch']}/endpoints/{LB0['endpoint']}"},
       {"name": "DATABRICKS_AGENTBRICKS_RUNTIME_STORE_SCHEMA", "value": SUP.get("runtime_store_schema", "foreman_runtime")},
       {"name": "MLFLOW_TRACING_SQL_WAREHOUSE_ID", "valueFrom": "sql-warehouse"},     # reading UC traces back
       {"name": "FOREMAN_TRACE_TABLES", "value": f"{CATALOG}.{SUP['traces']['schema']}.{SUP['traces']['table_prefix']}_otel_spans"}]
header = open(f"{AGENT_DIR}/app.yaml").read().split("command:")[0]
with open(f"{AGENT_DIR}/app.yaml", "w") as f:
    f.write(header + yaml.safe_dump({"command": ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"], "env": env},
                                    sort_keys=False, width=120))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2 · Where the traces go — Unity Catalog (GA)
# MAGIC One experiment for the agent's production traces. Every question becomes one trace: a span for each model call and
# MAGIC each Genie call, tagged with `mlflow.trace.session` and `mlflow.trace.user` so the MLflow UI can group a conversation.
# MAGIC
# MAGIC The experiment is **bound to Unity Catalog tables** (`<catalog>.<traces schema>.<prefix>_otel_spans`, `_logs`,
# MAGIC `_metrics`, `_annotations`). Why it matters: unlimited retention, UC permissions on who can read traces, and every
# MAGIC trace is a row you can query from SQL, notebooks, dashboards and Genie. Spans go to the workspace's OTel endpoint
# MAGIC (no direct cloud-storage upload from the app). A binding is set at creation and can't be changed, so a UC-bound
# MAGIC experiment is always a new experiment.

# COMMAND ----------

import mlflow
from mlflow.entities.trace_location import UnityCatalog

TR = SUP["traces"]
TRACE_SCHEMA = TR["schema"]
spark.sql(f"CREATE SCHEMA IF NOT EXISTS `{CATALOG}`.`{TRACE_SCHEMA}` COMMENT 'MLflow traces of the Foreman agent (OpenTelemetry tables)'")
os.environ["MLFLOW_TRACING_SQL_WAREHOUSE_ID"] = WAREHOUSE_ID      # the warehouse MLflow reads UC traces through
mlflow.set_tracking_uri("databricks")
exp_path = f"/Users/{ME}/{SUP['name']}/{TR['experiment']}"
w.workspace.mkdirs(f"/Workspace/Users/{ME}/{SUP['name']}")
exp = mlflow.set_experiment(experiment_name=exp_path, trace_location=UnityCatalog(
    catalog_name=CATALOG, schema_name=TRACE_SCHEMA, table_prefix=TR["table_prefix"]))
exp_id = exp.experiment_id
TRACE_TABLES = [f"{CATALOG}.{TRACE_SCHEMA}.{TR['table_prefix']}_otel_{t}" for t in ("spans", "logs", "metrics", "annotations")]
print(f"traces → {exp_path} ({exp_id})")
for t in TRACE_TABLES:
    print("   ", t, "✅" if spark.catalog.tableExists(t) else "— created on first trace")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3 · The app and its resources
# MAGIC Each resource both **grants** the app's service principal access and **injects** a value into `agent/app.yaml`
# MAGIC (`valueFrom`). That is why there is no secret, token or ID hard-coded anywhere in the agent.

# COMMAND ----------

LB = H["lakebase"]
branch = f"projects/{LB['project']}/branches/{LB['branch']}"
resources = [{"name": f"genie-{r['domain_key'].replace('_', '-')}",
              "genie_space": {"space_id": r["space_id"], "name": r["title"], "permission": "CAN_RUN"}} for r in registry]
resources += [{"name": "sql-warehouse", "sql_warehouse": {"id": WAREHOUSE_ID, "permission": "CAN_USE"}},
              {"name": "experiment", "experiment": {"experiment_id": exp_id, "permission": "CAN_EDIT"}}]
MODELS = list(dict.fromkeys([agent_config["router_llm"], agent_config["answer_llm"]]))   # the models the agent calls
if SUP.get("memory", True):                                       # optional: sessions + long-term memory
    resources.append({"name": "postgres", "postgres": {"branch": branch, "database": f"{branch}/databases/{LB['database']}",
                                                       "permission": "CAN_CONNECT_AND_CREATE"}})
spec = {"name": APP, "description": f"{COMPANY} Foreman: the operations supervisor agent (Agent Server: AgentKit DurableAgentServer)",
        "resources": resources}
try:
    w.api_client.do("GET", f"/api/2.0/apps/{APP}")
    w.api_client.do("POST", f"/api/2.0/apps/{APP}/update", body={"app": spec, "update_mask": "resources,description"})
    for _ in range(60):          # a deployment can't start while the resource update is still running
        u = w.api_client.do("GET", f"/api/2.0/apps/{APP}/update").get("status", {}).get("state")
        if u not in ("IN_PROGRESS", "PENDING"):
            break
        time.sleep(5)
    print(f"updated app {APP} ({u})")
except NotFound:
    w.api_client.do("POST", "/api/2.0/apps", body=spec)
    print(f"created app {APP} (compute starting)")
for _ in range(60):                                               # compute must be ACTIVE before a deployment
    app = w.api_client.do("GET", f"/api/2.0/apps/{APP}")
    if app.get("compute_status", {}).get("state") == "ACTIVE":
        break
    time.sleep(10)
SP = app["service_principal_client_id"]
print(f"service principal {SP}  ·  {app.get('url')}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4 · Unity Catalog grants
# MAGIC * gold: with `genie_auth: service_principal`, Genie runs its SQL and document search *as the app*, so the app
# MAGIC   needs the grants a person using the spaces would (least privilege: gold only). With `on_behalf_of_user` these
# MAGIC   are unused for Genie — each person's own grants apply — but keep them for the evaluation notebook (4c).
# MAGIC * traces: the app writes its traces into the UC trace tables.

# COMMAND ----------

grants = [f"GRANT USE CATALOG ON CATALOG `{CATALOG}` TO `{SP}`",
          f"GRANT USE SCHEMA, SELECT, EXECUTE ON SCHEMA `{CATALOG}`.`{GOLD_SCHEMA}` TO `{SP}`",
          # writing traces: USE SCHEMA + MODIFY and SELECT on each trace table (ALL PRIVILEGES is not enough)
          # the schema holds only trace tables, so schema-level MODIFY + SELECT is still least privilege — and it
          # covers tables MLflow creates later
          f"GRANT USE SCHEMA, MODIFY, SELECT ON SCHEMA `{CATALOG}`.`{TRACE_SCHEMA}` TO `{SP}`"]
grants += [f"GRANT MODIFY, SELECT ON TABLE {t} TO `{SP}`" for t in TRACE_TABLES if spark.catalog.tableExists(t)]
# Genie Agent mode reads attached files as the caller: with genie_auth = service_principal (and the eval notebook),
# that is this app — so it may read every domain's documents + notes volumes
grants += [f"GRANT USE SCHEMA ON SCHEMA `{CATALOG}`.`{LANDING_SCHEMA}` TO `{SP}`"]
grants += [f"GRANT READ VOLUME ON VOLUME `{CATALOG}`.`{LANDING_SCHEMA}`.`{v}` TO `{SP}`"
           for s_ in CFG["genie"]["spaces"] for v in (docs_volume(s_["docs_folder"]), notes_volume(s_["key"]))]
for stmt in grants:
    spark.sql(stmt)
    print(" ", stmt)

# Foundation models are Unity Catalog objects (system.ai.<model>), called by this app as its service principal.
# By default every principal inherits EXECUTE on them from the `system` catalog / `system.ai` schema, so usually there's
# nothing to do here. If an admin has restricted a model, the app needs EXECUTE on it: granted below if you have
# MANAGE on the model; otherwise the cell stops and says what to ask for. (No app resource is needed for these models.)
def can_execute(model: str) -> bool:
    eff = w.grants.get_effective(securable_type="function", full_name=f"system.ai.{model}", principal=SP)
    return any(str(p.privilege).endswith(("EXECUTE", "ALL_PRIVILEGES"))
               for a in (eff.privilege_assignments or []) for p in (a.privileges or []))

missing = []
for m in MODELS:
    if not m.startswith("databricks-"):
        continue                                       # not a Databricks-hosted foundation model
    if can_execute(m):
        print(f"✅ the app can call {m}")
        continue
    stmt = f"GRANT EXECUTE ON FUNCTION system.ai.`{m}` TO `{SP}`"
    try:
        spark.sql(stmt)
        print(f"  {stmt}   (access to {m} is restricted in this workspace)")
    except Exception as e:
        missing.append(m)
        print(f"⚠️ access to {m} is restricted and you can't grant it ({str(e)[:120]})")
if missing:
    raise RuntimeError(
        f"The Foreman app ({SP}) can't call {', '.join(missing)}. Ask someone with MANAGE on the model(s) to run "
        + "; ".join(f"GRANT EXECUTE ON FUNCTION system.ai.`{m}` TO `{SP}`" for m in missing)
        + " — or pick another model in supervisor.router_llm / answer_llm — then re-run this notebook.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5 · Deploy and smoke-test
# MAGIC The smoke test streams one real question and prints each step as it arrives — exactly what the Andon app shows.

# COMMAND ----------

dep = w.api_client.do("POST", f"/api/2.0/apps/{APP}/deployments", body={"source_code_path": AGENT_DIR})
for _ in range(90):
    d = w.api_client.do("GET", f"/api/2.0/apps/{APP}/deployments/{dep['deployment_id']}")
    state = d.get("status", {}).get("state")
    if state in ("SUCCEEDED", "FAILED"):
        break
    time.sleep(10)
print(f"deployment {state}: {d.get('status', {}).get('message')}")
assert state == "SUCCEEDED", d

# COMMAND ----------

import requests
url = w.api_client.do("GET", f"/api/2.0/apps/{APP}")["url"]
headers = {**w.config.authenticate(), "Content-Type": "application/json"}
answer = ""
t0 = time.time()
try:
    import uuid
    with requests.post(f"{url}/api/invocations", headers=headers, stream=True, timeout=600,   # the Agent Server protocol
                       json={"id": str(uuid.uuid4()), "session_id": str(uuid.uuid4()), "stream": True,
                             "input": {"question": "Which plant had the lowest OEE in FY26 Q4?", "user": ME}}) as r:
        r.raise_for_status()
        for line in r.iter_lines(decode_unicode=True):
            if line and line.startswith("data:"):
                ev = json.loads(line[5:])
                if ev["type"] in ("step", "step_done", "step_update", "done", "error"):
                    print(f"{time.time() - t0:6.1f}s  {ev['type']:<11} {ev.get('label') or ev.get('status') or ''}")
                if ev["type"] == "answer":
                    answer = ev["text"]
    print("\n" + answer[:600])
except requests.HTTPError as e:
    # Apps accept OAuth tokens only. A notebook's built-in token isn't one (401) — that is expected here; the app
    # itself is fine. Test it from your laptop: POST <url>/api/invocations with `databricks auth token` as the bearer.
    print(f"Smoke test skipped ({e.response.status_code}): call {url}/api/invocations with an OAuth token "
          f"(the Andon app does, as its service principal).")
dbutils.notebook.exit(json.dumps({"app": APP, "url": url, "experiment_id": exp_id, "service_principal": SP}))
