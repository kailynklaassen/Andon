"""
genie_benchmark — score Genie spaces against their benchmark questions using only GA APIs.
=========================================================================================

Each benchmark in 03_genie_spaces/spaces/<domain>.yml is one of:

    sql:         the certified answer. We run it ourselves and compare its result to Genie's result.
    expect_doc:  a document question. Genie must surface this document ID — asked in Agent mode, which searches the
                 documents attached to the space (Chat mode can't read files).

How a result is judged (deliberately simple and explainable):
  * every value in the expected result must appear in Genie's result
      - numbers within 1% (a rate may come back as 0.77 or 77.0 — both count)
      - text case-insensitive; month timestamps match on YYYY-MM
  * ranking questions (expected answer is a single row, e.g. "which plant is lowest"):
    the expected row must be Genie's FIRST row, so a wrong ordering fails
  * if Genie answers in text only, the expected values must appear in its text
  * text labels the question already names (e.g. 'FY26 Q2') don't have to be repeated in the result

Genie's own Benchmarks tab runs the same SQL-answer questions in the UI; the API behind it is Beta,
so this accelerator scores through the GA Conversation API instead.
"""
from __future__ import annotations

import re
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Callable

TOLERANCE = 0.01


# ----------------------------------------------------------------------------- Genie Agent mode (GA) — document questions
def ask_genie_agent(w, space_id: str, question: str, timeout_s: int = 600) -> dict:
    """Agent mode searches the files attached to the space. Returns the same shape as ask_genie: the answer text,
    and the cells of every result table it produced (so judge() works unchanged)."""
    import json
    import requests
    out = {"status": "", "error": "", "text": "", "sql": "", "columns": [], "rows": []}
    body = {"input": [{"type": "message", "role": "user", "content": [{"type": "input_text", "text": question}]}]}
    try:
        with requests.post(f"{w.config.host.rstrip('/')}/api/2.0/genie/agents/{space_id}/responses", json=body, stream=True,
                           timeout=(10, timeout_s), headers={**w.config.authenticate(), "Accept": "text/event-stream"}) as r:
            for line in r.iter_lines(decode_unicode=True):
                if not line or not line.startswith("data:"):
                    continue
                ev = json.loads(line[5:]); item = ev.get("item") or {}
                if ev.get("type") == "response.output_item.done":
                    if item.get("type") == "function_call":
                        out["sql"] += json.loads(item.get("arguments") or "{}").get("sql", "") + "\n"
                    elif item.get("type") == "function_call_output":
                        table = [l for l in str(item.get("output") or "").splitlines() if l.strip().startswith("|")]
                        out["rows"] += [[c.strip() for c in l.strip().strip("|").split("|")] for l in table[2:]]
                    elif item.get("type") == "message":
                        out["text"] += "".join(c.get("text", "") for c in item.get("content", []))
                if ev.get("type") in ("response.completed", "response.failed"):
                    out["status"] = "COMPLETED" if ev["type"] == "response.completed" else "FAILED"
                    break
    except Exception as e:
        out.update(status="ERROR", error=str(e)[:300])
    return out


# ----------------------------------------------------------------------------- Genie (Conversation API, GA)
def ask_genie(w, space_id: str, question: str, timeout_s: int = 300) -> dict:
    """Ask one question in a fresh conversation; return Genie's text, SQL, columns and rows."""
    api = w.api_client
    for attempt in range(6):                                   # back off on rate limits
        try:
            r = api.do("POST", f"/api/2.0/genie/spaces/{space_id}/start-conversation", body={"content": question})
            break
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e) or "rate" in str(e).lower():
                time.sleep(15 * (attempt + 1))
                continue
            return {"status": "ERROR", "error": str(e)[:300], "text": "", "sql": "", "columns": [], "rows": []}
    else:
        return {"status": "ERROR", "error": "rate limited", "text": "", "sql": "", "columns": [], "rows": []}
    base = f"/api/2.0/genie/spaces/{space_id}/conversations/{r['conversation_id']}/messages/{r['message_id']}"
    t0, m = time.time(), {}
    while time.time() - t0 < timeout_s:
        m = api.do("GET", base)
        if m.get("status") in ("COMPLETED", "FAILED", "CANCELLED"):
            break
        time.sleep(3)
    out = {"status": m.get("status", "TIMEOUT"), "error": (m.get("error") or {}).get("error", ""),
           "text": "", "sql": "", "columns": [], "rows": []}
    for att in m.get("attachments", []):
        if att.get("text"):
            out["text"] += att["text"]["content"] + " "
        if att.get("query"):
            out["sql"] = att["query"]["query"]
            out["text"] += (att["query"].get("description") or "") + " "
            res = api.do("GET", f"{base}/attachments/{att['attachment_id']}/query-result")
            sr = res.get("statement_response", {})
            out["columns"] = [c["name"] for c in sr.get("manifest", {}).get("schema", {}).get("columns", [])]
            out["rows"] = sr.get("result", {}).get("data_array", []) or []
    return out


