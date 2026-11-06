"""What the canvases and the map draw: the plant floor scene, the supply-network map layers, the Impact Web graph.
Built from the same insights the cards show, so a red machine on the floor is red for the same reason everywhere."""
from __future__ import annotations

import pandas as pd

from backend.core import data as D
from backend.core import insights as I
from backend.core import palette as T
from backend.core.cache import ttl_cache

RGB = {"critical": [214, 40, 57], "high": [242, 165, 65], "watch": [242, 165, 65], "warning": [242, 165, 65],
       "ok": [42, 157, 143], "none": [143, 163, 191]}


def _worst(sevs: list[str]) -> str:
    for s in ("critical", "high", "watch"):
        if s in sevs:
            return s
    return "ok"


def plant_status(insights: list[I.Insight]) -> dict[str, str]:
    out = {}
    for p in D.load("plants").plant_id:
        out[p] = _worst([i.severity for i in I.for_entity(insights, plant_id=p)])
    return out


# -----------------------------------------------------------------------------
# 1. Network map — suppliers → plants → distribution centers (deck.gl draws it in the browser)
# -----------------------------------------------------------------------------
def network(insights: list[I.Insight]) -> dict:
    """Layer data for the map: plants (status colored), DCs, suppliers and supplier→plant lanes.
    Lanes from a supplier the insight engine flagged are red and thick; the rest are faint."""
    plants = D.load("plants")
    status = plant_status(insights)
    oee = D.oee_by(["plant_id"], since=D.last_month()).set_index("plant_id").oee
    out_plants = [{"id": r.plant_id, "name": r.plant_name, "lon": r.longitude, "lat": r.latitude,
                   "status": status[r.plant_id], "color": RGB[status[r.plant_id]],
                   "tip": f"{r.plant_name} · {r.product_family} · {D.last_month():%b} OEE {oee.get(r.plant_id, float('nan')):.0%}"}
                  for r in plants.itertuples()]
    wh = D.load("warehouses")
    bad_dc = {"DC-MEM"} if any(i.carrier_id for i in insights if i.severity == "critical") else set()
    dcs = [{"id": r.warehouse_id, "lon": r.longitude, "lat": r.latitude, "tip": f"{r.warehouse_name} · {r.capacity_pallets:,} pallets",
            "color": RGB["critical"] if r.warehouse_id in bad_dc else [62, 124, 177]}
           for r in wh[wh.warehouse_type == "Distribution Center"].itertuples()]
    flagged = {i.supplier_id for i in insights if i.supplier_id and i.severity in ("critical", "high")}
    sup = D.load("suppliers")
    coords = {r.supplier_id: D.SUPPLIER_COORDS[r.city] for r in sup.itertuples() if r.city in D.SUPPLIER_COORDS}
    suppliers = [{"id": r.supplier_id, "name": r.supplier_name, "lat": coords[r.supplier_id][0], "lon": coords[r.supplier_id][1],
                  "tip": f"{r.supplier_name} · {r.category} · {r.city}, {r.country}",
                  "color": RGB["critical"] if r.supplier_id in flagged else [255, 255, 255]}
                 for r in sup.itertuples() if r.supplier_id in coords]
    at = {p["id"]: (p["lon"], p["lat"]) for p in out_plants}
    rc = D.load("receipts").groupby(["supplier_id", "plant_id"]).size().rename("n").reset_index()
    arcs = [{"from": [coords[r.supplier_id][1], coords[r.supplier_id][0]], "to": list(at[r.plant_id]),
             "hot": r.supplier_id in flagged, "width": 4 if r.supplier_id in flagged else max(1, min(3, r.n / 40)),
             "tip": f"{r.supplier_id} → {r.plant_id} · {r.n} POs"}
            for r in rc.itertuples() if r.supplier_id in coords and r.plant_id in at]
    return {"plants": out_plants, "dcs": dcs, "suppliers": suppliers, "arcs": arcs}


# -----------------------------------------------------------------------------
# 2. Scene builder for the plant floor canvas
# -----------------------------------------------------------------------------
SHORT = {"CNC Horizontal Machining Center": "CNC HMC", "CNC Vertical Mill": "CNC Mill", "Robotic Assembly Cell": "Assembly Cell",
         "End-of-Line Test Stand": "EOL Test", "Automated Packaging Line": "Packaging", "Servo Press-Fit Station": "Press-Fit",
         "Coordinate Measuring Machine": "CMM", "Terminal Crimp Press": "Crimp Press", "Automatic Wire Cut & Strip": "Wire Cut",
         "Crimp Pull Tester": "Pull Tester", "Robotic Deburr Cell": "Deburr Cell", "Carburizing Furnace": "Furnace",
         "Automatic Hardness Tester": "Hardness Test", "Harness Continuity Tester": "Continuity", "CNC Turning Center": "CNC Lathe",
         "Automatic Band Saw": "Band Saw", "Robotic MIG Welder": "MIG Welder", "Helium Leak Tester": "Leak Test",
         "Shot Blast Cabinet": "Shot Blast", "CNC Gear Hobber": "Gear Hobber", "Oil Quench Tank": "Quench Tank"}


