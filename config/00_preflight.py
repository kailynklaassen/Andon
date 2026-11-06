# Databricks notebook source
# MAGIC %md
# MAGIC # 00 · Pre-flight checks
# MAGIC
# MAGIC Checks your workspace is ready **before** anything is built — catalog, SQL warehouse, models, admin rights,
# MAGIC Lakebase — and says what to fix. `99_run_all` runs this first; you can run it alone any time.
# MAGIC
# MAGIC **All settings and what each one does (crucial vs optional):** [`config/README.md`](./README.md).
# MAGIC The values live in [`demo_config.yml`](./demo_config.yml) — the only file you edit.

# COMMAND ----------

# MAGIC %run ./config

# COMMAND ----------

# MAGIC %md
# MAGIC ## Pre-flight checks
# MAGIC Fails loudly, with what to fix, instead of failing an hour into `99_run_all`.

# COMMAND ----------

from databricks.sdk import WorkspaceClient
from databricks.sdk.errors import NotFound

w = WorkspaceClient()
checks = []

def check(name: str, ok: bool, fix: str = "") -> None:
    checks.append((name, ok))
    print(f"{'✅' if ok else '❌'} {name}" + ("" if ok else f"\n     → {fix}"))

check(f"catalog `{CATALOG}` exists", CATALOG in [c.name for c in w.catalogs.list()],
      "create it, or set workspace.catalog in config/demo_config.yml")
try:
    wid = get_warehouse_id()
    wh = w.warehouses.get(wid)
    check(f"SQL warehouse {wh.name} ({wid}) · {wh.cluster_size}, up to {wh.max_num_clusters} cluster(s)", True)
    if (wh.max_num_clusters or 1) < 2:
        print("     ⚠ 1 cluster: parallel Genie questions will queue. Consider max clusters ≥ 2 for live demos.")
except Exception as e:
    check("SQL warehouse", False, f"set workspace.warehouse_name or warehouse_id ({e})")
names = {e.name for e in w.serving_endpoints.list()}
# Foundation models are Unity Catalog objects (system.ai.<model>): you can only see and call the ones you have
# EXECUTE on, so a model that appears in Serving can still be missing here: an admin may have restricted it. (Step 4
# checks the Foreman app's own access when it deploys it.)
for key in ("router_llm", "answer_llm"):
    m = CFG["supervisor"].get(key)
    grant_hint = (f"you may not have access to it: check with SHOW GRANTS ON FUNCTION system.ai.`{m}` "
                  f"(or Catalog → system → ai → {m} → Permissions), and ask someone with MANAGE on it to "
                  "GRANT EXECUTE to you (Step 4 then also needs the Foreman app to have EXECUTE on it), "
                  "or pick another model")
    hint = f"not available to you. It may not be offered in this region, or {grant_hint}"
    if m not in names:                  # the list only shows endpoints you may use: find out whether it exists
        try:
            w.serving_endpoints.get(m)
        except Exception as e:
            if "EXECUTE" in str(e):
                hint = f"it exists, but you lack EXECUTE on system.ai.{m}. {grant_hint[0].upper() + grant_hint[1:]}"
    check(f"model `{m}` ({key}) is available to you", m in names, hint)
me = w.current_user.me()
check(f"you ({me.user_name}) are a workspace admin", any(g.display == "admins" for g in (me.groups or [])),
      "Steps 2c and 4 create groups, users and apps — ask an admin to run them")
LB = CFG["hitl"]["lakebase"]
try:
    w.postgres.get_project(name=f"projects/{LB['project']}")
    check(f"Lakebase project `{LB['project']}` exists", True)
except NotFound:
    print(f"ℹ️ Lakebase project `{LB['project']}` will be created by Step 0 (00_lakebase)")
except Exception as e:
    print(f"ℹ️ couldn't check Lakebase ({str(e)[:80]}) — Step 0 (00_lakebase) creates the project if needed")

failed = [n for n, ok in checks if not ok]
print("\n" + ("Ready. Run 99_run_all (or any step notebook on its own)." if not failed else f"Fix {len(failed)} item(s) above first."))
