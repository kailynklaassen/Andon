// The human-in-the-loop action panel. Generic on purpose: the backend describes each form (fields + options that come
// from the data), so adding an action type is a backend change only. Data corrections use a record picker whose every
// choice is a real record, column and value — the server resolves the exact cell on submit.
import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type ActionForm, type Entity, type Field } from "../api";
import { useShell } from "../app";
import { Card, Pill } from "./ui";

type Values = Record<string, unknown>;

function FieldInput({ f, value, set }: { f: Field; value: unknown; set: (v: unknown) => void }) {
  if (f.kind === "select")
    return <select value={String(value ?? "")} onChange={e => set(e.target.value)}>{f.options?.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}</select>;
  if (f.kind === "multiselect") {
    const cur = new Set((value as string[]) || []);
    return (
      <div className="choices">
        {f.options?.map(o => (
          <button type="button" key={o.value} className={cur.has(o.value) ? "on" : ""}
                  onClick={() => { cur.has(o.value) ? cur.delete(o.value) : cur.add(o.value); set([...cur]); }}>{o.label}</button>
        ))}
      </div>
    );
  }
  if (f.kind === "number") return <input type="number" value={String(value ?? 0)} onChange={e => set(Number(e.target.value))} />;
  if (f.kind === "date") return <input type="date" value={String(value ?? "")} onChange={e => set(e.target.value)} />;
  return <input type="text" value={String(value ?? "")} onChange={e => set(e.target.value)} />;
}

/** Record → field → current value (read-only, from the data) → corrected value (typed to the column). */
function CorrectionPicker({ entity, onChange }: { entity: Entity; onChange: (c: Values | null) => void }) {
  const recs = useQuery({ queryKey: ["records", entity], queryFn: () => api.records(entity) });
  const [ri, setRi] = useState(0);
  const rec = recs.data?.[ri];
  const fields = useQuery({ queryKey: ["recfields", rec?.dataset], queryFn: () => api.recordFields(rec!.dataset), enabled: !!rec });
  const [col, setCol] = useState("");
  const column = col && fields.data?.some(f => f.column === col) ? col : fields.data?.[0]?.column || "";
  const val = useQuery({ queryKey: ["recvalue", rec?.dataset, rec?.key, column], queryFn: () => api.recordValue(rec!.dataset, rec!.key, column),
                         enabled: !!rec && !!column });
  const [corrected, setCorrected] = useState<unknown>("");
  useEffect(() => { setCorrected(val.data?.kind === "select" ? val.data.options?.[0]?.value ?? "" : val.data?.default ?? ""); }, [val.data]);
  useEffect(() => {
    onChange(rec && column && corrected !== "" && corrected !== null
      ? { dataset: rec.dataset, key: rec.key, column, corrected_value: corrected } : null);
  }, [rec?.dataset, rec?.key, column, corrected]);   // eslint-disable-line react-hooks/exhaustive-deps

  if (recs.data && !recs.data.length) return <div className="muted">No correctable records for this item.</div>;
  const f: Field | null = val.data ? { name: "corrected", label: "Corrected value", kind: val.data.kind, options: val.data.options } : null;
  return (
    <>
      <label className="fld">Record
        <select value={ri} onChange={e => { setRi(Number(e.target.value)); setCol(""); }}>
          {recs.data?.map((r, i) => <option key={`${r.dataset}-${r.key}`} value={i}>{r.label}</option>)}
        </select>
      </label>
      <div className="two">
        <label className="fld">Field
          <select value={column} onChange={e => setCol(e.target.value)}>{fields.data?.map(x => <option key={x.column} value={x.column}>{x.label}</option>)}</select>
        </label>
        <label className="fld">Current value<input disabled value={val.data?.current ?? "…"} /></label>
      </div>
      {f && <label className="fld">Corrected value<FieldInput f={f} value={corrected} set={setCorrected} /></label>}
      {val.data && <div className="muted" style={{ fontFamily: "ui-monospace, Menlo, monospace", fontSize: 11.5 }}>{val.data.target}</div>}
    </>
  );
}

