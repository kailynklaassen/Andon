"""App & agent health (admins only) and the browser's error reports.

    GET  /api/admin/health?hours=168     one payload for the health page: Foreman's run summary (per user, per Genie
                                         space), recent runs with their errors, and this app's own issues
    POST /api/telemetry                  the browser reports an error it hit (any signed-in user)
    GET  /api/auth/check                 YOUR on-behalf-of-user status: is a user token forwarded, which scopes it
                                         carries, and does Genie accept it (any signed-in user, about themselves only)

Why one page for both: when someone says "Foreman is broken", the answer is usually in one of two places — the agent
(a Genie space erroring, slow, or denied for that user) or the app (Foreman unreachable, a stream cut off). Seeing both
side by side, per user and per session, with a link to each run's trace, is how you find it in seconds.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from backend.core import foreman_client as F
from backend.core import telemetry
from backend.identity import current_user, is_admin

router = APIRouter(prefix="/api", tags=["admin"])


@router.get("/admin/health")
def health(request: Request, hours: int = 168, user: str = "", status: str = "") -> dict:
    if not is_admin(request):
        raise HTTPException(403, "The health page is for app admins (app.admins in demo_config.yml).")
    out: dict = {"hours": hours, "agent_mode": F.mode(), "foreman_error": None}
    try:
        out["summary"] = F.get("/api/runs/summary", hours=hours) if F.mode() == "live" else None
        out["runs"] = F.get("/api/runs", hours=hours, user=user, status=status, limit=300) if F.mode() == "live" else []
        info = F.get("/api/info")
        out["traces_url"], out["trace_tables"], out["genie_auth"] = (info.get("traces_url", ""), info.get("trace_tables", ""),
                                                                     info.get("genie_auth", ""))
    except Exception as e:                       # the page still shows the app's own issues when Foreman is down
        out.update(summary=None, runs=[], foreman_error=str(e)[:300])
    out["app_events"] = telemetry.events(hours)
    return out


class ClientError(BaseModel):
    message: str = Field(max_length=2000)
    route: str = Field(default="", max_length=300)
    detail: dict = {}


@router.post("/telemetry")
def client_error(e: ClientError, request: Request) -> dict:
    telemetry.record("client_error", current_user(request), e.route, e.message, e.detail)
    return {"ok": True}


def _claims(token: str) -> dict:
    """The token's claims (scopes, expiry) — decoded, not verified: this is a diagnostic, not an auth decision."""
    import base64
    import json
    try:
        part = token.split(".")[1]
        return json.loads(base64.urlsafe_b64decode(part + "=" * (-len(part) % 4)))
    except Exception:
        return {}


@router.get("/auth/check")
def auth_check(request: Request) -> dict:
    """Troubleshoot on-behalf-of-user. Never returns or logs the token itself."""
    import time

    import requests
    from databricks.sdk.core import Config

    token = request.headers.get("x-forwarded-access-token")
    out = {"user": current_user(request), "token_forwarded": bool(token)}
    if not token:
        out["verdict"] = ("No user token reached the app. The app needs user authorization scopes (app.yaml / "
                          "user_api_scopes) and you must have authorized it.")
        return out
    c = _claims(token)
    scopes = c.get("scope") or c.get("scp") or ""
    scopes = scopes.split() if isinstance(scopes, str) else list(scopes)
    out.update(scopes=scopes, expires_in_s=int(c["exp"] - time.time()) if "exp" in c else None,
               token_kind="JWT" if c else "opaque (scopes not readable)")
    host = Config().host.rstrip("/")
    r = requests.get(f"{host}/api/2.0/genie/spaces", headers={"Authorization": f"Bearer {token}"}, timeout=20)
    out["genie_probe"] = {"status": r.status_code, "message": r.text[:300] if r.status_code != 200 else "ok"}
    out["verdict"] = ("Genie accepts your token — Foreman can run Genie as you." if r.ok else
                      "Genie rejected your token. If it says the token lacks the genie scope, your consent predates the "
                      "scope: revoke it (DELETE /api/2.0/oauth-app-integrations/<app oauth2_app_client_id>/user-consent/me), "
                      "then open the app in a private window and click Authorize.")
    return out
