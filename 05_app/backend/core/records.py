"""The record catalog — so every human correction points at an exact cell in the gold layer.

A data-correction action never says "the vibration looks wrong"; it says
    fact_maintenance_work_order · work_order_id = WO-900323 · failure_mode: "spindle bearing wear" → "tool changer fault"
Each entry maps an app dataset to its gold table, primary key and the columns a person may correct (with labels),
and to the BRONZE table the gold row is built from. An approved correction is written back to that bronze table
(06_human_in_the_loop/01_sync_approved_actions), so the fix flows bronze → silver → gold like any source-system change.
Only columns that exist 1:1 in bronze are correctable (derived gold columns such as repair_hours are not).
Choices for categorical columns come from the values that actually occur in the data, so a correction can only
ever propose a value the pipeline and Genie already understand.
"""
from __future__ import annotations

import pandas as pd

from backend.core import data as D

# dataset → gold table, key column, how to name one record, and the correctable columns (column → label)
CATALOG: dict[str, dict] = {
    "plants": {"table": "dim_plant", "key": "plant_id", "name": "plant_name", "bronze": "bronze_plants", "bronze_key": "plant_id", "fields": {
        "plant_name": "Plant name", "city": "City", "region": "Region", "product_family": "Product family",
        "pm_compliance_target": "PM compliance target"}},
    "lines": {"table": "dim_production_line", "key": "line_id", "name": "line_name", "bronze": "bronze_production_lines", "bronze_key": "line_id", "fields": {
        "line_name": "Line name", "ideal_cycle_time_s": "Ideal cycle time (s)", "work_center_count": "Work centers"}},
    "machines": {"table": "dim_work_center", "key": "machine_id", "name": "machine_name", "bronze": "bronze_work_centers", "bronze_key": "machine_id", "fields": {
        "machine_name": "Name", "machine_type": "Machine type", "oem": "OEM", "model": "Model",
        "criticality": "Criticality", "pm_interval_days": "PM interval (days)", "install_date": "Install date",
        "process_step": "Process step"}},
    "suppliers": {"table": "dim_supplier", "key": "supplier_id", "name": "supplier_name", "bronze": "bronze_suppliers", "bronze_key": "supplier_id", "fields": {
        "supplier_name": "Name", "city": "City", "country": "Country", "category": "Category",
        "quality_agreement_ppm_limit": "Contract PPM limit", "on_time_target": "On-time target"}},
    "materials": {"table": "dim_material", "key": "material_id", "name": "material_name", "bronze": "bronze_materials", "bronze_key": "material_id", "fields": {
        "material_name": "Name", "category": "Category", "primary_supplier_id": "Primary supplier",
        "lead_time_days": "Lead time (days)"}},
    "carriers": {"table": "dim_carrier", "key": "carrier_id", "name": "carrier_name", "bronze": "bronze_carriers", "bronze_key": "carrier_id", "fields": {
        "carrier_name": "Name", "mode": "Mode", "sla_on_time_target": "On-time SLA"}},
    "customers": {"table": "dim_customer", "key": "customer_id", "name": "customer_name", "bronze": "bronze_customers", "bronze_key": "customer_id", "fields": {
        "customer_name": "Name", "tier": "Tier", "serving_dc": "Serving DC", "otif_target": "OTIF target"}},
    "warehouses": {"table": "dim_warehouse", "key": "warehouse_id", "name": "warehouse_name", "bronze": "bronze_warehouses", "bronze_key": "warehouse_id", "fields": {
        "warehouse_name": "Name", "capacity_pallets": "Capacity (pallets)"}},
    "capas": {"table": "fact_capa", "key": "capa_id", "name": "title", "bronze": "bronze_capa", "bronze_key": "capa_id", "fields": {
        "status": "Status", "due_date": "Due date", "owner_id": "Owner", "root_cause_category": "Root cause category"}},
    "work_orders": {"table": "fact_maintenance_work_order", "key": "work_order_id", "name": "work_order_type", "bronze": "bronze_maintenance_work_orders", "bronze_key": "work_order_id", "fields": {
        "work_order_type": "Type", "priority": "Priority", "failure_mode": "Failure mode", "status": "Status",
        "labor_hours": "Labor hours", "parts_cost_usd": "Parts cost (USD)", "contractor_cost_usd": "Contractor cost (USD)"}},
    "ncrs": {"table": "fact_nonconformance", "key": "ncr_id", "name": "defect_code", "bronze": "bronze_nonconformances", "bronze_key": "ncr_id", "fields": {
        "defect_code": "Defect code", "severity": "Severity", "qty_affected": "Qty affected", "disposition": "Disposition",
        "cost_of_poor_quality_usd": "Cost of poor quality (USD)", "ncr_status": "Status", "capa_id": "CAPA"},
        "bronze_columns": {"ncr_status": "status"}},   # gold renames bronze status → ncr_status
    "receipts": {"table": "fact_supplier_receipt", "key": "po_number", "name": "material_id", "bronze": "bronze_goods_receipts", "bronze_key": "po_number", "fields": {
        "received_qty": "Received qty", "rejected_qty": "Rejected qty", "days_late": "Days late", "receipt_date": "Receipt date"}},
}