export function ActionPanel({ entity, allowed, insightId = "", defaults, preset, source = "human", details = "" }: {
  entity: Entity; allowed: string[]; insightId?: string; defaults?: Values; preset?: string; source?: "human" | "agent_suggested"; details?: string;
}) {
  const { toast } = useShell();
  const qc = useQueryClient();
  const types = useQuery({ queryKey: ["actionTypes"], queryFn: api.actionTypes, staleTime: Infinity });
  const opts = useMemo(() => [...new Set(preset ? [preset, ...allowed] : allowed)], [preset, allowed]);
  const [type, setType] = useState(opts[0]);
  useEffect(() => { if (!opts.includes(type)) setType(opts[0]); }, [opts, type]);
  const form = useQuery({ queryKey: ["form", type, entity, defaults], queryFn: () => api.form(type, entity, defaults), enabled: !!type });
  const [values, setValues] = useState<Values>({});
  const [title, setTitle] = useState("");
  const [priority, setPriority] = useState(source === "agent_suggested" ? "P1" : "P2");
  const [note, setNote] = useState(details);
  const [correction, setCorrection] = useState<Values | null>(null);
  useEffect(() => {                                   // reset the fields to the server's defaults when the form changes
    const f: ActionForm | undefined = form.data;
    if (!f) return;
    setValues(Object.fromEntries(f.fields.filter(x => x.kind !== "record").map(x => [x.name, x.default])));
    setTitle(f.title);
  }, [form.data]);
  const history = useQuery({ queryKey: ["ledger", entity.id], queryFn: () => api.ledger(entity.id) });
  const submit = useMutation({
    mutationFn: () => api.submit({ action_type: type, entity_type: entity.type, entity_id: entity.id, title, details: note, priority,
                                   payload: values, correction: type === "data_correction" ? correction : null, source, insight_id: insightId }),
    onSuccess: () => { toast(`${form.data?.label} submitted for ${entity.id}`); setNote(""); qc.invalidateQueries({ queryKey: ["ledger"] }); },
    onError: e => toast(e instanceof Error ? e.message : "Submit failed"),
  });
  const isCorrection = type === "data_correction";
  const ready = !!form.data && !submit.isPending && (!isCorrection || !!correction);

  return (
    <Card title="Actions" note={entity.id}>
      <div className="form">
        <div className="choices">
          {opts.map(o => <button key={o} type="button" className={o === type ? "on" : ""} onClick={() => setType(o)}>{types.data?.[o]?.label ?? o}</button>)}
        </div>
        {isCorrection && <CorrectionPicker key={`${entity.type}-${entity.id}`} entity={entity} onChange={setCorrection} />}
        <div className="two">
          {form.data?.fields.filter(f => f.kind !== "record").map(f => (
            <label key={f.name} className="fld" style={f.kind === "multiselect" ? { gridColumn: "1 / -1" } : undefined}>{f.label}
              <FieldInput f={f} value={values[f.name]} set={v => setValues(s => ({ ...s, [f.name]: v }))} />
            </label>
          ))}
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "3fr 1fr", gap: 10 }}>
          <label className="fld">Title<input value={title} onChange={e => setTitle(e.target.value)} /></label>
          <label className="fld">Priority<select value={priority} onChange={e => setPriority(e.target.value)}>{["P1", "P2", "P3"].map(p => <option key={p}>{p}</option>)}</select></label>
        </div>
        <label className="fld">Notes<textarea rows={3} value={note} placeholder="What you observed and what should change" onChange={e => setNote(e.target.value)} /></label>
        <div><button className="btn primary" disabled={!ready} onClick={() => submit.mutate()}>{submit.isPending ? "Submitting…" : "Submit"}</button></div>
      </div>
      {!!history.data?.rows.length && (
        <>
          <div className="section" style={{ margin: "18px 0 4px" }}>Recent actions</div>
          {history.data.rows.slice(0, 4).map(r => (
            <div key={r.action_id} className="row">
              <span><b style={{ color: "var(--navy)" }}>{r.title}</b><br /><span className="muted">{r.created_ts?.slice(0, 10)} · {r.created_by?.split("@")[0]}</span></span>
              <Pill tone="navy">{r.status}</Pill>
            </div>
          ))}
        </>
      )}
    </Card>
  );
}
