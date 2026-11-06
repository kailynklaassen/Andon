"""Data access for the KK's Parts Andon app (backend).

Two modes, one set of queries:

  * live     — every query runs on a SQL warehouse against the gold layer (in a Databricks App the
               app's service principal signs in through `Config()`; locally, your CLI profile does).
  * snapshot — the same queries read from parquet files in data/snapshot/ (an offline option for
               development; no snapshot is shipped in this repo — deployed apps always run live).

Confidential commercial columns (unit prices, PO / order values, standard costs — the ones the ABAC
column mask protects) are never selected, so a snapshot can't leak governed data.
"""
from __future__ import annotations

import os
import time
from pathlib import Path

import pandas as pd

from backend.core.cache import ttl_cache

SNAPSHOT_DIR = Path(__file__).resolve().parents[2] / "data" / "snapshot"

CATALOG = os.getenv("KK_CATALOG", "your_catalog")
GOLD = os.getenv("KK_GOLD_SCHEMA", "mfg_gold")
BRONZE = os.getenv("KK_BRONZE_SCHEMA", "mfg_bronze")   # where approved corrections are written back (via the sync job)


def data_mode() -> str:
    """'live' when a warehouse is configured and KK_DATA_MODE isn't forcing snapshot."""
    mode = os.getenv("KK_DATA_MODE", "auto").lower()
    if mode in ("live", "snapshot"):
        return mode
    return "live" if os.getenv("DATABRICKS_WAREHOUSE_ID") else "snapshot"


# -----------------------------------------------------------------------------
# 1. THE QUERIES — one per dataset the app needs. {g} = <catalog>.<gold schema>.
#    Kept small and pre-aggregated where the app never needs row detail.
# -----------------------------------------------------------------------------
QUERIES: dict[str, str] = {
    "plants": """SELECT plant_id, plant_name, city, state_country, region, latitude, longitude,
                        product_family, pm_compliance_target FROM {g}.dim_plant""",
    "warehouses": """SELECT warehouse_id, warehouse_name, warehouse_type, plant_id, city, state_country, region,
                            latitude, longitude, capacity_pallets FROM {g}.dim_warehouse""",
    "suppliers": """SELECT supplier_id, supplier_name, city, country, category, quality_agreement_ppm_limit,
                           on_time_target, approved_since FROM {g}.dim_supplier""",
    "customers": "SELECT customer_id, customer_name, industry, region, serving_dc, tier, otif_target FROM {g}.dim_customer",
    "carriers": "SELECT carrier_id, carrier_name, mode, sla_on_time_target FROM {g}.dim_carrier",
    "materials": """SELECT material_id, material_name, category, unit_of_measure, primary_supplier_id,
                           primary_supplier_name, lead_time_days FROM {g}.dim_material""",
    "lines": """SELECT line_id, line_name, line_sequence, work_center_count, ideal_cycle_time_s, plant_id, plant_name
                FROM {g}.dim_production_line""",
    "machines": """SELECT machine_id, machine_name, machine_type, process_step, oem, model, install_date, criticality,
                          pm_interval_days, line_id, plant_id FROM {g}.dim_work_center""",
    # OEE building blocks per line, shift and month (OEE itself is computed in pandas so it can be re-aggregated)
    "line_shift_month": """
        SELECT line_id, plant_id, shift, production_month AS month,
               SUM(planned_minutes) AS planned_min, SUM(run_minutes) AS run_min, SUM(ideal_minutes) AS ideal_min,
               SUM(total_units) AS total_units, SUM(good_units) AS good_units,
               SUM(scrap_units) AS scrap_units, SUM(rework_units) AS rework_units,
               SUM(dt_equipment_failure_min) AS dt_equipment_failure, SUM(dt_planned_maintenance_min) AS dt_planned_maintenance,
               SUM(dt_changeover_min) AS dt_changeover, SUM(dt_material_shortage_min) AS dt_material_shortage,
               SUM(dt_quality_hold_min) AS dt_quality_hold, SUM(dt_no_operator_min) AS dt_no_operator
        FROM {g}.fact_shift_production GROUP BY ALL""",
    "machine_daily": """
        SELECT reading_date, machine_id, avg_vibration_mm_s, max_vibration_mm_s, avg_temperature_c,
               avg_motor_load_pct, running_hours, down_hours, hours_above_4_5_mm_s, breakdowns
        FROM {g}.fact_machine_health_daily""",
    "work_orders": """
        SELECT work_order_id, created_ts, plant_id, line_id, machine_id, work_order_type, priority, failure_mode,
               description, status, pm_due_date, is_breakdown, is_pm_deferred, completed_ts, repair_hours,
               labor_hours, parts_cost_usd, contractor_cost_usd
        FROM {g}.fact_maintenance_work_order""",
    "downtime": """
        SELECT downtime_event_id, start_ts, shift, event_scope, plant_id, line_id, machine_id, reason_category,
               reason_detail, duration_minutes, related_work_order_id, related_po_number, related_ncr_id
        FROM {g}.fact_downtime_event""",
    "ncrs": """
        SELECT ncr_id, opened_date, source, plant_id, line_id, machine_id, part_number, material_id, supplier_id,
               defect_code, severity, qty_affected, disposition, cost_of_poor_quality_usd, ncr_status, capa_id
        FROM {g}.fact_nonconformance""",
    "capas": """
        SELECT capa_id, title, root_cause_category, plant_id, supplier_id, opened_date, due_date, closed_date, status,
               owner_id, linked_ncr_count, linked_copq_usd
        FROM {g}.fact_capa""",
    "inspections": """
        SELECT inspection_date, shift, plant_id, line_id, characteristic, characteristic_uom, nominal,
               lower_spec_limit, upper_spec_limit, sample_size, defects_found, measured_mean, cpk
        FROM {g}.fact_quality_inspection""",
    "receipts": """
        SELECT po_number, promised_date, receipt_date, supplier_id, material_id, plant_id, order_qty,
               received_qty, inspected_qty, rejected_qty, days_late, is_on_time, is_received
        FROM {g}.fact_supplier_receipt""",
    "shipments_month": """
        SELECT ship_month AS month, warehouse_id, carrier_id, customer_id,
               COUNT(*) AS shipments,
               COUNT(is_carrier_on_time) AS delivered,
               SUM(CAST(is_carrier_on_time AS INT)) AS carrier_on_time,
               SUM(CAST(is_on_time_to_customer AS INT)) AS on_time_to_customer,
               SUM(CAST(is_otif AS INT)) AS otif,
               SUM(freight_cost_usd) AS freight_cost_usd
        FROM {g}.fact_shipment GROUP BY ALL""",
    "plant_dc": """
        SELECT producing_plant_id AS plant_id, warehouse_id, COUNT(*) AS shipments
        FROM {g}.fact_shipment GROUP BY ALL""",
    "genie_spaces": "SELECT domain_key, title, url FROM {g}.genie_space_registry",
}

