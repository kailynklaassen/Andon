# Databricks notebook source
# MAGIC %md
# MAGIC # Step 3 · Create the four domain Genie spaces
# MAGIC
# MAGIC **What this does:** reads each definition in [`spaces/*.yml`](./spaces) and creates (or updates) a Genie space
# MAGIC through the Genie REST API. Then it writes a **registry table** (`mfg_gold.genie_space_registry`) that the
# MAGIC supervisor agent reads to discover its tools, and asks each space one sample question to prove it works.
# MAGIC
# MAGIC | Space | Sources | Volumes attached for Agent-mode file search |
# MAGIC |---|---|---|
# MAGIC | KK's Parts Production & OEE | `production_oee_metrics`, `production_downtime_metrics` + facts/dims | `genie_docs_production` + `app_notes_production` |
# MAGIC | KK's Parts Quality & Compliance | `quality_inspection_metrics`, `quality_ncr_metrics` + facts/dims | `genie_docs_quality` + `app_notes_quality` |
# MAGIC | KK's Parts Maintenance & Reliability | `maintenance_work_order_metrics`, `maintenance_asset_health_metrics` + facts/dims | `genie_docs_maintenance` + `app_notes_maintenance` |
# MAGIC | KK's Parts Supply Chain & Warehousing | `supply_supplier_performance_metrics`, `supply_inventory_metrics`, `supply_shipment_metrics` + facts/dims | `genie_docs_supply_chain` + `app_notes_supply_chain` |
# MAGIC
# MAGIC ### Genie best practices this encodes (most-governed first)
# MAGIC 1. **One domain per space** with a precise *description* — the supervisor routes on it.
# MAGIC 2. **Metric views first** — KPIs are defined once; Genie uses `MEASURE()` instead of inventing math.
# MAGIC 3. **Focused tables** for row-level detail, with **column configs**: entity matching on the values people type
# MAGIC    ("Greenville", "Ridgeway Freight"), synonyms, and hidden technical columns.
# MAGIC 4. **Join specs** so Genie never guesses a join (all many-to-one onto dimensions).
# MAGIC 5. **SQL snippets** for reusable business filters ("night shift", "current inventory").
# MAGIC 6. **Certified example SQL** that teaches query *shapes* (period comparison, ranking, detail drill-down).
# MAGIC 7. **Text instructions last** and short — only global behavior (date anchoring, fiscal calendar, summary style).
# MAGIC 8. **Sample questions** for users and **benchmarks** to measure accuracy over time.

# COMMAND ----------

# MAGIC %md
# MAGIC ### Why this step matters
# MAGIC Genie spaces are the agent's **domain experts** — and its tools. The supervisor only sees each space's name and description, so the description *is* the routing rule. Building them from versioned YAML makes them reviewable and reproducible.
# MAGIC
# MAGIC **Crucial**
# MAGIC * Sharp, non-overlapping space descriptions (they decide routing).
# MAGIC * Instructions + example SQL for the business's tricky definitions.
# MAGIC * The registry table: the agent discovers its tools from it — add a space, the agent gets a new expert.
# MAGIC
# MAGIC **Optional**
# MAGIC * The sample questions shown in the Genie UI.

# COMMAND ----------

# MAGIC %run ../config/config

# COMMAND ----------

import glob, json, os, time, uuid, yaml
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
WAREHOUSE_ID = get_warehouse_id()
ME = w.current_user.me().user_name
PARENT = f"/Workspace/Users/{ME}/{CFG['supervisor']['name']}/genie_spaces"
w.workspace.mkdirs(PARENT)
G = f"{CATALOG}.{GOLD_SCHEMA}"
NS = uuid.UUID("6f1c2b9e-6a0c-4d5e-9a51-6d2a1f0c9b11")
print(f"warehouse={WAREHOUSE_ID}  parent={PARENT}")


def _id(*parts) -> str:
    """Deterministic 32-hex id, so re-running updates the same items instead of duplicating them."""
    return uuid.uuid5(NS, "|".join(parts)).hex


