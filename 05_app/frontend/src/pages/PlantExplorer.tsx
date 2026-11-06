// Plant Explorer — network → plant floor → line → work center (and suppliers at the receiving dock).
// Where you are lives in the URL (?plant=&line=&machine=&supplier=), so every view is linkable and the back button works.
import { useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft } from "lucide-react";
import { api, type Detail } from "../api";
import { PageTitle, useForemanContext } from "../app";
import { ActionPanel } from "../components/ActionPanel";
import { Card, DataTable, ErrorBox, InsightCard, Kpis, Loading } from "../components/ui";
import { Chart, NetworkMap, SceneCanvas } from "../components/visuals";

const DOT: Record<string, string> = { critical: "#D62839", high: "#F2A541", watch: "#F2A541", ok: "#2A9D8F" };

function Tables({ tables }: { tables: Detail["tables"] }) {
  const [t, setT] = useState(0);
  if (!tables.length) return null;
  if (tables.length === 1) return <Card title={tables[0].title} note={tables[0].note}><DataTable table={tables[0]} height={280} /></Card>;
  return (
    <Card>
      <div className="tabs">{tables.map((x, i) => <button key={i} className={t === i ? "on" : ""} onClick={() => setT(i)}>{x.title}</button>)}</div>
      <DataTable table={tables[t] ?? tables[0]} />
    </Card>
  );
}

function DetailView({ d, back }: { d: Detail; back?: () => void }) {
  const wide = d.charts.length === 3;
  return (
    <>
      <PageTitle eyebrow={d.eyebrow} title={d.title} sub={d.subtitle}
                 right={back && <button className="btn" onClick={back}><ArrowLeft size={15} />Back to plant</button>} />
      <Kpis items={d.kpis} />
      <div className="split" style={{ marginTop: 16 }}>
        <div className="stack">
          {d.charts.length >= 2
            ? <div className="grid cols-2">{d.charts.slice(0, 2).map((c, i) => <Chart key={i} figure={c} />)}</div>
            : d.charts.map((c, i) => <Chart key={i} figure={c} />)}
          {wide && <Chart figure={d.charts[2]} />}
          <Tables tables={d.tables} />
        </div>
        <div className="stack">
          {d.related.map(i => <InsightCard key={i.id} insight={i} />)}
          <ActionPanel entity={d.entity} allowed={d.actions} insightId={d.insight_id} defaults={d.defaults} />
        </div>
      </div>
    </>
  );
}

export default function PlantExplorer() {
  const nav = useNavigate();
  const [params, setParams] = useSearchParams();
  const plant = params.get("plant"), line = params.get("line"), machine = params.get("machine"), supplier = params.get("supplier");
  const plants = useQuery({ queryKey: ["plants"], queryFn: api.plants });
  const network = useQuery({ queryKey: ["network"], queryFn: api.network, enabled: !plant });
  const sceneQ = useQuery({ queryKey: ["scene", plant], queryFn: () => api.scene(plant!), enabled: !!plant });
  const [level, id] = supplier ? ["supplier", supplier] : machine ? ["machine", machine] : line ? ["line", line] : ["plant", plant];
  const detail = useQuery({ queryKey: ["detail", level, id], queryFn: () => api.detail(level as "plant", id!), enabled: !!id });

  // the floor highlights the line / machine in the URL (the camera flies there)
  const scene = useMemo(() => sceneQ.data && { ...sceneQ.data, focusLine: line, selected: machine }, [sceneQ.data, line, machine]);
  const go = (p: Record<string, string>) => setParams(p);
  const where = supplier ? `supplier ${supplier} (ships to plant ${plant})` : machine ? `work center ${machine} on line ${line}`
              : line ? `line ${line} at plant ${plant}` : plant ? `plant ${plant}` : "the plant network";
  useForemanContext(where, detail.data?.ask ?? [], detail.data?.entity);

  return (
    <>
      <div className="rail">
        <span className="lvl">Enterprise</span>
        <button className={`node ${!plant ? "here" : ""}`} onClick={() => go({})}>KK's Parts</button>
        {plant && <><span className="arrow">›</span><span className="lvl">Plant</span>
          <button className={`node ${!line && !supplier ? "here" : ""}`} onClick={() => go({ plant })}>{plant}</button></>}
        {line && <><span className="arrow">›</span><span className="lvl">Line</span>
          <button className={`node ${!machine ? "here" : ""}`} onClick={() => go({ plant: plant!, line })}>{line}</button></>}
        {machine && <><span className="arrow">›</span><span className="lvl">Work center</span><button className="node here">{machine}</button></>}
        {supplier && <><span className="arrow">›</span><span className="lvl">Supplier</span><button className="node here">{supplier}</button></>}
      </div>
      <div className="choices" style={{ margin: "8px 0 14px" }}>
        {plants.data?.map(p => (
          <button key={p.id} className={p.id === plant ? "on" : ""} onClick={() => go({ plant: p.id })}>
            <span className="statusdot" style={{ background: DOT[p.status] }} />{p.id} · {p.city} · {p.oee != null ? `${Math.round(p.oee * 100)}% OEE` : ""}
          </button>
        ))}
      </div>

      {!plant && (
        <>
          <PageTitle title="Plant Explorer" sub="Select a plant to view its lines and work centers." />
          <Card>{network.data ? <NetworkMap data={network.data} height={520} onPlant={id => go({ plant: id })} /> : <Loading height={520} />}</Card>
        </>
      )}

      {plant && (
        <>
          {scene ? <SceneCanvas scene={scene} onSelect={s => {
            if (s.kind === "machine") go({ plant, line: s.line || "", machine: s.id });
            else if (s.kind === "line") go({ plant, line: s.id });
            else if (s.kind === "plant") go({ plant });
            else if (s.kind === "supplier") go({ plant, supplier: s.id });
            else if (s.kind === "warehouse" && s.id.startsWith("DC")) nav(`/impact?node=${s.id}`);
          }} /> : <Loading height={610} />}
          {detail.error ? <ErrorBox error={detail.error} />
            : detail.data ? <DetailView d={detail.data} back={supplier ? () => go({ plant }) : undefined} /> : <Loading height={400} />}
        </>
      )}
    </>
  );
}
