"""
Foreman — the KK's Parts operations supervisor agent. ONE implementation, framework-free.
=========================================================================================

This file is the whole agent loop. The host adds no logic of its own:

    server.py            Agent Server (AgentKit DurableAgentServer) on Databricks Apps  ← the Andon app calls this
    03_evaluate_supervisor  runs the same loop in-process against the evaluation set

WHAT A RUN LOOKS LIKE (every step is an EVENT the UI shows live, and a SPAN in the MLflow trace)
---------------------------------------------------------------------------------------------
    1. memory   recall what this user told Foreman in earlier conversations         (Lakebase, memory.py)
    2. plan     a FAST model picks which domain experts to ask                       (router_llm, e.g. Haiku)
    3. route    one step per Genie space, all in PARALLEL, each streaming Genie's own status:
                "reading tables → writing SQL → running the query → done (SQL, rows)"
    4. answer   a STRONG model writes the answer from the evidence, streamed token by token (answer_llm)
                (it may ask for one more round of experts if the evidence points to another domain)
    5. done     the trace id, so the UI can link straight to the trace in MLflow

WHY THIS SHAPE (the parts that matter for any agentic framework)
---------------------------------------------------------------
* CRUCIAL — stream the steps. A cross-domain question takes 30-90 s, almost all of it inside Genie. Users
  wait happily when they can see "Maintenance Genie is running the query"; they abandon a spinner.
* CRUCIAL — run independent tools in parallel. A 3-domain question costs one Genie round-trip, not three.
* CRUCIAL — trace every run. One MLflow trace per question, a span per model call and per Genie call, tagged
  with the session and the user. This is how you debug a wrong answer and how evaluation finds regressions.
* RECOMMENDED — split the models. Routing is a small decision (which tools, what to ask), so a fast model
  does it; the expensive model only writes the final answer. Both are config, not code.
* OPTIONAL — long-term memory. Useful for preferences and context ("I run Greenville"); never for data facts,
  which must always come from Genie so they stay governed and current.

WHO GENIE RUNS AS (config supervisor.genie_auth)
* on_behalf_of_user (Apps user authorization, GA) — the calling app passes the signed-in person's Genie-scoped
  OAuth token with each question; Genie calls use it, so every answer respects THAT person's Unity Catalog
  permissions (their groups, the ABAC mask). Models, memory and tracing still run as the app's service principal.
  The token is used for Genie calls only and is never logged, traced or stored.
* service_principal — Genie runs as the app for everyone (one governed identity; simplest; no per-user view).

Nothing about KK's Parts is hardcoded: tools come from the Genie space registry and the prompt from
system_prompt.md, both written into supervisor_config.yaml by build_config.py (04_supervisor_agent/02_deploy_agent_app).
"""
from __future__ import annotations

import contextvars
import json
import queue
import re
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Iterator

import mlflow
from databricks.sdk import WorkspaceClient
from databricks_openai import DatabricksOpenAI
from mlflow.entities import SpanType

def _markdown_rows(table: str, limit: int = 25) -> list[dict]:
    """Agent mode returns each query result as a markdown table ("**title**\\n\\n| a | b |\\n| --- |..."). Rows as dicts,
    for the UI's "SQL and rows" panel and the run log's row counts."""
    lines = [l.strip() for l in table.splitlines() if l.strip().startswith("|")]
    if len(lines) < 2:
        return []
    cells = lambda l: [c.strip() for c in l.strip("|").split("|")]
    head = cells(lines[0])
    return [dict(zip(head, cells(l))) for l in lines[2:2 + limit]]


# Agent-mode tools other than SQL, named for people (Genie's file search over the volumes attached to the space)
GENIE_TOOLS = {"search_context_files": "the attached files (documents and approved notes)"}

# Genie reports where it is in answering; we turn its status codes into words a plant manager understands.
GENIE_STATUS = {
    "SUBMITTED": "queued",
    "FETCHING_METADATA": "reading the space's tables",
    "FILTERING_CONTEXT": "picking the relevant tables",
    "ASKING_AI": "writing the SQL",
    "PENDING_WAREHOUSE": "waiting for the SQL warehouse",
    "EXECUTING_QUERY": "running the query",
    "COMPLETED": "done",
}


def tool_name(domain_key: str) -> str:
    return f"ask_{domain_key}_genie"