DATE_COLS = {
    "line_shift_month": ["month"], "machine_daily": ["reading_date"],
    "work_orders": ["created_ts", "pm_due_date", "completed_ts"], "downtime": ["start_ts"],
    "ncrs": ["opened_date"], "capas": ["opened_date", "due_date", "closed_date"],
    "inspections": ["inspection_date"], "receipts": ["promised_date", "receipt_date"],
    "shipments_month": ["month"], "machines": ["install_date"],
}


# -----------------------------------------------------------------------------
# 2. LIVE: SQL warehouse connection (cached per process, as the Apps guidance requires)
# -----------------------------------------------------------------------------
@ttl_cache(seconds=3000, data=False)  # one connection per process; re-opened before the OAuth token ages out
def _connection():
    from databricks import sql
    from databricks.sdk.core import Config

    cfg = Config()   # Apps: injected SP credentials · local: DATABRICKS_CONFIG_PROFILE
    return sql.connect(server_hostname=cfg.host,
                       http_path=f"/sql/1.0/warehouses/{os.environ['DATABRICKS_WAREHOUSE_ID']}",
                       credentials_provider=lambda: cfg.authenticate)


def run_sql(statement: str) -> pd.DataFrame:
    """Retries transient warehouse errors with a fresh connection: a serverless warehouse that is starting or
    scaling out answers "session is not fully initialized yet", and long-lived connections eventually get closed."""
    for attempt in range(4):
        try:
            with _connection().cursor() as cur:
                cur.execute(statement)
                return cur.fetchall_arrow().to_pandas()
        except Exception as e:
            transient = any(t in str(e) for t in ("not fully initialized", "Invalid SessionHandle", "closed",
                                                  "Connection reset", "timed out", "TEMPORARILY_UNAVAILABLE"))
            if not transient or attempt == 3:
                raise
            _connection.cache_clear()
            time.sleep(2 * (attempt + 1))


