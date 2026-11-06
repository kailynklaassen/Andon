// App & agent health (admins) — is Foreman healthy, and who is having a bad time?
// Two sources side by side: Foreman's run log (every question, each Genie call's time and errors, Lakebase) and this
// app's own issues (API errors, Foreman unreachable, errors the browser hit). Every run links to its MLflow trace in
// Unity Catalog. Click a user or a session to filter everything to them.
import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ExternalLink, X } from "lucide-react";
import { api, type Kpi, type Run } from "../api";
import { PageTitle, useForemanContext } from "../app";
import { Card, ErrorBox, Kpis, Loading, Pill } from "../components/ui";

const WINDOWS = [{ h: 24, label: "Last 24 h" }, { h: 168, label: "Last 7 days" }, { h: 720, label: "Last 30 days" }];
const when = (iso: string) => new Date(iso).toLocaleString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
const who = (email?: string | null) => (email ? email.split("@")[0] : "—");
const short = (space: string) => space.replace(/^KK's Parts /, "");
const issues = (r: Run) => r.status === "error" || r.steps.some(s => s.status === "error");

export default function HealthPage() {
  const [hours, setHours] = useState(168);
  const [user, setUser] = useState("");
  const [session, setSession] = useState("");
  const health = useQuery({ queryKey: ["health", hours], queryFn: () => api.health(hours), refetchInterval: 30_000 });
  useForemanContext("the App & agent health page");

  const runs = useMemo(() => (health.data?.runs ?? []).filter(r => (!user || r.user === user) && (!session || r.session_id === session)),
                       [health.data, user, session]);
  const events = useMemo(() => (health.data?.app_events ?? []).filter(e => !user || e.user === user), [health.data, user]);

  if (health.error) return <ErrorBox error={health.error} />;
  if (!health.data) return <Loading height={400} />;
  const d = health.data, s = d.summary;
  const trace = (id: string) => (d.traces_url ? `${d.traces_url}?traceId=${encodeURIComponent(id)}` : "");
  const errRate = s && s.runs ? (100 * s.errors) / s.runs : 0;
  const kpis: Kpi[] = s ? [
    { label: "Questions asked", value: String(s.runs), compare: `${s.users.length} user(s)`, tone: "", spark: null, ref: null },
    { label: "Runs with an issue", value: `${errRate.toFixed(1)}%`, compare: `${s.errors} of ${s.runs} (failed, or a Genie call failed)`, tone: errRate > 5 ? "bad" : errRate > 0 ? "warn" : "good", spark: null, ref: null },
    { label: "Stopped by the user", value: String(s.stopped), compare: "closed or cancelled mid-answer", tone: s.stopped ? "warn" : "", spark: null, ref: null },
    { label: "Typical answer time", value: `${s.p50_s}s`, compare: `slowest 5%: ${s.p95_s}s+`, tone: s.p50_s > 90 ? "bad" : s.p50_s > 45 ? "warn" : "good", spark: null, ref: null },
    { label: "App issues", value: String(d.app_events.length), compare: "API errors, Foreman unreachable, browser errors", tone: d.app_events.length ? "warn" : "good", spark: null, ref: null },
  ] : [];
  const attention = runs.filter(issues);

  return (
    <>
      <PageTitle title="App & agent health" eyebrow="Admins"
                 sub="Every Foreman run and every app issue — by user and session, each linked to its MLflow trace."
                 right={<div className="btns">{WINDOWS.map(w => (
                   <button key={w.h} className={`btn small${w.h === hours ? " primary" : ""}`} onClick={() => setHours(w.h)}>{w.label}</button>))}</div>} />
      {(user || session) && (
        <div className="btns" style={{ marginBottom: 10 }}>
          {user && <button className="btn small" onClick={() => setUser("")}><X size={13} />user: {who(user)}</button>}
          {session && <button className="btn small" onClick={() => setSession("")}><X size={13} />session: {session.slice(0, 8)}</button>}
        </div>)}
      {d.foreman_error && <Card><div className="health-err">Couldn't read Foreman's run log: {d.foreman_error}</div></Card>}
      {s && <Kpis items={kpis} />}

      <div style={{ margin: "16px 0" }}>
        <Card title="Needs attention" note={<span className="muted">{attention.length} run(s) with an issue · {events.length} app issue(s)</span>}>
          {!attention.length && !events.length && <span className="muted">Nothing went wrong in this window.</span>}
          {!!attention.length && <RunTable runs={attention} trace={trace} onUser={setUser} onSession={setSession} />}
        </Card>
      </div>

      {s && (
        <div className="grid cols-2" style={{ alignItems: "start" }}>
          <Card title="By user">
            <div className="tblwrap" style={{ maxHeight: 320 }}><table className="tbl">
              <thead><tr><th>User</th><th>Questions</th><th>Conversations</th><th>Errors</th><th>Avg time</th><th>Last asked</th></tr></thead>
              <tbody>{s.users.map(u => (
                <tr key={u.user}>
                  <td><button className="linkish" onClick={() => setUser(u.user)}>{u.user || "unknown"}</button></td>
                  <td className="num">{u.runs}</td><td className="num">{u.sessions}</td>
                  <td className="num">{u.errors ? <Pill tone="critical">{u.errors}</Pill> : 0}</td>
                  <td className="num">{u.avg_s}s</td><td>{when(u.last)}</td>
                </tr>))}</tbody>
            </table></div>
          </Card>
          <Card title="Genie spaces (the agent's tools)" note={<span className="muted">Genie runs as: {d.genie_auth === "on_behalf_of_user" ? "the person asking" : "the Foreman app"}</span>}>
            <div className="tblwrap" style={{ maxHeight: 320 }}><table className="tbl">
              <thead><tr><th>Space</th><th>Calls</th><th>Errors</th><th>Avg</th><th>Slowest 5%</th></tr></thead>
              <tbody>{s.genie_spaces.map(g => (
                <tr key={g.space}><td>{short(g.space)}</td><td className="num">{g.calls}</td>
                  <td className="num">{g.errors ? <Pill tone="critical">{g.errors}</Pill> : 0}</td>
                  <td className="num">{g.avg_s}s</td><td className="num">{g.p95_s}s</td></tr>))}</tbody>
            </table></div>
          </Card>
        </div>)}

      <div style={{ margin: "16px 0" }}>
        <Card title="Recent runs" note={<span className="muted">{runs.length} shown · refreshes every 30 s</span>}>
          {runs.length ? <RunTable runs={runs} trace={trace} onUser={setUser} onSession={setSession} />
                       : <span className="muted">{d.agent_mode === "live" ? "No Foreman runs in this window." : "Foreman is in offline demo mode — there is no run log."}</span>}
        </Card>
      </div>

      <div style={{ margin: "16px 0" }}>
        <Card title="App issues" note={<span className="muted">from this app: API errors, Foreman unreachable, errors in the browser</span>}>
          {!events.length ? <span className="muted">No app issues in this window.</span> : (
            <div className="tblwrap" style={{ maxHeight: 360 }}><table className="tbl">
              <thead><tr><th>When</th><th>User</th><th>Kind</th><th>Where</th><th>What happened</th></tr></thead>
              <tbody>{events.map((e, i) => (
                <tr key={i}><td>{when(e.event_ts)}</td>
                  <td><button className="linkish" onClick={() => setUser(e.user)}>{who(e.user)}</button></td>
                  <td><Pill tone={e.kind === "client_error" ? "watch" : "critical"}>{e.kind.replace(/_/g, " ")}</Pill></td>
                  <td>{e.route}</td><td className="health-err">{e.message}</td></tr>))}</tbody>
            </table></div>)}
        </Card>
      </div>

      {d.trace_tables && (
        <Card title="Query the traces yourself">
          <div className="muted" style={{ marginBottom: 6 }}>Every span of every run is a row in Unity Catalog — use it from SQL, notebooks, dashboards or Genie:</div>
          <pre style={{ background: "var(--mist)", padding: 10, borderRadius: 8, fontSize: 12, whiteSpace: "pre-wrap" }}>{`SELECT * FROM ${d.trace_tables} ORDER BY start_time_unix_nano DESC LIMIT 100`}</pre>
          {d.traces_url && <a href={d.traces_url} target="_blank" rel="noreferrer"><ExternalLink size={12} /> Open the experiment in MLflow</a>}
        </Card>)}
    </>
  );
}

function RunTable({ runs, trace, onUser, onSession }: { runs: Run[]; trace: (id: string) => string;
                                                        onUser: (u: string) => void; onSession: (s: string) => void }) {
  return (
    <div className="tblwrap" style={{ maxHeight: 460 }}><table className="tbl">
      <thead><tr><th>When</th><th>User</th><th>Conversation</th><th>Question</th><th>Status</th><th>Time</th><th>Genie calls</th><th>Trace</th></tr></thead>
      <tbody>{runs.map(r => (
        <tr key={r.run_id}>
          <td>{when(r.started_ts)}</td>
          <td><button className="linkish" onClick={() => onUser(r.user)}>{who(r.user)}</button></td>
          <td><button className="linkish" onClick={() => onSession(r.session_id)} title={r.session_id}>{(r.session_id || "").slice(0, 8)}</button></td>
          <td style={{ maxWidth: 340 }}>{r.question}{r.error && <div className="health-err">{r.error}</div>}
            {r.steps.filter(st => st.error).map((st, i) => <div key={i} className="health-err">{short(st.space)}: {st.error}</div>)}</td>
          <td><Pill tone={r.status === "ok" ? (issues(r) ? "watch" : "ok") : r.status === "stopped" ? "watch" : "critical"}>{r.status}</Pill></td>
          <td className="num">{r.duration_ms ? `${(r.duration_ms / 1000).toFixed(0)}s` : "—"}</td>
          <td><div className="health-steps">{r.steps.map((st, i) => (
            <span key={i} className={st.status === "error" ? "error" : ""} title={st.error || `${st.rows} row(s)`}>
              {short(st.space)} · {st.seconds}s{st.status === "error" ? " · error" : ""}</span>))}</div></td>
          <td>{/^(tr-|trace:)/.test(r.run_id) && trace(r.run_id)
            ? <a href={trace(r.run_id)} target="_blank" rel="noreferrer" title={r.run_id}><ExternalLink size={12} /> open</a> : "—"}</td>
        </tr>))}</tbody>
    </table></div>
  );
}