def build_tools(genie_spaces: list[dict]) -> list[dict]:
    """One function-calling tool per Genie space. The model only sees name + description, so the
    description IS the routing rule — it comes straight from the Genie space's own description."""
    return [{
        "type": "function",
        "function": {
            "name": tool_name(s["domain_key"]),
            "description": f"Ask the '{s['title']}' Genie space (a domain expert). {s['description']}",
            "parameters": {
                "type": "object",
                "properties": {"question": {
                    "type": "string",
                    "description": "A complete, self-contained question for this domain (include machine/plant/"
                                   "supplier IDs and the time period). To use the domain's documents, say so, e.g. "
                                   "'according to the OEM manual...' or 'what does the contract say...'."}},
                "required": ["question"],
            },
        },
    } for s in genie_spaces]


def text_of(content) -> str:
    """Reasoning models may return content as blocks ({type: reasoning|text}); keep only the visible text."""
    if isinstance(content, list):
        return "".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text")
    return content or ""


class Foreman:
    """The supervisor. `run()` yields events; hosts turn them into SSE (server.py) or Responses items."""

    def __init__(self, config: dict, workspace_client: Callable[[], WorkspaceClient] = WorkspaceClient,
                 memory=None, runlog=None):
        self.cfg = config
        self.spaces = config["genie_spaces"]
        self.tools = build_tools(self.spaces)
        self.space_by_tool = {tool_name(s["domain_key"]): s for s in self.spaces}
        self.answer_llm = config["answer_llm"]
        self.router_llm = config.get("router_llm") or self.answer_llm
        self.max_iterations = int(config.get("max_iterations", 6))
        self.max_tool_rounds = int(config.get("max_tool_rounds", 2))   # rounds of Genie calls before we must answer
        self.genie_timeout_s = int(config.get("genie_timeout_seconds", 300))
        self.workspace_client = workspace_client          # who we call Databricks as (app SP, or the caller)
        self.memory = memory                              # memory.Memory or None (sessions + long-term memory)
        self.runlog = runlog                              # runlog.RunLog or None (the health page's run summaries)
        self.genie_auth = config.get("genie_auth") or "service_principal"
        self.genie_mode = config.get("genie_mode") or "agent"        # agent (Agent-mode API) | chat (Conversation API)

    # ------------------------------------------------------------------ Genie, one space
    def ask_genie(self, w: WorkspaceClient, space: dict, question: str, emit: Callable[[dict], None],
                  step_id: str) -> dict:
        """One question to one Genie space, in the mode config chooses (supervisor.genie_mode).

        agent (default) — Genie Agent mode (Agent-mode API, GA): Genie plans, runs several SQL queries and
            searches the files in the volumes attached to the space (documents + approved notes), then answers. Faster for questions that need documents or notes, and it never refuses them as "SQL only".
        chat — the Conversation API: one SQL answer per question. Kept for spaces without documents."""
        if self.genie_mode == "chat":
            return self.ask_genie_chat(w, space, question, emit, step_id)
        return self.ask_genie_agent(w, space, question, emit, step_id)

    def ask_genie_agent(self, w: WorkspaceClient, space: dict, question: str, emit: Callable[[dict], None],
                        step_id: str) -> dict:
        """Genie Agent mode: POST /api/2.0/genie/agents/{space_id}/responses, streamed (SSE). Each output item —
        reasoning, a query (function_call), its result (function_call_output), the answer (message) — becomes a live
        status in the UI, so people see "Genie is querying: App notes · S&OP review" instead of a spinner."""
        import requests
        with mlflow.start_span(name=f"genie · {space['title']}", span_type=SpanType.TOOL) as span:
            span.set_inputs({"space_id": space["space_id"], "question": question, "mode": "agent"})
            out = {"genie_space": space["title"], "status": "", "answer": "", "sql": [], "results": [], "error": None}
            calls, t0 = {}, time.time()

            def status(text):
                emit({"type": "step_update", "id": step_id, "status": text, "elapsed_s": round(time.time() - t0, 1)})

            try:
                body = {"input": [{"type": "message", "role": "user", "content": [{"type": "input_text", "text": question}]}]}
                headers = {**w.config.authenticate(), "Content-Type": "application/json", "Accept": "text/event-stream"}
                url = f"{w.config.host.rstrip('/')}/api/2.0/genie/agents/{space['space_id']}/responses"
                status("thinking")
                with requests.post(url, headers=headers, json=body, stream=True, timeout=(10, self.genie_timeout_s)) as r:
                    if r.status_code >= 400:
                        raise RuntimeError(f"{r.status_code} {r.text[:400]}")
                    for line in r.iter_lines(decode_unicode=True):
                        if not line or not line.startswith("data:"):
                            continue
                        ev = json.loads(line[5:])
                        kind, item = ev.get("type", ""), ev.get("item") or {}
                        it = item.get("type")
                        if kind == "response.output_item.added":
                            if it == "reasoning":
                                status("reasoning about the question")
                            elif it == "function_call":
                                args = json.loads(item.get("arguments") or "{}")
                                args.setdefault("title", GENIE_TOOLS.get(item.get("name"), item.get("name")))
                                args["tool"] = item.get("name")
                                calls[item.get("call_id")] = args
                                status(f"{'searching' if args['tool'] != 'execute_sql' else 'querying'}: {args['title']}")
                            elif it == "message":
                                status("writing its answer")
                            elif it and it != "function_call_output":
                                status(it.replace("_", " "))       # e.g. file search: shown as Genie names it
                        elif kind == "response.output_item.done":
                            if it == "function_call_output":
                                args = calls.get(item.get("call_id"), {})
                                table = str(item.get("output") or "")
                                out["sql"].append(args.get("sql", ""))
                                out["results"].append({"sql": args.get("sql", ""), "title": args.get("title", ""),
                                                       "tool": args.get("tool", "execute_sql"),
                                                       "rows": _markdown_rows(table), "table": table[:6000]})
                                status(f"got results: {args.get('title', '')}")
                            elif it == "message":
                                out["answer"] += "".join(c.get("text", "") for c in item.get("content", [])
                                                         if c.get("type") == "output_text")
                        elif kind in ("response.completed", "response.failed"):
                            resp = ev.get("response") or {}
                            out["status"] = resp.get("status", "").upper()
                            if kind == "response.failed":
                                out["error"] = str((resp.get("error") or {}).get("message") or resp.get("error"))[:500]
                            break
                if not out["status"]:
                    out.update(status="TIMEOUT", error=f"Genie didn't finish within {self.genie_timeout_s} s")
            except Exception as e:                        # never crash the conversation on one expert
                out["error"] = self._genie_error(str(e))
            span.set_outputs({k: out[k] for k in ("status", "answer", "sql", "error")}
                             | {"row_counts": [len(r["rows"]) for r in out["results"]]})
            return out

    def _genie_error(self, msg: str) -> str:
        reason = msg.split(" Config:")[0][:300]           # the SDK appends its config; keep only the reason
        if "required scopes" in msg:                     # OBO token issued before the app had the genie scope
            return ("Your sign-in doesn't include Genie access yet — reload the app and click "
                    f"Authorize to grant it. ({reason})")
        if any(t in msg for t in ("PERMISSION_DENIED", "does not have", "403", "not authorized")):
            return f"ACCESS DENIED: no access to this domain. ({reason})"
        return reason

    def ask_genie_chat(self, w: WorkspaceClient, space: dict, question: str, emit: Callable[[dict], None],
                       step_id: str) -> dict:
        """One question to one Genie space (Conversation API, GA). Polls fast (0.5 s, backing off to 1.5 s)
        and emits every status change, so the UI can say what Genie is doing right now."""
        with mlflow.start_span(name=f"genie · {space['title']}", span_type=SpanType.TOOL) as span:
            span.set_inputs({"space_id": space["space_id"], "question": question})
            api = w.api_client
            # results: one entry per query Genie ran. Genie often runs two for one question (the document search AND
            # a data query); keeping only the last one silently drops the documents — approved app notes included.
            out = {"genie_space": space["title"], "status": "", "answer": "", "sql": [], "results": [], "error": None}
            try:
                r = api.do("POST", f"/api/2.0/genie/spaces/{space['space_id']}/start-conversation",
                           body={"content": question})
                base = (f"/api/2.0/genie/spaces/{space['space_id']}/conversations/{r['conversation_id']}"
                        f"/messages/{r['message_id']}")
                t0, wait, last, m = time.time(), 0.5, None, {}
                while time.time() - t0 < self.genie_timeout_s:
                    m = api.do("GET", base)
                    status = m.get("status")
                    if status != last:
                        emit({"type": "step_update", "id": step_id, "status": GENIE_STATUS.get(status, status.lower()),
                              "elapsed_s": round(time.time() - t0, 1)})
                        last, wait = status, 0.5
                    if status in ("COMPLETED", "FAILED", "CANCELLED"):
                        break
                    time.sleep(wait)
                    wait = min(wait * 1.5, 1.5)
                out["status"] = m.get("status", "TIMEOUT")
                out["error"] = (m.get("error") or {}).get("error") if isinstance(m.get("error"), dict) else m.get("error")
                for att in m.get("attachments", []):
                    if att.get("text"):
                        out["answer"] += att["text"]["content"]
                    if att.get("query"):
                        out["sql"].append(att["query"]["query"])
                        out["answer"] += " " + (att["query"].get("description") or "")
                        res = api.do("GET", f"{base}/attachments/{att['attachment_id']}/query-result")
                        sr = res.get("statement_response", {})
                        cols = [c["name"] for c in sr.get("manifest", {}).get("schema", {}).get("columns", [])]
                        rows = [dict(zip(cols, row)) for row in sr.get("result", {}).get("data_array", [])[:25]]
                        out["results"].append({"sql": att["query"]["query"], "rows": rows})
            except Exception as e:                        # never crash the conversation on one expert
                msg = str(e)
                out["error"] = self._genie_error(msg)
            span.set_outputs({k: out[k] for k in ("status", "answer", "sql", "error")}
                             | {"row_counts": [len(r["rows"]) for r in out["results"]]})
            return out

    # ------------------------------------------------------------------ one model call (streamed)
    def call_llm(self, llm, model: str, messages: list[dict], emit: Callable[[dict], None] | None,
                 tools: bool = True) -> dict:
        """Stream a chat completion. Text tokens are emitted as they arrive (only when `emit` is given — the
        final answer); tool calls are accumulated and returned. Traced as an LLM span by mlflow.openai.autolog."""
        kwargs = {"model": model, "messages": messages if tools else self.as_evidence(messages),
                  "max_tokens": 4000, "stream": True}
        if tools:
            kwargs["tools"] = self.tools
        text, calls = [], {}
        for chunk in llm.chat.completions.create(**kwargs):
            if not chunk.choices:
                continue
            d = chunk.choices[0].delta
            piece = text_of(getattr(d, "content", None))
            if piece:
                text.append(piece)
                if emit:
                    emit({"type": "token", "text": piece})
            for tc in getattr(d, "tool_calls", None) or []:
                c = calls.setdefault(tc.index, {"id": "", "name": "", "arguments": ""})
                c["id"] = tc.id or c["id"]
                if tc.function and tc.function.name:
                    c["name"] = tc.function.name
                if tc.function and tc.function.arguments:
                    c["arguments"] += tc.function.arguments
        return {"text": "".join(text), "tool_calls": [calls[i] for i in sorted(calls)]}

    # ------------------------------------------------------------------ the loop
    def genie_client(self, w: WorkspaceClient, user_token: str | None) -> WorkspaceClient:
        """Who Genie runs as for this question (see WHO GENIE RUNS AS above)."""
        if self.genie_auth != "on_behalf_of_user":
            return w
        if not user_token:
            raise PermissionError("Genie runs on behalf of the signed-in user, but no user token came with this "
                                  "question. Open Foreman from the Andon app (it passes your token), or set "
                                  "supervisor.genie_auth: service_principal.")
        # host from the app's own config; auth_type pins the user's token even though the app's SP credentials are
        # also in the environment
        return WorkspaceClient(host=w.config.host, token=user_token, auth_type="pat")

    def run(self, question: str, *, history: list[dict] | None = None, context: str = "",
            session_id: str | None = None, user: str = "", genie_token: str | None = None) -> Iterator[dict]:
        """Answer one question. Yields events; the last one is {"type": "done", ...}.

        Tool calls run on worker threads and push their events onto a queue, so a Genie space's status shows
        up the moment it changes, even while other spaces are still working."""
        events: queue.Queue = queue.Queue()
        DONE = object()                                        # sentinel: the worker finished (no StopIteration games)

        # what the health page sees: filled in as the run goes, written once at the end (ok / error / stopped)
        rec = {"run_id": str(uuid.uuid4()), "session_id": session_id, "user": user, "question": question,
               "started": time.time(), "status": "ok", "steps": [], "router_llm": self.router_llm,
               "answer_llm": self.answer_llm, "genie_auth": self.genie_auth, "stopped": False}

        def worker():
            try:
                self._run(question, history or [], context, session_id, user, events.put, genie_token, rec)
            except Exception as e:                             # surface, don't hang the stream
                rec.update(status="error", error=str(e))
                events.put({"type": "error", "message": str(e)[:500]})
            finally:
                rec["duration_ms"] = int((time.time() - rec["started"]) * 1000)
                if rec["stopped"] and rec["status"] == "ok":
                    rec["status"] = "stopped"
                if self.runlog:
                    self.runlog.record(rec)
                events.put(DONE)

        ctx = contextvars.copy_context()                       # keep the caller's MLflow context in the thread
        threading.Thread(target=ctx.run, args=(worker,), daemon=True).start()
        try:
            while True:
                try:
                    ev = events.get(timeout=8)
                except queue.Empty:                            # quiet while Genie works: keep proxies from closing us
                    yield {"type": "heartbeat"}
                    continue
                if ev is DONE:
                    return
                yield ev
        except GeneratorExit:                                  # the client went away (Stop, closed tab, redeploy)
            rec["stopped"] = True
            raise

    def _run(self, question: str, history: list[dict], context: str, session_id: str | None, user: str,
             emit: Callable[[dict], None], genie_token: str | None = None, rec: dict | None = None) -> None:
        t0 = time.time()
        rec = rec if rec is not None else {"steps": []}
        session_id = session_id or str(uuid.uuid4())
        rec["session_id"] = session_id
        w = self.workspace_client()
        llm = DatabricksOpenAI(workspace_client=w)              # OpenAI SDK → Foundation Model API (Unity Gateway)
        genie_w = self.genie_client(w, genie_token)             # the user (OBO) or the app, per config
        as_user = genie_w is not w
        with mlflow.start_span(name="foreman", span_type=SpanType.AGENT) as root:
            root.set_inputs({"question": question, "context": context, "session_id": session_id})
            # Sessions view in MLflow groups traces by these two standard metadata keys.
            mlflow.update_current_trace(metadata={"mlflow.trace.session": session_id, "mlflow.trace.user": user or "unknown"},
                                        tags={"app": "kkparts-andon", "router_llm": self.router_llm, "answer_llm": self.answer_llm,
                                              "genie_auth": self.genie_auth})
            trace_id = mlflow.get_active_trace_id()
            if trace_id:
                rec["run_id"] = trace_id                       # the health page links each run to its trace
            emit({"type": "start", "session_id": session_id, "trace_id": trace_id})

            # 1 · memory: earlier turns of this session + what this user told us before
            remembered = []
            if self.memory:
                sid = self._step(emit, "memory", "Recalling earlier context")
                if not history:
                    history = self.memory.history(session_id)
                remembered = self.memory.recall(user, question)
                said = [f"{len(history) // 2} earlier turn(s) of this conversation"] if history else []
                said += [f"{len(remembered)} thing(s) you told me before"] if remembered else []
                emit({"type": "step_done", "id": sid, "label": "Recalled " + " and ".join(said) if said
                      else "New conversation, nothing to recall", "detail": remembered})

            system = self.cfg["system_prompt"]
            if remembered:
                system += "\n\n## What this user told you in earlier conversations (context, not data)\n" + \
                          "\n".join(f"- {m}" for m in remembered)
            user_msg = f"[App context — the user is looking at: {context}]\n{question}" if context else question
            messages = [{"role": "system", "content": system}, *history[-8:], {"role": "user", "content": user_msg}]

            answer = ""
            for i in range(self.max_iterations):
                # 2 · plan (first round: fast router model) / answer (strong model, streamed)
                model = self.router_llm if i == 0 else self.answer_llm
                may_ask = i < self.max_tool_rounds                   # after N rounds of experts, answer with what we have
                sid = self._step(emit, "plan", "Deciding which domain experts to ask" if i == 0
                                 else "Reviewing the evidence", model=model)
                msg = self.call_llm(llm, model, messages, emit=None if i == 0 else emit, tools=may_ask)
                if not msg["tool_calls"]:
                    if i == 0:                                 # the router would answer directly → let the strong model write it
                        emit({"type": "step_done", "id": sid, "label": "No data needed — answering directly"})
                        msg = self.call_llm(llm, self.answer_llm, messages, emit=emit, tools=False)
                    else:
                        emit({"type": "step_done", "id": sid, "label": "Writing the answer"})
                    answer = msg["text"]
                    break
                picked = [self.space_by_tool.get(c["name"], {}).get("title", c["name"]) for c in msg["tool_calls"]]
                emit({"type": "step_done", "id": sid, "label": f"Asking {', '.join(picked)}", "model": model})
                messages.append({"role": "assistant", "content": msg["text"],
                                 "tool_calls": [{"id": c["id"], "type": "function",
                                                 "function": {"name": c["name"], "arguments": c["arguments"]}}
                                                for c in msg["tool_calls"]]})

                # 3 · route: every chosen Genie space at once, each streaming its own status
                def call(c):
                    space = self.space_by_tool[c["name"]]
                    q = json.loads(c["arguments"] or "{}").get("question", question)
                    step = self._step(emit, "route", f"{space['title']} Genie" + (" (as you)" if as_user else ""),
                                      space=space["title"], domain=space["domain_key"], question=q, as_user=as_user)
                    started = time.time()
                    res = self.ask_genie(genie_w, space, q, emit, step)
                    rec["steps"].append({"space": space["title"], "seconds": round(time.time() - started, 1),
                                         "status": "error" if res["error"] else "done", "error": res["error"],
                                         "genie_status": res["status"],
                                         "rows": sum(len(r["rows"]) for r in res["results"])})
                    # documents and approved notes are files attached to the space; Agent mode searches them
                    files = [r for r in res["results"] if r.get("tool") == "search_context_files"]
                    data = [row for r in res["results"] if r.get("tool", "execute_sql") == "execute_sql" for row in r["rows"]]
                    notes = sorted(set(re.findall(r"NOTE-[0-9A-F]{8}", res["answer"].replace("\u2011", "-"))))
                    found = ((["searched the documents"] if files else [])
                             + ([f"used {len(notes)} approved note(s)"] if notes else [])
                             + ([f"{len(data)} row(s)"] if data or not (files or notes) else []))
                    emit({"type": "step_done", "id": step, "status": "done" if not res["error"] else "error",
                          "label": f"{space['title']}: " + (" + ".join(found) if not res["error"] else res["error"]),
                          "sql": res["sql"], "rows": [row for r in res["results"] for row in r["rows"]][:10],
                          "error": res["error"]})
                    evidence = {**res, "results": [{k: v for k, v in r.items() if k != "rows" or "table" not in r}
                                                   for r in res["results"]]}       # agent mode: the markdown table is the evidence
                    return json.dumps(evidence, default=str)[:20000]   # keep the model's context bounded

                # copy the trace context HERE (parent thread), one copy per task, so each Genie span nests under the run
                with ThreadPoolExecutor(max_workers=len(msg["tool_calls"])) as pool:
                    futures = [pool.submit(contextvars.copy_context().run, call, c) for c in msg["tool_calls"]]
                    results = [f.result() for f in futures]
                for c, result in zip(msg["tool_calls"], results):
                    messages.append({"role": "tool", "tool_call_id": c["id"], "content": result})
            else:
                answer = "I reached my step limit before finishing. Try a narrower question."
                emit({"type": "token", "text": answer})

            emit({"type": "answer", "text": answer})
            root.set_outputs({"answer": answer})
            if self.memory:                                   # store the turn; distill memories off the hot path
                self.memory.save_turn(session_id, user, question, answer, trace_id)
                threading.Thread(target=self.memory.remember, args=(llm, self.router_llm, user, session_id,
                                                                    question, trace_id), daemon=True).start()
            emit({"type": "done", "session_id": session_id, "trace_id": trace_id,
                  "elapsed_ms": int((time.time() - t0) * 1000)})

    @staticmethod
    def as_evidence(messages: list[dict]) -> list[dict]:
        """The conversation with tool calls folded into plain text, for an answer-only call.

        Why: when the model must answer now, we call it WITHOUT tools. A history that still contains tool calls then
        isn't valid for Claude, and `tool_choice="none"` makes Sonnet return only a reasoning block. So the experts'
        answers become one evidence message instead."""
        out, evidence = [], []
        for m in messages:
            if m["role"] == "tool":
                evidence.append(m["content"])
            elif m["role"] == "assistant" and m.get("tool_calls"):
                continue
            else:
                out.append(m)
        if evidence:
            out.append({"role": "user", "content": "Evidence from the domain experts you consulted (JSON, one per call):\n"
                        + "\n".join(evidence) + "\n\nAnswer my question above from this evidence now."})
        return out

    @staticmethod
    def _step(emit, kind: str, label: str, **extra) -> str:
        sid = uuid.uuid4().hex[:8]
        emit({"type": "step", "id": sid, "kind": kind, "label": label, "ts": time.time(), **extra})
        return sid
