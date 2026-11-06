// The typed API client. Every shape here mirrors backend/core/shapes.py and the route that returns it.
// Errors carry the backend's `detail`, so a failed request says WHY instead of "API error: 500".

export type Tone = "bad" | "warn" | "good" | "";
export interface Kpi { label: string; value: string; compare: string; tone: Tone; spark: number[] | null; ref: number | null }
export interface Insight {
  id: string; severity: "critical" | "high" | "watch"; domain: string; title: string; headline: string; detail: string;
  impact_usd: number; plant_id: string | null; line_id: string | null; machine_id: string | null; supplier_id: string | null;
  carrier_id: string | null; customer_id: string | null; capa_id: string | null; lines: string[]; quality_lines: string[];
  actions: string[]; ask: string; entity: [string, string];
}
export interface Figure { data: unknown[]; layout: Record<string, unknown> }
export interface Column { key: string; label: string; format: string }
export interface Table { title?: string; note?: string; columns: Column[]; rows: Record<string, unknown>[]; total: number }
export interface Entity { type: string; id: string }
export interface Detail {
  eyebrow: string; title: string; subtitle: string; kpis: Kpi[]; charts: Figure[]; tables: Table[]; related: Insight[];
  entity: Entity; actions: string[]; insight_id?: string; ask: string[]; defaults?: Record<string, unknown>;
}
export interface Meta { user: string; is_admin: boolean; genie_access: boolean | null; data_mode: string; agent_mode: string; ledger: string; data_through: string; dashboard_url: string }

// App & agent health (admins) — mirrors backend/routes/admin.py and 04_supervisor_agent/agent/runlog.py
export interface RunStep { space: string; seconds: number; status: string; error: string | null; genie_status: string; rows: number }
export interface Run { run_id: string; session_id: string; user: string; question: string; status: "ok" | "error" | "stopped";
  error: string | null; started_ts: string; duration_ms: number; genie_auth: string; steps: RunStep[] }
export interface RunSummary { hours: number; runs: number; errors: number; stopped: number; p50_s: number; p95_s: number;
  users: { user: string; runs: number; errors: number; sessions: number; avg_s: number; last: string }[];
  genie_spaces: { space: string; calls: number; errors: number; avg_s: number; p95_s: number }[] }
export interface AppEvent { event_ts: string; user: string; kind: string; route: string; message: string; detail: Record<string, unknown> }
export interface Health { hours: number; agent_mode: string; foreman_error: string | null; summary: RunSummary | null; runs: Run[];
  app_events: AppEvent[]; traces_url?: string; trace_tables?: string; genie_auth?: string }
export interface Board { subtitle: string; kpis: Kpi[]; critical: Insight[]; watch: Insight[]; charts: Record<string, Figure> }
export interface PlantChip { id: string; name: string; city: string; status: string; oee: number | null }
export interface MapPoint { id: string; name?: string; lon: number; lat: number; tip: string; color: number[]; status?: string }
export interface Network { plants: MapPoint[]; dcs: MapPoint[]; suppliers: MapPoint[]; arcs: { from: number[]; to: number[]; hot: boolean; width: number; tip: string }[] }
export interface GraphNode { id: string; kind: string; label: string; tip: string; r: number; status: string; kindLabel: string; name: string }
export interface Graph { columns: { kind: string; label: string }[]; nodes: GraphNode[]; edges: { s: string; t: string; w: number; status: string }[];
  issues: { id: string; title: string; target: string | null }[] }
export interface NodeDetail {
  node: GraphNode; kind: string; related: Insight[]; neighbors: { id: string; name: string }[]; chart: Figure | null;
  explore: Record<string, string> | null; entity: Entity; actions: string[]; insight_id: string; defaults: Record<string, unknown>; ask: string;
}
export interface Option { value: string; label: string }
export interface Field { name: string; label: string; kind: "select" | "multiselect" | "number" | "date" | "text" | "record"; options?: Option[]; default?: unknown }
export interface ActionForm { action_type: string; label: string; icon: string; fields: Field[]; title: string }
export interface RecordRef { dataset: string; key: string; label: string }
export interface FieldValue { current: string; kind: "select" | "number" | "date" | "text"; target: string; options?: Option[]; default?: unknown }
export interface Action {
  action_id: string; created_ts: string; created_by: string; action_type: string; entity_type: string; entity_id: string; title: string;
  details: string; priority: string; status: string; source: string; insight_id: string; payload: string; reviewed_by: string | null;
  reviewed_ts: string | null; kind: string | null; target: string | null; sync_status: string | null; synced_ts: string | null;
  sync_ref: string | null; sync_error: string | null;
}
export interface Ledger { backend: string; rows: Action[]; sync_job: boolean }
export interface ActionEvent { event_ts: string; actor: string; event: string; detail: string }
export interface ForemanInfo { genie_auth?: string; trace_tables?: string; mode: string; memory: boolean; traces_url: string; router_llm: string; answer_llm: string; tools: { name: string; domain: string }[] }
export interface SessionRow { session_id: string; title: string; updated_ts: string }
export interface Turn { role: "user" | "assistant"; content: string; trace_id: string | null; created_ts: string }
export interface Memory { memory_id: number; fact: string; created_ts: string }