def _typed(name: str, df: pd.DataFrame) -> pd.DataFrame:
    for c in DATE_COLS.get(name, []):
        if c in df:   # timestamps are plant-local wall-clock times; drop the warehouse's UTC tag
            df[c] = pd.to_datetime(df[c])
            if df[c].dt.tz is not None:
                df[c] = df[c].dt.tz_localize(None)
    for c in df.columns:   # the warehouse returns DECIMAL as object; the app wants floats
        if df[c].dtype == object:
            try:
                df[c] = pd.to_numeric(df[c])
            except (ValueError, TypeError):
                pass
    return df


@ttl_cache(seconds=600)           # every page reads these; a 10-minute cache is what makes pages instant
def load(name: str) -> pd.DataFrame:
    if data_mode() == "live":
        return _typed(name, run_sql(QUERIES[name].format(g=f"`{CATALOG}`.`{GOLD}`")))
    return _typed(name, pd.read_parquet(SNAPSHOT_DIR / f"{name}.parquet"))


# -----------------------------------------------------------------------------
# 3. DERIVED VIEWS the pages share (all definitions match the gold metric views)
# -----------------------------------------------------------------------------
OEE_TARGET = 0.85
OEM_VIBRATION_LIMIT = 4.5      # Hartwell manual §7.4 — replace spindle bearings
OEM_VIBRATION_ALERT = 3.5
INTERNAL_PM_LIMIT = 7.1        # PM-CNC-030 Rev C (outdated)
DOWNTIME_REASONS = {
    "dt_equipment_failure": "Equipment Failure", "dt_planned_maintenance": "Planned Maintenance",
    "dt_changeover": "Changeover", "dt_material_shortage": "Material Shortage",
    "dt_quality_hold": "Quality Hold", "dt_no_operator": "No Operator",
}


def add_oee(df: pd.DataFrame) -> pd.DataFrame:
    """OEE = Availability × Performance × Quality, computed from summed minutes/units."""
    df = df.copy()
    df["availability"] = df.run_min / df.planned_min
    df["performance"] = df.ideal_min / df.run_min
    df["quality"] = df.good_units / df.total_units
    df["oee"] = df.availability * df.performance * df.quality
    return df


SUM_COLS = ["planned_min", "run_min", "ideal_min", "total_units", "good_units", "scrap_units", "rework_units",
            *DOWNTIME_REASONS]


def oee_by(keys: list[str], since: pd.Timestamp | None = None) -> pd.DataFrame:
    df = load("line_shift_month")
    if since is not None:
        df = df[df.month >= since]
    return add_oee(df.groupby(keys, as_index=False)[SUM_COLS].sum())


def today() -> pd.Timestamp:
    """'Today' for the story = the last day in the data (2026-09-30)."""
    return load("machine_daily").reading_date.max()


def last_month() -> pd.Timestamp:
    return load("line_shift_month").month.max()


def pm_compliance(keys: list[str]) -> pd.DataFrame:
    wo = load("work_orders")
    pm = wo[wo.work_order_type.str.lower() == "preventive"].copy()
    pm["done"] = pm.status.str.lower() == "completed"
    return pm.groupby(keys, as_index=False).agg(pm_due=("done", "size"), pm_done=("done", "sum")) \
             .assign(pm_compliance=lambda d: d.pm_done / d.pm_due)


@ttl_cache(seconds=600)
def monthly_vibration() -> pd.DataFrame:
    """Average running vibration per machine and month, weighted by running hours — the same definition as the
    `Average Vibration mm/s` measure in the maintenance metric view (and so the same numbers Genie reports)."""
    d = load("machine_daily").assign(month=lambda t: t.reading_date.dt.to_period("M").dt.start_time)
    d = d.assign(w=d.avg_vibration_mm_s * d.running_hours)
    g = d.groupby(["machine_id", "month"], as_index=False)[["w", "running_hours"]].sum()
    return g.assign(vibration=g.w / g.running_hours.where(g.running_hours > 0))[["machine_id", "month", "vibration"]]