def build_serialized_space(spec: dict) -> dict:
    """Translate one spaces/*.yml file into the Genie `serialized_space` (version 2) structure.
    The API is strict: ids are 32-hex, text fields are arrays, and every id-keyed list is sorted."""
    k = spec["key"]
    tables = []
    for t in spec.get("tables", []):
        entry = {"identifier": f"{G}.{t['name']}"}
        cc = []
        for c in t.get("column_configs", []):
            c = dict(c)
            if "description" in c and isinstance(c["description"], str):
                c["description"] = [c["description"]]
            cc.append(c)
        if cc:
            entry["column_configs"] = sorted(cc, key=lambda c: c["column_name"])
        tables.append(entry)
    metric_views = [{"identifier": f"{G}.{m}"} for m in spec.get("metric_views", [])]

    join_specs = [{
        "id": _id(k, "join", j["left"], j["right"]),
        "left": {"identifier": f"{G}.{j['left']}", "alias": j["left"]},
        "right": {"identifier": f"{G}.{j['right']}", "alias": j["right"]},
        "sql": [j["condition"], f"--rt=FROM_RELATIONSHIP_TYPE_{j['rt']}--"],
    } for j in spec.get("join_specs", [])]

    snippets = {}
    for kind in ("filters", "expressions", "measures"):
        items = []
        for s in spec.get("sql_snippets", {}).get(kind, []):
            item = {"id": _id(k, kind, s["display_name"]), "display_name": s["display_name"], "sql": [s["sql"]]}
            if s.get("alias"):
                item["alias"] = s["alias"]
            if s.get("synonyms") and kind != "expressions":
                item["synonyms"] = s["synonyms"]
            items.append(item)
        if items:
            snippets[kind] = sorted(items, key=lambda x: x["id"])

    examples = []
    for e in spec.get("example_sqls", []):
        item = {"id": _id(k, "example", e["question"]), "question": [e["question"]],
                "sql": [e["sql"].replace("{G}", G).strip()]}
        if e.get("usage_guidance"):
            item["usage_guidance"] = [e["usage_guidance"]]
        examples.append(item)

    instructions = {
        "text_instructions": [{"id": _id(k, "text"), "content": [spec["text_instructions"].strip()]}],
        "example_question_sqls": sorted(examples, key=lambda x: x["id"]),
        "join_specs": sorted(join_specs, key=lambda x: x["id"]),
        # Governed UC functions Genie may call (none by default: documents and notes are attached files).
        "sql_functions": sorted([{"id": _id(k, "fn", f), "identifier": f"{G}.{f}"} for f in spec.get("sql_functions", [])],
                                key=lambda x: x["id"]),
    }
    if snippets:
        instructions["sql_snippets"] = snippets

    return {
        "version": 2,
        "config": {"sample_questions": sorted(
            [{"id": _id(k, "sample", q), "question": [q]} for q in spec.get("sample_questions", [])], key=lambda x: x["id"])},
        "data_sources": {"tables": sorted(tables, key=lambda x: x["identifier"]),
                         "metric_views": sorted(metric_views, key=lambda x: x["identifier"])},
        "instructions": instructions,
        "benchmarks": {"questions": sorted([
            {"id": _id(k, "bench", b["question"]), "question": [b["question"]],
             "answer": [{"format": "SQL", "content": [b["sql"].replace("{G}", G).strip()]}]}
            for b in spec.get("benchmarks", []) if "sql" in b], key=lambda x: x["id"])},   # doc checks: 02_benchmark
    }

# COMMAND ----------

# MAGIC %md
# MAGIC ### Create or update each space (idempotent — matched by title)

# COMMAND ----------

def list_spaces():
    out, token = [], None
    while True:
        r = w.api_client.do("GET", "/api/2.0/genie/spaces", query={"page_size": 100, **({"page_token": token} if token else {})})
        out += r.get("spaces", [])
        token = r.get("next_page_token")
        if not token:
            return out

