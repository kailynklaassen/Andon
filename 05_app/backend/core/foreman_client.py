"""Foreman, as the Andon backend sees it: a client for the agent server (app kkparts-foreman), plus an offline stand-in.

    live  — POST {KK_FOREMAN_URL}/api/invocations (the Agent Server protocol) with the app's OAuth token and stream the
            agent's events straight through, reconnecting to the same durable run if the connection drops.
            The backend adds who is asking (the signed-in person, from X-Forwarded-Email) and what they're looking at,
            so the agent's memory and the MLflow trace belong to the person, not to the app.
            On-behalf-of-user (Apps user authorization, GA): the platform gives this app each person's token, scoped
            to Genie only (app.yaml user_api_scopes); it goes to Foreman in X-Foreman-User-Token, so the Genie calls
            for that question run AS the person. The app itself stays one service principal for everything else.
    demo  — no agent configured (laptop, offline demo): scripted answers for the four storylines, emitted in the SAME
            event shape (step / step_update / step_done / token / answer / done), so the UI is identical. The UI says so.

Event shapes are documented in 04_supervisor_agent/agent/server.py.
"""
from __future__ import annotations

import json
import os
import time
import uuid
from typing import Iterator

import requests

FOREMAN_URL = os.getenv("KK_FOREMAN_URL", "").rstrip("/")


def mode() -> str:
    m = os.getenv("KK_AGENT_MODE", "auto").lower()
    if m in ("live", "demo"):
        return m
    return "live" if FOREMAN_URL else "demo"


def _headers() -> dict:
    from databricks.sdk.core import Config
    return {**Config().authenticate(), "Content-Type": "application/json", "Accept": "text/event-stream"}


def stream(question: str, *, user: str, context: str = "", session_id: str | None = None,
           user_token: str | None = None) -> Iterator[str]:
    """Yields ready-to-send SSE lines. user_token: the asker's Genie-scoped token (never logged).

    Foreman runs on AgentKit's DurableAgentServer: POST /api/invocations starts a durable run and streams its events.
    If the connection drops mid-answer, we reconnect to GET /api/invocations/{id}/events?after=<last event id> and
    the person sees the rest of the same answer — the run kept going on the server."""
    session_id = session_id or str(uuid.uuid4())          # the Agent Server orders invocations within a session
    if mode() == "demo":
        for ev in _demo(question, context, session_id):
            yield f"event: {ev['type']}\ndata: {json.dumps(ev)}\n\n"
        return
    invocation_id = str(uuid.uuid4())                     # idempotency key: a retried POST never runs twice
    body = {"id": invocation_id, "session_id": session_id, "stream": True,
            "input": {"question": question, "user": user, "context": context}}
    last_event, finished = 0, False
    for attempt in range(4):
        try:
            headers = {**_headers(), **({"X-Foreman-User-Token": user_token} if user_token and attempt == 0 else {})}
            if attempt == 0:
                r = requests.post(f"{FOREMAN_URL}/api/invocations", headers=headers, json=body, stream=True, timeout=900)
            else:                                         # resume the same run where the stream broke
                r = requests.get(f"{FOREMAN_URL}/api/invocations/{invocation_id}/events", headers=headers,
                                 params={"after": last_event}, stream=True, timeout=900)
            with r:
                r.raise_for_status()
                for line in r.iter_lines(decode_unicode=True):
                    if line.startswith("id:"):
                        last_event = int(line[3:].strip() or last_event)
                    if line.startswith("event: run.completed") or line.startswith("event: run.failed"):
                        finished = True
                    yield (line + "\n") if line else "\n"
            if finished or attempt == 3:
                return
            time.sleep(1.5 * (attempt + 1))
        except Exception as e:
            if attempt < 3:
                time.sleep(1.5 * (attempt + 1))
                continue
            from backend.core import telemetry
            telemetry.record("foreman_unreachable", user, "/api/foreman/chat", str(e)[:500],
                             {"question": question[:300], "session_id": session_id, "invocation_id": invocation_id})
            ev = {"type": "error", "message": f"Couldn't reach Foreman ({str(e)[:200]})."}
            yield f"event: error\ndata: {json.dumps(ev)}\n\n"
            return