# which dataset holds the master record for each entity type the app shows
ENTITY_DATASET = {"plant": "plants", "line": "lines", "machine": "machines", "supplier": "suppliers",
                  "material": "materials", "carrier": "carriers", "customer": "customers", "dc": "warehouses",
                  "warehouse": "warehouses", "capa": "capas"}


def gold_table(dataset: str) -> str:
    return f"{D.CATALOG}.{D.GOLD}.{CATALOG[dataset]['table']}"


def bronze_target(dataset: str, column: str) -> dict:
    """Where an approved correction of this gold column is written: bronze table, its key column and column name."""
    spec = CATALOG[dataset]
    return {"bronze_table": f"{D.CATALOG}.{D.BRONZE}.{spec['bronze']}", "bronze_key": spec["bronze_key"],
            "bronze_column": spec.get("bronze_columns", {}).get(column, column)}


def _fmt_date(v) -> str:
    return f"{v:%b %d, %Y}" if isinstance(v, pd.Timestamp) and pd.notna(v) else ""


def related_records(entity_type: str, entity_id: str, limit: int = 40) -> list[dict]:
    """Records a person may correct from this node: its own master row first, then its recent transactions."""
    out: list[dict] = []

    def add(dataset, key_value, label):
        out.append({"dataset": dataset, "key": key_value, "label": label})

    ds = ENTITY_DATASET.get(entity_type)
    if ds:
        m = D.load(ds).set_index(CATALOG[ds]["key"])
        if entity_id in m.index:
            add(ds, entity_id, f"{entity_id} · {m.loc[entity_id][CATALOG[ds]['name']]} ({CATALOG[ds]['table']})")
    if entity_type == "machine":
        wo = D.load("work_orders").query("machine_id == @entity_id").sort_values("created_ts", ascending=False)
        for r in wo.head(limit).itertuples():
            add("work_orders", r.work_order_id, f"{r.work_order_id} · {_fmt_date(r.created_ts)} · {r.work_order_type}"
                + (f" · {r.failure_mode}" if isinstance(r.failure_mode, str) else ""))
        for r in D.load("ncrs").query("machine_id == @entity_id").sort_values("opened_date", ascending=False).head(limit).itertuples():
            add("ncrs", r.ncr_id, f"{r.ncr_id} · {_fmt_date(r.opened_date)} · {r.defect_code}")
    elif entity_type == "line":
        for r in D.load("ncrs").query("line_id == @entity_id").sort_values("opened_date", ascending=False).head(limit).itertuples():
            add("ncrs", r.ncr_id, f"{r.ncr_id} · {_fmt_date(r.opened_date)} · {r.defect_code}")
    elif entity_type == "supplier":
        rc = D.load("receipts").query("supplier_id == @entity_id").sort_values("promised_date", ascending=False)
        for r in rc.head(limit).itertuples():
            add("receipts", r.po_number, f"{r.po_number} · {_fmt_date(r.promised_date)} · {r.material_id} → {r.plant_id}")
    elif entity_type == "capa":
        for r in D.load("ncrs").query("capa_id == @entity_id").sort_values("opened_date", ascending=False).head(limit).itertuples():
            add("ncrs", r.ncr_id, f"{r.ncr_id} · {_fmt_date(r.opened_date)} · {r.defect_code}")
    elif entity_type == "defect":                       # Impact Web defect cluster, id "D:<plant>:<defect code>"
        _, plant, code = entity_id.split(":", 2)
        n = D.load("ncrs").query("plant_id == @plant and defect_code == @code").sort_values("opened_date", ascending=False)
        for r in n.head(limit).itertuples():
            add("ncrs", r.ncr_id, f"{r.ncr_id} · {_fmt_date(r.opened_date)} · {r.line_id or ''} · {r.disposition}")
    return out


def current_value(dataset: str, key_value: str, column: str):
    df = D.load(dataset)
    row = df[df[CATALOG[dataset]["key"]] == key_value]
    return None if row.empty else row.iloc[0][column]


# Names and free-form identifiers are corrected as text (a typo fix or a new value must be possible);
# every other text column has a closed set of values in the data and is corrected from a dropdown.
FREE_TEXT = {"plant_name", "line_name", "machine_name", "supplier_name", "material_name", "carrier_name",
             "customer_name", "warehouse_name", "city", "model"}


def column_kind(dataset: str, column: str) -> tuple[str, list | None]:
    """How to edit a column: ('select', choices) for categories, else 'date' / 'number' / 'text'."""
    s = D.load(dataset)[column]
    if column in FREE_TEXT:
        return "text", None
    if pd.api.types.is_datetime64_any_dtype(s):
        return "date", None
    if pd.api.types.is_numeric_dtype(s) and not pd.api.types.is_bool_dtype(s):
        return "number", None
    vals = sorted(v for v in s.dropna().unique().tolist() if str(v).strip())
    if vals:                                      # a closed set of values already in the data
        return "select", vals
    return "text", None


def choices(dataset: str, column: str, **where) -> list:
    """Distinct values of a column, optionally filtered (e.g. failure modes seen on this machine type)."""
    df = D.load(dataset)
    for k, v in where.items():
        df = df[df[k] == v]
    return sorted(v for v in df[column].dropna().unique().tolist() if str(v).strip())
