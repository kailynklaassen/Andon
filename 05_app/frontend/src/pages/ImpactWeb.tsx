// Impact Web — how one problem propagates. Click a node to trace its upstream causes and downstream effects; the
// selected node's evidence, trend and actions sit underneath the graph.
import { useEffect, useMemo } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { X } from "lucide-react";
import { api } from "../api";
import { PageTitle, useForemanContext, useShell } from "../app";
import { ActionPanel } from "../components/ActionPanel";
import { Card, ErrorBox, Loading, Pill, Section } from "../components/ui";
import { Chart, SceneCanvas } from "../components/visuals";

export default function ImpactWeb() {
  const nav = useNavigate();
  const { openForeman } = useShell();
  const [params, setParams] = useSearchParams();
  const graph = useQuery({ queryKey: ["graph"], queryFn: api.graph });
  const cleared = params.get("node") === "";
  const selected = params.get("node") || (cleared ? null : graph.data?.issues[0]?.target ?? null);   // open on the top issue
  const node = useQuery({ queryKey: ["node", selected], queryFn: () => api.node(selected!), enabled: !!selected });
  useEffect(() => { if (graph.data && !params.has("node") && selected) setParams({ node: selected }, { replace: true }); }, [graph.data]);   // eslint-disable-line react-hooks/exhaustive-deps

  const scene = useMemo(() => graph.data && ({ type: "web", sceneId: "impact-web", height: 500, virtualHeight: 700, columns: graph.data.columns,
    nodes: graph.data.nodes, edges: graph.data.edges, selected, eyebrow: "",
    title: `${graph.data.nodes.length} entities · ${graph.data.edges.length} relationships`,
    help: "Click to trace · drag to move · Ctrl/⌘ + scroll to zoom · double-click to reset" }), [graph.data, selected]);
  const n = node.data;
  useForemanContext(n ? `${n.node.kindLabel.replace(/s$/, "").toLowerCase()} ${n.node.name} (${n.node.id}) on the Impact Web` : "the Impact Web",
                    n ? [n.ask] : [], n?.entity);

  if (graph.error) return <ErrorBox error={graph.error} />;
  return (
    <>
      <PageTitle title="Impact Web" sub="Relationships across suppliers, operations, quality, logistics and customers." />
      <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap", marginBottom: 12 }}>
        <span className="eyebrow">Trace an issue</span>
        {graph.data?.issues.map(i => (
          <button key={i.id} className={`btn small ${i.target === selected ? "primary" : ""}`} onClick={() => setParams({ node: i.target ?? "" })}>{i.title}</button>
        ))}
        {selected && <button className="btn small ghost" onClick={() => setParams({ node: "" })}><X size={14} />Clear</button>}
      </div>
      {scene ? <SceneCanvas scene={scene} onSelect={s => setParams({ node: s.id || "" })} /> : <Loading height={500} />}

      <Section>{n ? `Selected · ${n.node.kindLabel.replace(/s$/, "").toLowerCase()}` : "Selected"}</Section>
      {!selected && <Card><span className="muted">Select a node on the graph, or an issue above, to see its details, trend and actions here.</span></Card>}
      {selected && !n && (node.error ? <ErrorBox error={node.error} /> : <Loading height={300} />)}
      {n && (
        <div className="grid" style={{ gridTemplateColumns: n.chart ? "minmax(0,1.05fr) minmax(0,1.45fr) minmax(0,1.1fr)" : "minmax(0,1.4fr) minmax(0,1.1fr)", alignItems: "start" }}>
          <Card>
            <div style={{ fontWeight: 800, color: "var(--navy)", fontSize: 20, marginBottom: 4 }}>{n.node.name}</div>
            <div className="muted" style={{ fontSize: 13, lineHeight: 1.5 }}>{n.node.tip}</div>
            {n.related.map(i => (
              <div key={i.id} style={{ marginTop: 12 }}>
                <Pill tone={i.severity}>{i.severity}</Pill>
                <div className="redtxt" style={{ margin: "8px 0 4px" }}>{i.headline}</div>
                <div className="muted" style={{ fontSize: 13, lineHeight: 1.55 }}>{i.detail}</div>
              </div>
            ))}
            <div style={{ fontSize: 13, lineHeight: 1.55, margin: "12px 0" }}><b>Connected ({n.neighbors.length})</b><br />
              {n.neighbors.slice(0, 12).map(x => x.name).join(", ")}</div>
            <div className="btns">
              {n.explore && <button className="btn primary" onClick={() => nav(`/explorer?${new URLSearchParams(n.explore!)}`)}>Open in explorer</button>}
              <button className="btn" onClick={() => openForeman(n.ask)}>Ask Foreman</button>
            </div>
          </Card>
          {n.chart && <Chart figure={n.chart} height={470} />}
          <ActionPanel entity={n.entity} allowed={n.actions} insightId={n.insight_id} defaults={n.defaults} />
        </div>
      )}
    </>
  );
}
