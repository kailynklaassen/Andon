# 05_app — KK's Parts Andon (FastAPI + React, Databricks App `kkparts-andon`)

On a line, the andon is the signal board plus the cord anyone can pull to flag a problem and call for help. This app is
that loop for the whole operation: **data → insight → agent recommendation → human decision → back into the lakehouse.**

| Page | What it's for |
|---|---|
| **Andon Board** | Today's briefing: KPI tiles, the critical issues to decide on, the supply-network map (click a plant), watch list, performance charts, optional AI/BI dashboard tab. |
| **Plant Explorer** | The physical hierarchy on an interactive canvas: plant floor → line → work center (and suppliers at the receiving dock). Every level: KPIs, charts, tables, the insights touching it, and the action panel. Where you are is in the URL. |
| **Impact Web** | A draggable graph of how a problem propagates: supplier → material → plant → line → machine → defect → CAPA → DC → carrier → customer. Details, trend and actions for the selected node sit under the graph. |
| **Foreman** | The supervisor agent, full screen (also a drawer on every page that knows what you're looking at). Every step is visible: recall → which experts → each Genie space's live status, SQL and rows → the streamed answer → its MLflow trace. Shows what Foreman remembers about you. |
| **Action Ledger** | Every human action with approve / reject / done, where each approved action landed in the lakehouse, its audit trail, and *Sync now*. |

## How it's built
```
backend/                       FastAPI (uvicorn backend.main:app)
  main.py                      routers + serves frontend/dist on the same origin (no CORS); warms the caches at startup
  identity.py                  who is asking (X-Forwarded-Email on Apps)
  routes/                      THIN HTTP handlers: board, explorer, impact, actions, foreman (SSE proxy)
  core/                        the logic, no HTTP:
    data.py                    one dict of gold queries; live (SQL warehouse) or snapshot (parquet)
    cache.py                   stale-while-revalidate cache — after the first computation nobody waits on the warehouse
    insights.py                rules that FIND the issues in the data (vibration drift, supplier breach, carrier SLA, ...)
    charts.py · scenes.py      Plotly figures (sent as JSON) · floor scene, map layers, impact graph
    ledger.py · forms.py · records.py   the Lakebase human-in-the-loop ledger · data-bound action forms · correctable cells
    foreman_client.py          streams the agent server's events (or an offline scripted stand-in, same event shapes)
frontend/                      React 19 + Vite + TanStack Query + Plotly.js + deck.gl/MapLibre
  src/api.ts                   typed client, mirrors backend/core/shapes.py
  src/app.tsx                  shell: banner, nav, Foreman drawer, toast
  src/components/              ui (KPI tiles, tables, cards) · visuals (charts, map, canvas) · ActionPanel · ForemanChat
  src/canvas/kkCanvas.js       the SVG canvas (plant floor + impact web), framework-free
  src/pages/                   AndonBoard · PlantExplorer · ImpactWeb · ForemanPage · ActionLedger
00_deploy_app.py               Step 5 notebook: renders app.yaml from config, resources, grants, deploy
```

**Why it's fast:** the gold queries are computed once per process and refreshed in the background (cached responses
~3 ms server-side), the browser caches each response for 5 minutes, and the agent's answer streams token by token
with every step shown — no page waits on the agent.

## Run it
**Deploy:** run `05_app/00_deploy_app` (or `99_run_all`). It writes `app.yaml` from `config/demo_config.yml`, declares
the resources (SQL warehouse, Lakebase, the sync job), grants `SELECT` on gold and `CAN_USE` on the Foreman app, and
deploys. Databricks Apps runs `npm install` and `npm run build` itself — nothing pre-built is committed. Each person
authorizes the app once on first visit. Uploading by hand: `databricks sync . <workspace path>/05_app` (honours
`.gitignore`, so `node_modules` never goes up).

**How the app measures things (so it agrees with the bible, the metric views and Genie):** vibration is the
running-hours-weighted *monthly* average and a limit is crossed in the first month above it; before/after numbers
split at the change point the detector finds; machine KPIs cover Apr–Sep; carrier and customer performance is FY26.
