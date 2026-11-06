// Foreman chat — used full-page and in the drawer. The point of this component: never just "loading".
// Every agent event becomes a visible step (recall → decide → each Genie space's live status → answer), the answer
// streams token by token, and every answer links to its MLflow trace.
import { useEffect, useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Brain, CircleStop, ExternalLink, MessagesSquare, Plus, Route, Search, X } from "lucide-react";
import { api, streamForeman, type AgentEvent } from "../api";
import { useShell } from "../app";
import { ActionPanel } from "./ActionPanel";

interface Step { id: string; kind: string; label: string; status: "running" | "done" | "error"; live?: string; question?: string;
  sql?: string[]; rows?: Record<string, unknown>[]; detail?: string[]; started: number; ended?: number }
interface Message { role: "user" | "assistant"; text: string; steps?: Step[]; trace_id?: string | null; elapsed_ms?: number;
  running?: boolean; error?: string; actions?: string[]; demo?: boolean }

const SESSION_KEY = "foreman-session";
const ICON = { memory: Brain, plan: Route, route: Search } as const;

function StepList({ steps }: { steps: Step[] }) {
  return (
    <div className="steps">
      {steps.map(s => {
        const Icon = ICON[s.kind as keyof typeof ICON] ?? Route;
        const secs = (((s.ended ?? Date.now()) - s.started) / 1000).toFixed(1);
        return (
          <div key={s.id} className={`step ${s.status}`}>
            <span className="lbl"><Icon size={13} style={{ verticalAlign: -2, marginRight: 5 }} />{s.label}</span>
            {s.status === "running" && s.live && <span className="st">· {s.live}</span>}
            {s.kind === "route" && <span className="st">{secs}s</span>}
            {s.question && <div className="q">“{s.question}”</div>}
            {s.detail && s.detail.length > 0 && <div className="q">{s.detail.join(" · ")}</div>}
            {(s.sql?.length || s.rows?.length) ? (
              <details><summary>SQL and rows</summary>
                {s.sql?.map((q, i) => <pre key={i}>{q}</pre>)}
                {s.rows && s.rows.length > 0 && <pre>{JSON.stringify(s.rows.slice(0, 5), null, 1)}</pre>}
              </details>
            ) : null}
          </div>
        );
      })}
    </div>
  );
}

