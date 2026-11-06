"""The human-in-the-loop API: build an action form, submit it, review it, see where it went in the lakehouse.

    GET  /api/actions/types                      every action type (label, icon)
    GET  /api/actions/form/{type}                the form for one entity: fields with data-bound options
    GET  /api/records · /records/fields · /records/value     the deterministic correction picker
    POST /api/actions                            submit → Lakebase hitl.actions (+ a 'submitted' event)
    GET  /api/actions                            the ledger (optionally ?entity_id=)
    POST /api/actions/{id}/review                Approved | Rejected | Done (Approved → the outbox)
    GET  /api/actions/{id}/events                the audit trail
    POST /api/actions/sync                       run the lakehouse sync job now
"""
from __future__ import annotations

import json
import os
from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from backend.core import forms as F
from backend.core import ledger as A
from backend.core import shapes as X
from backend.identity import current_user

router = APIRouter(prefix="/api", tags=["actions"])


@router.get("/actions/types")
def types() -> dict:
    return {k: {"label": v["label"], "icon": v["icon"], "domain": v["domain"]} for k, v in A.ACTION_TYPES.items()}


@router.get("/actions/form/{action_type}")
def form(action_type: str, entity_type: str, entity_id: str, defaults: str = "{}") -> dict:
    if action_type not in A.ACTION_TYPES:
        raise HTTPException(404, f"unknown action type {action_type}")
    return X.clean(F.action_form(action_type, entity_type, entity_id, json.loads(defaults or "{}")))


@router.get("/records")
def records(entity_type: str, entity_id: str) -> list[dict]:
    return X.clean(F.records_for(entity_type, entity_id))


def _known(dataset: str, column: str | None = None) -> None:
    """A clear 404 for a dataset or column the correction catalog doesn't have (instead of a 500)."""
    from backend.core import records as R
    if dataset not in R.CATALOG:
        raise HTTPException(404, f"unknown dataset '{dataset}' — one of: {', '.join(sorted(R.CATALOG))}")
    if column is not None and column not in R.CATALOG[dataset]["fields"]:
        raise HTTPException(404, f"'{column}' isn't a correctable column of {dataset}")


@router.get("/records/fields")
def record_fields(dataset: str) -> list[dict]:
    _known(dataset)
    return F.fields_for(dataset)


@router.get("/records/value")
def record_value(dataset: str, key: str, column: str) -> dict:
    _known(dataset, column)
    return X.clean(F.field_value(dataset, key, column))


class Correction(BaseModel):
    dataset: str
    key: str
    column: str
    corrected_value: str | float | int | None


class NewAction(BaseModel):
    action_type: str
    entity_type: str
    entity_id: str
    title: str = Field(min_length=1, max_length=300)
    details: str = ""
    priority: Literal["P1", "P2", "P3"] = "P2"
    payload: dict = {}
    correction: Correction | None = None       # data_correction only: resolved to an exact cell on the server
    source: Literal["human", "agent_suggested"] = "human"
    insight_id: str = ""


@router.post("/actions")
def submit(a: NewAction, request: Request) -> dict:
    if a.action_type not in A.ACTION_TYPES:
        raise HTTPException(400, f"unknown action type {a.action_type}")
    payload = dict(a.payload)
    if a.action_type == "data_correction":
        if not a.correction or a.correction.corrected_value in (None, ""):
            raise HTTPException(400, "a data correction needs a record, a field and a corrected value")
        try:
            payload = F.correction_payload(a.correction.dataset, a.correction.key, a.correction.column, a.correction.corrected_value)
        except ValueError as e:
            raise HTTPException(400, str(e))
    row = A.record(current_user(request), a.action_type, a.entity_type, a.entity_id, a.title, a.details, a.priority,
                   payload, a.source, a.insight_id)
    return X.clean(row)


@router.get("/actions")
def ledger(entity_id: str | None = None) -> dict:
    df = A.ledger()
    if entity_id and len(df):
        df = df[df.entity_id == entity_id]
    return {"backend": A.backend(), "rows": X.clean(df.to_dict("records")),
            "sync_job": bool(os.getenv("KK_SYNC_JOB_ID")) and A.backend() == "lakebase"}


class Review(BaseModel):
    status: Literal["Approved", "Rejected", "Done"]


@router.post("/actions/{action_id}/review")
def review(action_id: str, r: Review, request: Request) -> dict:
    A.review(current_user(request), action_id, r.status)
    return {"ok": True}


@router.get("/actions/{action_id}/events")
def events(action_id: str) -> list[dict]:
    return X.clean(A.events(action_id).to_dict("records"))


@router.post("/actions/sync")
def sync_now() -> dict:
    job = os.getenv("KK_SYNC_JOB_ID")
    if not job:
        raise HTTPException(400, "no sync job configured (KK_SYNC_JOB_ID)")
    from databricks.sdk import WorkspaceClient
    run = WorkspaceClient().jobs.run_now(job_id=int(job))
    return {"run_id": run.run_id}
