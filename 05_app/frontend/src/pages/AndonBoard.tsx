// Andon Board — the home page: what needs a decision today, where it is, and how the operation is trending.
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { MessagesSquare } from "lucide-react";
import { api, type Insight } from "../api";
import { PageTitle, useForemanContext, useShell } from "../app";
import { Card, ErrorBox, Kpis, Loading, Pill, Section } from "../components/ui";
import { Chart, NetworkMap } from "../components/visuals";

const DOMAIN: Record<string, string> = { production: "Production", maintenance: "Maintenance", quality: "Quality", supply_chain: "Supply Chain" };

/** Where an issue lives: the explorer for physical things, the impact web for the rest. */
export function issueLink(i: Insight): string {
  const plant = i.plant_id || (i.line_id || "").split("-")[0];
  if (plant) {
    const p = new URLSearchParams({ plant, ...(i.line_id ? { line: i.line_id } : {}), ...(i.machine_id ? { machine: i.machine_id } : {}) });
    return `/explorer?${p}`;
  }
  return `/impact?node=${encodeURIComponent(i.machine_id || i.supplier_id || i.carrier_id || "")}`;
}

export default function AndonBoard() {
  const nav = useNavigate();
  const { openForeman } = useShell();
  const board = useQuery({ queryKey: ["board"], queryFn: api.board });
  const network = useQuery({ queryKey: ["network"], queryFn: api.network });
  const meta = useQuery({ queryKey: ["meta"], queryFn: api.meta, staleTime: Infinity });
  const [tab, setTab] = useState(0);
  useForemanContext("the Andon Board (enterprise overview)", board.data?.critical.slice(0, 3).map(i => i.ask) ?? []);

  if (board.error) return <ErrorBox error={board.error} />;
  const b = board.data;
  return (
    <>
      <PageTitle title="Andon Board" sub={b?.subtitle ?? " "} />
      {b ? <Kpis items={b.kpis} /> : <Loading height={110} />}

      <Section>Critical issues</Section>
      <div className="grid cols-4">
        {(b?.critical ?? [null, null, null, null]).map((i, n) => i ? (
          <section key={i.id} className="card" style={{ display: "flex", flexDirection: "column" }}>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <Pill tone="critical">{i.title.split(" · ")[0]}</Pill><Pill tone="navy">{DOMAIN[i.domain] ?? i.domain}</Pill>
            </div>
            <div className="clamp2" style={{ fontWeight: 800, color: "var(--navy)", fontSize: 17, margin: "14px 0 2px", lineHeight: 1.3, height: 44 }}>
              {i.title.split(" · ").slice(1).join(" · ") || i.title}</div>
            <div className="clamp2 redtxt" style={{ fontSize: 15, lineHeight: 1.4, height: 42 }}>{i.headline}</div>
            <div className="clamp5 muted" style={{ fontSize: 13, marginTop: 10, lineHeight: 1.55, height: 101 }}>{i.detail}</div>
            <div className="btns" style={{ marginTop: 14 }}>
              <button className="btn primary" onClick={() => nav(issueLink(i))}>Open</button>
              <button className="btn" onClick={() => openForeman(i.ask)}>Ask Foreman</button>
            </div>
          </section>
        ) : <Loading key={n} height={290} />)}
      </div>

      <Section>Supply network</Section>
      <div className="split">
        <Card title="Supplier → plant lanes" note={<><span style={{ color: "var(--red)" }}>●</span> contract breach · select a plant to open it</>}>
          {network.data ? <NetworkMap data={network.data} onPlant={id => nav(`/explorer?plant=${id}`)} /> : <Loading height={440} />}
        </Card>
        <Card title="Watch list" note={`${b?.watch.length ?? 0} items`} style={{ maxHeight: 520, overflow: "auto" }}>
          {b?.watch.map(i => (
            <div key={i.id} className="row">
              <span><Pill tone={i.severity}>{i.severity}</Pill>&nbsp; <b>{i.title}</b><br /><span className="muted">{i.headline}</span></span>
              <button className="btn small ghost" title="Ask Foreman" onClick={() => openForeman(i.ask)}><MessagesSquare size={16} /></button>
            </div>
          )) ?? <Loading />}
        </Card>
      </div>

      <Section>Performance</Section>
      <div className="tabs">
        {["Plant performance", "Quality & cost", ...(meta.data?.dashboard_url ? ["Dashboard"] : [])].map((t, n) =>
          <button key={t} className={tab === n ? "on" : ""} onClick={() => setTab(n)}>{t}</button>)}
      </div>
      {b && tab === 0 && <div className="grid cols-2"><Chart figure={b.charts.oee} /><Chart figure={b.charts.downtime} /></div>}
      {b && tab === 1 && <div className="grid cols-2"><Chart figure={b.charts.copq} /><Chart figure={b.charts.defects} /></div>}
      {tab === 2 && meta.data?.dashboard_url && <iframe title="Dashboard" src={meta.data.dashboard_url} style={{ width: "100%", height: 900, border: 0, borderRadius: 16 }} />}
    </>
  );
}
