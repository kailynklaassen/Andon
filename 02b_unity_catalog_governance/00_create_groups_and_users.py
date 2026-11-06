# Databricks notebook source
# MAGIC %md
# MAGIC # Step 2c-0 · Identity — account groups and demo users (run as a WORKSPACE admin)
# MAGIC
# MAGIC Unity Catalog grants and ABAC policies need **account-level** groups (workspace-local groups are invisible to
# MAGIC Unity Catalog: `PRINCIPAL_DOES_NOT_EXIST`). You do **not** need to be an account admin: the workspace identity API
# MAGIC (`/api/2.0/identity/...`) lets a workspace admin create *account* groups and users in the account that owns
# MAGIC this workspace and assign them here.
# MAGIC
# MAGIC What it does (idempotent — safe to re-run):
# MAGIC 1. creates every group in `governance.groups` (`config/demo_config.yml`)
# MAGIC 2. creates the demo users (e.g. `you+maintenance@example.com`) if they don't exist
# MAGIC 3. puts each user in its group
# MAGIC 4. assigns each group to this workspace (workspace + Databricks SQL access)
# MAGIC
# MAGIC > If your users and groups come from your identity provider (SCIM / automatic identity management), skip this
# MAGIC > step and just put your real group names in `governance.groups`.

# COMMAND ----------

# MAGIC %md
# MAGIC ### Why this step matters
# MAGIC An agent inherits the permissions of whoever it runs as. Groups per domain are what make "the supply chain team can see prices, plant ops can't" true for people **and** for the agent.
# MAGIC
# MAGIC **Crucial**
# MAGIC * Account-level groups mapped to the domains; the agent's identity deliberately *not* in the confidential groups.
# MAGIC
# MAGIC **Optional**
# MAGIC * The demo users (`+domain` addresses) — use your real groups instead.

# COMMAND ----------

# MAGIC %run ../config/config

# COMMAND ----------

from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
GOV = CFG["governance"]
HEADERS = {"X-Databricks-Workspace-Id": str(w.get_workspace_id())}
ENTITLEMENTS = ["WORKSPACE_ACCESS", "DATABRICKS_SQL_ACCESS"]


def identity(method: str, path: str, **kw) -> dict:
    return w.api_client.do(method, f"/api/2.0/identity/{path}", headers=HEADERS, **kw)


def find(kind: str, field: str, value: str) -> dict | None:
    """kind = groups | users. The filter language is `<snake_case_field> eq "<value>"`."""
    return next(iter(identity("GET", kind, query={"filter": f'{field} eq "{value}"'}).get(kind, [])), None)


def ensure_group(name: str) -> dict:
    return find("groups", "group_name", name) or identity("POST", "groups", body={"group_name": name})


def ensure_user(email: str) -> tuple[dict, bool]:
    user = find("users", "username", email)
    if user:
        return user, False
    local = email.split("@")[0]
    return identity("POST", "users", body={"username": email, "account_user_status": "ACTIVE",
                                           "full_name": {"given_name": local, "family_name": "(demo)"}}), True


def ensure_member(group_id: str, principal_id: str):
    try:
        identity("POST", f"groups/{group_id}/direct-members", body={"principal_id": int(principal_id)})
    except Exception as e:
        if "already" not in str(e).lower() and "exists" not in str(e).lower():
            raise


def ensure_workspace_assignment(principal_id: str):
    try:
        identity("POST", "workspace-assignments", body={"principal_id": int(principal_id), "entitlements": ENTITLEMENTS})
    except Exception as e:
        if "already" not in str(e).lower() and "exists" not in str(e).lower():
            raise

# COMMAND ----------

for g in GOV["groups"]:
    group = ensure_group(g["name"])
    for email in g["members"]:
        email = email.replace("{admin}", GOV["admin_email"])
        user, created = ensure_user(email)
        ensure_member(group["group_id"], user["user_id"])
        print(f"  {g['name']:<22} ← {email}{'  (new user)' if created else ''}")
    ensure_workspace_assignment(group["group_id"])
    print(f"✅ {g['name']} (domains: {', '.join(g['domains'])}) — account group, assigned to this workspace")
