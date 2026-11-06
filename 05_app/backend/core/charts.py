"""House-style Plotly charts. Each function returns a go.Figure; the API sends it as figure JSON and the React app
renders it with Plotly.js — so chart logic lives in one place, in Python, next to the data it explains."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from backend.core import data as D
from backend.core import palette as T


def oee_trend(keys_filter: dict | None = None, by: str = "plant_id", title: str = "OEE by month") -> go.Figure:
    raw = D.load("line_shift_month")
    for k, v in (keys_filter or {}).items():   # filter the raw rows, then re-aggregate OEE
        raw = raw[raw[k] == v]
    df = D.add_oee(raw.groupby([by, "month"], as_index=False)[D.SUM_COLS].sum())
    fig = go.Figure()
    palette = [T.NAVY, T.RED, "#3E7CB1", T.STEEL, T.NAVY_3, "#9CC3FF"]
    for i, (k, g) in enumerate(df.groupby(by)):
        fig.add_scatter(x=g.month, y=g.oee, name=k, mode="lines+markers", line=dict(width=2.6, color=palette[i % 6]),
                        marker=dict(size=5), hovertemplate=f"{k} %{{x|%b %Y}}: %{{y:.1%}}<extra></extra>")
    fig.add_hline(y=D.OEE_TARGET, line_dash="dot", line_color=T.SLATE, annotation_text="85% target",
                  annotation_font_color=T.SLATE)
    fig.update_layout(**T.plotly_layout(title=title, height=300, yaxis=dict(tickformat=".0%", gridcolor=T.LINE)))
    return fig


def downtime_mix(keys_filter: dict | None = None, title: str = "Downtime by reason") -> go.Figure:
    df = D.load("line_shift_month")
    if keys_filter:
        for k, v in keys_filter.items():
            df = df[df[k] == v]
    g = df.groupby("month")[list(D.DOWNTIME_REASONS)].sum() / 60
    colors = {"dt_equipment_failure": T.RED, "dt_material_shortage": "#F2A541", "dt_quality_hold": "#E0707C",
              "dt_changeover": T.NAVY_3, "dt_planned_maintenance": T.STEEL, "dt_no_operator": "#C9D3E3"}
    fig = go.Figure()
    for c, label in D.DOWNTIME_REASONS.items():
        fig.add_bar(x=g.index, y=g[c], name=label, marker_color=colors[c],
                    hovertemplate=f"{label}: %{{y:,.0f}} h<extra></extra>")
    fig.update_layout(**T.plotly_layout(title=title, barmode="stack", height=300, yaxis=dict(title="hours", gridcolor=T.LINE)))
    return fig


def vibration_chart(machine_id: str) -> go.Figure:
    """The signature chart: daily running vibration with its MONTHLY average (the number the bible, the metric
    view and Genie report), the OEM limit and the outdated internal PM limit, breakdowns and deferred PMs, and the
    months the machine was over the OEM limit but under the PM trigger shaded."""
    d = D.load("machine_daily").query("machine_id == @machine_id").sort_values("reading_date")
    mv = D.monthly_vibration().query("machine_id == @machine_id").sort_values("month")
    wo = D.load("work_orders").query("machine_id == @machine_id")
    mid = mv.month + pd.Timedelta(days=14)   # plot each month's average mid-month
    fig = go.Figure()
    fig.add_scatter(x=d.reading_date, y=d.avg_vibration_mm_s, mode="lines", name="Daily average",
                    line=dict(color="rgba(22,52,107,.28)", width=1.2), hovertemplate="%{x|%b %d}: %{y:.2f} mm/s<extra></extra>")
    fig.add_scatter(x=mid, y=mv.vibration, mode="lines+markers+text", name="Monthly average", line=dict(color=T.NAVY, width=3),
                    marker=dict(size=7, color=T.NAVY), text=[f"{v:.2f}" for v in mv.vibration], textposition="top center",
                    textfont=dict(size=10, color=T.NAVY), hovertemplate="%{x|%B}: %{y:.2f} mm/s<extra>monthly average</extra>")
    hartwell = D.load("machines").set_index("machine_id").loc[machine_id].oem == "Hartwell Machine Tools"
    if hartwell:   # 4.5 / 7.1 mm/s are Hartwell's HMC limit and KK's PM-CNC-030 trigger
        oem_x = D.first_month_above(machine_id, D.OEM_VIBRATION_LIMIT)
        int_x = D.first_month_above(machine_id, D.INTERNAL_PM_LIMIT)
        if pd.notna(oem_x):
            end = int_x if pd.notna(int_x) else d.reading_date.max()
            fig.add_vrect(x0=oem_x, x1=end, fillcolor="rgba(214,40,57,.08)", line_width=0,
                          annotation_text=f"{(end.year - oem_x.year) * 12 + end.month - oem_x.month} months over OEM limit",
                          annotation_position="top left", annotation_font=dict(color=T.RED, size=11))
        label = dict(bgcolor="rgba(255,255,255,.9)", borderpad=3)   # copied per line: plotly mutates it
        fig.add_hline(y=D.OEM_VIBRATION_LIMIT, line_color=T.RED, line_width=2, annotation_position="top left",
                      annotation_text="OEM limit 4.5 mm/s", annotation_font_color=T.RED, annotation=dict(label))
        fig.add_hline(y=D.INTERNAL_PM_LIMIT, line_color=T.SLATE, line_dash="dash", annotation_position="top left",
                      annotation_text="PM-CNC-030 limit 7.1 mm/s", annotation_font_color=T.SLATE, annotation=dict(label))
    bk = wo[wo.is_breakdown.astype(bool)]
    if len(bk):
        daily = d.set_index("reading_date").avg_vibration_mm_s.rolling(7, min_periods=1).mean()
        y = [float(daily.asof(t)) if t >= daily.index.min() else 0 for t in bk.created_ts]
        fig.add_scatter(x=bk.created_ts, y=y, mode="markers", name="Breakdown",
                        marker=dict(symbol="x-thin", size=8, color=T.RED, line=dict(width=1.6, color=T.RED)),
                        text=bk.failure_mode, hovertemplate="%{x|%b %d}: %{text}<extra>breakdown</extra>")
    dfr = wo[wo.is_pm_deferred.astype(bool)]
    if len(dfr):
        fig.add_scatter(x=dfr.pm_due_date, y=[0.4] * len(dfr), mode="markers", name="Deferred PM",
                        marker=dict(symbol="triangle-up", size=12, color=T.AMBER),
                        hovertemplate="PM due %{x|%b %d} — deferred<extra></extra>")
    fig.update_layout(**T.plotly_layout(title=f"{machine_id} · running vibration", height=360,
                                        xaxis=dict(range=[d.reading_date.min(), d.reading_date.max() + pd.Timedelta(days=6)]),
                                        yaxis=dict(title="mm/s", gridcolor=T.LINE)))
    return fig


def shift_quality(line_id: str) -> go.Figure:
    ins = D.load("inspections").query("line_id == @line_id")
    ins = ins.assign(week=ins.inspection_date.dt.to_period("W").dt.start_time)
    g = ins.groupby(["week", "shift"]).agg(defects=("defects_found", "sum"), n=("sample_size", "sum")).reset_index()
    g["rate"] = g.defects / g.n
    fig = go.Figure()
    for s, c in (("A", T.STEEL), ("B", T.NAVY_3), ("C", T.RED)):
        x = g[g["shift"] == s]
        fig.add_scatter(x=x.week, y=x.rate, name=f"Shift {s}", line=dict(color=c, width=2.6 if s == "C" else 1.8),
                        hovertemplate=f"Shift {s} %{{x|%b %d}}: %{{y:.1%}}<extra></extra>")
    char = ins.characteristic.iloc[0] if len(ins) else ""
    fig.update_layout(**T.plotly_layout(title=f"{line_id} · {char} defect rate by shift (weekly)", height=300,
                                        yaxis=dict(tickformat=".0%", gridcolor=T.LINE)))
    return fig


def supplier_trend(supplier_id: str) -> go.Figure:
    rc = D.load("receipts").query("supplier_id == @supplier_id and is_received")
    rc = rc.assign(month=rc.promised_date.dt.to_period("M").dt.start_time)
    g = rc.groupby("month").agg(on_time=("is_on_time", "mean"), rej=("rejected_qty", "sum"), rec=("received_qty", "sum"))
    g["ppm"] = g.rej / g.rec * 1e6
    lim = D.load("suppliers").set_index("supplier_id").loc[supplier_id].quality_agreement_ppm_limit
    fig = go.Figure()
    fig.add_bar(x=g.index, y=g.ppm, name="Incoming PPM", marker_color=[T.RED if v > lim else T.NAVY_3 for v in g.ppm],
                hovertemplate="%{x|%b %Y}: %{y:,.0f} PPM<extra></extra>")
    fig.add_scatter(x=g.index, y=g.on_time, name="On-time", yaxis="y2", line=dict(color=T.NAVY, width=2.6),
                    hovertemplate="%{x|%b %Y}: %{y:.0%} on-time<extra></extra>")
    fig.add_hline(y=lim, line_dash="dash", line_color=T.RED, annotation_text=f"contract {lim:,.0f} PPM",
                  annotation_position="top left", annotation_font_color=T.RED)
    fig.update_layout(**T.plotly_layout(title=f"{supplier_id} · quality & delivery", height=320,
                                        yaxis=dict(title="PPM", gridcolor=T.LINE),
                                        yaxis2=dict(overlaying="y", side="right", tickformat=".0%", range=[0, 1.05], showgrid=False)))
    return fig


def carrier_trend(carrier_id: str) -> go.Figure:
    sh = D.load("shipments_month")
    car = D.load("carriers").set_index("carrier_id")
    g = sh.groupby(["month", "carrier_id"])[["carrier_on_time", "delivered"]].sum().reset_index()
    g["rate"] = g.carrier_on_time / g.delivered
    fig = go.Figure()
    for cid, x in g.groupby("carrier_id"):
        hot = cid == carrier_id
        fig.add_scatter(x=x.month, y=x.rate, name=car.loc[cid].carrier_name,
                        line=dict(color=T.RED if hot else "rgba(143,163,191,.6)", width=3 if hot else 1.4),
                        hovertemplate=f"{car.loc[cid].carrier_name} %{{x|%b}}: %{{y:.0%}}<extra></extra>")
    fig.add_hline(y=car.loc[carrier_id].sla_on_time_target, line_dash="dot", line_color=T.NAVY, annotation_text="SLA",
                  annotation_position="top left")
    hot = g[g.carrier_id == carrier_id].sort_values("month")
    if len(hot):   # label the highlighted carrier at its last point instead of an 8-item legend
        fig.add_annotation(x=hot.month.iloc[-1], y=hot.rate.iloc[-1], text=car.loc[carrier_id].carrier_name,
                           showarrow=False, yshift=-14, xanchor="right", font=dict(color=T.RED, size=12))
    fig.update_layout(**T.plotly_layout(title="Carrier on-time vs SLA · others in grey", height=300, showlegend=False,
                                        xaxis=dict(tickformat="%b", gridcolor=T.LINE),
                                        yaxis=dict(tickformat=".0%", gridcolor=T.LINE)))
    return fig


def copq_by_plant() -> go.Figure:
    ncr = D.load("ncrs")
    g = ncr.assign(m=ncr.opened_date.dt.to_period("M").dt.start_time).groupby(["m", "plant_id"]) \
        .cost_of_poor_quality_usd.sum().unstack().fillna(0)
    fig = go.Figure()
    for i, p in enumerate(g.columns):
        fig.add_bar(x=g.index, y=g[p], name=p, marker_color=[T.NAVY, T.RED, "#3E7CB1", T.STEEL, T.NAVY_3][i % 5])
    fig.update_layout(**T.plotly_layout(title="Cost of poor quality by plant", barmode="stack", height=320,
                                        yaxis=dict(tickprefix="$", gridcolor=T.LINE)))
    return fig


def top_defects() -> go.Figure:
    ncr = D.load("ncrs")
    top = ncr[ncr.opened_date >= "2026-04-01"].groupby(["defect_code"]).agg(ncrs=("ncr_id", "size"),
                                                                              copq=("cost_of_poor_quality_usd", "sum"))
    top = top.sort_values("copq", ascending=True).tail(8)
    fig = go.Figure(go.Bar(x=top.copq, y=top.index, orientation="h", cliponaxis=False,
                           marker_color=[T.RED if v == top.copq.max() else T.NAVY_3 for v in top.copq],
                           text=[f"{n} NCRs" for n in top.ncrs], textposition="outside"))
    fig.update_layout(**T.plotly_layout(title="Top defects by cost · since April", height=320,
                                        margin=dict(l=12, r=70, t=48, b=12), xaxis=dict(tickprefix="$", gridcolor=T.LINE)))
    return fig
