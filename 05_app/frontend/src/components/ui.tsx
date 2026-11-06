// Small building blocks: KPI tiles with sparklines, pills, cards, tables, loading and error states.
import type { ReactNode } from "react";
import type { Column, Insight, Kpi, Table } from "../api";
import { useShell } from "../app";

export function Spark({ values, color, target }: { values: number[]; color: string; target?: number | null }) {
  const vals = values.filter(v => Number.isFinite(v));
  if (vals.length < 2) return null;
  const w = 78, h = 30;
  const lo = Math.min(...vals, ...(target ? [target] : [])), hi = Math.max(...vals, ...(target ? [target] : []));
  const x = (i: number) => (i / (vals.length - 1)) * w;
  const y = (v: number) => h - 3 - ((v - lo) / (hi - lo || 1)) * (h - 6);
  const pts = vals.map((v, i) => `${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(" ");
  const last = vals[vals.length - 1];
  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`}>
      {target != null && <line x1={0} x2={w} y1={y(target)} y2={y(target)} stroke="#8FA3BF" strokeDasharray="2 3" strokeWidth={1} />}
      <polyline points={pts} fill="none" stroke={color} strokeWidth={1.8} strokeLinejoin="round" />
      <circle cx={x(vals.length - 1)} cy={y(last)} r={2.6} fill={target != null && last < target ? "#D62839" : color} />
    </svg>
  );
}

export function Kpis({ items }: { items: Kpi[] }) {
  if (!items.length) return null;
  return (
    <div className="kpis">
      {items.map(k => (
        <div key={k.label} className={`kpi ${k.tone}`}>
          <div className="lbl">{k.label}</div>
          <div className="val">{k.value}</div>
          <div className="cmp">{k.compare}</div>
          {k.spark && <Spark values={k.spark} color={k.tone === "bad" ? "#D62839" : "#0A1F44"} target={k.ref} />}
        </div>
      ))}
    </div>
  );
}

export const Pill = ({ tone, children }: { tone: string; children: ReactNode }) => <span className={`pill ${tone}`}>{children}</span>;

export function Card({ title, note, children, style }: { title?: ReactNode; note?: ReactNode; children: ReactNode; style?: React.CSSProperties }) {
  return (
    <section className="card" style={style}>
      {(title || note) && <div className="cardhead"><span className="t">{title}</span><span className="s">{note}</span></div>}
      {children}
    </section>
  );
}

export const Section = ({ children }: { children: ReactNode }) => <div className="section">{children}</div>;

export function Loading({ height = 120 }: { height?: number }) {
  return <div className="skeleton" style={{ height }} />;
}

export function ErrorBox({ error }: { error: unknown }) {
  return <div className="err">Couldn't load this: {error instanceof Error ? error.message : String(error)}</div>;
}

const money = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });
export function fmt(v: unknown, format: string): string {
  if (v === null || v === undefined || v === "") return "—";
  if (format === "money" && typeof v === "number") return money.format(v);
  if (format === "hours" && typeof v === "number") return v.toFixed(1);
  if (format === "mms" && typeof v === "number") return `${v.toFixed(2)} mm/s`;
  if (format === "pct" && typeof v === "number") return `${(v * 100).toFixed(1)}%`;
  if (format === "date" && typeof v === "string") return new Date(v).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
  if (format === "datetime" && typeof v === "string")
    return new Date(v).toLocaleString("en-US", { month: "short", day: "numeric", year: "numeric", hour: "2-digit", minute: "2-digit" });
  if (typeof v === "number") return Number.isInteger(v) ? v.toLocaleString() : v.toFixed(2);
  return String(v);
}

export function DataTable({ table, height = 320 }: { table: Table; height?: number }) {
  return (
    <div className="tblwrap" style={{ maxHeight: height }}>
      <table className="tbl">
        <thead><tr>{table.columns.map((c: Column) => <th key={c.key}>{c.label}</th>)}</tr></thead>
        <tbody>
          {table.rows.map((r, i) => (
            <tr key={i}>
              {table.columns.map(c => {
                const v = r[c.key];
                if (c.format === "status") return <td key={c.key}><Pill tone={String(v)}>{String(v)}</Pill></td>;
                return <td key={c.key} className={typeof v === "number" ? "num" : ""}>{fmt(v, c.format)}</td>;
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function InsightCard({ insight }: { insight: Insight }) {
  const { openForeman } = useShell();
  return (
    <Card title={insight.title} note={<Pill tone={insight.severity}>{insight.severity}</Pill>}>
      <div className="redtxt" style={{ margin: "2px 0 6px" }}>{insight.headline}</div>
      <div className="muted" style={{ fontSize: 13, lineHeight: 1.55 }}>{insight.detail}</div>
      <div style={{ marginTop: 12 }}><button className="btn small" onClick={() => openForeman(insight.ask)}>Ask Foreman</button></div>
    </Card>
  );
}
