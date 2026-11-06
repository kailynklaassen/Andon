# Databricks notebook source
# MAGIC %md
# MAGIC # Step 5 · Deploy the Andon app (FastAPI + React on Databricks Apps)
# MAGIC
# MAGIC **What this does:** deploys this folder as the Databricks App **`kkparts-andon`** — the human end of the agentic loop:
# MAGIC the Andon Board, Plant Explorer, Impact Web, the Foreman chat and the Action Ledger.
# MAGIC
# MAGIC ```
# MAGIC  browser (React) ──/api──► FastAPI (this app) ──► SQL warehouse   gold layer (cached, stale-while-revalidate)
# MAGIC                                               ──► Lakebase        the human-in-the-loop ledger (schema owned by the app)
# MAGIC                                               ──► kkparts-foreman the agent server (streamed steps, traced in MLflow)
# MAGIC                                               ──► kkparts-hitl-sync  "Sync now" (the job from Step 6a)
# MAGIC ```
# MAGIC
# MAGIC **Why this step matters:** the agent is only useful if people act on it. The app puts every insight where the
# MAGIC work happens (plant → line → machine), makes the agent's reasoning visible, and turns each human decision into a
# MAGIC governed record that flows back into the lakehouse (Step 6).
# MAGIC
# MAGIC **Crucial vs optional**
# MAGIC * **Crucial** — the SQL warehouse resource and `SELECT` on gold (every page reads gold); `CAN_USE` on the Foreman app
# MAGIC   (the app calls the agent as itself, passing who is asking).
# MAGIC * **Crucial for the human-in-the-loop** — the Lakebase `postgres` resource. Without it the ledger falls back to a
# MAGIC   local file that doesn't survive a redeploy.
# MAGIC * **Crucial for per-user governance** — user authorization with the **`genie`** scope (Apps user authorization, GA).
# MAGIC   The platform then hands the app each signed-in person's token, limited to Genie; the app forwards it to Foreman
# MAGIC   with each question, so Genie answers with *that person's* permissions. The app stays one service principal for
# MAGIC   everything else (gold data, Lakebase, calling Foreman). Changing scopes asks each person to authorize again.
# MAGIC * **Optional** — the `sync-job` resource (only powers the *Sync now* button; the job runs on its schedule anyway),
# MAGIC   `KK_DASHBOARD_EMBED_URL` (an AI/BI dashboard tab), and `app.admins` (who sees the App & agent health page).
# MAGIC
# MAGIC **How the front end gets built:** nothing is pre-built or committed. On deploy, Databricks Apps sees `package.json`, runs
# MAGIC `npm install` and `npm run build` (React → `frontend/dist`), installs `requirements.txt`, then starts `uvicorn`.
# MAGIC
# MAGIC **Run after:** Step 4b (the Foreman app must exist) and Step 6a (the sync job). Re-running is safe.

# COMMAND ----------

# MAGIC %pip install -q -U "databricks-sdk>=0.81" pyyaml
# MAGIC %restart_python

# COMMAND ----------

# MAGIC %run ../config/config

# COMMAND ----------

import json, time
import yaml
from databricks.sdk import WorkspaceClient
from databricks.sdk.errors import NotFound

w = WorkspaceClient()
H, SUP = CFG["hitl"], CFG["supervisor"]
APP, FOREMAN = H["app_name"], SUP["app_name"]
APP_DIR = f"{REPO_ROOT}/05_app"
LB = H["lakebase"]
BRANCH = f"projects/{LB['project']}/branches/{LB['branch']}"
WAREHOUSE_ID = get_warehouse_id()
ME = w.current_user.me().user_name