def _short(name: str) -> str:
    base = name.split(" #")[0]
    return SHORT.get(base, base)[:15]


def floor_scene(plant_id: str, insights: list[I.Insight], focus_line: str | None, selected: str | None,
                height: int = 600) -> dict:
    plants = D.load("plants").set_index("plant_id")
    lines = D.load("lines").query("plant_id == @plant_id").sort_values("line_sequence")
    ms = D.machine_status().query("plant_id == @plant_id")
    lm = D.last_month()
    oee_now = D.oee_by(["line_id"], since=lm).set_index("line_id")
    by_month = D.oee_by(["line_id", "month"])
    oee_first = by_month[by_month.month == by_month.month.min()].set_index("line_id").oee   # October, FY start
    pmc = D.pm_compliance(["line_id"]).set_index("line_id").pm_compliance
    by_machine = {i.machine_id: i for i in insights if i.machine_id}
    by_line = {}
    for i in insights:
        if i.line_id:
            by_line.setdefault(i.line_id, []).append(i)
    # a line is starved when a breaching supplier's shortages hit it hardest (its top lines by shortage stops)
    starved = {l for i in insights if i.id.startswith("SUP-") for l in i.lines}

    out_lines = []
    for ln in lines.itertuples():
        o = oee_now.loc[ln.line_id]
        sev = _worst([i.severity for i in by_line.get(ln.line_id, [])])
        hit = [i for i in insights if ln.line_id in i.lines + i.quality_lines]   # e.g. a supplier starving / holding it
        if hit and sev == "ok":
            sev = "high"
        drop = o.oee - oee_first.get(ln.line_id, o.oee)
        nodes = []
        for m in ms[ms.line_id == ln.line_id].sort_values("process_step").itertuples():
            ins = by_machine.get(m.machine_id)
            status = "critical" if ins and ins.severity == "critical" else m.status
            nodes.append({
                "id": m.machine_id, "name": m.machine_name, "short": _short(m.machine_name), "type": m.machine_type,
                "crit": m.criticality, "status": status, "oem": f"{m.oem} {m.model}",
                "metric": f"{m.vib_now:.2f} mm/s", "metricSub": f"{m.breakdowns_6m} breakdowns · Apr–Sep",
                "tipLines": [f"Vibration, {lm:%b} average: {m.vib_now:.2f} mm/s (baseline {m.vib_base:.2f})",
                             f"Breakdowns Apr–Sep: {m.breakdowns_6m} · deferred PMs: {m.pm_deferred}",
                             f"NCRs Apr–Sep: {m.ncrs_6m} · PM interval {m.pm_interval_days} d"],
                "issue": ins.headline if ins else "",
            })
        badge = f"OEE {o.oee:.0%}" + (f" · was {oee_first[ln.line_id]:.0%} in Oct" if drop < -0.05 else "")
        out_lines.append({
            "id": ln.line_id, "name": ln.line_name, "status": sev, "badge": badge,
            "kpis": f"Sep OEE {o.oee:.1%} (A {o.availability:.0%} · P {o.performance:.0%} · Q {o.quality:.1%})  ·  "
                    f"PM compliance {pmc.get(ln.line_id, float('nan')):.0%}  ·  cycle {ln.ideal_cycle_time_s:.0f}s",
            "flowRate": float(o.oee), "starved": ln.line_id in starved, "nodes": nodes,
        })

    rc = D.load("receipts").query("plant_id == @plant_id")
    top = rc.groupby("supplier_id").size().sort_values(ascending=False).head(6).index
    sup = D.load("suppliers").set_index("supplier_id")
    sup_ins = {i.supplier_id: i for i in insights if i.supplier_id and i.id.startswith("SUP-")}
    inbound = [{"id": s, "kind": "supplier", "label": sup.loc[s].supplier_name, "sub": f"{s} · {sup.loc[s].category}",
                "status": sup_ins[s].severity if s in sup_ins else "ok",
                "tip": f"{sup.loc[s].city}, {sup.loc[s].country} · {len(rc[rc.supplier_id == s])} POs to {plant_id}",
                "issue": sup_ins[s].headline if s in sup_ins else ""} for s in top]
    car_ins = [i for i in insights if i.carrier_id and i.id.startswith("CAR-")]
    outbound = [{"id": f"WH-{plant_id}", "kind": "warehouse", "label": f"WH-{plant_id}", "sub": "Plant warehouse", "status": "ok"}]
    for dc in ("DC-MEM", "DC-RNO", "DC-RTM"):
        bad = any(dc in i.detail for i in car_ins)
        outbound.append({"id": dc, "kind": "warehouse", "label": dc, "sub": "Distribution center",
                         "status": "critical" if bad else "ok", "issue": car_ins[0].headline if bad else ""})
    p = plants.loc[plant_id]
    return {"type": "floor", "sceneId": f"floor-{plant_id}", "height": height, "plantId": plant_id,
            "plantName": f"{p.plant_name} · {p.city}, {p.state_country}", "eyebrow": "", "title": "",   # the plant name is drawn on the floor itself
            "help": "Click a line or machine to drill in · drag to pan · Ctrl/⌘ + scroll to zoom · double-click to reset",
            "focusLine": focus_line, "selected": selected, "lines": out_lines, "inbound": inbound, "outbound": outbound}


