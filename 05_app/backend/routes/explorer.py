"""Plant Explorer — the physical hierarchy: plant floor → line → work center (and the suppliers at the receiving dock).

Every level returns the same parts: a header, KPI tiles, charts, tables, the insights touching that node, and the
actions a person may take there. The floor scene is separate so the canvas can stay mounted while panels change.
"""
from __future__ import annotations

import pandas as pd
from fastapi import APIRouter, HTTPException

from backend.core import charts as C
from backend.core import data as D
from backend.core import insights as I
from backend.core import scenes as S
from backend.core import shapes as X
from backend.core.cache import ttl_cache

router = APIRouter(prefix="/api/explorer", tags=["explorer"])


def _related(**ref) -> list[dict]:
    return [X.insight(i) for i in I.for_entity(I.all_insights(), **ref)[:3]]


@router.get("/plants")
@ttl_cache(seconds=600)
def plants() -> list[dict]:
    p = D.load("plants")
    status = S.plant_status(I.all_insights())
    oee = D.oee_by(["plant_id"], since=D.last_month()).set_index("plant_id").oee
    return X.clean([{"id": r.plant_id, "name": r.plant_name, "city": r.city, "status": status[r.plant_id],
                     "oee": oee.get(r.plant_id)} for r in p.itertuples()])


@router.get("/scene/{plant_id}")
@ttl_cache(seconds=600)
def scene(plant_id: str) -> dict:
    if plant_id not in set(D.load("plants").plant_id):
        raise HTTPException(404, f"unknown plant {plant_id}")
    return X.clean(S.floor_scene(plant_id, I.all_insights(), None, None, height=610))


@router.get("/plant/{plant_id}")
@ttl_cache(seconds=600)
def plant(plant_id: str) -> dict:
    plants_df = D.load("plants").set_index("plant_id")
    if plant_id not in plants_df.index:
        raise HTTPException(404, f"unknown plant {plant_id}")
    p = plants_df.loc[plant_id]
    insights = I.all_insights()
    status = S.plant_status(insights)
    oee_sep = D.oee_by(["plant_id"], since=D.last_month()).set_index("plant_id").oee
    pm = D.pm_compliance(["plant_id"]).set_index("plant_id").loc[plant_id]
    fy = D.oee_by(["plant_id"]).set_index("plant_id").loc[plant_id]
    ncr = D.load("ncrs").query("plant_id == @plant_id")
    return {
        "eyebrow": f"Plant · {p.region}", "title": p.plant_name, "subtitle": f"{p.product_family} · {p.city}, {p.state_country}",
        "kpis": [
            X.kpi(f"OEE · {D.last_month():%b}", f"{oee_sep[plant_id]:.1%}", f"FY26 {fy.oee:.1%}", "bad" if oee_sep[plant_id] < .75 else "warn"),
            X.kpi("PM compliance · FY26", f"{pm.pm_compliance:.1%}", f"plant target {p.pm_compliance_target:.0%}",
                  "warn" if pm.pm_compliance < p.pm_compliance_target else "good"),
            X.kpi("NCRs · FY26", f"{len(ncr):,}", f"${ncr.cost_of_poor_quality_usd.sum() / 1e6:,.2f}M cost of poor quality"),
            X.kpi("Open issues", f"{len(I.for_entity(insights, plant_id=plant_id))}", "", "bad" if status[plant_id] == "critical" else ""),
        ],
        "charts": [X.figure(C.oee_trend({"plant_id": plant_id}, by="line_id", title="OEE by line")),
                   X.figure(C.downtime_mix({"plant_id": plant_id}, title="Downtime by reason"))],
        "tables": [], "related": _related(plant_id=plant_id),
        "entity": {"type": "plant", "id": plant_id}, "actions": ["comment", "assign_owner", "data_correction"],
        "ask": [i["ask"] for i in _related(plant_id=plant_id)] or [f"How is {p.plant_name} performing this quarter versus target, and what's driving it?"],
    }


