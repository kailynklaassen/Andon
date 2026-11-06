# Databricks notebook source
# MAGIC %md
# MAGIC # Step 2c · Unity Catalog governance — tags, domain grants, and an ABAC column mask
# MAGIC
# MAGIC **Why this matters for agents:** the supervisor calls Genie **on behalf of the user** who asked. So whatever Unity
# MAGIC Catalog allows that user is exactly what the agent can see — no separate "AI permissions" to maintain. Govern the
# MAGIC data once; SQL, dashboards, Genie and the supervisor all inherit it.
# MAGIC
# MAGIC | Layer | Mechanism | In this demo |
# MAGIC |---|---|---|
# MAGIC | **Who** | Account groups (Step 2b-0) | `kkparts_admins`, one group per domain, `kkparts_plant_ops` (Production + Maintenance + Quality) |
# MAGIC | **Which domain** | Tags + `GRANT` | Every gold object is tagged `kkparts_domain`; each group gets `SELECT` on exactly the objects its Genie spaces use |
# MAGIC | **Which documents and notes** | `READ VOLUME` | Each group may read only its domains' `genie_docs_<domain>` / `app_notes_<domain>` volumes — Genie Agent mode reads the attached files as the person asking |
# MAGIC | **Which values** | **ABAC** column-mask policy | Commercially sensitive columns (supplier prices, PO and order values, standard costs, list prices) carry a governed tag; one schema-level policy masks them for everyone except admins and Supply Chain — on *every* tagged table, including tables added later |
# MAGIC
# MAGIC ABAC policies are evaluated dynamically from tags, so the rule is written once at the schema level instead of on
# MAGIC each table. It flows through metric views and Genie automatically: a Plant Ops user asking for supplier spend gets
# MAGIC NULLs, a Supply Chain user gets the numbers — from the same Genie space and the same supervisor.

# COMMAND ----------

# MAGIC %md
# MAGIC ### Why this step matters
# MAGIC Govern the data once, and every consumer — Genie, the agent, the app, a notebook — gets the same answer about who may see what. No permission logic in agent code.
# MAGIC
# MAGIC **Crucial**
# MAGIC * Least-privilege grants per domain, and the **ABAC column mask** on confidential values: the agent reports them as confidential instead of leaking them.
# MAGIC
# MAGIC **Optional**
# MAGIC * Domain tags (useful for discovery and policy targeting, not required for the mask).

# COMMAND ----------

# MAGIC %run ../config/config

# COMMAND ----------

import glob, yaml
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()
GOV = CFG["governance"]
G = f"`{CATALOG}`.`{GOLD_SCHEMA}`"
GROUPS = GOV["groups"]
ADMINS = next(g["name"] for g in GROUPS if g["name"].endswith("_admins"))

def sql(stmt: str, quiet: bool = False):
    if not quiet:
        print("  " + " ".join(stmt.split())[:150])
    return spark.sql(stmt)

# Which gold objects does each domain's Genie space use? (single source of truth: 03_genie_spaces/spaces/*.yml)
space_objects = {}
for path in glob.glob(f"{REPO_ROOT}/03_genie_spaces/spaces/*.yml"):
    spec = yaml.safe_load(open(path))
    space_objects[spec["key"]] = [t["name"] for t in spec.get("tables", [])] + spec.get("metric_views", [])
gold_objects = {r.tableName for r in spark.sql(f"SHOW TABLES IN {G}").collect()}

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1 · Tag every gold object with its domain
# MAGIC Facts and metric views get the domain of the Genie space that owns them; dimensions shared by several spaces are
# MAGIC tagged `shared`. Tags show up in Catalog Explorer and drive the grants below.

# COMMAND ----------

owner = {}
for domain, objs in space_objects.items():
    for o in objs:
        owner.setdefault(o, set()).add(domain)
for obj, domains in sorted(owner.items()):
    if obj in gold_objects:
        value = next(iter(domains)) if len(domains) == 1 else "shared"
        sql(f"ALTER TABLE {G}.`{obj}` SET TAGS ('kkparts_domain' = '{value}')", quiet=True)
print(f"tagged {len(owner)} gold objects with kkparts_domain")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2 · Domain grants (least privilege)

# COMMAND ----------