# ----------------------------------------------------------------------------- comparison
def _num(v) -> float | None:
    try:
        return float(str(v).replace(",", "").replace("%", "").replace("$", ""))
    except (TypeError, ValueError):
        return None


def _value_in(expected, cells: list) -> bool:
    e = _num(expected)
    if e is not None:
        for c in cells:
            g = _num(c)
            if g is None:
                continue
            for scale in (1, 100, 0.01):                       # 0.77 vs 77.0
                if abs(g - e * scale) <= TOLERANCE * max(abs(e * scale), 1e-9):
                    return True
        return False
    s = str(expected)
    if re.match(r"^\d{4}-\d{2}-\d{2}", s):                     # month / date: match on YYYY-MM
        return any(str(c).startswith(s[:7]) for c in cells)
    return any(s.lower() in str(c).lower() for c in cells)


def _value_in_text(expected, text: str) -> bool:
    e = _num(expected)
    if e is None:
        return str(expected).lower() in text.lower()
    nums = [_num(x) for x in re.findall(r"-?\d[\d,]*\.?\d*", text)]
    return _value_in(expected, [n for n in nums if n is not None])


def judge(bench: dict, expected_rows: list | None, genie: dict) -> tuple[str, str]:
    """Return (PASS|FAIL|ERROR, reason)."""
    if genie["status"] != "COMPLETED":
        return "ERROR", f"Genie {genie['status']}: {genie['error'][:200]}"
    cells = [c for row in genie["rows"] for c in row]
    if "expect_doc" in bench:
        ok = _value_in(bench["expect_doc"], cells) or bench["expect_doc"].lower() in genie["text"].lower()
        return ("PASS", f"cited {bench['expect_doc']}") if ok else ("FAIL", f"{bench['expect_doc']} not in Genie's result")
    if not expected_rows:
        return "ERROR", "benchmark SQL returned no rows"
    if not genie["rows"]:
        missing = [v for row in expected_rows for v in row if v is not None and not _value_in_text(v, genie["text"])]
        return ("PASS", "answered in text") if not missing else ("FAIL", f"no result rows; text lacks {missing[:3]}")
    if len(expected_rows) == 1 and len(genie["rows"]) > 1:      # ranking question: must be Genie's top row
        missing = [v for v in expected_rows[0] if v is not None and not _value_in(v, genie["rows"][0])]
        return ("PASS", "top row matches") if not missing else ("FAIL", f"top row {genie['rows'][0][:4]} lacks {missing[:3]}")
    in_question = lambda v: _num(v) is None and str(v).lower() in bench["question"].lower()   # e.g. 'FY26 Q2' labels
    missing = [v for row in expected_rows for v in row
               if v is not None and not in_question(v) and not _value_in(v, cells)]
    return ("PASS", "result matches") if not missing else ("FAIL", f"missing {missing[:3]}")


# ----------------------------------------------------------------------------- run a whole suite
def run_suite(w, spaces: dict[str, str], benchmarks: dict[str, list], run_sql: Callable[[str], list],
              gold: str, parallel_spaces: int = 4) -> list[dict]:
    """spaces = {domain: space_id}; benchmarks = {domain: [bench, ...]}; run_sql(sql) -> list of row lists."""
    def one_space(domain: str) -> list[dict]:
        results = []
        for b in benchmarks.get(domain, []):
            expected = run_sql(b["sql"].replace("{G}", gold)) if "sql" in b else None
            t0 = time.time()
            g = (ask_genie_agent if "expect_doc" in b else ask_genie)(w, spaces[domain], b["question"])
            status, reason = judge(b, expected, g)
            results.append({"domain": domain, "question": b["question"], "status": status, "reason": reason,
                            "expected": str(expected)[:500] if expected is not None else b.get("expect_doc"),
                            "genie_rows": str(g["rows"][:5])[:500], "genie_sql": g["sql"][:2000],
                            "seconds": round(time.time() - t0, 1)})
        return results
    with ThreadPoolExecutor(max_workers=parallel_spaces) as pool:
        return [r for rs in pool.map(one_space, [d for d in benchmarks if d in spaces]) for r in rs]