# -----------------------------------------------------------------------------
# 3. Impact Web graph
# -----------------------------------------------------------------------------
COLUMNS = [("supplier", "Suppliers"), ("material", "Materials"), ("plant", "Plants"), ("line", "Lines"),
           ("machine", "Work centers"), ("defect", "Defects"), ("capa", "CAPAs"), ("dc", "Distribution"),
           ("carrier", "Carriers"), ("customer", "Customers")]


@ttl_cache(seconds=600)
def impact_graph() -> tuple[list[dict], list[dict]]:
    """The Impact Web: one column per entity type, edges where material, problems or orders flow."""
    ins = I.all_insights()
    hot = {x for i in ins if i.severity in ("critical", "high")
           for x in (i.supplier_id, i.machine_id, i.line_id, i.carrier_id, i.customer_id, i.capa_id) if x}
    sev = {}
    for i in ins:
        for x in (i.supplier_id, i.machine_id, i.line_id, i.carrier_id, i.customer_id, i.capa_id, i.plant_id):
            if x and (x not in sev or I.SEVERITY_RANK[i.severity] < I.SEVERITY_RANK[sev[x]]):
                sev[x] = i.severity
    nodes, edges = {}, []
    # full names for the detail panel (graph labels are shortened to keep the canvas readable)
    full = {**D.load("customers").set_index("customer_id").customer_name.to_dict(),
            **D.load("materials").set_index("material_id").material_name.to_dict(),
            **D.load("suppliers").set_index("supplier_id").supplier_name.to_dict()}

    def node(nid, kind, label, tip="", r=9, status=None):
        if nid not in nodes:
            st_ = status or ("critical" if sev.get(nid) == "critical" else "high" if sev.get(nid) in ("high",) else "ok")
            nodes[nid] = {"id": nid, "kind": kind, "label": label, "tip": tip, "r": r, "status": st_,
                          "kindLabel": dict(COLUMNS)[kind], "name": full.get(nid, label)}

    def edge(s, t, w=1.5):
        edges.append({"s": s, "t": t, "w": w})

    rc = D.load("receipts")
    mats = D.load("materials").set_index("material_id")
    sups = D.load("suppliers").set_index("supplier_id")
    ncr = D.load("ncrs")
    # suppliers: the flagged ones + castings + top volume
    vol = rc.groupby("supplier_id").size().sort_values(ascending=False)
    keep_s = list(dict.fromkeys([s for s in hot if s in sups.index] + list(sups[sups.category == "Castings"].index) + list(vol.head(3).index)))
    for s in keep_s:
        r = sups.loc[s]
        node(s, "supplier", r.supplier_name, f"{r.category} · {r.city} · limit {r.quality_agreement_ppm_limit:,.0f} PPM", 11)
    hot_mats = set()
    m_p = rc[rc.supplier_id.isin(keep_s)].groupby(["supplier_id", "material_id", "plant_id"]).size().rename("n").reset_index()
    for r in m_p.itertuples():
        mname = mats.loc[r.material_id].material_name if r.material_id in mats.index else r.material_id
        status = "critical" if sev.get(r.supplier_id) == "critical" else None
        if status:
            hot_mats.add(r.material_id)
        node(r.material_id, "material", mname[:24], f"{r.material_id} · primary supplier {r.supplier_id}", 8, status)
        node(r.plant_id, "plant", r.plant_id, "", 14)
        edge(r.supplier_id, r.material_id, 2)
        edge(r.material_id, r.plant_id, min(5, 1 + r.n / 30))
    lines = D.load("lines")
    for r in lines.itertuples():
        node(r.plant_id, "plant", r.plant_id, "", 14)
        node(r.line_id, "line", r.line_id, r.line_name, 9)
        edge(r.plant_id, r.line_id, 2)
    ms = D.machine_status()
    for r in ms[(ms.status != "ok") | ms.machine_id.isin(hot)].itertuples():
        node(r.machine_id, "machine", r.machine_id, f"{r.machine_name} · {r.vib_now:.2f} mm/s Sep avg · {r.breakdowns_6m} breakdowns Apr–Sep",
             10, "critical" if r.machine_id in hot or r.status == "critical" else "high")
        edge(r.line_id, r.machine_id, 2)
    # defect clusters since April: (plant, defect) with enough volume to matter
    recent = ncr[ncr.opened_date >= "2026-04-01"]
    cl = recent.groupby(["plant_id", "defect_code"]).agg(n=("ncr_id", "size"), copq=("cost_of_poor_quality_usd", "sum"),
                                                         capa=("capa_id", lambda x: x.dropna().mode().iloc[0] if x.notna().any() else None)).reset_index()
    for r in cl[cl.n >= 12].itertuples():
        did = f"D:{r.plant_id}:{r.defect_code}"
        node(did, "defect", f"{r.defect_code} · {r.plant_id}", f"{r.n} NCRs since Apr · ${r.copq/1e3:,.0f}K COPQ",
             min(16, 6 + r.n / 15), "critical" if r.capa in hot else "high" if r.n > 40 else "ok")
        capa = r.capa if isinstance(r.capa, str) else None
        sub = recent[(recent.plant_id == r.plant_id) & (recent.defect_code == r.defect_code)]
        for lid in sub.line_id.dropna().value_counts().head(2).index:
            edge(lid, did, 1.5)
        for mid in sub.machine_id.dropna().value_counts().head(1).index:
            if mid in nodes:
                edge(mid, did, 2.5)
        for mat in sub.material_id.dropna().value_counts().head(3).index:
            if mat in nodes:
                edge(mat, did, 2)
        if capa:
            edge(did, capa, 2)
    caps = D.load("capas")
    for r in caps[caps.status != "Closed"].itertuples():
        node(r.capa_id, "capa", r.capa_id, f"{r.title} · {r.status} · due {r.due_date:%b %d}", 10)
        if isinstance(r.supplier_id, str) and r.supplier_id in nodes:
            edge(r.supplier_id, r.capa_id, 1)
    pdc = D.load("plant_dc")
    for r in pdc.itertuples():
        if r.warehouse_id.startswith("DC"):
            node(r.warehouse_id, "dc", r.warehouse_id, "Distribution center", 12)
            edge(r.plant_id, r.warehouse_id, min(4, 1 + r.shipments / 900))
    sh = D.load("shipments_month")
    car = D.load("carriers").set_index("carrier_id")
    dc_car = sh.groupby(["warehouse_id", "carrier_id"]).shipments.sum().reset_index()
    for r in dc_car[dc_car.shipments > 150].itertuples():
        node(r.carrier_id, "carrier", car.loc[r.carrier_id].carrier_name, f"SLA {car.loc[r.carrier_id].sla_on_time_target:.0%}", 10)
        edge(r.warehouse_id, r.carrier_id, min(5, r.shipments / 600))
    cu = D.load("customers").set_index("customer_id")
    strat = cu[cu.tier == "Strategic"].index
    c_car = sh[sh.customer_id.isin(strat)].groupby(["carrier_id", "customer_id"])[["otif", "delivered"]].sum().reset_index()
    for r in c_car[c_car.delivered > 60].itertuples():
        otif = r.otif / r.delivered
        node(r.customer_id, "customer", cu.loc[r.customer_id].customer_name[:22], f"{cu.loc[r.customer_id].industry} · Strategic", 9,
             "critical" if r.customer_id in hot else None)
        if r.carrier_id in nodes:
            edge(r.carrier_id, r.customer_id, 1.2)
    # an edge is "critical" when both ends are part of a flagged chain
    crit = {k for k, v in nodes.items() if v["status"] == "critical"} | hot_mats
    for e in edges:
        e["status"] = "critical" if e["s"] in crit and e["t"] in crit else "ok"
    return list(nodes.values()), edges