def first_month_above(machine_id: str, limit: float) -> pd.Timestamp:
    """A limit is crossed in the first MONTH whose average running vibration is above it (never a daily spike)."""
    mv = monthly_vibration().query("machine_id == @machine_id and vibration > @limit")
    return mv.month.min() if len(mv) else pd.NaT


WINDOW_MONTHS = 6   # "recent" window for machine KPIs: Apr–Sep, the period the FY26 story plays out in


@ttl_cache(seconds=600)
def machine_status() -> pd.DataFrame:
    """One row per work center with its health now — drives node colors and the machine KPIs.
    vib_now = last month's average running vibration; vib_base = the Oct–Dec baseline (same weighting)."""
    m = load("machines")
    mv = monthly_vibration()
    lm = mv.month.max()
    now = mv[mv.month == lm].set_index("machine_id").vibration.rename("vib_now")
    base = mv[mv.month < "2026-01-01"].groupby("machine_id").vibration.mean().rename("vib_base")
    since = today() - pd.DateOffset(months=WINDOW_MONTHS) + pd.Timedelta(days=1)
    wo = load("work_orders")
    bk = wo[wo.is_breakdown.astype(bool) & (wo.created_ts >= since)].groupby("machine_id").size().rename("breakdowns_6m")
    deferred = wo[wo.is_pm_deferred.astype(bool)].groupby("machine_id").size().rename("pm_deferred")
    ncr = load("ncrs")
    ncr6 = ncr[ncr.opened_date >= since].groupby("machine_id").size().rename("ncrs_6m")
    out = m.set_index("machine_id").join([now, base, bk, deferred, ncr6]).reset_index()
    out[["breakdowns_6m", "pm_deferred", "ncrs_6m"]] = out[["breakdowns_6m", "pm_deferred", "ncrs_6m"]].fillna(0).astype(int)
    # Machines of different types run at very different vibration levels (a cold header runs at ~4.4 mm/s),
    # so health is judged against each machine's own baseline, not one absolute number.
    out["vib_ratio"] = out.vib_now / out.vib_base

    def status(r):
        if r.vib_ratio >= 2.0 or r.breakdowns_6m >= 12:
            return "critical"
        if r.vib_ratio >= 1.5 or r.breakdowns_6m >= 8 or r.ncrs_6m >= 20:
            return "warning"
        return "ok"
    out["status"] = out.apply(status, axis=1)
    return out


def supplier_shortages(supplier_id: str, since: pd.Timestamp) -> pd.DataFrame:
    """Material-shortage downtime events whose purchase order belongs to this supplier."""
    dt = load("downtime")
    po = load("receipts").set_index("po_number").supplier_id
    ms = dt[(dt.reason_category == "Material Shortage") & (dt.start_ts >= since)]
    return ms[ms.related_po_number.map(po) == supplier_id]


# Supplier cities → coordinates for the network map (dim_supplier carries city/country only).
SUPPLIER_COORDS = {
    "Saltillo": (25.4232, -101.0053), "Erie": (42.1292, -80.0851), "Katowice": (50.2649, 19.0238),
    "Pittsburgh": (40.4406, -79.9959), "Jamshedpur": (22.8046, 86.2029), "Duisburg": (51.4344, 6.7623),
    "Greenville": (34.90, -82.25), "Osaka": (34.6937, 135.5023), "Cleveland": (41.4993, -81.6944),
    "Toledo": (41.6528, -83.5379), "Dayton": (39.7589, -84.1916), "Gdansk": (54.3520, 18.6466),
    "Hamburg": (53.5511, 9.9937), "Penang": (5.4141, 100.3288), "Austin": (30.2672, -97.7431),
    "Budapest": (47.4979, 19.0402), "Pune": (18.62, 73.75), "Nashik": (19.9975, 73.7898),
    "Houston": (29.7604, -95.3698), "Porto": (41.1579, -8.6291), "Indianapolis": (39.7684, -86.1581),
    "Lodz": (51.7592, 19.4560), "Monterrey": (25.75, -100.20), "Mumbai": (19.0760, 72.8777),
}