existing = {s["title"]: s["space_id"] for s in list_spaces()}
registry = []
for path in sorted(glob.glob(f"{REPO_ROOT}/03_genie_spaces/spaces/*.yml")):
    spec = yaml.safe_load(open(path))
    docs_dir = docs_path(spec["key"])
    os.makedirs(docs_dir, exist_ok=True)

    def upsert(space: dict) -> tuple[str, str]:
        body = {"title": spec["title"], "description": spec["description"], "warehouse_id": WAREHOUSE_ID,
                "serialized_space": json.dumps(space)}
        if spec["title"] in existing:
            sid = existing[spec["title"]]
            w.api_client.do("PATCH", f"/api/2.0/genie/spaces/{sid}", body=body)
            return sid, "updated"
        sid = w.api_client.do("POST", "/api/2.0/genie/spaces", body={**body, "parent_path": PARENT})["space_id"]
        existing[spec["title"]] = sid
        return sid, "created"

    space = build_serialized_space(spec)
    # ---- Files Genie searches in Agent mode ("Analyze files in volumes"): this domain's documents (PDFs) AND its
    # approved app notes (markdown). The pattern, per space:
    #   * volumes      → Agent mode reads the files directly (content search, kept in sync with the volume)
    #   * no search functions: each note states its priority (P1/P2/P3) in its text and the space instructions say
    #     how to weigh it; Agent mode cites document and note IDs from the files
    # Foreman asks Genie in Agent mode (supervisor.genie_mode).
    # The FIRST attach request kicks off index creation and can return VOLUME_INDEX_FEATURE_PREVIEW_NOT_ENABLED while it
    # initializes; retrying ~1 minute later succeeds. If it never succeeds, the workspace lacks the preview — the space
    # can't read documents or notes until it's enabled, and the registry says so.
    # Each volume gets a description — the docs' best practice: what it holds, how it's organized, how to use it.
    docs_status = "not requested"
    vols = {}
    if CFG["genie"].get("attach_documents", True):
        vols[f"{docs_dir}/"] = (f"{COMPANY} {spec['title']} documents: procedures, standards, OEM manuals, contracts, "
                                f"root-cause and field reports, policies and meeting minutes (PDF). The document ID is in "
                                f"each file name and title - cite it. Use for limits, procedures, decisions and 'why' questions.")
    if CFG["genie"].get("attach_app_notes", True):
        vols[f"{notes_path(spec['key'])}/"] = (
            "Approved notes from the Andon operations app: decisions and context people added and a reviewer approved, "
            "one markdown file per note (NOTE-<id>.md). Each file states its priority - P1 = approved decision that "
            "supersedes older recommendations in documents, P2 = important context, P3 = for information - plus what it "
            "is about, who approved it and when. Newer than the documents and the data; cite the note ID and priority.")

    def volume_list(with_descriptions: bool) -> list:
        # the API requires volumes sorted by path (like every list in the serialized space)
        return [{"path": v, **({"description": d} if with_descriptions else {})} for v, d in sorted(vols.items())]

    if vols:
        with_desc = True
        for attempt in range(6):
            with_docs = {**space, "data_sources": {**space["data_sources"], "volumes": volume_list(with_desc)}}
            try:
                space_id, action = upsert(with_docs)
                docs_status = f"files: {', '.join(v.rstrip('/').split('/')[-1] for v in sorted(vols))}"
                break
            except Exception as e:
                if with_desc and "description" in str(e).lower():
                    print("   (this API version takes no volume description — add it in the Sources tab)")
                    with_desc = False
                    continue
                if "VOLUME_INDEX_FEATURE_PREVIEW_NOT_ENABLED" not in str(e):
                    raise
                print(f"   … file index initializing for {vols} (attempt {attempt + 1}/6)")
                time.sleep(45)
        else:
            space_id, action = upsert(space)
            docs_status = "PENDING: enable preview 'Analyze Files in Volumes with Genie Agents', then re-run"
    else:
        space_id, action = upsert(space)

    registry.append(dict(domain_key=spec["key"], title=spec["title"], space_id=space_id,
                         description=spec["description"], docs_path=docs_dir, docs_status=docs_status,
                         url=f"{w.config.host.rstrip('/')}/genie/rooms/{space_id}"))
    if spec.get("sql_functions"):
        docs_status = f"{docs_status} · functions: {', '.join(spec['sql_functions'])}()"
        registry[-1]["docs_status"] = docs_status
    # Who may open/ask this space: the groups whose domains include it (UC still decides what data they see).
    acl = [{"group_name": g["name"], "permission_level": "CAN_RUN"}
           for g in CFG.get("governance", {}).get("groups", []) if spec["key"] in g["domains"]]
    if acl:
        w.api_client.do("PATCH", f"/api/2.0/permissions/genie/{space_id}", body={"access_control_list": acl})
    print(f"✅ {action:<7} {spec['title']:<40} {space_id}   docs: {docs_status}   CAN_RUN: {[a['group_name'] for a in acl]}")

