/* global React, SP, SPIcon */
// Variation B — additional surfaces
const { ProjectRail, TopBar } = SP;
const { Plus, Folder, Message, FileText, Languages, Clock, Upload, Send, Check, X, ChevronDown, ChevronRight, Trash, Copy, AlertTriangle, Sparkle, History: HistoryIcon, Lock, ShieldCheck } = SPIcon;

// ---------- CREATE PROJECT (B style) ----------
const B_CreateProject = () => (
  <div className="sp-app" style={{ position: "relative" }}>
    <ProjectRail activeProject={null}/>
    <div className="workspace">
      <TopBar crumbs={["Workspace"]}/>
      <div className="content" style={{ filter: "blur(0.5px)", opacity: 0.55 }}>
        <h1 style={{ fontSize: 22 }}>What should we do today, Dr. Lee?</h1>
      </div>
    </div>
    <div className="modal-shade">
      <div className="modal" style={{ width: 480 }}>
        <h3>Start a new project</h3>
        <p className="lead">Each project keeps documents, threads, and runs scoped to one student case.</p>
        <label className="label">Case label</label>
        <input className="input" defaultValue="Case 2026-014"/>
        <div className="helper">
          <Check size={11} style={{ verticalAlign: "-1px", color: "var(--success)", marginRight: 4 }}/>
          Looks good. Format <span className="kbd">Case 20XX-NNN</span> is recommended.
        </div>

        <div className="divider"/>

        <label className="label">Internal student ID <span className="muted tiny">(optional, hashed at the gateway)</span></label>
        <input className="input" placeholder="district-id-XXXXX" defaultValue=""/>
        <div className="helper">
          <Lock size={11} style={{ verticalAlign: "-1px", marginRight: 4 }}/>
          Sent once, never returned. Hashed with a keyed BLAKE2b function.
        </div>

        <div style={{ marginTop: 16, padding: 12, background: "var(--bg-secondary)", borderRadius: 8, fontSize: 12, color: "var(--text-secondary)", lineHeight: 1.55 }}>
          <strong style={{ color: "var(--text-primary)" }}>Don't include</strong> names, dates of birth, SSNs, or 6+ digit IDs in the label. The gateway will reject them.
        </div>

        <div className="actions">
          <button className="btn">Cancel</button>
          <button className="btn primary"><Plus size={13}/> Create project</button>
        </div>
      </div>
    </div>
  </div>
);

