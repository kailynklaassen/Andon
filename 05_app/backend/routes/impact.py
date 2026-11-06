"""Impact Web — the relational model you can touch: supplier → material → plant → line → machine → defect → CAPA →
DC → carrier → customer. The graph is one cached payload; a node's details are fetched when it's selected."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.core import charts as C
from backend.core import insights as I
from backend.core import scenes as S
from backend.core import shapes as X
from backend.core.cache import ttl_cache

router = APIRouter(prefix="/api/impact", tags=["impact"])

REFS = {"supplier": "supplier_id", "machine": "machine_id", "line": "line_id", "plant": "plant_id",
        "carrier": "carrier_id", "customer": "customer_id", "capa": "capa_id"}
CHARTS = {"supplier": C.supplier_trend, "carrier": C.carrier_trend, "machine": C.vibration_chart}


def _target(i: I.Insight, ids: set[str]) -> str | None:
    k, v = i.entity
    return v if v in ids else i.machine_id or i.supplier_id or i.carrier_id


@router.get("/graph")
@ttl_cache(seconds=600)
def graph() -> dict:
    nodes, edges = S.impact_graph()
    ids = {n["id"] for n in nodes}
    crit = [i for i in I.all_insights() if i.severity == "critical"]
    return X.clean({"columns": [{"kind": k, "label": l} for k, l in S.COLUMNS], "nodes": nodes, "edges": edges,
                    "issues": [{"id": i.id, "title": i.title, "target": _target(i, ids)} for i in crit]})


@router.get("/node/{node_id:path}")
@ttl_cache(seconds=600)
def node(node_id: str) -> dict:
    nodes, edges = S.impact_graph()
    by_id = {n["id"]: n for n in nodes}
    n = by_id.get(node_id)
    if not n:
        raise HTTPException(404, f"unknown node {node_id}")
    kind = n["kind"]
    neigh = sorted({e["t"] if e["s"] == node_id else e["s"] for e in edges if node_id in (e["s"], e["t"])})
    xs = I.for_entity(I.all_insights(), **{REFS[kind]: node_id}) if kind in REFS else []
    explore = None
    if kind in ("plant", "line", "machine"):
        plant = node_id.split("-")[0]
        explore = {"plant": plant, **({"line": node_id} if kind == "line" else {}),
                   **({"line": "-".join(node_id.split("-")[:2]), "machine": node_id} if kind == "machine" else {})}
    vib = bool(xs) and xs[0].id.startswith("VIB-")
    return X.clean({
        "node": n, "kind": kind, "related": [X.insight(i) for i in xs[:2]],
        "neighbors": [{"id": x, "name": by_id[x]["name"]} for x in neigh],
        "chart": X.figure(CHARTS[kind](node_id)) if kind in CHARTS else None,
        "explore": explore, "entity": {"type": kind, "id": node_id},
        "actions": (xs[0].actions if xs else ["comment"]) + ["data_correction"],
        "insight_id": xs[0].id if xs else "", "defaults": {"failure_mode": "spindle bearing wear"} if vib else {},
        "ask": xs[0].ask if xs else (f"Explain {n['name']} ({node_id}) and how it connects to "
                                     f"{', '.join(by_id[x]['name'] for x in neigh[:4])}."),
    })
