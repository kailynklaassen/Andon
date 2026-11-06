"""Andon Board — the home page: today's status and the issues that need a decision."""
from __future__ import annotations

import pandas as pd
from fastapi import APIRouter

from backend.core import charts as C
from backend.core import data as D
from backend.core import insights as I
from backend.core import scenes as S
from backend.core import shapes as X
from backend.core.cache import ttl_cache

router = APIRouter(prefix="/api", tags=["board"])


@router.get("/board")
@ttl_cache(seconds=600)
def board() -> dict:
    insights = I.all_insights()
    crit = [i for i in insights if i.severity == "critical"]
    watch = [i for i in insights if i.severity != "critical"]

    ent = D.oee_by(["month"]).sort_values("month")
    oee_now = ent.oee.iloc[-1]
    pm = D.pm_compliance(["plant_id"])
    pm_all = pm.pm_done.sum() / pm.pm_due.sum()
    ncr = D.load("ncrs")
    q4 = ncr[ncr.opened_date >= "2026-07-01"]
    copq_m = ncr.assign(m=ncr.opened_date.dt.to_period("M").dt.start_time).groupby("m").cost_of_poor_quality_usd.sum()
    caps = D.load("capas")
    overdue = caps[(caps.status != "Closed") & (caps.due_date < D.today())]
    rc = D.load("receipts")
    rc90 = rc[(rc.promised_date > D.today() - pd.Timedelta(days=90)) & rc.is_received.astype(bool)]
    sh = D.load("shipments_month")
    sh_q = sh[sh.month > D.today() - pd.Timedelta(days=92)]
    otif = sh_q.otif.sum() / sh_q.delivered.sum()
    otif_m = sh.groupby("month")[["otif", "delivered"]].sum()
    kpis = [
        X.kpi(f"Enterprise OEE · {D.last_month():%b}", f"{oee_now:.1%}", f"target 85% · Oct {ent.oee.iloc[0]:.1%}",
              "bad" if oee_now < .8 else "warn", list(ent.oee), D.OEE_TARGET),
        X.kpi("PM compliance FY26", f"{pm_all:.1%}", "policy target 95%", "warn" if pm_all < .95 else "good"),
        X.kpi("Poor-quality cost · Q4", f"${q4.cost_of_poor_quality_usd.sum() / 1e6:,.2f}M", f"{len(q4)} NCRs Jul–Sep", "bad",
              list(copq_m.tail(12))),
        X.kpi("Supplier on-time · 90d", f"{rc90.is_on_time.mean():.0%}",
              f"{rc90.rejected_qty.sum() / rc90.received_qty.sum() * 1e6:,.0f} PPM incoming", "warn"),
        X.kpi("Customer OTIF · Q4", f"{otif:.1%}", "standard 95%", "bad" if otif < .93 else "warn",
              list(otif_m.otif / otif_m.delivered), 0.95),
        X.kpi("Overdue CAPAs", f"{len(overdue)}",
              f"oldest {(D.today() - overdue.due_date.min()).days} days late" if len(overdue) else "none",
              "bad" if len(overdue) else "good"),
    ]
    return {"subtitle": f"{len(crit)} critical issues · {len(watch)} on the watch list",
            "kpis": kpis, "critical": [X.insight(i) for i in crit[:4]], "watch": [X.insight(i) for i in watch[:9]],
            "charts": {"oee": X.figure(C.oee_trend(title="OEE by plant")),
                       "downtime": X.figure(C.downtime_mix(title="Downtime hours by reason")),
                       "copq": X.figure(C.copq_by_plant()), "defects": X.figure(C.top_defects())}}


@router.get("/network")
@ttl_cache(seconds=600)
def network() -> dict:
    return X.clean(S.network(I.all_insights()))
