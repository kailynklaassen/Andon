"""
KK's Parts Andon — FastAPI backend (Databricks App: kkparts-andon).
==================================================================

    browser (React, frontend/)  ──/api/*──►  this app  ──►  SQL warehouse (gold, cached 10 min)
                                                       ──►  Lakebase (the human-in-the-loop ledger)
                                                       ──►  Foreman agent server (kkparts-foreman, streamed)

Layout: routes/ are thin HTTP handlers; core/ holds the logic (data, insights, charts, scenes, ledger, forms) and
knows nothing about HTTP. The React build (frontend/dist, produced by `npm run build` — Databricks Apps runs it at
deploy) is served from the same origin, so there is no CORS to configure and the platform's sign-in covers both.

"""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse

from backend.core import data as D
from backend.core import foreman_client as F
from backend.core import ledger as A
from backend.identity import current_user, genie_access, is_admin
from backend.routes import actions, admin, board, explorer, foreman, impact

app = FastAPI(title="KK's Parts Andon")
for r in (board.router, explorer.router, impact.router, actions.router, foreman.router, admin.router):
    app.include_router(r)


@app.middleware("http")
async def log_failures(request: Request, call_next):
    """Every API failure lands on the App & agent health page, with who hit it and where."""
    from fastapi.responses import JSONResponse

    from backend.core import telemetry
    try:
        response = await call_next(request)
    except Exception as e:
        telemetry.record("api_error", current_user(request), request.url.path, f"{type(e).__name__}: {e}"[:2000])
        return JSONResponse({"detail": "Something went wrong on our side; it has been logged."}, status_code=500)
    if response.status_code >= 500 and request.url.path.startswith("/api/"):
        telemetry.record("api_error", current_user(request), request.url.path, f"HTTP {response.status_code}")
    return response


@app.on_event("startup")
def warm_caches() -> None:
    """Run the shared queries once at startup (in the background), so the first person to open the app doesn't pay
    the warehouse round-trips — every page after that is served from the 10-minute cache."""
    import threading

    def warm():
        try:
            board.board(); board.network(); impact.graph(); explorer.plants()
            for p in D.load("plants").plant_id:
                explorer.scene(p)
        except Exception as e:                       # warming is best-effort; the request path still works
            print(f"cache warm-up skipped: {e}")
    threading.Thread(target=warm, daemon=True).start()


@app.on_event("startup")
def watch_for_corrections() -> None:
    """Refresh the cached gold data as soon as an approved correction reaches gold.

    Why: pages are served from a 10-minute cache, so without this a person who approves a correction could look at
    the old value for up to 10 minutes after the pipeline applied it. The sync job writes an `in_gold` event to the
    Lakebase ledger after its pipeline refresh; this checks for a new one every minute (one tiny query) and
    recomputes the caches in the background. Notes need nothing here — they never touch cached gold data."""
    import threading
    import time

    from backend.core import cache

    def watch():
        seen = None
        while True:
            try:
                latest = A.last_in_gold()
                if seen is not None and latest is not None and latest != seen:
                    print(f"correction reached gold at {latest}: refreshing cached data")
                    cache.refresh_all()
                seen = latest if latest is not None else seen or "none"
            except Exception as e:                   # Lakebase scaled to zero, token refresh, ... try again next minute
                print(f"correction watcher: {e}")
            time.sleep(60)
    if A.backend() == "lakebase":
        threading.Thread(target=watch, daemon=True).start()


@app.get("/api/meta")
def meta(request: Request) -> dict:
    return {"user": current_user(request), "is_admin": is_admin(request), "genie_access": genie_access(request),
            "data_mode": D.data_mode(), "agent_mode": F.mode(), "ledger": A.backend(),
            "data_through": f"{D.today():%b %d, %Y}", "dashboard_url": os.getenv("KK_DASHBOARD_EMBED_URL", "")}


@app.get("/api/health")
def health() -> dict:
    return {"ok": True}


# ---------------------------------------------------------------------------- the React app (same origin)
DIST = (Path(__file__).resolve().parent.parent / "frontend" / "dist").resolve()


@app.get("/{path:path}", include_in_schema=False)
def spa(path: str):
    if path.startswith("api/"):
        raise HTTPException(404)
    target = (DIST / path).resolve()
    if path and target.is_file() and DIST in target.parents:      # never serve anything outside dist/
        return FileResponse(target)
    index = DIST / "index.html"
    if not index.exists():
        raise HTTPException(503, "frontend not built — run `npm run build` (Databricks Apps does it at deploy)")
    return FileResponse(index, headers={"Cache-Control": "no-cache"})   # index never cached: new builds load at once
