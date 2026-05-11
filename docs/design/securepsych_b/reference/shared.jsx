/* global React, SPIcon */
const { Plus, Folder, Message, FileText, Languages, Clock, ShieldCheck, Server, WifiOff, LogOut, Upload, Search, Send, Settings, Check, X, ChevronDown, ChevronRight, Trash, Copy, Sliders, AlertTriangle, EyeOff, ArrowRight, Sparkle, PanelLeft, Hash, History, Lock } = SPIcon;

// ---- Trust pills ----
const TrustPills = () => (
  <div className="trust-pills">
    <span className="trust-pill"><ShieldCheck size={11}/> FERPA</span>
    <span className="trust-pill"><Server size={11}/> On-prem</span>
    <span className="trust-pill"><WifiOff size={11}/> Air-gapped</span>
  </div>
);

// ---- Project rail (full) ----
const ProjectRail = ({ activeProject = "Case 2026-014", activeTab = null, projects, threads }) => {
  const projs = projects || [
    { code: "Case 2026-014", meta: "today", active: true },
    { code: "Case 2026-011", meta: "Apr 28" },
    { code: "Case 2026-007", meta: "Apr 22" },
    { code: "Case 2025-098", meta: "Apr 14" },
    { code: "Case 2025-091", meta: "Apr 09" },
  ];
  const thrs = threads || [
    { title: "Cognitive scores · WISC-V", active: true },
    { title: "Reading interventions" },
    { title: "ADHD differential" },
  ];
  return (
    <aside className="rail">
      <div className="rail-header">
        <span className="brand">
          <span className="brand-mark">SP</span>
          SecurePsych
        </span>
      </div>
      <div className="rail-section">
        <button className="rail-btn"><Plus size={14}/> New project</button>
      </div>
      <div className="rail-section">
        <div className="rail-label">Recent projects</div>
        {projs.map((p, i) => (
          <button key={i} className={"rail-item" + (p.code === activeProject ? " active" : "")}>
            <Folder size={14}/>
            <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{p.code}</span>
            <span className="meta">{p.meta}</span>
          </button>
        ))}
        <button className="rail-item muted" style={{ fontSize: 12 }}>
          <span style={{ width: 14 }}/> Load more…
        </button>
      </div>
      {activeTab === "qa" && (
        <div className="rail-section">
          <div className="rail-label">Threads in {activeProject}</div>
          {thrs.map((t, i) => (
            <button key={i} className={"rail-item" + (t.active ? " active" : "")}>
              <Hash size={13}/>
              <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{t.title}</span>
            </button>
          ))}
          <button className="rail-item muted" style={{ fontSize: 12 }}>
            <Plus size={13}/> New thread
          </button>
        </div>
      )}
      <div className="rail-spacer"/>
      <div className="rail-footer">
        <TrustPills/>
        <div className="user-row">
          <span className="avatar">DL</span>
          <span style={{ flex: 1 }}>Dr. Lee</span>
          <button className="icon-btn" title="Sign out"><LogOut size={14}/></button>
        </div>
      </div>
    </aside>
  );
};

// ---- TopBar ----
const TopBar = ({ crumbs, right }) => (
  <div className="topbar">
    <div className="crumb">
      {crumbs.map((c, i) => (
        <React.Fragment key={i}>
          {i > 0 && <span className="sep"><ChevronRight size={12}/></span>}
          <span className={i === crumbs.length - 1 ? "title" : ""}>{c}</span>
        </React.Fragment>
      ))}
    </div>
    <div className="right">
      {right || (
        <>
          <span className="status-pill"><span className="dot"/> System operational</span>
          <button className="icon-btn"><Settings size={15}/></button>
        </>
      )}
    </div>
  </div>
);

// ---- Tabs row (used by Variation A) ----
const Tabs = ({ items, active }) => (
  <div className="tabs">
    {items.map((it) => (
      <button key={it.key} className={"tab" + (it.key === active ? " active" : "")}>
        {it.icon}
        {it.label}
        {it.count != null && <span className="pill">{it.count}</span>}
      </button>
    ))}
  </div>
);

window.SP = { TrustPills, ProjectRail, TopBar, Tabs };