def get(path: str, **params):
    """Sessions / memories / info from the agent server (empty in demo mode)."""
    if mode() == "demo":
        return [] if path != "/api/info" else {"memory": False, "traces_url": "", "router_llm": "", "answer_llm": "", "tools": []}
    r = requests.get(f"{FOREMAN_URL}{path}", headers=_headers(), params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def delete(path: str, **params):
    if mode() == "demo":
        return {"ok": True}
    r = requests.delete(f"{FOREMAN_URL}{path}", headers=_headers(), params=params, timeout=30)
    r.raise_for_status()
    return r.json()


# -----------------------------------------------------------------------------
# Offline stand-in. Answers use only numbers from the narrative bible / gold data.
# -----------------------------------------------------------------------------
SPACE_LABEL = {"production": "KK's Parts Production & OEE", "quality": "KK's Parts Quality & Compliance",
               "maintenance": "KK's Parts Maintenance & Reliability", "supply_chain": "KK's Parts Supply Chain & Warehousing"}

_SCRIPTS = [
    (("spindle", "wc01", "vibration", "greenville", "gvl-l3", "gearbox", "hartwell", "pm-cnc"), {
        "routes": [("maintenance", "Monthly avg vibration and breakdowns for GVL-L3-WC01 since 2026-03-15, and what the "
                                   "Hartwell OEM manual and PM-CNC-030 say about the bearing replacement limit",
                    "SELECT reading_month, AVG(avg_vibration_mm_s) FROM fact_machine_health_daily WHERE machine_id = 'GVL-L3-WC01' GROUP BY 1"),
                   ("production", "GVL-L3 OEE by month FY26",
                    "SELECT production_month, MEASURE(oee) FROM production_oee_metrics WHERE line_id = 'GVL-L3' GROUP BY 1")],
        "text": """**GVL-L3-WC01 (Hartwell HAR-119 HMC #1) is the Greenville Gearbox Assembly bottleneck and its spindle bearings are failing.**

- Vibration rose from a **2.8 mm/s** baseline to **8.75 mm/s** in September (Apr 3.44 → May 4.39 → Jun 5.23 → Jul 6.46 → Aug 7.57).
- The **Hartwell manual §7.4** says *replace spindle bearings at 4.5 mm/s*. Our **PM-CNC-030 Rev C** still uses **7.1 mm/s**, so monthly PMs were signed off "within limit" while the machine was already past the OEM limit — about **two months** of lost warning. Two PMs were also deferred (Jun 27, Sep 4).
- Since Mar 15: **30 breakdowns**, ≈**286 repair hours**, ≈**$243K** parts + contractor (≈$146K Hartwell field service).
- Line OEE fell from **82% (Oct)** to **50% (Sep)**; bore-position NCRs rose and **CAPA-2026-103** is open and overdue.

**Recommended:** (1) raise a P1 work order to replace the spindle cartridge (10-week lead, $68,400 quote — order now, nothing on site), (2) approve **MOC-2026-031** to align PM-CNC-030 to 4.5 mm/s, (3) copy Columbus's spare-spindle program for A-critical CNCs.""",
        "actions": ["work_order", "threshold_change"]}),
    (("brightline", "porosity", "casting", "sup-1007", "ppm", "scar", "supplier"), {
        "routes": [("supply_chain", "Brightline Castings SUP-1007 on-time delivery by month FY26 and what the master supply agreement says",
                    "SELECT promised_month, AVG(CAST(is_on_time AS INT)) FROM fact_supplier_receipt WHERE supplier_id='SUP-1007' GROUP BY 1"),
                   ("quality", "Incoming PPM for SUP-1007 vs the 500 PPM SQA limit, porosity NCRs and COPQ since May, status of SCAR-2026-014",
                    "SELECT MEASURE(supplier_ppm) FROM quality_inspection_metrics WHERE supplier_id='SUP-1007'")],
        "text": """**Brightline Castings (SUP-1007, Saltillo) broke both sides of its contract after moving to a new furnace line on May 1.**

- On-time delivery **92% → 44%**, late shipments average **9.3 days** late.
- Incoming quality **237 → 2,726 PPM** vs a **500 PPM** SQA-BLC-2023 limit (5×).
- Downstream: **214 material-shortage stops** (mostly GVL-L3, MTY-L3, CLB-L2, MTY-L1) and **380 porosity NCRs** costing ≈**$1.68M** COPQ.
- **SCAR-2026-014 / CAPA-2026-101** was due Jul 24 and is **overdue** — Brightline's 8D had containment only, no permanent fix.

**Recommended:** escalate to Level 3 / controlled shipping, and start the **Keystone Foundry** dual-source PPAP for MAT-5001/5002 (~12 weeks, +6% piece price) — the COPQ alone dwarfs the price delta.""",
        "actions": ["scar_escalation", "dual_source"]}),
    (("ridgeway", "carrier", "apex", "otif", "memphis", "freight", "car-04"), {
        "routes": [("supply_chain", "Ridgeway Freight CAR-04 carrier on-time by month vs SLA, Apex OTIF by carrier, and the service credit clause in CTA-RF-2024-07",
                    "SELECT ship_month, AVG(CAST(is_carrier_on_time AS INT)) FROM fact_shipment WHERE carrier_id='CAR-04' GROUP BY 1")],
        "text": """**Ridgeway Freight (CAR-04) is at 77% on-time for FY26 against a 95% SLA** — and it carries ~38% of Memphis volume.

- Worst months: **Nov 69%**, **Jul 74% · Aug 72% · Sep 73%** (peak season + summer driver shortage).
- **Apex Agricultural Equipment** (Strategic, served from DC-MEM): OTIF **88.3% on Ridgeway** vs ~98% on other carriers, **92.6% overall** vs the **95% OTIF** Apex requires. Rebecca Haines escalated in August.
- **CTA-RF-2024-07**: 2% of monthly freight spend in service credits for every point below 92%, and termination for convenience on 60 days' notice.

**Recommended:** claim the service credits, move Apex lanes to BlueLine Express (97.4%) or Summit (94.6%), and send Apex a recovery plan.""",
        "actions": ["carrier_review", "customer_response"]}),
    (("crimp", "wro", "wroclaw", "night", "c shift", "shift c", "wc02", "lumex"), {
        "routes": [("quality", "Crimp height defect rate and Cpk on WRO-L1 by shift before and after 2026-06-08, and the root cause in 8D-WRO-2026-009",
                    "SELECT shift, AVG(cpk), SUM(defects_found)/SUM(sample_size) FROM fact_quality_inspection WHERE line_id='WRO-L1' GROUP BY 1")],
        "text": """**It's a night-shift method problem on WRO-L1-WC02 (Lumex Terminal Crimp Press #2), not a machine problem.**

- Since the crimp die change on **Jun 8**, **C shift** runs a **13.6%** defect rate vs **~1.4–1.5%** on A/B; Cpk dropped to about **0.3** (target ≥ 1.33). Spec: **1.650 ± 0.050 mm**.
- 8D-WRO-2026-009 root cause: C shift sets die shut-height from superseded **WI-WRO-CR-07 Rev D** (not Rev E), has had **no Level 3 certified setter since May**, and the crimp-force alarm limits were widened during the die change and never restored.
- **CAPA-2026-102** (due Aug 22) is still **In Progress**.

**Recommended:** contain C-shift output since Jun 8, pull Rev D from the floor, restore the force-monitor limits, and certify a C-shift setter.""",
        "actions": ["containment", "work_instruction"]}),
    (("columbus", "clb", "best practice", "benchmark"), {
        "routes": [("maintenance", "PM compliance and breakdowns by plant FY26, and the Columbus best-practice case study",
                    "SELECT plant_id, MEASURE(pm_compliance) FROM maintenance_work_order_metrics GROUP BY 1")],
        "text": """**Columbus is the reliability benchmark:** **96.6% PM compliance**, the lowest breakdown rate, and **81.3% OEE** — best of the US plants.
Its practices: condition-based PM triggers at **OEM limits**, a weekly reliability stand-up, and a **spare-spindle program** for A-critical CNCs. Greenville (80.6% PM compliance, GVL-L3 at 76.7%) is the obvious place to copy them.""",
        "actions": ["comment"]}),
]



def suggested_actions(question: str, context: str = "") -> list[str]:
    """Rule-based for now: the storyline the question is about → the actions that fit it."""
    q = f"{question} {context}".lower()
    for keys, s in _SCRIPTS:
        if any(k in q for k in keys):
            return s["actions"]
    return []


def _demo(question: str, context: str, session_id: str) -> Iterator[dict]:
    q = f"{question} {context}".lower()
    script = next((s for keys, s in _SCRIPTS if any(k in q for k in keys)), None)
    t0 = time.time()
    yield {"type": "start", "session_id": session_id, "trace_id": None, "demo": True}
    sid = uuid.uuid4().hex[:8]
    yield {"type": "step", "id": sid, "kind": "plan", "label": "Deciding which domain experts to ask"}
    time.sleep(0.6)
    if not script:
        yield {"type": "step_done", "id": sid, "label": "No scripted answer for this question"}
        text = ("*(Offline demo — scripted answers cover the four storylines: the GVL-L3-WC01 spindle, Brightline Castings, "
                "Ridgeway Freight and the WRO-L1 night-shift crimp defects.)* Connect the app to the Foreman agent "
                "(`KK_FOREMAN_URL`) for live answers over all four Genie spaces.")
    else:
        yield {"type": "step_done", "id": sid, "label": "Asking " + ", ".join(SPACE_LABEL[s] for s, _, _ in script["routes"])}
        for space, sub_q, sql in script["routes"]:
            rid = uuid.uuid4().hex[:8]
            yield {"type": "step", "id": rid, "kind": "route", "label": f"{SPACE_LABEL[space]} Genie", "space": SPACE_LABEL[space],
                   "domain": space, "question": sub_q}
            for st in ("picking the relevant tables", "writing the SQL", "running the query"):
                time.sleep(0.4)
                yield {"type": "step_update", "id": rid, "status": st}
            yield {"type": "step_done", "id": rid, "status": "done", "label": f"{SPACE_LABEL[space]}: scripted evidence",
                   "sql": [sql], "rows": []}
        text = script["text"]
    pid = uuid.uuid4().hex[:8]
    yield {"type": "step", "id": pid, "kind": "plan", "label": "Writing the answer"}
    for word in text.split(" "):
        yield {"type": "token", "text": word + " "}
        time.sleep(0.008)
    yield {"type": "step_done", "id": pid, "label": "Writing the answer"}
    yield {"type": "answer", "text": text}
    yield {"type": "done", "session_id": session_id, "trace_id": None, "elapsed_ms": int((time.time() - t0) * 1000), "demo": True}
