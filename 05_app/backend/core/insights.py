"""The insight engine — "where should I focus today?"

Each detector scans the gold data for one *kind* of problem (not one hard-coded storyline), so the same
rules find the planted stories and anything else that crosses a line:

  vibration_drift     a machine whose monthly average vibration is far above its own baseline / the OEM limit
  supplier_breach     a supplier over its contract PPM limit or under its on-time target
  carrier_sla         a carrier below its contract on-time SLA
  shift_anomaly       one shift's defect rate on a line far above the other shifts
  capa_overdue        corrective actions past due
  customer_otif       strategic customers below their OTIF target

Numbers are measured the way the narrative bible, the metric views and Genie measure them: vibration as the
running-hours-weighted MONTHLY average, and before/after comparisons split at the change point the detector
finds in the data (the month a supplier's breach began, the week a shift's defect rate jumped) rather than
an arbitrary trailing window.

Every Insight carries the hierarchy it touches (plant / line / machine / supplier ...), so the app can
light up the right nodes in the map, floor and process views, plus the human actions that close the loop.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from backend.core import data as D
from backend.core.cache import ttl_cache

SEVERITY_RANK = {"critical": 0, "high": 1, "watch": 2}


@dataclass
class Insight:
    id: str
    severity: str                 # critical | high | watch
    domain: str                   # maintenance | quality | supply_chain | production
    title: str
    headline: str                 # the number that matters
    detail: str
    impact_usd: float = 0.0
    plant_id: str | None = None
    line_id: str | None = None
    machine_id: str | None = None
    supplier_id: str | None = None
    carrier_id: str | None = None
    customer_id: str | None = None
    capa_id: str | None = None
    lines: list[str] = field(default_factory=list)     # lines starved of material by it (shortage stops)
    quality_lines: list[str] = field(default_factory=list)   # lines where its defects are caught (quality holds)
    actions: list[str] = field(default_factory=list)   # keys into actions.ACTION_TYPES
    ask: str = ""                                       # the question to hand the supervisor agent

    @property
    def entity(self) -> tuple[str, str]:
        for kind in ("machine_id", "line_id", "supplier_id", "carrier_id", "customer_id", "capa_id", "plant_id"):
            if getattr(self, kind):
                return kind.removesuffix("_id"), getattr(self, kind)
        return "enterprise", "KK"


def _window(df: pd.DataFrame, col: str, days: int) -> pd.DataFrame:
    return df[df[col] > D.today() - pd.Timedelta(days=days)]


def _months(n: int) -> str:
    words = {1: "one month", 2: "two months", 3: "three months", 4: "four months", 5: "five months"}
    return words.get(n, f"{n} months")


def vibration_drift() -> list[Insight]:
    out = []
    ms = D.machine_status()
    mv = D.monthly_vibration()
    wo = D.load("work_orders")
    lm = D.last_month()
    for r in ms[ms.vib_ratio >= 1.5].itertuples():
        m = mv[mv.machine_id == r.machine_id].sort_values("month")
        # when the drift began: first month ≥ 15% over baseline that stays there through the latest month
        above = (m.vibration >= 1.15 * r.vib_base).values
        run = len(above) - (list(reversed(above)).index(False) if False in above else len(above))
        onset = m.month.iloc[run] if run < len(m) else m.month.iloc[0]
        bk = wo[(wo.machine_id == r.machine_id) & wo.is_breakdown.astype(bool) & (wo.created_ts >= onset)]
        cost = float((bk.parts_cost_usd + bk.contractor_cost_usd).sum())
        critical = r.vib_ratio >= 2.0
        trend = " → ".join(f"{t:%b} {v:.2f}" for t, v in zip(m.month.tail(6), m.vibration.tail(6)))
        detail = (f"{r.machine_name} ({r.oem} {r.model}, criticality {r.criticality}). Monthly average vibration "
                  f"{trend} mm/s, against a {r.vib_base:.2f} mm/s baseline.")
        if r.oem == "Hartwell Machine Tools":   # 4.5 / 7.1 mm/s are Hartwell's HMC limits and KK's PM-CNC-030
            oem_x = D.first_month_above(r.machine_id, D.OEM_VIBRATION_LIMIT)
            int_x = D.first_month_above(r.machine_id, D.INTERNAL_PM_LIMIT)
            if pd.notna(oem_x):
                detail += f" It crossed the OEM 4.5 mm/s limit in {oem_x:%B}"
                if pd.notna(int_x):
                    n = (int_x.year - oem_x.year) * 12 + int_x.month - oem_x.month
                    detail += f", {_months(n)} before reaching the internal 7.1 mm/s PM limit ({int_x:%B})"
                detail += "."
        if len(bk):
            detail += (f" {len(bk)} breakdowns since vibration began rising in {onset:%B} — "
                       f"{bk.repair_hours.sum():,.0f} repair hours, ${cost/1e3:,.0f}K parts + contractor.")
        out.append(Insight(
            id=f"VIB-{r.machine_id}", severity="critical" if critical else "watch", domain="maintenance",
            title=f"Vibration drift · {r.machine_id}",
            headline=f"{r.vib_now:.2f} mm/s in {lm:%b} · {r.vib_ratio:.1f}× baseline",
            detail=detail, impact_usd=cost, plant_id=r.plant_id, line_id=r.line_id, machine_id=r.machine_id,
            actions=["work_order", "threshold_change", "comment"] if critical else ["inspect", "comment"],
            ask=f"Why is {r.machine_id} vibrating at {r.vib_now:.2f} mm/s, what does the OEM manual say, "
                f"and what is it costing us in OEE and breakdowns?"))
    return out


def supplier_breach() -> list[Insight]:
    out = []
    rc = D.load("receipts")
    rc = rc[rc.is_received.astype(bool)].assign(month=lambda t: t.promised_date.dt.to_period("M").dt.start_time)
    sup = D.load("suppliers").set_index("supplier_id")
    ncr = D.load("ncrs")
    capas = D.load("capas")
    for sid, g in rc.groupby("supplier_id"):
        s = sup.loc[sid]
        mon = g.groupby("month").agg(ok=("is_on_time", "mean"), rej=("rejected_qty", "sum"), rec=("received_qty", "sum"))
        mon["ppm"] = mon.rej / mon.rec * 1e6
        bad = ((mon.ppm > s.quality_agreement_ppm_limit) | (mon.ok < s.on_time_target - 0.15)).values
        if not bad[-1]:
            continue
        # the breach began in the first month of the current unbroken run of bad months
        k = len(bad) - (list(reversed(bad)).index(False) if False in bad else len(bad))
        start = mon.index[k]
        after, before = g[g.month >= start], g[g.month < start]
        ppm_a = after.rejected_qty.sum() / after.received_qty.sum() * 1e6
        ppm_b = before.rejected_qty.sum() / before.received_qty.sum() * 1e6 if len(before) else float("nan")
        ppm_x = ppm_a / s.quality_agreement_ppm_limit
        otd_gap = s.on_time_target - after.is_on_time.mean()
        if len(after) < 15 or (ppm_x < 1.5 and otd_gap < 0.10):   # small overages are noise, not a breach
            continue
        late = after[after.days_late > 0].days_late.mean()
        caps = capas.query("supplier_id == @sid").capa_id
        sn = ncr[((ncr.supplier_id == sid) | ncr.capa_id.isin(caps)) & (ncr.opened_date >= start)]
        short = D.supplier_shortages(sid, start)
        top_lines = list(short.line_id.value_counts().head(4).index)
        q_lines = list(sn.line_id.value_counts().pipe(lambda v: v[v >= 25]).head(3).index)
        out.append(Insight(
            id=f"SUP-{sid}", severity="critical" if ppm_x >= 2 else "high", domain="supply_chain",
            title=f"Supplier breach · {s.supplier_name}",
            headline=f"{ppm_a:,.0f} PPM since {start:%b} ({ppm_x:.1f}× limit) · {after.is_on_time.mean():.0%} on-time",
            detail=(f"Since {start:%B %-d}: incoming quality {ppm_b:,.0f} → {ppm_a:,.0f} PPM against a "
                    f"{s.quality_agreement_ppm_limit:,.0f} PPM contract limit; on-time "
                    f"{before.is_on_time.mean():.0%} → {after.is_on_time.mean():.0%} against {s.on_time_target:.0%}"
                    + (f", late deliveries average {late:.1f} days" if pd.notna(late) else "") + ". "
                    f"{len(short)} material-shortage stops (mostly {', '.join(top_lines)}) and {len(sn)} NCRs "
                    f"(${sn.cost_of_poor_quality_usd.sum()/1e6:,.2f}M cost of poor quality)"
                    + (f", with quality holds hitting {', '.join(q_lines)} hardest" if q_lines else "") + "."),
            impact_usd=float(sn.cost_of_poor_quality_usd.sum()), supplier_id=sid, lines=top_lines, quality_lines=q_lines,
            actions=["scar_escalation", "dual_source", "comment"],
            ask=f"How bad is {s.supplier_name}'s quality and delivery, what does the supplier quality agreement "
                f"allow, and which plants and lines are hurt?"))
    return out


def carrier_sla() -> list[Insight]:
    out = []
    sh = D.load("shipments_month")
    car = D.load("carriers").set_index("carrier_id")
    cu = D.load("customers").set_index("customer_id")
    fy = sh.groupby("carrier_id")[["delivered", "carrier_on_time", "shipments"]].sum()
    fy["on_time"] = fy.carrier_on_time / fy.delivered
    for cid, r in fy.iterrows():
        c = car.loc[cid]
        gap = c.sla_on_time_target - r.on_time
        if gap < 0.08:
            continue
        x = sh[sh.carrier_id == cid]
        dc = x.groupby("warehouse_id").shipments.sum().idxmax()
        share = x[x.warehouse_id == dc].shipments.sum() / sh[sh.warehouse_id == dc].shipments.sum()
        mo = x.groupby("month")[["carrier_on_time", "delivered"]].sum().tail(3)
        recent = " · ".join(f"{t:%b} {v:.0%}" for t, v in zip(mo.index, mo.carrier_on_time / mo.delivered))
        strat = cu[cu.tier == "Strategic"].index
        sc = sh[sh.customer_id.isin(strat) & (sh.warehouse_id == dc)]
        on = sc[sc.carrier_id == cid]
        off = sc[sc.carrier_id != cid]
        out.append(Insight(
            id=f"CAR-{cid}", severity="critical" if gap >= 0.15 else "high", domain="supply_chain",
            title=f"Carrier below SLA · {c.carrier_name}",
            headline=f"{r.on_time:.0%} on-time in FY26 vs {c.sla_on_time_target:.0%} SLA",
            detail=(f"Last three months {recent}. Carries {share:.0%} of {dc} shipments. Strategic customers from "
                    f"{dc} get {on.on_time_to_customer.sum()/on.delivered.sum():.1%} on-time to their requested date "
                    f"on {c.carrier_name} vs {off.on_time_to_customer.sum()/off.delivered.sum():.1%} on other carriers. "
                    f"Service credits apply below 92%."),
            carrier_id=cid, actions=["carrier_review", "comment"],
            ask=f"Why is {c.carrier_name} missing its on-time SLA, what does the contract let us do, "
                f"and which customers are affected?"))
    return out


def shift_anomaly() -> list[Insight]:
    out = []
    ins = D.load("inspections")
    ncr = D.load("ncrs")
    for line, li in ins.groupby("line_id"):
        recent = li[li.inspection_date > D.today() - pd.Timedelta(days=90)]
        rate = recent.groupby("shift")[["defects_found", "sample_size"]].sum()
        rate = rate.defects_found / rate.sample_size
        worst = rate.idxmax()
        if rate[worst] < 0.05 or rate[worst] < 3 * rate.drop(worst).mean():
            continue
        # when it started: the split date that best separates the worst shift's defect rate (single change point),
        # reported from the start of that week
        w = li[li["shift"] == worst].groupby("inspection_date")[["defects_found", "sample_size"]].sum()
        cum = w.cumsum()
        tot = cum.iloc[-1]
        idx = w.index[10:-10]
        jump = [(tot.defects_found - cum.loc[t].defects_found) / (tot.sample_size - cum.loc[t].sample_size)
                - cum.loc[t].defects_found / cum.loc[t].sample_size for t in idx]
        k = max(range(len(idx)), key=jump.__getitem__)
        cp = w.index[w.index.get_loc(idx[k]) + 1]           # first day of the new regime
        start = (cp - pd.Timedelta(days=cp.weekday())).normalize()
        after, before = li[li.inspection_date >= start], li[li.inspection_date < start]
        ra = after.groupby("shift")[["defects_found", "sample_size"]].sum()
        ra = ra.defects_found / ra.sample_size
        rb = before.groupby("shift")[["defects_found", "sample_size"]].sum()
        rb = rb.defects_found / rb.sample_size
        aw = after[after["shift"] == worst]
        others = ra.drop(worst)
        char, uom = aw.characteristic.iloc[0], aw.characteristic_uom.iloc[0]
        tol = (aw.upper_spec_limit.iloc[0] - aw.lower_spec_limit.iloc[0]) / 2
        hot = ncr[(ncr.line_id == line) & ncr.machine_id.notna() & (ncr.opened_date >= start)].machine_id.value_counts()
        out.append(Insight(
            id=f"SHIFT-{line}-{worst}", severity="critical", domain="quality",
            title=f"Shift {worst} defects · {line}",
            headline=f"{ra[worst]:.1%} defect rate on shift {worst} vs {others.min():.1%}–{others.max():.1%} on the others",
            detail=(f"{char} on {line} since the week of {start:%b} {start.day}: shift {worst} averages "
                    f"{aw.measured_mean.mean():.3f} {uom} against {aw.nominal.iloc[0]:.3f} ± {tol:.3f} {uom}, Cpk "
                    f"{aw.cpk.mean():.2f} against a 1.33 target. Before that every shift ran "
                    f"{rb.min():.1%}–{rb.max():.1%}. Only one shift is affected, which points to setup or method "
                    f"rather than the machine."),
            plant_id=line.split("-")[0], line_id=line, machine_id=hot.index[0] if len(hot) else None,
            actions=["containment", "work_instruction", "comment"],
            ask=f"Why does shift {worst} on {line} have a {ra[worst]:.1%} defect rate on {char.lower()} "
                f"and what does the 8D say the root cause is?"))
    return out


def capa_overdue() -> list[Insight]:
    out = []
    c = D.load("capas")
    t = D.today()
    od = c[(c.status != "Closed") & (c.due_date < t)]
    for r in od.itertuples():
        days = (t - r.due_date).days
        out.append(Insight(
            id=f"CAPA-{r.capa_id}", severity="high" if days > 30 else "watch", domain="quality",
            title=f"Overdue CAPA · {r.capa_id}", headline=f"{days} days past due · {r.status}",
            detail=f"“{r.title}” — {int(r.linked_ncr_count)} linked NCRs, ${r.linked_copq_usd/1e3:,.0f}K COPQ.",
            impact_usd=float(r.linked_copq_usd), plant_id=r.plant_id,
            supplier_id=r.supplier_id if isinstance(r.supplier_id, str) else None, capa_id=r.capa_id,
            actions=["capa_update", "assign_owner", "comment"],
            ask=f"What is the status of {r.capa_id} ({r.title}) and what is blocking it?"))
    return out


def customer_otif() -> list[Insight]:
    """Strategic customers below their OTIF target over FY26, attributed to the carrier lane that hurts most."""
    sh = D.load("shipments_month")
    cu = D.load("customers").set_index("customer_id")
    g = sh.groupby("customer_id")[["delivered", "otif"]].sum().join(cu)
    g["otif_rate"] = g.otif / g.delivered
    below = g[(g.tier == "Strategic") & (g.otif_rate < g.otif_target)].sort_values("otif_rate")
    if below.empty:
        return []
    lane = sh[sh.customer_id.isin(below.index)].groupby("carrier_id")[["otif", "delivered"]].sum()
    worst = (lane.otif / lane.delivered).idxmin()
    on = sh[sh.customer_id.isin(below.index) & (sh.carrier_id == worst)].groupby("customer_id")[["otif", "delivered"]].sum()
    on_rate = on.otif / on.delivered
    carrier = D.load("carriers").set_index("carrier_id").loc[worst].carrier_name
    short = carrier.split()[0]
    names = "; ".join(f"{r.customer_name} {r.otif_rate:.1%}" + (f" ({on_rate[cid]:.1%} on {short})" if cid in on_rate else "")
                      for cid, r in below.iterrows())
    return [Insight(
        id="CUST-OTIF", severity="high", domain="supply_chain",
        title=f"{len(below)} strategic customers below OTIF",
        headline=f"All below {below.otif_target.iloc[0]:.0%} OTIF in FY26 · weakest lane {carrier}",
        detail=f"FY26 OTIF (on time and in full): {names}.",
        customer_id=below.index[0], carrier_id=worst, actions=["customer_response", "comment"],
        ask=f"Which strategic customers are below their OTIF target, how much of it is {carrier}, and what should we "
            f"tell Apex Agricultural Equipment?" if "CUST-2001" in below.index else
            f"Which strategic customers are below their OTIF target and why?")]


@ttl_cache(seconds=600)                       # detectors run once per data refresh, not per request
def all_insights() -> list[Insight]:
    items = [*vibration_drift(), *shift_anomaly(), *supplier_breach(), *carrier_sla(), *customer_otif(), *capa_overdue()]
    return sorted(items, key=lambda i: (SEVERITY_RANK[i.severity], -i.impact_usd))


def for_entity(insights: list[Insight], **ref) -> list[Insight]:
    """Insights touching a node of the hierarchy, e.g. for_entity(xs, line_id='GVL-L3')."""
    (k, v), = ref.items()
    touched = lambda i: [i.line_id, *i.lines, *i.quality_lines]   # noqa: E731
    return [i for i in insights if getattr(i, k) == v
            or (k == "line_id" and v in touched(i))
            or (k == "plant_id" and any((l or "").startswith(v) for l in touched(i)))]
