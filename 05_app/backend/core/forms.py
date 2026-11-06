"""Action forms, described as data — so the React form is generic and every choice comes from the gold layer.

Two ideas keep the human-in-the-loop data deterministic:
  1. A field's options are values that ACTUALLY occur in the data (failure modes seen on this machine type, suppliers
     in the same category, owners on CAPAs). A person can't submit a value the pipeline and Genie don't know.
  2. A data correction is resolved ON THE SERVER: the client sends (dataset, key, column, corrected value) and the
     server looks up the current value and the bronze target itself (records.py), so the stored payload names one exact
     cell and can't be tampered with from the browser.
"""
from __future__ import annotations

from datetime import date

import pandas as pd

from backend.core import data as D
from backend.core import ledger as A
from backend.core import records as R


def _opt(value, label=None) -> dict:
    return {"value": value, "label": label if label is not None else str(value)}


def _bound(kind: str, entity_type: str, entity_id: str, default) -> dict:
    """Options for a data-bound field kind (see ledger.ACTION_TYPES)."""
    if kind == "failure_mode":
        wo = D.load("work_orders")
        opts = R.choices("work_orders", "failure_mode")
        m = D.load("machines").set_index("machine_id")
        if entity_type == "machine" and entity_id in m.index:   # this machine's most frequent first, then its type's
            mtype = m.loc[entity_id].machine_type
            same = set(wo[wo.machine_id.isin(m[m.machine_type == mtype].index)].failure_mode.dropna())
            mine = list(wo[wo.machine_id == entity_id].failure_mode.dropna().value_counts().index)
            opts = mine + [x for x in opts if x in same and x not in mine] or opts
        return {"kind": "select", "options": [_opt(o) for o in opts], "default": default if default in opts else opts[0]}
    if kind == "alt_supplier":
        sup = D.load("suppliers").set_index("supplier_id")
        cat = sup.loc[entity_id].category if entity_id in sup.index else None
        alts = sup[(sup.category == cat) & (sup.index != entity_id)] if cat else sup
        return {"kind": "select", "options": [_opt(s, f"{s} · {alts.loc[s].supplier_name}") for s in alts.index],
                "default": alts.index[0] if len(alts) else None}
    if kind == "materials":
        mats = D.load("materials").query("primary_supplier_id == @entity_id")
        return {"kind": "multiselect", "options": [_opt(r.material_id, f"{r.material_id} · {r.material_name}") for r in mats.itertuples()],
                "default": list(mats.material_id[:2])}
    if kind == "owner":
        owners = R.choices("capas", "owner_id")
        return {"kind": "select", "options": [_opt(o) for o in owners], "default": owners[0] if owners else None}
    raise ValueError(kind)


def action_form(action_type: str, entity_type: str, entity_id: str, defaults: dict | None = None) -> dict:
    spec = A.ACTION_TYPES[action_type]
    fields = []
    for name, kind, default in spec["fields"]:
        default = (defaults or {}).get(name, default)
        f = {"name": name, "label": name.replace("_", " ").capitalize()}
        if kind == "record":
            f["kind"] = "record"                                     # the client renders the record picker
        elif kind == "select":
            f.update(kind="select", options=[_opt(o) for o in default], default=default[0])
        elif kind == "number":
            f.update(kind="number", default=float(default or 0))
        elif kind == "date":
            f.update(kind="date", default=str(default or date(2026, 10, 14)))
        elif kind == "text":
            f.update(kind="text", default=default or "")
        else:
            f.update(_bound(kind, entity_type, entity_id, default))
        fields.append(f)
    return {"action_type": action_type, "label": spec["label"], "icon": spec["icon"], "fields": fields,
            "title": f"{spec['label']} — {entity_id}"}


# ------------------------------------------------------------------ data corrections: record → field → value
def records_for(entity_type: str, entity_id: str) -> list[dict]:
    return R.related_records(entity_type, entity_id)


def fields_for(dataset: str) -> list[dict]:
    return [{"column": c, "label": label} for c, label in R.CATALOG[dataset]["fields"].items()]


def _show(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "—"
    return f"{v:%Y-%m-%d}" if isinstance(v, pd.Timestamp) else str(v)


def field_value(dataset: str, key: str, column: str) -> dict:
    """The current value (read-only in the form) and how the corrected value is entered."""
    cur = R.current_value(dataset, key, column)
    kind, opts = R.column_kind(dataset, column)
    out = {"current": _show(cur), "kind": kind, "target": f"{R.gold_table(dataset)} · {R.CATALOG[dataset]['key']} = {key} · {column}"}
    if kind == "select":
        out["options"] = [_opt(o) for o in opts if o != cur] or [_opt(o) for o in opts]
    elif kind == "number":
        out["default"] = float(cur) if cur is not None and pd.notna(cur) else 0.0
    elif kind == "date":
        out["default"] = _show(cur) if isinstance(cur, pd.Timestamp) else "2026-09-30"
    return out


def correction_payload(dataset: str, key: str, column: str, corrected) -> dict:
    """The exact cell a correction names — computed server-side from the catalog, never trusted from the client."""
    if dataset not in R.CATALOG or column not in R.CATALOG[dataset]["fields"]:
        raise ValueError(f"{dataset}.{column} is not correctable")
    return {"table": R.gold_table(dataset), "dataset": dataset, "key_column": R.CATALOG[dataset]["key"], "key_value": key,
            "column": column, "current_value": _show(R.current_value(dataset, key, column)), "corrected_value": corrected,
            **R.bronze_target(dataset, column)}
