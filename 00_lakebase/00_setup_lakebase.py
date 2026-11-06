# Databricks notebook source
# MAGIC %md
# MAGIC # Step 0 · Lakebase — the operational database for the agent and the app
# MAGIC
# MAGIC **What this does:** makes sure the one Lakebase (Autoscaling Postgres) project exists and is reachable, then shows
# MAGIC what lives in it. Everything transactional in the accelerator is here; everything analytical stays in Delta.
# MAGIC
# MAGIC ```
# MAGIC  Lakebase project  hitl.lakebase.project (kkparts-hitl) · branch production · endpoint primary · db databricks_postgres
# MAGIC   ├─ schema andon     owned by the Andon app's service principal (created on its first start)
# MAGIC   │    actions · approved_actions (the outbox) · action_events (audit trail) · app_events (health page)
# MAGIC   └─ schema foreman   owned by the Foreman app's service principal (created on its first start)
# MAGIC        sessions · turns (conversations) · memories (long-term, per user) · runs (health page run log)
# MAGIC
# MAGIC  read by: the sync job (06_human_in_the_loop) — the outbox → bronze corrections + Genie notes → back to Lakebase
# MAGIC ```
# MAGIC
# MAGIC ### Why this step matters
# MAGIC The app needs fast, concurrent, read-your-own-writes storage for human actions, and the agent needs a place to keep
# MAGIC conversations and memory — that is what Lakebase is for. Both apps attach this project as a `postgres` resource
# MAGIC (Steps 4b and 5), so it must exist **before** they deploy; that is why it is Step 0.
# MAGIC
# MAGIC **Crucial**
# MAGIC * The project exists before the apps deploy (they get `CAN_CONNECT_AND_CREATE` on its database).
# MAGIC * **Each app creates — and so owns — its own schema.** Deploy an app before running it locally against Lakebase,
# MAGIC   otherwise *your* identity creates the schema and the app can't use it.
# MAGIC
# MAGIC **Optional**
# MAGIC * Sessions/memory (`supervisor.memory: false` turns them off; the ledger still uses Lakebase).
# MAGIC * Capacity: the project's default autoscaling compute with scale-to-zero is plenty for a demo.
# MAGIC
# MAGIC **Where the code that uses it lives** (it stays with each app, because an app deploys its own folder):
# MAGIC `05_app/backend/core/ledger.py` + `telemetry.py` (schema `andon`) · `04_supervisor_agent/agent/memory.py` +
# MAGIC `runlog.py` (schema `foreman`) · `06_human_in_the_loop/01_sync_approved_actions` + `02_mark_in_gold` (the sync job).

# COMMAND ----------

# MAGIC %pip install -q "databricks-sdk>=0.81" "psycopg[binary]>=3.2"
# MAGIC %restart_python

# COMMAND ----------

# MAGIC %run ../config/config

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1 · The project (created if missing)
# MAGIC Creating it provisions a `production` branch, a `primary` read-write endpoint and the `databricks_postgres` database.

# COMMAND ----------

from databricks.sdk import WorkspaceClient
from databricks.sdk.errors import NotFound
from databricks.sdk.service.postgres import Project, ProjectSpec

w = WorkspaceClient()
LB = CFG["hitl"]["lakebase"]
BRANCH = f"projects/{LB['project']}/branches/{LB['branch']}"
ENDPOINT = f"{BRANCH}/endpoints/{LB['endpoint']}"

try:
    w.postgres.get_project(name=f"projects/{LB['project']}")
    print(f"Lakebase project {LB['project']} exists")
except NotFound:
    print(f"Creating Lakebase project {LB['project']} (a few minutes) ...")
    w.postgres.create_project(project=Project(spec=ProjectSpec(display_name=f"{COMPANY} — operational database (agent + app)")),
                              project_id=LB["project"]).wait()
endpoint = w.postgres.get_endpoint(name=ENDPOINT)
print(f"  endpoint {endpoint.name} → {endpoint.status.hosts.host}")
print(f"  database {LB.get('postgres_database', 'databricks_postgres')}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2 · What's in it (and who owns it)
# MAGIC Read-only inventory, as you (the project owner). Empty until the apps have started once.

# COMMAND ----------

import psycopg

token = w.postgres.generate_database_credential(endpoint=ENDPOINT).token
schemas = (LB["schema"], CFG["supervisor"].get("memory_schema", "foreman"))
with psycopg.connect(host=endpoint.status.hosts.host, dbname=LB.get("postgres_database", "databricks_postgres"),
                     user=w.current_user.me().user_name, password=token, sslmode="require") as conn, conn.cursor() as cur:
    cur.execute("""SELECT n.nspname, pg_get_userbyid(n.nspowner), c.relname, c.reltuples::bigint
                   FROM pg_namespace n LEFT JOIN pg_class c ON c.relnamespace = n.oid AND c.relkind = 'r'
                   WHERE n.nspname = ANY(%s) ORDER BY 1, 3""", (list(schemas),))
    rows = cur.fetchall()
if not rows:
    print("No app schemas yet — they appear after Steps 4b and 5 deploy the apps.")
for schema, owner, table, approx_rows in rows:
    print(f"  {schema:<10} owner {owner:<38} {table or '(no tables yet)':<20} ~{max(approx_rows or 0, 0)} rows")