@router.get("/line/{line_id}")
@ttl_cache(seconds=600)
def line(line_id: str) -> dict:
    lines = D.load("lines").set_index("line_id")
    if line_id not in lines.index:
        raise HTTPException(404, f"unknown line {line_id}")
    ln = lines.loc[line_id]
    p = D.load("plants").set_index("plant_id").loc[ln.plant_id]
    o = D.oee_by(["line_id"], since=D.last_month()).set_index("line_id").loc[line_id]
    fy = D.oee_by(["line_id"]).set_index("line_id").loc[line_id]
    pmc = D.pm_compliance(["line_id"]).set_index("line_id").loc[line_id]
    ms = D.machine_status().query("line_id == @line_id").sort_values("process_step")
    rel = _related(line_id=line_id)
    return {
        "eyebrow": f"Production line · {p.plant_name}", "title": f"{line_id} · {ln.line_name}",
        "subtitle": f"{int(ln.work_center_count)} work centers · ideal cycle {ln.ideal_cycle_time_s:.1f} s per unit",
        "kpis": [
            X.kpi(f"OEE · {D.last_month():%b}", f"{o.oee:.1%}", f"FY26 {fy.oee:.1%} · target 85%", "bad" if o.oee < .7 else "warn" if o.oee < .85 else "good"),
            X.kpi("Availability", f"{o.availability:.1%}", f"FY26 {fy.availability:.1%}"),
            X.kpi("Performance", f"{o.performance:.1%}", f"FY26 {fy.performance:.1%}"),
            X.kpi("First pass yield", f"{o.quality:.1%}", f"FY26 {fy.quality:.1%}"),
            X.kpi(f"Good units · {D.last_month():%b}", f"{o.good_units:,.0f}", f"scrap {o.scrap_units:,.0f} · rework {o.rework_units:,.0f}"),
            X.kpi("PM compliance", f"{pmc.pm_compliance:.1%}", f"{int(pmc.pm_done)} of {int(pmc.pm_due)} PMs", "warn" if pmc.pm_compliance < .9 else "good"),
        ],
        "charts": [X.figure(C.oee_trend({"line_id": line_id}, by="line_id", title="OEE by month")),
                   X.figure(C.downtime_mix({"line_id": line_id}, title="Downtime by reason")),
                   X.figure(C.shift_quality(line_id))],
        "tables": [{"title": "Work centers", "note": f"{len(ms)} in process order",
                    **X.table(ms, {"process_step": "Step", "machine_id": "Work center", "machine_name": "Name", "oem": "OEM",
                                   "criticality": "Crit.", "vib_now": "Vibration (Sep avg)", "breakdowns_6m": "Breakdowns Apr–Sep",
                                   "ncrs_6m": "NCRs Apr–Sep", "pm_deferred": "Deferred PMs", "status": "Status"},
                              {"vib_now": "mms", "status": "status"})}],
        "related": rel, "entity": {"type": "line", "id": line_id},
        "actions": list(dict.fromkeys([a for x in rel for a in x["actions"]] + ["comment", "data_correction"])),
        "insight_id": rel[0]["id"] if rel else "", "ask": [i["ask"] for i in rel],
    }