export function ForemanChat({ initialQuestion, onClose, compact = false }: { initialQuestion?: string; onClose?: () => void; compact?: boolean }) {
  const { context, seeds, entity } = useShell();
  const qc = useQueryClient();
  const info = useQuery({ queryKey: ["foremanInfo"], queryFn: api.foremanInfo, staleTime: 300_000 });
  const types = useQuery({ queryKey: ["actionTypes"], queryFn: api.actionTypes, staleTime: Infinity });
  const meta = useQuery({ queryKey: ["meta"], queryFn: api.meta, staleTime: Infinity });
  // Genie runs as you (on-behalf-of-user) — but only once you've granted the app Genie access
  const needsGenieConsent = info.data?.genie_auth === "on_behalf_of_user" && meta.data?.genie_access === false;
  const [session, setSession] = useState<string | null>(() => localStorage.getItem(SESSION_KEY));
  const [msgs, setMsgs] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [pending, setPending] = useState<{ type: string; summary: string } | null>(null);
  const abort = useRef<AbortController | null>(null);
  const bottom = useRef<HTMLDivElement>(null);
  const [, tick] = useState(0);

  // the conversation survives reloads: the agent stores it server-side by session id (Lakebase)
  const past = useQuery({ queryKey: ["turns", session], queryFn: () => api.turns(session!), enabled: !!session && !!info.data?.memory });
  useEffect(() => {
    if (past.data && !msgs.length) setMsgs(past.data.map(t => ({ role: t.role, text: t.content, trace_id: t.trace_id })));
  }, [past.data]);   // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { bottom.current?.scrollIntoView({ behavior: "smooth" }); }, [msgs]);
  useEffect(() => { if (!busy) return; const t = window.setInterval(() => tick(n => n + 1), 500); return () => window.clearInterval(t); }, [busy]);
  const asked = useRef(false);                        // StrictMode runs effects twice in dev: ask the opening question once
  // A question seeded from a page ("Ask Foreman about this machine") is a new topic: start a fresh conversation, so
  // the agent doesn't recall an unrelated earlier thread (and the turns stay grouped by topic in the session list).
  useEffect(() => { if (initialQuestion && !asked.current) { asked.current = true; newConversation(); ask(initialQuestion, null); } }, []);   // eslint-disable-line react-hooks/exhaustive-deps

  function update(fn: (m: Message) => Message) {
    setMsgs(ms => { const out = [...ms]; out[out.length - 1] = fn(out[out.length - 1]); return out; });
  }

  async function ask(question: string, sessionId: string | null = session) {   // sessionId: null = start a new conversation
    if (!question.trim() || busy) return;
    setInput(""); setBusy(true); setPending(null);
    setMsgs(ms => [...ms, { role: "user", text: question }, { role: "assistant", text: "", steps: [], running: true }]);
    const ctrl = new AbortController(); abort.current = ctrl;
    const t0 = Date.now();
    const on = (e: AgentEvent) => {
      if (e.type === "start") {
        setSession(e.session_id); localStorage.setItem(SESSION_KEY, e.session_id);
        update(m => ({ ...m, trace_id: e.trace_id, demo: e.demo }));
      } else if (e.type === "step") {
        update(m => ({ ...m, steps: [...(m.steps || []), { id: e.id, kind: e.kind, label: e.label, status: "running", question: e.question, started: Date.now() }] }));
      } else if (e.type === "step_update") {
        update(m => ({ ...m, steps: m.steps?.map(s => (s.id === e.id ? { ...s, live: e.status } : s)) }));
      } else if (e.type === "step_done") {
        update(m => ({ ...m, steps: m.steps?.map(s => (s.id === e.id ? { ...s, label: e.label || s.label, status: e.error ? "error" : "done",
                                                                       sql: e.sql, rows: e.rows, detail: e.detail, ended: Date.now() } : s)) }));
      } else if (e.type === "token") {
        update(m => ({ ...m, text: m.text + e.text }));
      } else if (e.type === "answer") {
        update(m => ({ ...m, text: e.text }));
      } else if (e.type === "done") {
        update(m => ({ ...m, running: false, elapsed_ms: e.elapsed_ms, trace_id: e.trace_id ?? m.trace_id }));
      } else if (e.type === "error") {
        update(m => ({ ...m, running: false, error: e.message }));
        api.reportError(`Foreman error: ${e.message}`, "/foreman", { question: question.slice(0, 300) });
      }
    };
    try {
      await streamForeman({ question, context, session_id: sessionId }, on, ctrl.signal);
    } catch (err) {
      if (!ctrl.signal.aborted) {
        const message = err instanceof Error ? err.message : String(err);
        update(m => ({ ...m, running: false, error: message }));
        api.reportError(`Foreman stream failed: ${message}`, "/foreman", { question: question.slice(0, 300) });
      }
    } finally {
      update(m => ({ ...m, running: false, elapsed_ms: m.elapsed_ms ?? Date.now() - t0 }));
      setBusy(false); abort.current = null;
      api.suggest(question, context).then(a => update(m => ({ ...m, actions: a }))).catch(() => undefined);
      qc.invalidateQueries({ queryKey: ["memories"] });
      qc.invalidateQueries({ queryKey: ["sessions"] });           // a new conversation shows up under "Recent conversations"
    }
  }

  function stop() {
    abort.current?.abort();
    update(m => ({ ...m, running: false, error: "Stopped.",
                   steps: m.steps?.map(s => (s.status === "running" ? { ...s, status: "error", live: "stopped" } : s)) }));
    setBusy(false);
  }
  function newConversation() { localStorage.removeItem(SESSION_KEY); setSession(null); setMsgs([]); setPending(null); }
  const traceUrl = info.data?.traces_url;

  return (
    <div style={{ display: "flex", flexDirection: "column", height: compact ? "100%" : "calc(100vh - 230px)", minHeight: 480 }}>
      <div className={compact ? "dhead" : ""} style={compact ? undefined : { display: "flex", alignItems: "center", gap: 12, marginBottom: 12 }}>
        <MessagesSquare size={20} color="#D62839" />
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: 800, color: "var(--navy)", fontSize: 17 }}>Foreman</div>
          <div className="muted">{context ? `Looking at ${context}` : "Ask about any plant, line, machine, supplier, carrier or customer."}
            {info.data?.mode === "demo" && " · offline demo answers"}</div>
        </div>
        <button className="btn small" onClick={newConversation} title="Start a new conversation"><Plus size={14} />New</button>
        {onClose && <button className="btn small ghost" onClick={onClose} aria-label="Close"><X size={16} /></button>}
      </div>

      <div className={compact ? "dbody" : ""} style={compact ? undefined : { flex: 1, overflow: "auto" }}>
        <div className="chat">
          {needsGenieConsent && (
            <div className="err" style={{ marginBottom: 10 }}>
              <b>Foreman asks Genie as you, and you haven't granted this app Genie access yet.</b> Your sign-in to Andon was
              authorized before it asked for Genie. Open Andon in a private window, sign in and click <b>Authorize</b> on the
              consent screen (it now lists Genie), then come back. <a href="/api/auth/check" target="_blank" rel="noreferrer">Check my access</a>
            </div>)}
          {!msgs.length && (
            <div className="card" style={{ padding: 16 }}>
              <div className="eyebrow" style={{ marginBottom: 8 }}>Suggested questions</div>
              <div className="stack" style={{ gap: 8 }}>
                {(seeds.length ? seeds : ["Why is Greenville Gearbox Assembly producing so much less than earlier in the year?",
                  "What's going on with Brightline Castings and what should we do?", "Which plant had the lowest OEE in FY26 Q4?"]).map(q => (
                  <button key={q} className="btn" style={{ justifyContent: "flex-start", textAlign: "left" }} onClick={() => ask(q)}>{q}</button>))}
              </div>
            </div>
          )}
          {msgs.map((m, i) => m.role === "user" ? <div key={i} className="msg user">{m.text}</div> : (
            <div key={i} className="msg">
              {m.steps && m.steps.length > 0 && <StepList steps={m.steps} />}
              {m.running && !m.text && <div className="muted">Working… {(((Date.now()) - (m.steps?.[0]?.started ?? Date.now())) / 1000).toFixed(0)}s</div>}
              {m.text && <div className="md"><ReactMarkdown remarkPlugins={[remarkGfm]}>{m.text}</ReactMarkdown></div>}
              {m.error && <div className="err" style={{ marginTop: 8 }}>{m.error}</div>}
              {!m.running && (m.elapsed_ms || m.trace_id) && (
                <div className="muted" style={{ marginTop: 10, display: "flex", gap: 12, flexWrap: "wrap", alignItems: "center" }}>
                  {m.elapsed_ms ? <span>{(m.elapsed_ms / 1000).toFixed(1)}s</span> : null}
                  {m.trace_id && (traceUrl
                    ? <a href={`${traceUrl}?traceId=${encodeURIComponent(m.trace_id)}`} target="_blank" rel="noreferrer" title={m.trace_id}><ExternalLink size={12} /> MLflow trace {m.trace_id.slice(0, 14)}…</a>
                    : <span title={m.trace_id}>trace {m.trace_id.slice(0, 14)}…</span>)}
                  {m.demo && <span>offline demo</span>}
                </div>
              )}
              {!m.running && !!m.actions?.length && (
                <div className="btns" style={{ marginTop: 10 }}>
                  {m.actions.map(a => <button key={a} className="btn small" onClick={() => setPending({ type: a, summary: m.text.slice(0, 600) })}>{types.data?.[a]?.label ?? a.replace(/_/g, " ")}</button>)}
                </div>
              )}
            </div>
          ))}
          {pending && <ActionPanel entity={entity} allowed={[pending.type, "comment"]} preset={pending.type} source="agent_suggested" details={pending.summary} />}
          <div ref={bottom} />
        </div>
      </div>

      <div className="ask" style={compact ? undefined : { borderRadius: 14, border: "1px solid var(--line)", marginTop: 12 }}>
        <textarea rows={1} value={input} placeholder="Ask Foreman about anything you see…" onChange={e => setInput(e.target.value)}
                  onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); ask(input); } }} />
        {busy ? <button className="btn" onClick={stop}><CircleStop size={16} />Stop</button>
              : <button className="btn primary" disabled={!input.trim()} onClick={() => ask(input)}>Ask</button>}
      </div>
    </div>
  );
}