foreman = w.api_client.do("GET", f"/api/2.0/apps/{FOREMAN}")       # Step 4b deployed it
job = next((j for j in w.jobs.list(name=H["sync"]["job_name"])), None)  # Step 6a created it
print(f"Foreman: {foreman['url']}")
print(f"sync job: {job.job_id if job else '— (run Step 6a for the Sync now button)'}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1 · `app.yaml`, rendered from `demo_config.yml`
# MAGIC Resource IDs come in through `valueFrom` (the platform injects them); everything else that differs per workspace —
# MAGIC catalog, schemas, the Foreman URL, the Lakebase endpoint — is written here from config, so nobody edits `app.yaml`.

# COMMAND ----------

env = [
    {"name": "DATABRICKS_WAREHOUSE_ID", "valueFrom": "sql-warehouse"},
    {"name": "KK_FOREMAN_URL", "value": foreman["url"]},
    *([{"name": "KK_SYNC_JOB_ID", "valueFrom": "sync-job"}] if job else []),
    {"name": "KK_LAKEBASE_ENDPOINT", "value": f"{BRANCH}/endpoints/{LB['endpoint']}"},
    {"name": "KK_HITL_SCHEMA", "value": LB["schema"]},
    {"name": "KK_CATALOG", "value": CATALOG},
    {"name": "KK_GOLD_SCHEMA", "value": GOLD_SCHEMA},
    {"name": "KK_BRONZE_SCHEMA", "value": BRONZE_SCHEMA},
    {"name": "KK_DATA_MODE", "value": "live"},
    {"name": "KK_AGENT_MODE", "value": "live"},
    {"name": "KK_DASHBOARD_EMBED_URL", "value": CFG.get("app", {}).get("dashboard_embed_url", "")},
    # who sees the App & agent health page ({admin} = whoever runs this deploy)
    {"name": "KK_ADMINS", "value": ",".join(a.replace("{admin}", ME) for a in CFG.get("app", {}).get("admins", ["{admin}"]))},
]
header = open(f"{APP_DIR}/app.yaml").read().split("command:")[0]       # keep the explanatory comment block
with open(f"{APP_DIR}/app.yaml", "w") as f:
    f.write(header + yaml.safe_dump({"command": ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"],
                                     "env": env}, sort_keys=False, width=120))
print(open(f"{APP_DIR}/app.yaml").read()[-900:])

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2 · The app and its resources (each one grants access *and* injects a value)

# COMMAND ----------

resources = [{"name": "sql-warehouse", "sql_warehouse": {"id": WAREHOUSE_ID, "permission": "CAN_USE"}},
             {"name": "postgres", "postgres": {"branch": BRANCH, "database": f"{BRANCH}/databases/{LB['database']}",
                                               "permission": "CAN_CONNECT_AND_CREATE"}}]
if job:
    resources.append({"name": "sync-job", "job": {"id": str(job.job_id), "permission": "CAN_MANAGE_RUN"}})
# user authorization: on_behalf_of_user needs only the `genie` scope (least privilege — the app reads gold as itself)
scopes = ["genie"] if SUP.get("genie_auth") == "on_behalf_of_user" else []
spec = {"name": APP, "description": f"{COMPANY} Andon: plant drill-down, impact web, Foreman agent, human-in-the-loop ledger",
        "resources": resources, "user_api_scopes": scopes}
try:
    w.api_client.do("GET", f"/api/2.0/apps/{APP}")
    w.api_client.do("POST", f"/api/2.0/apps/{APP}/update", body={"app": spec, "update_mask": "resources,description,user_api_scopes"})
    for _ in range(60):          # a deployment can't start while the resource update is still running
        u = w.api_client.do("GET", f"/api/2.0/apps/{APP}/update").get("status", {}).get("state")
        if u not in ("IN_PROGRESS", "PENDING"):
            break
        time.sleep(5)
    print(f"updated app {APP} ({u})")
except NotFound:
    w.api_client.do("POST", "/api/2.0/apps", body=spec)
    print(f"created app {APP}")
for _ in range(60):
    app = w.api_client.do("GET", f"/api/2.0/apps/{APP}")
    if app.get("compute_status", {}).get("state") == "ACTIVE":
        break
    time.sleep(10)
SP = app["service_principal_client_id"]
print(f"service principal {SP} · {app['url']}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3 · Grants the resources don't cover
# MAGIC * Unity Catalog: `SELECT` on gold (least privilege — the app never reads bronze or silver).
# MAGIC * `CAN_USE` on the Foreman app: Databricks Apps accept OAuth tokens only from identities allowed to use them.

# COMMAND ----------

for stmt in (f"GRANT USE CATALOG ON CATALOG `{CATALOG}` TO `{SP}`",
             f"GRANT USE SCHEMA, SELECT ON SCHEMA `{CATALOG}`.`{GOLD_SCHEMA}` TO `{SP}`"):
    spark.sql(stmt)
    print(" ", stmt)
w.api_client.do("PATCH", f"/api/2.0/permissions/apps/{FOREMAN}",
                body={"access_control_list": [{"service_principal_name": SP, "permission_level": "CAN_USE"}]})
print(f"  CAN_USE on app {FOREMAN} → {SP}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4 · Deploy (Databricks Apps builds the React front end) and check it's up

# COMMAND ----------

dep = w.api_client.do("POST", f"/api/2.0/apps/{APP}/deployments", body={"source_code_path": APP_DIR})
for _ in range(90):
    d = w.api_client.do("GET", f"/api/2.0/apps/{APP}/deployments/{dep['deployment_id']}")
    state = d.get("status", {}).get("state")
    if state in ("SUCCEEDED", "FAILED"):
        break
    time.sleep(10)
print(f"deployment {state}: {d.get('status', {}).get('message')}")
assert state == "SUCCEEDED", f"see the app logs: {app['url']}/logz"
print(f"\n✅ {APP} is live: {app['url']}  (first visit asks each person to authorize the app once)")
dbutils.notebook.exit(json.dumps({"app": APP, "url": app["url"], "service_principal": SP}))