# Genie runs each question's SQL on the space's warehouse AS the person asking, so the same groups need CAN_USE on it
# (a workspace's starter warehouse is often open to all users; a dedicated demo warehouse usually isn't).
groups = [{"group_name": g["name"], "permission_level": "CAN_USE"} for g in CFG.get("governance", {}).get("groups", [])]
if groups:
    w.api_client.do("PATCH", f"/api/2.0/permissions/sql/warehouses/{WAREHOUSE_ID}", body={"access_control_list": groups})
    print(f"CAN_USE on warehouse {WAREHOUSE_ID}: {[g['group_name'] for g in groups]}")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Registry — how the supervisor finds its tools
# MAGIC The supervisor agent (Step 4) never hardcodes space IDs. It reads this table, so re-deploying into a new
# MAGIC workspace (new IDs) just works.

# COMMAND ----------

spark.createDataFrame(registry).write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{CATALOG}.{GOLD_SCHEMA}.genie_space_registry")
os.makedirs(REGISTRY_PATH, exist_ok=True)
with open(f"{REGISTRY_PATH}/genie_space_registry.json", "w") as f:
    json.dump(registry, f, indent=2)
display(spark.table(f"{CATALOG}.{GOLD_SCHEMA}.genie_space_registry"))

# COMMAND ----------

# MAGIC %md
# MAGIC ### Smoke test — ask each space one question through the Conversation API
# MAGIC This is the same API the supervisor agent uses.

# COMMAND ----------

def ask(space_id: str, question: str, timeout_s: int = 180) -> dict:
    r = w.api_client.do("POST", f"/api/2.0/genie/spaces/{space_id}/start-conversation", body={"content": question})
    conv, msg = r["conversation_id"], r["message_id"]
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        m = w.api_client.do("GET", f"/api/2.0/genie/spaces/{space_id}/conversations/{conv}/messages/{msg}")
        if m.get("status") in ("COMPLETED", "FAILED", "CANCELLED"):
            return m
        time.sleep(3)
    return {"status": "TIMEOUT"}

tests = {
    "production": "Which plant had the lowest OEE in FY26 Q4?",
    "quality": "How many porosity NCRs were opened since May 2026?",
    "maintenance": "Which machine had the most breakdowns this fiscal year?",
    "supply_chain": "What is the carrier on-time rate by carrier out of Memphis?",
}
for r in registry:
    m = ask(r["space_id"], tests[r["domain_key"]])
    sql = next((a["query"]["query"] for a in m.get("attachments", []) if a.get("query")), None)
    text = next((a["text"]["content"] for a in m.get("attachments", []) if a.get("text")), "")
    print(f"\n[{r['domain_key']}] {tests[r['domain_key']]}  → {m.get('status')}")
    if sql:
        print("  SQL:", " ".join(sql.split())[:400])
    if text:
        print("  Answer:", text[:400])
