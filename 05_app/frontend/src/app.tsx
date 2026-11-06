// App shell: the navy banner + nav, the page outlet, and the two things every page can reach —
// Foreman (a drawer that knows what you're looking at) and a toast.
import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Activity, Factory, FileCheck2, LayoutDashboard, MessagesSquare, Network } from "lucide-react";
import { api, type Entity } from "./api";
import { ForemanChat } from "./components/ForemanChat";

interface Shell {
  /** What the person is looking at, in words Foreman understands ("machine GVL-L3-WC01 on line GVL-L3"). Pages set it. */
  context: string; setContext: (c: string) => void;
  /** Suggested questions for the current page. */
  seeds: string[]; setSeeds: (s: string[]) => void;
  /** The entity on screen — where an action Foreman suggests is filed. */
  entity: Entity; setEntity: (e: Entity) => void;
  openForeman: (question?: string) => void;
  toast: (msg: string) => void;
}
const ShellCtx = createContext<Shell | null>(null);
export const useShell = () => useContext(ShellCtx)!;

/** Pages call this to tell Foreman where the user is. */
export function useForemanContext(context: string, seeds: string[] = [], entity: Entity = ENTERPRISE) {
  const { setContext, setSeeds, setEntity } = useShell();
  const key = seeds.join("|") + entity.type + entity.id;
  useEffect(() => { setContext(context); setSeeds(seeds); setEntity(entity); }, [context, key]);   // eslint-disable-line react-hooks/exhaustive-deps
}
export const ENTERPRISE: Entity = { type: "plant", id: "KK" };

const NAV = [
  { to: "/", label: "Andon Board", icon: LayoutDashboard },
  { to: "/explorer", label: "Plant Explorer", icon: Factory },
  { to: "/impact", label: "Impact Web", icon: Network },
  { to: "/foreman", label: "Foreman", icon: MessagesSquare },
  { to: "/ledger", label: "Action Ledger", icon: FileCheck2 },
];

export function Layout() {
  const meta = useQuery({ queryKey: ["meta"], queryFn: api.meta, staleTime: Infinity });
  const [context, setContext] = useState("");
  const [seeds, setSeeds] = useState<string[]>([]);
  const [entity, setEntity] = useState<Entity>(ENTERPRISE);
  const [drawer, setDrawer] = useState<{ open: boolean; question?: string; nonce: number }>({ open: false, nonce: 0 });
  const [msg, setMsg] = useState("");
  const toast = useCallback((m: string) => { setMsg(m); window.setTimeout(() => setMsg(""), 3200); }, []);
  const openForeman = useCallback((question?: string) => setDrawer(d => ({ open: true, question, nonce: d.nonce + 1 })), []);
  const offline = [meta.data?.data_mode !== "live" && "data", meta.data?.agent_mode !== "live" && "Foreman"].filter(Boolean);

  return (
    <ShellCtx.Provider value={{ context, setContext, seeds, setSeeds, entity, setEntity, openForeman, toast }}>
      <header className="banner">
        <div className="banner-inner">
          <div className="brandrow">
            <img src="/logo_white.svg" alt="KK's Parts — Precision, driven." />
            <div className="sep" />
            <div className="app">Andon<small>{meta.data ? `Data through ${meta.data.data_through}` : " "}</small></div>
            <div className="spacer" />
            {meta.data && (offline.length
              ? <span className="chip demo" title={`Not connected: ${offline.join(", ")}`}><span className="dot" />Offline mode</span>
              : <span className="chip"><span className="dot" />Connected</span>)}
            {meta.data && <span className="chip">{meta.data.user}</span>}
            {meta.data?.is_admin && (
              <NavLink to="/health" className={({ isActive }) => `chip admin${isActive ? " active" : ""}`} title="App & agent health (admins)">
                <Activity size={14} />Health
              </NavLink>)}
          </div>
          <nav className="nav">
            {NAV.map(({ to, label, icon: Icon }) => (
              <NavLink key={to} to={to} end={to === "/"} className={({ isActive }) => (isActive ? "active" : "")}>
                <Icon size={16} />{label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>
      <main className="page"><Outlet /></main>
      <button className="fab" onClick={() => openForeman()}><MessagesSquare size={18} />Ask Foreman</button>
      {drawer.open && (
        <>
          <div className="drawer-bg" onClick={() => setDrawer(d => ({ ...d, open: false }))} />
          <aside className="drawer" role="dialog" aria-label="Foreman">
            <ForemanChat key={drawer.nonce} initialQuestion={drawer.question} onClose={() => setDrawer(d => ({ ...d, open: false }))} compact />
          </aside>
        </>
      )}
      {msg && <div className="toast">{msg}</div>}
    </ShellCtx.Provider>
  );
}

export function PageTitle({ title, sub, eyebrow, right }: { title: string; sub?: string; eyebrow?: string; right?: ReactNode }) {
  return (
    <div className="head" style={{ display: "flex", alignItems: "flex-end", gap: 16 }}>
      <div style={{ flex: 1 }}>
        {eyebrow && <div className="eyebrow">{eyebrow}</div>}
        <div className="title">{title}</div>
        {sub && <div className="sub">{sub}</div>}
      </div>
      {right}
    </div>
  );
}