@router.get("/machine/{machine_id}")
@ttl_cache(seconds=600)
def machine(machine_id: str) -> dict:
    st = D.machine_status().set_index("machine_id")
    if machine_id not in st.index:
        raise HTTPException(404, f"unknown work center {machine_id}")
    ms = st.loc[machine_id]
    wo = D.load("work_orders").query("machine_id == @machine_id").sort_values("created_ts", ascending=False)
    bk = wo[wo.is_breakdown.astype(bool)]
    bk6 = bk[bk.created_ts >= D.today() - pd.DateOffset(months=D.WINDOW_MONTHS) + pd.Timedelta(days=1)]   # Apr–Sep
    ncr = D.load("ncrs").query("machine_id == @machine_id").sort_values("opened_date", ascending=False)
    rel = _related(machine_id=machine_id)
    return {
        "eyebrow": f"Work center · {ms.line_id} · step {ms.process_step}", "title": f"{machine_id} · {ms.machine_name}",
        "subtitle": f"{ms.oem} {ms.model} · installed {ms.install_date:%Y} · criticality {ms.criticality} · PM every {ms.pm_interval_days} days",
        "kpis": [
            X.kpi(f"Vibration · {D.last_month():%b} avg", f"{ms.vib_now:.2f} mm/s", f"baseline {ms.vib_base:.2f} · {ms.vib_ratio:.1f}×",
                  "bad" if ms.vib_ratio >= 2 else "warn" if ms.vib_ratio >= 1.35 else "good"),
            X.kpi("Breakdowns · Apr–Sep", f"{ms.breakdowns_6m}", f"{len(bk)} in FY26", "bad" if ms.breakdowns_6m >= 12 else ""),
            X.kpi("Repair hours · Apr–Sep", f"{bk6.repair_hours.sum():,.0f} h", f"MTTR {bk6.repair_hours.mean() if len(bk6) else 0:.1f} h"),
            X.kpi("Repair cost · Apr–Sep", f"${(bk6.parts_cost_usd + bk6.contractor_cost_usd).sum() / 1e3:,.0f}K",
                  f"contractor ${bk6.contractor_cost_usd.sum() / 1e3:,.0f}K"),
            X.kpi("Deferred PMs", f"{ms.pm_deferred}", "FY26", "warn" if ms.pm_deferred else "good"),
            X.kpi("NCRs · Apr–Sep", f"{ms.ncrs_6m}", f"{len(ncr)} in FY26", "bad" if ms.ncrs_6m >= 20 else ""),
        ],
        "charts": [X.figure(C.vibration_chart(machine_id))],
        "tables": [
            {"title": f"Work orders ({len(wo)})", **X.table(wo, {
                "work_order_id": "Work order", "created_ts": "Created", "work_order_type": "Type", "priority": "Priority",
                "failure_mode": "Failure mode", "status": "Status", "repair_hours": "Repair h", "parts_cost_usd": "Parts",
                "contractor_cost_usd": "Contractor"}, {"created_ts": "datetime", "repair_hours": "hours",
                                                      "parts_cost_usd": "money", "contractor_cost_usd": "money"})},
            {"title": f"Nonconformances ({len(ncr)})", **X.table(ncr, {
                "ncr_id": "NCR", "opened_date": "Opened", "defect_code": "Defect", "severity": "Severity", "qty_affected": "Qty",
                "disposition": "Disposition", "cost_of_poor_quality_usd": "Cost", "capa_id": "CAPA", "ncr_status": "Status"},
                {"opened_date": "date", "cost_of_poor_quality_usd": "money"})},
        ],
        "related": rel, "entity": {"type": "machine", "id": machine_id},
        "actions": (rel[0]["actions"] + ["data_correction"]) if rel else ["work_order", "inspect", "comment", "data_correction"],
        "insight_id": rel[0]["id"] if rel else "", "ask": [i["ask"] for i in rel],
        "defaults": {"failure_mode": "spindle bearing wear"} if ms.vib_ratio >= 2 else {},
    }


@router.get("/supplier/{supplier_id}")
@ttl_cache(seconds=600)
def supplier(supplier_id: str) -> dict:
    sups = D.load("suppliers").set_index("supplier_id")
    if supplier_id not in sups.index:
        raise HTTPException(404, f"unknown supplier {supplier_id}")
    s = sups.loc[supplier_id]
    mats = D.load("materials").query("primary_supplier_id == @supplier_id")
    rel = _related(supplier_id=supplier_id)
    return {
        "eyebrow": "Supplier", "title": f"{supplier_id} · {s.supplier_name}",
        "subtitle": f"{s.category} · {s.city}, {s.country} · contract {s.quality_agreement_ppm_limit:,.0f} PPM, {s.on_time_target:.0%} on-time",
        "kpis": [], "charts": [X.figure(C.supplier_trend(supplier_id))],
        "tables": [{"title": "Materials supplied", "note": f"{len(mats)} primary-sourced",
                    **X.table(mats, {"material_id": "Material", "material_name": "Name", "category": "Category",
                                     "lead_time_days": "Lead time (days)"})}],
        "related": rel, "entity": {"type": "supplier", "id": supplier_id},
        "actions": (rel[0]["actions"] if rel else ["comment"]) + ["data_correction"],
        "insight_id": rel[0]["id"] if rel else "", "ask": [i["ask"] for i in rel],
    }
