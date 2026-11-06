"""Foreman routes: the browser talks only to this app; this app talks to the agent server (kkparts-foreman).

Why proxy instead of letting the browser call the agent directly: the agent app is a different origin with its own
sign-in, and the backend is where we know WHO is asking (the platform's X-Forwarded-Email) and can add it to the
request — so memory and traces belong to the person. On-behalf-of-user: it also forwards the person's Genie-scoped
token (x-forwarded-access-token, from the app's user authorization) so Genie answers with THEIR permissions.
"""
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend.core import foreman_client as F
from backend.identity import current_user

router = APIRouter(prefix="/api/foreman", tags=["foreman"])


class Ask(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    context: str = ""            # what the person is looking at ("machine GVL-L3-WC01 on line GVL-L3")
    session_id: str | None = None


@router.post("/chat")
def chat(a: Ask, request: Request):
    lines = F.stream(a.question, user=current_user(request), context=a.context, session_id=a.session_id,
                     user_token=request.headers.get("x-forwarded-access-token"))
    return StreamingResponse(lines, media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@router.get("/suggest")
def suggest(question: str, context: str = "") -> list[str]:
    return F.suggested_actions(question, context)


@router.get("/info")
def info() -> dict:
    return {"mode": F.mode(), **F.get("/api/info")}


@router.get("/sessions")
def sessions(request: Request):
    return F.get("/api/sessions", user=current_user(request))


@router.get("/sessions/{session_id}")
def session(session_id: str):
    return F.get(f"/api/sessions/{session_id}")


@router.get("/memories")
def memories(request: Request):
    return F.get("/api/memories", user=current_user(request))


@router.delete("/memories/{memory_id}")
def forget(memory_id: int, request: Request):
    return F.delete(f"/api/memories/{memory_id}", user=current_user(request))