export class ApiError extends Error {
  constructor(public status: number, message: string) { super(message); }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, { ...init, headers: { "Content-Type": "application/json", ...(init?.headers || {}) } });
  if (!res.ok) {
    let detail = res.statusText;
    try { const body = await res.json(); detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail ?? body); } catch { /* not JSON */ }
    throw new ApiError(res.status, `${res.status} · ${detail}`);
  }
  return res.json() as Promise<T>;
}

const q = (params: Record<string, string | undefined>) =>
  "?" + new URLSearchParams(Object.entries(params).filter(([, v]) => v !== undefined) as [string, string][]).toString();

export const api = {
  meta: () => request<Meta>("/api/meta"),
  board: () => request<Board>("/api/board"),
  network: () => request<Network>("/api/network"),
  plants: () => request<PlantChip[]>("/api/explorer/plants"),
  scene: (plant: string) => request<Record<string, unknown>>(`/api/explorer/scene/${plant}`),
  detail: (level: "plant" | "line" | "machine" | "supplier", id: string) => request<Detail>(`/api/explorer/${level}/${encodeURIComponent(id)}`),
  graph: () => request<Graph>("/api/impact/graph"),
  node: (id: string) => request<NodeDetail>(`/api/impact/node/${encodeURIComponent(id)}`),
  actionTypes: () => request<Record<string, { label: string; icon: string; domain: string }>>("/api/actions/types"),
  form: (type: string, e: Entity, defaults?: Record<string, unknown>) =>
    request<ActionForm>(`/api/actions/form/${type}${q({ entity_type: e.type, entity_id: e.id, defaults: JSON.stringify(defaults || {}) })}`),
  records: (e: Entity) => request<RecordRef[]>(`/api/records${q({ entity_type: e.type, entity_id: e.id })}`),
  recordFields: (dataset: string) => request<{ column: string; label: string }[]>(`/api/records/fields${q({ dataset })}`),
  recordValue: (dataset: string, key: string, column: string) => request<FieldValue>(`/api/records/value${q({ dataset, key, column })}`),
  submit: (body: Record<string, unknown>) => request<Action>("/api/actions", { method: "POST", body: JSON.stringify(body) }),
  ledger: (entity_id?: string) => request<Ledger>(`/api/actions${entity_id ? q({ entity_id }) : ""}`),
  review: (id: string, status: string) => request<{ ok: boolean }>(`/api/actions/${id}/review`, { method: "POST", body: JSON.stringify({ status }) }),
  events: (id: string) => request<ActionEvent[]>(`/api/actions/${id}/events`),
  sync: () => request<{ run_id: number }>("/api/actions/sync", { method: "POST" }),
  foremanInfo: () => request<ForemanInfo>("/api/foreman/info"),
  sessions: () => request<SessionRow[]>("/api/foreman/sessions"),
  turns: (id: string) => request<Turn[]>(`/api/foreman/sessions/${id}`),
  memories: () => request<Memory[]>("/api/foreman/memories"),
  forget: (id: number) => request<{ ok: boolean }>(`/api/foreman/memories/${id}`, { method: "DELETE" }),
  suggest: (question: string, context: string) => request<string[]>(`/api/foreman/suggest${q({ question, context })}`),
  health: (hours: number) => request<Health>(`/api/admin/health${q({ hours: String(hours) })}`),
  /** Report an error the browser hit, so it shows on the health page. Never throws. */
  reportError: (message: string, route: string, detail: Record<string, unknown> = {}) =>
    fetch("/api/telemetry", { method: "POST", headers: { "Content-Type": "application/json" },
                              body: JSON.stringify({ message: message.slice(0, 2000), route, detail }) }).catch(() => undefined),
};

// ---------------------------------------------------------------------------------------------- Foreman stream
export type AgentEvent =
  | { type: "start"; session_id: string; trace_id: string | null; demo?: boolean }
  | { type: "step"; id: string; kind: "memory" | "plan" | "route"; label: string; space?: string; domain?: string; question?: string; model?: string }
  | { type: "step_update"; id: string; status: string; elapsed_s?: number }
  | { type: "step_done"; id: string; label: string; status?: string; sql?: string[]; rows?: Record<string, unknown>[]; error?: string | null; detail?: string[] }
  | { type: "token"; text: string }
  | { type: "answer"; text: string }
  | { type: "heartbeat" }
  | { type: "done"; session_id: string; trace_id: string | null; elapsed_ms: number; demo?: boolean }
  | { type: "error"; message: string };

/** POST a question and call `on` for every Server-Sent Event. Abort with the signal to cancel. */
export async function streamForeman(body: { question: string; context: string; session_id?: string | null }, on: (e: AgentEvent) => void,
                                    signal?: AbortSignal): Promise<void> {
  const res = await fetch("/api/foreman/chat", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body), signal });
  if (!res.ok || !res.body) throw new ApiError(res.status, `Foreman is unavailable (${res.status})`);
  const reader = res.body.getReader();
  const dec = new TextDecoder();
  let buf = "";
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buf += dec.decode(value, { stream: true });
    let i;
    while ((i = buf.indexOf("\n\n")) >= 0) {                     // one SSE event per blank-line-terminated block
      const block = buf.slice(0, i); buf = buf.slice(i + 2);
      const data = block.split("\n").filter(l => l.startsWith("data:")).map(l => l.slice(5)).join("\n");
      if (data) { try { on(JSON.parse(data)); } catch { /* ignore a malformed line */ } }
    }
  }
}
