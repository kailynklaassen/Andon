// Action Ledger — every action submitted in the app, its review, and where it went in the lakehouse.
// Approve moves an action into the Lakebase outbox; the sync job writes value changes to bronze and notes to Genie.
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Download, RefreshCw } from "lucide-react";
import { api, type Action } from "../api";
import { PageTitle, useForemanContext, useShell } from "../app";
import { Card, ErrorBox, Loading, Pill, Section } from "../components/ui";

const STATUSES = ["Submitted", "Approved", "Rejected", "Done"];
const who = (email?: string | null) => (email ? email.split("@")[0] : "");

function change(payload: string): string {
  try {
    const p = JSON.parse(payload || "{}");
    if (!p.column) return "";
    return `${String(p.table).split(".").pop()} · ${p.key_column} = ${p.key_value} · ${p.column}: ${p.current_value} → ${p.corrected_value}`;
  } catch { return ""; }
}

function lakehouse(a: Action): string {
  if (!a.kind) return "";
  // notes: the domains the supervisor routed it to, read from where it landed (app_notes_<domain>/NOTE-….md)
  const routed = [...String(a.sync_ref || "").matchAll(/app_notes_([a-z_]+)\//g)].map(m => m[1].replace(/_/g, " "));
  const where = a.kind === "value_change" ? String(a.target).split(".").pop()
    : `${(routed.length ? routed : [String(a.target).replace(/_/g, " ")]).join(" + ")} Genie notes`;
  const state = ({ pending: "waiting for sync", synced: "synced", failed: "sync failed" } as Record<string, string>)[a.sync_status || ""] ?? a.sync_status;
  return `→ ${where} · ${state}`;
}

export default function ActionLedger() {
  const { toast } = useShell();
  const qc = useQueryClient();
  const ledger = useQuery({ queryKey: ["ledger"], queryFn: () => api.ledger(), refetchInterval: 15_000 });
  const types = useQuery({ queryKey: ["actionTypes"], queryFn: api.actionTypes, staleTime: Infinity });
  const [trail, setTrail] = useState<string>("");
  const events = useQuery({ queryKey: ["events", trail], queryFn: () => api.events(trail), enabled: !!trail });
  const review = useMutation({ mutationFn: ({ id, status }: { id: string; status: string }) => api.review(id, status),
                               onSuccess: () => qc.invalidateQueries({ queryKey: ["ledger"] }) });
  const sync = useMutation({ mutationFn: api.sync, onSuccess: r => toast(`Sync job started (run ${r.run_id}) — this page refreshes itself`),
                             onError: e => toast(e instanceof Error ? e.message : "Sync failed") });
  useForemanContext("the Action Ledger");

  if (ledger.error) return <ErrorBox error={ledger.error} />;
  if (!ledger.data) return <Loading height={400} />;
  const rows = ledger.data.rows;
  const pending = rows.filter(r => r.sync_status === "pending").length;
  const csv = () => {
    const cols = Object.keys(rows[0] || {});
    const body = [cols.join(","), ...rows.map(r => cols.map(c => JSON.stringify((r as unknown as Record<string, unknown>)[c] ?? "")).join(","))].join("\n");
    const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([body], { type: "text/csv" })); a.download = "kkparts_actions.csv"; a.click();
  };

  return (
    <>
      <PageTitle title="Action Ledger" sub="Actions submitted from the app, their review, and their sync to the lakehouse."
                 right={ledger.data.sync_job && (
                   <button className="btn" disabled={!pending || sync.isPending} onClick={() => sync.mutate()}><RefreshCw size={15} />Sync now</button>)} />
      {ledger.data.sync_job && <div className="muted" style={{ marginTop: -6, marginBottom: 6 }}>
        {pending ? `${pending} approved action(s) waiting for the lakehouse sync (runs on a schedule).` : "All approved actions are synced to the lakehouse."}</div>}
      {!rows.length && <Card><span className="muted">No actions yet. Actions submitted from a plant, line, work center, supplier or Foreman answer appear here for review.</span></Card>}
      {!!rows.length && (
        <div className="grid cols-4" style={{ alignItems: "start" }}>
          {STATUSES.map(s => {
            const col = rows.filter(r => r.status === s);
            return (
              <div key={s} className="stack">
                <Section>{s} · {col.length}</Section>
                {col.slice(0, 12).map(r => (
                  <section key={r.action_id} className="card" style={{ padding: "18px 20px" }}>
                    <div style={{ fontWeight: 800, color: "var(--navy)" }}>{r.title}</div>
                    <div style={{ margin: "8px 0", display: "flex", gap: 6 }}>
                      <Pill tone={r.priority === "P1" ? "critical" : "navy"}>{r.priority}</Pill>
                      <Pill tone="navy">{r.source === "agent_suggested" ? "Foreman" : "Manual"}</Pill>
                    </div>
                    <div className="muted">{r.entity_type} {r.entity_id}<br />{r.created_ts?.slice(0, 10)} · {who(r.created_by)}</div>
                    {change(r.payload) && <div className="mono" style={{ margin: "8px 0" }}>{change(r.payload)}</div>}
                    {lakehouse(r) && <div className="muted" style={{ color: r.sync_status === "failed" ? "var(--red)" : undefined, margin: "6px 0" }}>{lakehouse(r)}</div>}
                    {r.details && <div style={{ fontSize: 13, lineHeight: 1.55, margin: "6px 0" }}>{r.details.slice(0, 220)}</div>}
                    <div className="btns" style={{ marginTop: 8 }}>
                      {s === "Submitted" && <>
                        <button className="btn primary small" onClick={() => review.mutate({ id: r.action_id, status: "Approved" })}>Approve</button>
                        <button className="btn small" onClick={() => review.mutate({ id: r.action_id, status: "Rejected" })}>Reject</button></>}
                      {s === "Approved" && <button className="btn primary small" onClick={() => review.mutate({ id: r.action_id, status: "Done" })}>Mark done</button>}
                      {ledger.data.backend === "lakebase" && <button className="btn small ghost" onClick={() => setTrail(r.action_id)}>History</button>}
                    </div>
                  </section>
                ))}
              </div>
            );
          })}
        </div>
      )}

      {trail && (
        <>
          <Section>Audit trail · {rows.find(r => r.action_id === trail)?.title}</Section>
          <Card>
            {events.data ? (
              <table className="tbl"><thead><tr><th>When</th><th>Who</th><th>Event</th><th>Detail</th></tr></thead>
                <tbody>{events.data.map((e, i) => (
                  <tr key={i}><td>{new Date(e.event_ts).toLocaleString()}</td><td>{who(e.actor)}</td><td><Pill tone={e.event === "sync_failed" ? "critical" : e.event === "in_gold" || e.event === "searchable_in_genie" ? "ok" : "navy"}>{e.event === "in_gold" ? "live in gold" : e.event.replaceAll("_", " ")}</Pill></td>
                    <td className="muted" style={{ whiteSpace: "normal" }}>{e.detail}</td></tr>))}</tbody></table>
            ) : <Loading />}
          </Card>
        </>
      )}

      {!!rows.length && (
        <>
          <Section>All actions</Section>
          <Card>
            <div className="tblwrap" style={{ maxHeight: 360 }}>
              <table className="tbl">
                <thead><tr>{["Submitted", "By", "Action", "Entity", "Title", "Change", "Priority", "Status", "Lakehouse", "Landed in"].map(h => <th key={h}>{h}</th>)}</tr></thead>
                <tbody>{rows.map(r => (
                  <tr key={r.action_id}>
                    <td>{new Date(r.created_ts).toLocaleString("en-US", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}</td>
                    <td>{who(r.created_by)}</td><td>{types.data?.[r.action_type]?.label ?? r.action_type}</td><td>{r.entity_id}</td><td>{r.title}</td>
                    <td>{change(r.payload)}</td><td>{r.priority}</td><td>{r.status}</td><td>{lakehouse(r)}</td><td>{r.sync_ref ?? ""}</td>
                  </tr>))}</tbody>
              </table>
            </div>
            <div style={{ marginTop: 12 }}><button className="btn small" onClick={csv}><Download size={14} />Export CSV</button></div>
          </Card>
        </>
      )}
    </>
  );
}
