"""The JSON shapes the API returns. One place, so the React types (frontend/src/api.ts) mirror exactly this."""
from __future__ import annotations

import json
import math
from dataclasses import asdict

import pandas as pd
import plotly.graph_objects as go

from backend.core import insights as I


def clean(v):
    """JSON-safe: NaN/inf → None, numpy/pandas scalars → Python, timestamps → ISO strings."""
    if isinstance(v, dict):
        return {str(k): clean(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [clean(x) for x in v]
    if v is pd.NaT or v is None:                                         # empty timestamps (NaT) and nulls
        return None
    if isinstance(v, pd.Timestamp):
        return None if pd.isna(v) else v.isoformat()
    if hasattr(v, "item") and not isinstance(v, (str, bytes)):          # numpy scalar
        v = v.item()
    if isinstance(v, float) and not math.isfinite(v):
        return None
    return v


def insight(i: I.Insight) -> dict:
    d = asdict(i)
    d["entity"] = list(i.entity)
    return clean(d)


def kpi(label: str, value: str, compare: str = "", tone: str = "", spark: list[float] | None = None,
        ref: float | None = None) -> dict:
    """A KPI tile. tone: bad | warn | good | '' (neutral). spark: the trend behind the number (oldest first)."""
    return clean({"label": label, "value": value, "compare": compare, "tone": tone,
                  "spark": [float(x) for x in spark] if spark is not None else None, "ref": ref})


def figure(fig: go.Figure) -> dict:
    """Plotly figure JSON for react-plotly (data + layout)."""
    return json.loads(fig.to_json())


def table(df: pd.DataFrame, columns: dict[str, str], formats: dict[str, str] | None = None, limit: int = 500) -> dict:
    """A table: column order + labels + display format ('money', 'hours', 'date', 'datetime', 'pct', 'mms', ...)."""
    cols = [c for c in columns if c in df.columns]
    rows = df[cols].head(limit).to_dict("records")
    return {"columns": [{"key": c, "label": columns[c], "format": (formats or {}).get(c, "")} for c in cols],
            "rows": clean(rows), "total": int(len(df))}
