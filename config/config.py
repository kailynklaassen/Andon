# Databricks notebook source
# MAGIC %md
# MAGIC # ⚙️ Config loader
# MAGIC
# MAGIC **You don't edit this notebook — you edit [`demo_config.yml`](./demo_config.yml).**
# MAGIC
# MAGIC Every step notebook starts with `%run ../config/config`. This notebook:
# MAGIC 1. Finds the repo root (works in a Git folder, a workspace folder, or locally).
# MAGIC 2. Loads `demo_config.yml` into `CFG`.
# MAGIC 3. Derives every name the demo uses (catalog, schemas, volumes, paths) so no step hardcodes them.
# MAGIC 4. Exposes small helpers (`fq()`, `ensure_uc_objects()`, `get_warehouse_id()`).
# MAGIC
# MAGIC Optional overrides: if the calling notebook defines widgets named `catalog` or `warehouse_id`,
# MAGIC those win over the YAML — handy for running the same repo into a different catalog.

# COMMAND ----------

import os
import yaml


def _repo_root() -> str:
    """Walk up from the current notebook until we find config/demo_config.yml."""
    try:
        nb_path = (dbutils.notebook.entry_point.getDbutils().notebook().getContext()  # noqa: F821
                   .notebookPath().get())
        here = "/Workspace" + nb_path if not nb_path.startswith("/Workspace") else nb_path
        here = os.path.dirname(here)
    except Exception:          # running locally / outside a notebook
        here = os.getcwd()
    while here and here != "/":
        if os.path.exists(os.path.join(here, "config", "demo_config.yml")):
            return here
        here = os.path.dirname(here)
    raise FileNotFoundError("Could not find config/demo_config.yml above this notebook")


REPO_ROOT = _repo_root()
with open(os.path.join(REPO_ROOT, "config", "demo_config.yml")) as f:
    CFG = yaml.safe_load(f)


def _widget(name: str, default: str) -> str:
    """Return a widget value if the caller defined that widget and filled it in."""
    try:
        v = dbutils.widgets.get(name)  # noqa: F821
        return v.strip() or default
    except Exception:
        return default


# ---- Unity Catalog names (everything downstream uses these) -------------------
CATALOG = _widget("catalog", CFG["workspace"]["catalog"])
SCHEMAS = CFG["workspace"]["schemas"]
LANDING_SCHEMA, BRONZE_SCHEMA = SCHEMAS["landing"], SCHEMAS["bronze"]
SILVER_SCHEMA, GOLD_SCHEMA = SCHEMAS["silver"], SCHEMAS["gold"]
APP_SCHEMA = SCHEMAS.get("app", "mfg_app")                        # Delta mirror of the app's HITL ledger
RAW_VOLUME, DOCS_PREFIX = CFG["workspace"]["volumes"]["raw"], CFG["workspace"]["volumes"]["docs_prefix"]
RAW_PATH = f"/Volumes/{CATALOG}/{LANDING_SCHEMA}/{RAW_VOLUME}"     # source-system files land here
REGISTRY_PATH = f"{RAW_PATH}/_registry"                             # genie_space_registry.json for tools/apps


def docs_volume(domain: str) -> str:
    """Each Genie space gets its own documents volume (Genie indexes one volume per space)."""
    return f"{DOCS_PREFIX}_{domain}"


def docs_path(domain: str) -> str:
    return f"/Volumes/{CATALOG}/{LANDING_SCHEMA}/{docs_volume(domain)}"


NOTES = CFG.get("hitl", {}).get("notes", {})


def notes_volume(domain: str) -> str:
    """Each Genie space also gets its own volume of approved app comments (only that domain's notes)."""
    return f"{NOTES.get('volume_prefix', 'app_notes')}_{domain}"


def notes_path(domain: str) -> str:
    return f"/Volumes/{CATALOG}/{LANDING_SCHEMA}/{notes_volume(domain)}"
COMPANY = CFG["company"]["name"]


def correction_table(bronze_table: str) -> str:
    """Delta table the HITL sync appends approved corrections to; a pipeline append flow feeds it into bronze."""
    return f"{CATALOG}.{LANDING_SCHEMA}.app_corrections_{bronze_table.removeprefix('bronze_')}"


def sql_str(text: str) -> str:
    """Escape text for a single-quoted SQL literal — names like "KK's Parts" contain apostrophes."""
    return text.replace("\\", "\\\\").replace("'", "\\'")


def fq(schema: str, obj: str) -> str:
    """Fully-qualified, back-tick-safe UC name: fq(GOLD_SCHEMA, 'oee_daily')."""
    return f"`{CATALOG}`.`{schema}`.`{obj}`"


def ensure_uc_objects() -> None:
    """Create the medallion schemas + the raw, documents and app-notes volumes if they don't exist (idempotent)."""
    for layer, schema in SCHEMAS.items():
        spark.sql(f"CREATE SCHEMA IF NOT EXISTS `{CATALOG}`.`{schema}` "  # noqa: F821
                  f"COMMENT '{sql_str(COMPANY)} demo - {layer} layer'")
    vols = [(RAW_VOLUME, "Raw source-system extracts (ERP, MES, CMMS, QMS, WMS, IoT, HR)")]
    vols += [(docs_volume(s["docs_folder"]), f"Documents for the Genie space: {s['title']}") for s in CFG["genie"]["spaces"]]
    vols += [(notes_volume(s["key"]), f"Approved app comments for the Genie space: {s['title']}") for s in CFG["genie"]["spaces"]]
    for vol, comment in vols:
        spark.sql(f"CREATE VOLUME IF NOT EXISTS `{CATALOG}`.`{LANDING_SCHEMA}`.`{vol}` COMMENT '{sql_str(comment)}'")  # noqa: F821


def get_warehouse_id() -> str:
    """warehouse_id if set, else the warehouse named workspace.warehouse_name, else the first serverless one we can see."""
    wid = _widget("warehouse_id", CFG["workspace"].get("warehouse_id") or "")
    if wid:
        return wid
    from databricks.sdk import WorkspaceClient
    whs = list(WorkspaceClient().warehouses.list())
    name = CFG["workspace"].get("warehouse_name")
    if name:                                   # a name travels between workspaces; an ID doesn't
        match = [w for w in whs if w.name == name]
        if not match:
            raise RuntimeError(f"No SQL warehouse named '{name}' — create it, or fix workspace.warehouse_name")
        return match[0].id
    whs.sort(key=lambda w: (not w.enable_serverless_compute, str(w.state) != "State.RUNNING"))
    if not whs:
        raise RuntimeError("No SQL warehouse found — set workspace.warehouse_id in demo_config.yml")
    return whs[0].id


print(f"Config loaded from {REPO_ROOT}/config/demo_config.yml")
print(f"  company : {COMPANY}")
print(f"  catalog : {CATALOG}   schemas: {LANDING_SCHEMA} → {BRONZE_SCHEMA} → {SILVER_SCHEMA} → {GOLD_SCHEMA}")
print(f"  raw     : {RAW_PATH}")
print(f"  docs    : {docs_path('<domain>')}  (one volume per Genie space)")
