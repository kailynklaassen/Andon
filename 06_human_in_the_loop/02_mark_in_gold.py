# Databricks notebook source
# MAGIC %md
# MAGIC # Step 6c · Record that approved corrections reached gold
# MAGIC
# MAGIC The last task of job `kkparts-hitl-sync`, after `refresh_pipeline`. It writes one **`in_gold`** event per approved
# MAGIC value change that the pipeline has now carried bronze → silver → gold:
# MAGIC
# MAGIC ```
# MAGIC sync_approved_actions ─► corrections_landed? ─► refresh_pipeline ─► mark_in_gold (this)
# MAGIC                                                                         │
# MAGIC                       Lakebase <schema>.action_events  event = 'in_gold'  ├─► the Action Ledger timeline shows it
# MAGIC                                                                         └─► the Andon app sees it within a minute
# MAGIC                                                                             and refreshes its cached gold data
# MAGIC ```
# MAGIC
# MAGIC ### Why this step matters
# MAGIC "Synced" only means the correction is in bronze. The person who approved it cares when it is **live** — in gold,
# MAGIC in the metric views Genie and Foreman query, and on the app's pages. This event is that signal, in the audit trail.
# MAGIC
# MAGIC **What needs refreshing after an approval — and what doesn't**
# MAGIC | Approved action | Needs | Why |
# MAGIC |---|---|---|
# MAGIC | value change | **pipeline update** (the job's `refresh_pipeline` task) | Bronze → silver (latest version wins) → gold are pipeline tables. |
# MAGIC | value change | **app cache refresh** (this event) | The app caches gold for 10 minutes. |
# MAGIC | value change | nothing in Genie | Metric views are views: Genie reads the new gold values on its next query. |
# MAGIC | note | nothing | The note's file lands in its `app_notes_<domain>` volume; Genie indexes it automatically. |
# MAGIC
# MAGIC **Crucial:** only runs after a successful pipeline update (task dependency), so `in_gold` is never written early.
# MAGIC **Optional:** the whole step — without it the app picks up new values when its 10-minute cache expires.

# COMMAND ----------

# MAGIC %pip install "psycopg[binary]>=3.2" "databricks-sdk>=0.81" --quiet
# MAGIC %restart_python

# COMMAND ----------

# MAGIC %run ../config/config

# COMMAND ----------

import json

import psycopg
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
H, LB = CFG["hitl"], CFG["hitl"]["lakebase"]
PG_SCHEMA = LB["schema"]
BRANCH = f"projects/{LB['project']}/branches/{LB['branch']}"
ENDPOINT = f"{BRANCH}/endpoints/{LB['endpoint']}"
RUN_ID = _widget("run_id", "")

host = w.postgres.get_endpoint(name=ENDPOINT).status.hosts.host
dbname = LB.get("postgres_database") or w.postgres.get_database(name=f"{BRANCH}/databases/{LB['database']}").status.postgres_database
token = w.postgres.generate_database_credential(endpoint=ENDPOINT).token

# Every synced value change without an in_gold event yet: this run's, plus any an earlier failed refresh left behind
# (a pipeline update processes everything that has landed, not just this run's corrections).
with psycopg.connect(host=host, dbname=dbname, user=w.current_user.me().user_name, password=token,
                     sslmode="require") as conn, conn.cursor() as cur:
    cur.execute(f"""
        SELECT a.action_id::text, a.target, a.sync_run_id FROM {PG_SCHEMA}.approved_actions a
        WHERE a.kind = 'value_change' AND a.sync_status = 'synced'
          AND NOT EXISTS (SELECT 1 FROM {PG_SCHEMA}.action_events e
                          WHERE e.action_id = a.action_id AND e.event = 'in_gold')""")
    live = cur.fetchall()
    for action_id, target, sync_run in live:
        cur.execute(f"INSERT INTO {PG_SCHEMA}.action_events (action_id, actor, event, detail) VALUES (%s, %s, %s, %s)",
                    (action_id, f"job:{H['sync']['job_name']}", "in_gold",
                     json.dumps({"bronze_table": target, "synced_by_run": sync_run, "refreshed_by_run": RUN_ID})))
        print(f"✅ in gold: {action_id} ({target})")
print(f"{len(live)} correction(s) marked in_gold")
