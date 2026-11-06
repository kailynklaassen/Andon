"""KK's Parts visual identity for the backend: the palette and the house style for every Plotly chart.

The same colors live in frontend/src/theme.ts (the UI) — keep the two in step.

Palette rules
  NAVY   structure: banners, nav, headings, healthy-but-neutral data
  RED    attention: critical status, the one number you must act on, primary buttons
  WHITE  canvas: cards float on a cool mist background
  AMBER / TEAL are status-only accents (warning / healthy) — never decoration.
"""
from __future__ import annotations


NAVY = "#0A1F44"
NAVY_2 = "#16346B"
NAVY_3 = "#2A4A82"
RED = "#D62839"
RED_DARK = "#A4161A"
WHITE = "#FFFFFF"
MIST = "#EEF2F8"
LINE = "#DCE3EE"
INK = "#0B1324"
SLATE = "#5B6B82"
AMBER = "#F2A541"
TEAL = "#2A9D8F"
STEEL = "#8FA3BF"

STATUS_COLOR = {"critical": RED, "warning": AMBER, "watch": AMBER, "high": AMBER, "ok": TEAL}
DOMAIN = {   # label, accent, glyph
    "production": ("Production", NAVY_3, "⚙"),
    "maintenance": ("Maintenance", NAVY_2, "🛠"),
    "quality": ("Quality", RED, "◎"),
    "supply_chain": ("Supply Chain", "#3E7CB1", "⇄"),
}


def plotly_layout(**kw) -> dict:
    """House style for every plotly chart."""
    base = dict(
        font=dict(family="Inter, Segoe UI, system-ui, sans-serif", color=INK, size=12),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=12, r=20, t=48, b=12), hoverlabel=dict(bgcolor=NAVY, font_color=WHITE, bordercolor=NAVY),
        xaxis=dict(gridcolor=LINE, zeroline=False, linecolor=LINE, tickangle=0, automargin=True, nticks=7),
        yaxis=dict(gridcolor=LINE, zeroline=False, linecolor=LINE),
        legend=dict(orientation="h", y=-0.16, x=0, yanchor="top", font=dict(size=11)),
        title=dict(font=dict(size=14, color=NAVY), x=0, xanchor="left", xref="paper", pad=dict(b=8)),
    )
    for k, v in kw.items():   # merge axis/legend/title dicts so per-chart tweaks keep the house defaults
        base[k] = {**base[k], **v} if isinstance(v, dict) and isinstance(base.get(k), dict) else v
    return base