// ---------- HISTORY (B - cards in a column) ----------
const B_History = () => (
  <div className="sp-app">
    <ProjectRail activeProject="Case 2026-014"/>
    <div className="workspace">
      <TopBar crumbs={["Case 2026-014", "History"]}
        right={
          <div className="seg">
            <button><Folder size={12}/></button>
            <button><Message size={12}/></button>
            <button><FileText size={12}/></button>
            <button><Languages size={12}/></button>
            <button className="active"><HistoryIcon size={12}/></button>
          </div>
        }
      />
      <div className="content">
        <div className="page-h">
          <div><h1>History</h1><div className="sub">Everything that happened in this project.</div></div>
          <div style={{ display: "flex", gap: 8 }}>
            <div className="seg">
              <button className="active">All</button>
              <button>Q&A</button>
              <button>Summaries</button>
              <button>Jargon</button>
            </div>
            <button className="btn sm">Export</button>
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
          {[
            { kind: "Q&A", icon: <Message size={13}/>, title: "Cognitive scores · WISC-V", excerpt: "What cognitive assessments were administered and what were the composite scores? · 3 turns", when: "23 min ago", meta: "fast · 3 citations" },
            { kind: "Summary", icon: <FileText size={13}/>, title: "eval_2024_REDACTED.pdf", excerpt: "Psychoeducational summary across 6 sections. WISC-V FSIQ 88; WIAT-4 Word Reading 74…", when: "1 hr ago", meta: "24 pages · 87s" },
            { kind: "Jargon", icon: <Languages size={13}/>, title: "Level 3 · Parent", excerpt: "Phonological processing deficits → 'difficulty with the sound-based building blocks of reading…'", when: "yesterday", meta: "FK 7.1 · 342 chars" },
            { kind: "Doc", icon: <Upload size={13}/>, title: "eval_2024_REDACTED.pdf ingested", excerpt: "5 entities redacted: Marcus Johnson → {STUDENT_NAME_1}, 01/15/2012 → {DATE_OF_BIRTH_1}, +3 more.", when: "yesterday", meta: "187 chunks · standard" },
          ].map((r, i) => (
            <div key={i} className="card" style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ width: 26, height: 26, borderRadius: 8, background: "var(--bg-secondary)", display: "grid", placeItems: "center", color: "var(--text-secondary)" }}>{r.icon}</span>
                <span className="bold small" style={{ flex: 1 }}>{r.title}</span>
                <span className="tag">{r.kind}</span>
              </div>
              <div className="muted small" style={{ lineHeight: 1.55 }}>{r.excerpt}</div>
              <div style={{ display: "flex", alignItems: "center", gap: 10, marginTop: 4 }}>
                <span className="muted tiny">{r.when}</span>
                <span className="muted tiny">·</span>
                <span className="muted tiny">{r.meta}</span>
                <button className="btn sm" style={{ marginLeft: "auto" }}>Open</button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  </div>
);

// ---------- DELETE CONFIRM (B style) ----------
const B_DeleteConfirm = () => (
  <div className="sp-app" style={{ position: "relative" }}>
    <ProjectRail activeProject="Case 2026-014"/>
    <div className="workspace">
      <TopBar crumbs={["Case 2026-014", "Documents"]}/>
      <div className="content" style={{ filter: "blur(0.4px)", opacity: 0.55 }}>
        <h1 style={{ fontSize: 20 }}>Documents</h1>
      </div>
    </div>
    <div className="modal-shade">
      <div className="modal" style={{ width: 440 }}>
        <h3>Delete eval_2024_REDACTED.pdf?</h3>
        <p className="lead">This removes the document from the index and discards its 187 chunks. Threads referencing it will keep their text but lose live citations.</p>
        <div style={{ background: "var(--danger-soft)", color: "var(--danger)", padding: "8px 12px", borderRadius: 8, fontSize: 12.5, display: "flex", gap: 8, alignItems: "center" }}>
          <ShieldCheck size={13}/> Hard-delete · cannot be undone · required by FERPA.
        </div>
        <div className="actions">
          <button className="btn">Cancel</button>
          <button className="btn" style={{ background: "var(--danger)", color: "white", borderColor: "var(--danger)" }}>Delete permanently</button>
        </div>
      </div>
    </div>
  </div>
);

// ---------- SUMMARIZER IN-PROGRESS (B style — friendly, content-shaped) ----------
const B_SummarizerInProgress = () => (
  <div className="sp-app">
    <ProjectRail activeProject="Case 2026-014"/>
    <div className="workspace">
      <TopBar crumbs={["Case 2026-014", "Summarize"]}
        right={
          <div className="seg">
            <button><Folder size={12}/></button>
            <button><Message size={12}/></button>
            <button className="active"><FileText size={12}/></button>
            <button><Languages size={12}/></button>
            <button><HistoryIcon size={12}/></button>
          </div>
        }
      />
      <div className="content">
        <div className="page-h">
          <div><h1>Summarize</h1><div className="sub">Generating structured summary…</div></div>
        </div>

        <div className="composer" style={{ marginBottom: 22 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <FileText size={14} style={{ color: "var(--accent)" }}/>
            <span className="bold small">eval_2024_REDACTED.pdf</span>
            <span className="muted tiny">24 pages</span>
            <span className="tag accent" style={{ marginLeft: "auto" }}>
              <span style={{ width: 6, height: 6, borderRadius: 999, background: "var(--accent)", display: "inline-block", marginRight: 4, animation: "pulse 1.2s infinite" }}/>
              elapsed 0:38 · ~0:50 remaining
            </span>
          </div>
        </div>

        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          <div style={{ padding: "12px 18px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", gap: 10 }}>
            <span className="bold small">Summary</span>
            <span className="tag">streaming…</span>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "200px 1fr", minHeight: 360 }}>
            <nav style={{ borderRight: "1px solid var(--border)", padding: "12px 8px", background: "var(--bg-secondary)" }}>
              {[
                { l: "Student", done: true },
                { l: "Referral", done: true },
                { l: "Cognitive", done: true, current: false },
                { l: "Achievement", current: true },
                { l: "Diagnoses", done: false },
                { l: "Recommendations", done: false },
              ].map((s, i) => (
                <div key={i} style={{
                  display: "flex", alignItems: "center", gap: 6,
                  padding: "7px 10px", fontSize: 12.5,
                  color: s.current ? "var(--accent)" : s.done ? "var(--text-primary)" : "var(--text-muted)",
                  fontWeight: s.current ? 600 : 500,
                  background: s.current ? "var(--accent-soft)" : "transparent",
                  borderRadius: 6
                }}>
                  {s.done && <Check size={11} style={{ color: "var(--success)" }}/>}
                  {s.current && <span style={{ width: 6, height: 6, borderRadius: 999, background: "var(--accent)", animation: "pulse 1.2s infinite" }}/>}
                  {!s.done && !s.current && <span style={{ width: 6, height: 6, borderRadius: 999, background: "var(--bg-tertiary)" }}/>}
                  <span>{s.l}</span>
                </div>
              ))}
            </nav>
            <div style={{ padding: 22, fontSize: 13.5, lineHeight: 1.65 }}>
              <div className="bold" style={{ fontSize: 15, marginBottom: 4 }}>Cognitive Assessment</div>
              <div className="muted small" style={{ marginBottom: 10 }}>WISC-V</div>
              <div className="mono" style={{ fontSize: 12 }}>{`Full Scale IQ           88  (Low Average)
Verbal Comprehension    92  (Average)
Visual Spatial          90  (Average)
Fluid Reasoning         85  (Low Average)
Working Memory          88  (Average)
Processing Speed        79  (Below Average)`}</div>

              <div style={{ marginTop: 18 }}>
                <div className="bold" style={{ fontSize: 15, marginBottom: 8 }}>Achievement <span className="muted tiny" style={{ fontWeight: 400 }}>· streaming</span></div>
                <div className="ph-line" style={{ width: "82%", marginBottom: 7 }}/>
                <div className="ph-line" style={{ width: "76%", marginBottom: 7 }}/>
                <div className="ph-line" style={{ width: "60%", marginBottom: 7 }}/>
                <div className="ph-line" style={{ width: "44%" }}/>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <style>{`@keyframes pulse { 0%,100% { opacity: 1 } 50% { opacity: 0.35 } }`}</style>
  </div>
);

window.VariationBExtra = { B_CreateProject, B_History, B_DeleteConfirm, B_SummarizerInProgress };