for g in GROUPS:
    grp = f"`{g['name']}`"
    sql(f"GRANT USE CATALOG ON CATALOG `{CATALOG}` TO {grp}")
    sql(f"GRANT USE SCHEMA ON SCHEMA {G} TO {grp}")
    sql(f"GRANT USE SCHEMA ON SCHEMA `{CATALOG}`.`{LANDING_SCHEMA}` TO {grp}")   # to reach the volumes below (no table reads)
    allowed = sorted({o for d in g["domains"] for o in space_objects.get(d, []) if o in gold_objects})
    for o in allowed:
        sql(f"GRANT SELECT ON TABLE {G}.`{o}` TO {grp}", quiet=True)
    for d in g["domains"]:
        # Genie Agent mode reads the attached files AS the person asking: their domains' documents + notes volumes only
        for vol in (docs_volume(d), notes_volume(d)):
            sql(f"GRANT READ VOLUME ON VOLUME `{CATALOG}`.`{LANDING_SCHEMA}`.`{vol}` TO {grp}", quiet=True)
    print(f"✅ {g['name']:<22} SELECT on {len(allowed)} objects, documents: {', '.join(g['domains'])}")
# (SELECT on gold.genie_space_registry is granted by 03_genie_spaces/01_create_genie_spaces, which creates it)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3 · ABAC — mask confidential columns
# MAGIC 1. Make sure the governed tag exists (`governance.confidential.tag`). Accounts have a limit on governed tags; if it's
# MAGIC    reached we use the system governed tag in `fallback_tag` instead.
# MAGIC 2. Tag each confidential column listed in config.
# MAGIC 3. One masking function: *is the caller in a group allowed to see confidential values?*
# MAGIC 4. One policy **on the schema**: "for any table with a confidential-tagged column, mask it", `EXCEPT` the groups
# MAGIC    allowed to see it. Pipeline refreshes run as the owner (an admin), so stored data is never masked.

# COMMAND ----------

CONF = GOV["confidential"]
TAG, TAG_VALUE = CONF["tag"], "confidential"
try:
    w.api_client.do("GET", f"/api/2.1/tag-policies/{TAG}")
except Exception:
    try:
        w.api_client.do("POST", "/api/2.1/tag-policies", body={
            "tag_key": TAG, "description": "KK's Parts demo data classification (ABAC column masks)",
            "values": [{"name": TAG_VALUE}]})
        print(f"created governed tag {TAG}")
    except Exception as e:
        if "maximum number of tag policies" not in str(e):
            raise
        TAG, TAG_VALUE = CONF["fallback_tag"], None
        print(f"⚠️ account governed-tag limit reached — using system governed tag {TAG}")
tag_sql = f"'{TAG}' = '{TAG_VALUE}'" if TAG_VALUE else f"'{TAG}'"
match = f"has_tag_value('{TAG}', '{TAG_VALUE}')" if TAG_VALUE else f"has_tag('{TAG}')"

for table, cols in CONF["columns"].items():
    for c in cols:
        sql(f"ALTER TABLE {G}.`{table}` ALTER COLUMN `{c}` SET TAGS ({tag_sql})", quiet=True)
    print(f"tagged {table}: {', '.join(cols)}")

visible = CONF["visible_to"]
sql(f"""CREATE OR REPLACE FUNCTION {G}.`mask_confidential`(value DOUBLE) RETURNS DOUBLE
        COMMENT 'ABAC column mask: confidential commercial values are visible only to {", ".join(visible)}'
        RETURN CASE WHEN {" OR ".join(f"is_account_group_member('{g}')" for g in visible)} THEN value ELSE NULL END""")
sql(f"""CREATE OR REPLACE POLICY `kkparts_confidential_mask` ON SCHEMA {G}
        COMMENT 'Confidential commercial values (prices, costs, PO and order values) are masked outside {", ".join(visible)}'
        COLUMN MASK {G}.`mask_confidential`
        TO `account users` EXCEPT {", ".join(f"`{g}`" for g in visible)}
        FOR TABLES
        MATCH COLUMNS {match} AS conf
        ON COLUMN conf""")
print(f"✅ confidential columns masked for everyone except {visible}")

display(spark.sql(f"SHOW POLICIES ON SCHEMA {G}"))
