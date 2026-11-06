// Foreman, full screen: the conversation on the left; what the agent is, what it remembers about you and your past
// conversations on the right.
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Trash2 } from "lucide-react";
import { api } from "../api";
import { PageTitle, useForemanContext } from "../app";
import { ForemanChat } from "../components/ForemanChat";
import { Card } from "../components/ui";

export default function ForemanPage() {
  const qc = useQueryClient();
  const info = useQuery({ queryKey: ["foremanInfo"], queryFn: api.foremanInfo, staleTime: 300_000 });
  const memories = useQuery({ queryKey: ["memories"], queryFn: api.memories, enabled: !!info.data?.memory });
  const sessions = useQuery({ queryKey: ["sessions"], queryFn: api.sessions, enabled: !!info.data?.memory });
  const forget = useMutation({ mutationFn: api.forget, onSuccess: () => qc.invalidateQueries({ queryKey: ["memories"] }) });
  useForemanContext("");
  const i = info.data;
  return (
    <>
      <PageTitle title="Foreman" sub="The operations supervisor agent: it routes your question to the right Genie spaces and shows each step." />
      <div className="split">
        <ForemanChat />
        <div className="stack">
          <Card title="How Foreman answers" note={i?.mode === "demo" ? "offline demo" : "live"}>
            <div className="muted" style={{ fontSize: 13, lineHeight: 1.6 }}>
              A fast model ({i?.router_llm || "router"}) picks the domain experts and writes their questions; they run in parallel;
              a strong model ({i?.answer_llm || "answer"}) writes the answer from what they return. Every run is an MLflow trace.
            </div>
            <div className="choices" style={{ marginTop: 10 }}>{i?.tools.map(t => <span key={t.domain} className="tool">{t.name}</span>)}</div>
            {i?.traces_url && <div style={{ marginTop: 10 }}><a href={i.traces_url} target="_blank" rel="noreferrer">Open the traces in MLflow</a></div>}
          </Card>
          <Card title="What Foreman remembers about you" note={i?.memory ? `${memories.data?.length ?? 0} facts` : "memory off"}>
            {!i?.memory && <div className="muted">Memory needs the agent's Lakebase resource.</div>}
            {memories.data?.length === 0 && <div className="muted">Nothing yet. Tell it your role or plant ("I run Greenville") and it will remember.</div>}
            {memories.data?.map(m => (
              <div key={m.memory_id} className="row">
                <span>{m.fact}<br /><span className="muted">{m.created_ts.slice(0, 10)}</span></span>
                <button className="btn small ghost" title="Forget this" onClick={() => forget.mutate(m.memory_id)}><Trash2 size={14} /></button>
              </div>
            ))}
          </Card>
          {!!sessions.data?.length && (
            <Card title="Recent conversations" note={`${sessions.data.length}`}>
              {sessions.data.slice(0, 8).map(s => (
                <div key={s.session_id} className="row">
                  <span className="clamp2" style={{ fontSize: 13 }}>{s.title}</span>
                  <button className="btn small" onClick={() => { localStorage.setItem("foreman-session", s.session_id); location.reload(); }}>Open</button>
                </div>
              ))}
            </Card>
          )}
        </div>
      </div>
    </>
  );
}
