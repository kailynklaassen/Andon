"""Who is using the app.

On Databricks Apps every request arrives through the platform's proxy, which has already signed the person in and adds
X-Forwarded-Email / X-Forwarded-Preferred-Username. That's the identity the ledger records (created_by, reviewed_by)
and that Foreman's memory and traces are keyed on. Locally there is no proxy, so KK_LOCAL_USER (or a placeholder) is used.

Admins (KK_ADMINS, rendered from app.admins in demo_config.yml) also see the App & agent health page.
"""
from __future__ import annotations

import os

from fastapi import Request


def current_user(request: Request) -> str:
    h = request.headers
    return (h.get("X-Forwarded-Email") or h.get("X-Forwarded-Preferred-Username")
            or os.getenv("KK_LOCAL_USER", "you@kkparts.local"))


def is_admin(request: Request) -> bool:
    admins = {a.strip().lower() for a in os.getenv("KK_ADMINS", "").split(",") if a.strip()}
    return current_user(request).lower() in admins or (not os.getenv("DATABRICKS_APP_NAME") and not admins)


def genie_access(request: Request) -> bool | None:
    """On-behalf-of-user: does this person's forwarded token carry the `genie` scope? None = no token at all (local
    run, or user authorization is off). False = they authorized the app before it asked for Genie: re-authorize."""
    import base64
    import json
    token = request.headers.get("x-forwarded-access-token")
    if not token:
        return None
    try:
        part = token.split(".")[1]
        claims = json.loads(base64.urlsafe_b64decode(part + "=" * (-len(part) % 4)))
        scopes = claims.get("scope") or claims.get("scp") or ""
        return "genie" in (scopes.split() if isinstance(scopes, str) else scopes)
    except Exception:
        return None
