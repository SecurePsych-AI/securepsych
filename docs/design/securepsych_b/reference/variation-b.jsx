/* global React, SP, SPIcon */
// Variation B — Unified composer: rail + single workspace, side-panel citations, side-by-side PII
const { ProjectRail, TopBar, TrustPills } = SP;
const { Plus, Folder, Message, FileText, Languages, Clock, ShieldCheck, Upload, Send, Check, X, ChevronDown, ChevronRight, Trash, Copy, AlertTriangle, EyeOff, ArrowRight, Sparkle, History, Hash, Lock } = SPIcon;

// ---------- LOGIN — Minimal centered ----------
const B_Login = () => (
  <div style={{ width: "100%", height: "100%", background: "var(--bg-primary)", display: "grid", placeItems: "center" }}>
    <div style={{ width: 340, padding: "24px 0", display: "flex", flexDirection: "column", alignItems: "stretch" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 28, justifyContent: "center" }}>
        <span className="brand-mark" style={{ width: 30, height: 30, fontSize: 13 }}>SP</span>
        <span className="bold" style={{ fontSize: 15 }}>SecurePsych</span>
      </div>
      <h2 style={{ margin: "0 0 4px", fontSize: 22, fontWeight: 600, letterSpacing: "-0.015em", textAlign: "center" }}>Sign in</h2>
      <p style={{ color: "var(--text-secondary)", fontSize: 13.5, margin: "0 0 24px", textAlign: "center" }}>
        Local server · session-only token
      </p>
      <label className="label">Username</label>
      <input className="input" defaultValue="dr.lee"/>
      <div style={{ height: 12 }}/>
      <label className="label">Password</label>
      <input className="input" type="password" defaultValue="••••••••••"/>
      <button className="btn primary lg" style={{ justifyContent: "center", width: "100%", marginTop: 18 }}>Sign in</button>
      <div style={{ marginTop: 22, display: "flex", justifyContent: "center" }}><TrustPills/></div>
    </div>
  </div>
);

// ---------- DASHBOARD — Unified-composer welcome ----------
const B_Dashboard = () => (
  <div className="sp-app">
    <ProjectRail activeProject={null}/>
    <div className="workspace">
      <TopBar crumbs={["Workspace"]}/>
      <div className="content" style={{ padding: 0, display: "flex", flexDirection: "column" }}>
        <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", padding: "40px 28px" }}>
          <div style={{ width: "100%", maxWidth: 720 }}>
            <div style={{ textAlign: "center", marginBottom: 28 }}>
              <h1 style={{ margin: 0, fontSize: 28, fontWeight: 600, letterSpacing: "-0.02em" }}>What should we do today, Dr. Lee?</h1>
              <div className="muted" style={{ marginTop: 8, fontSize: 14 }}>Pick a project, then ask, summarize, or simplify — all from one composer.</div>
            </div>

            <div className="composer" style={{ padding: "14px 16px 12px" }}>
              <textarea rows={3} placeholder="Start by selecting a project, or describe what you want to do…"/>
              <div className="row">
                <button className="btn sm"><Folder size={12}/> Select project <ChevronDown size={11}/></button>
                <div className="seg accent">
                  <button className="active"><Message size={11}/> Ask</button>
                  <button><FileText size={11}/> Summarize</button>
                  <button><Languages size={11}/> Simplify</button>
                </div>
                <div className="right">
                  <button className="btn sm ghost muted"><Upload size={12}/> Attach PDF</button>
                  <button className="btn primary sm"><Send size={12}/></button>
                </div>
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8, marginTop: 14 }}>
              {[
                { icon: <Message size={12}/>, label: "Ask: \u201CWhat were the FSIQ composite scores?\u201D" },
                { icon: <FileText size={12}/>, label: "Summarize: latest evaluation" },
                { icon: <Languages size={12}/>, label: "Simplify: this paragraph at parent level" },
              ].map((s, i) => (
                <button key={i} className="card" style={{ padding: 12, textAlign: "left", cursor: "pointer", display: "flex", gap: 8, alignItems: "center", border: "1px solid var(--border)", background: "var(--bg-primary)", fontSize: 12.5, color: "var(--text-secondary)" }}>
                  <span style={{ color: "var(--accent)" }}>{s.icon}</span>
                  {s.label}
                </button>
              ))}
            </div>

            <div style={{ marginTop: 32 }}>
              <div className="rail-label" style={{ padding: "0 0 8px" }}>Continue where you left off</div>
              <div className="card" style={{ padding: 0, overflow: "hidden" }}>
                {[
                  { kind: "Q&A", icon: <Message size={13}/>, title: "Cognitive scores · WISC-V", project: "Case 2026-014", when: "23 min ago" },
                  { kind: "Summary", icon: <FileText size={13}/>, title: "eval_2024_REDACTED.pdf", project: "Case 2026-014", when: "1 hr ago" },
                  { kind: "Jargon", icon: <Languages size={13}/>, title: "Phonological processing · L3", project: "Case 2026-011", when: "yesterday" },
                ].map((r, i, arr) => (
                  <div key={i} style={{
                    display: "flex", alignItems: "center", gap: 10, padding: "11px 14px",
                    borderBottom: i < arr.length - 1 ? "1px solid var(--border)" : "none"
                  }}>
                    <span style={{ width: 24, height: 24, borderRadius: 7, background: "var(--bg-secondary)", display: "grid", placeItems: "center", color: "var(--text-secondary)" }}>{r.icon}</span>
                    <span className="medium" style={{ flex: 1 }}>{r.title}</span>
                    <span className="tag">{r.kind}</span>
                    <span className="muted small" style={{ minWidth: 110, textAlign: "right" }}>{r.project}</span>
                    <span className="muted tiny" style={{ minWidth: 70, textAlign: "right" }}>{r.when}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
);

// ---------- PII REVIEW — Side-by-side text comparison ----------
const B_PIIReview = () => {
  const entities = [
    { token: "STUDENT_NAME_1", original: "Marcus Johnson", count: 14 },
    { token: "STUDENT_NAME_2", original: "Marcus", count: 22 },
    { token: "DATE_OF_BIRTH_1", original: "01/15/2012", count: 6 },
    { token: "PARENT_NAME_1", original: "Tanya Johnson", count: 3 },
    { token: "DISTRICT_ID_1", original: "987654-23A", count: 1 },
  ];
  const Highlight = ({ children, kind = "orig" }) => (
    <mark style={{
      background: kind === "orig" ? "var(--warning-soft)" : "var(--accent-soft)",
      color: kind === "orig" ? "var(--warning)" : "var(--accent)",
      padding: "1px 5px", borderRadius: 4,
      fontWeight: 500
    }}>{children}</mark>
  );
  return (
    <div className="sp-app">
      <ProjectRail activeProject="Case 2026-014"/>
      <div className="workspace">
        <TopBar crumbs={["Case 2026-014", "Upload document", "Review redactions"]}/>
        <div className="content">
          <div className="page-h">
            <div>
              <h1>Confirm what gets stored</h1>
              <div className="sub">Compare the original sample text with what will actually be ingested. Originals are discarded on confirm.</div>
            </div>
            <div style={{ display: "flex", gap: 8 }}>
              <button className="btn">Cancel</button>
              <button className="btn primary"><Check size={14}/> Confirm and ingest</button>
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
            <div className="card" style={{ padding: 0 }}>
              <div style={{ padding: "10px 14px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", gap: 8 }}>
                <EyeOff size={13} style={{ color: "var(--warning)" }}/>
                <span className="bold small">Original — discarded</span>
                <span className="tag warn" style={{ marginLeft: "auto" }}>eval_2024.pdf</span>
              </div>
              <div style={{ padding: 16, fontSize: 13, lineHeight: 1.7, color: "var(--text-primary)", maxHeight: 240, overflow: "auto" }}>
                This psychoeducational evaluation was conducted for <Highlight>Marcus Johnson</Highlight>, born <Highlight>01/15/2012</Highlight>, by a licensed school psychologist on March 15, 2024. The referral was initiated by <Highlight>Tanya Johnson</Highlight> (parent) due to concerns regarding <Highlight>Marcus</Highlight>'s reading fluency and comprehension. District ID: <Highlight>987654-23A</Highlight>.
              </div>
            </div>

            <div className="card" style={{ padding: 0 }}>
              <div style={{ padding: "10px 14px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", gap: 8 }}>
                <ShieldCheck size={13} style={{ color: "var(--accent)" }}/>
                <span className="bold small">Stored — what we keep</span>
                <span className="tag accent" style={{ marginLeft: "auto" }}>eval_2024_REDACTED.pdf</span>
              </div>
              <div style={{ padding: 16, fontSize: 13, lineHeight: 1.7, color: "var(--text-primary)", maxHeight: 240, overflow: "auto" }}>
                This psychoeducational evaluation was conducted for <Highlight kind="rep">{"{STUDENT_NAME_1}"}</Highlight>, born <Highlight kind="rep">{"{DATE_OF_BIRTH_1}"}</Highlight>, by a licensed school psychologist on March 15, 2024. The referral was initiated by <Highlight kind="rep">{"{PARENT_NAME_1}"}</Highlight> (parent) due to concerns regarding <Highlight kind="rep">{"{STUDENT_NAME_2}"}</Highlight>'s reading fluency and comprehension. District ID: <Highlight kind="rep">{"{DISTRICT_ID_1}"}</Highlight>.
              </div>
            </div>
          </div>

          <div className="card" style={{ marginTop: 14, padding: 0, overflow: "hidden" }}>
            <div style={{ padding: "10px 14px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", gap: 10 }}>
              <span className="bold small">Replacement map</span>
              <span className="muted tiny">5 entities · 46 occurrences across 24 pages</span>
              <span className="tag" style={{ marginLeft: "auto" }}>standard chunking · ~187 chunks</span>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 0 }}>
              {entities.map((e, i) => (
                <div key={i} style={{
                  padding: "12px 14px",
                  borderRight: i < entities.length - 1 ? "1px solid var(--border)" : "none",
                }}>
                  <div className="muted tiny" style={{ marginBottom: 4 }}>{e.count}× occurrences</div>
                  <div style={{ fontFamily: "var(--font-mono)", fontSize: 12, color: "var(--text-primary)", marginBottom: 4 }}>{e.original}</div>
                  <div style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 11 }}>
                    <ArrowRight size={11} style={{ color: "var(--text-muted)" }}/>
                    <span style={{ fontFamily: "var(--font-mono)", fontSize: 11, background: "var(--accent-soft)", color: "var(--accent)", padding: "1px 6px", borderRadius: 999 }}>{`{${e.token}}`}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// ---------- CHAT — Side-panel citations ----------
const B_Chat = () => (
  <div className="sp-app">
    <ProjectRail activeProject="Case 2026-014" activeTab="qa"/>
    <div className="workspace">
      <TopBar crumbs={["Case 2026-014", "Cognitive scores · WISC-V"]}
        right={
          <>
            <div className="seg">
              <button><Folder size={12}/></button>
              <button className="active"><Message size={12}/></button>
              <button><FileText size={12}/></button>
              <button><Languages size={12}/></button>
              <button><History size={12}/></button>
            </div>
            <span className="status-pill"><span className="dot"/> Operational</span>
          </>
        }
      />
      <div className="content" style={{ padding: 0, display: "grid", gridTemplateColumns: "1fr 320px", minHeight: 0, overflow: "hidden" }}>
        <div style={{ display: "flex", flexDirection: "column", minHeight: 0, borderRight: "1px solid var(--border)" }}>
          <div className="scroll" style={{ flex: 1, padding: "26px 28px 12px" }}>
            <div className="msg user">
              <span className="bubble-avatar">DL</span>
              <div className="body">
                <div className="who">Dr. Lee</div>
                What cognitive assessments were administered and what were the composite scores?
              </div>
            </div>
            <div className="msg assistant">
              <span className="bubble-avatar"><Sparkle size={14}/></span>
              <div className="body">
                <div className="who">SecurePsych</div>
                <p style={{ margin: "0 0 10px" }}>
                  The Wechsler Intelligence Scale for Children (WISC-V) was administered. The student obtained a Full Scale IQ (FSIQ) composite score of <strong>88</strong>, placing performance in the Low Average range (25th percentile). Verbal Comprehension Index was <strong>92</strong>, Fluid Reasoning <strong>85</strong>, and Processing Speed <strong>79</strong> (Below Average, 8th percentile).
                </p>
                <p style={{ margin: 0 }}>
                  No additional cognitive batteries were administered in this evaluation.
                </p>
                <div style={{ marginTop: 14, display: "flex", alignItems: "center", gap: 8 }}>
                  <span className="muted tiny">Cited 3 sources →</span>
                  <button className="btn sm"><Copy size={11}/> Copy</button>
                </div>
              </div>
            </div>
          </div>

          <div style={{ padding: "14px 28px 22px", borderTop: "1px solid var(--border)" }}>
            <div className="composer">
              <textarea rows={2} placeholder="Ask anything about eval_2024_REDACTED.pdf…"/>
              <div className="row">
                <button className="btn sm ghost muted"><FileText size={12}/> All docs <ChevronDown size={11}/></button>
                <div className="seg">
                  <button className="active">Fast</button>
                  <button>Deep</button>
                </div>
                <div className="right">
                  <button className="btn primary sm"><Send size={12}/> Send</button>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right: citations side-panel */}
        <aside style={{ background: "var(--bg-secondary)", display: "flex", flexDirection: "column", minHeight: 0 }}>
          <div style={{ padding: "14px 16px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", gap: 8 }}>
            <FileText size={13} style={{ color: "var(--text-secondary)" }}/>
            <span className="bold small">Sources</span>
            <span className="muted tiny">3 citations</span>
          </div>
          <div className="scroll" style={{ padding: 12, display: "flex", flexDirection: "column", gap: 10 }}>
            {[
              { n: 1, page: 12, snippet: "Wechsler Intelligence Scale for Children, Fifth Edition (WISC-V) was administered to assess overall cognitive ability. Full Scale IQ composite = 88 (Low Average, 25th percentile)…", active: true },
              { n: 2, page: 13, snippet: "Index scores: Verbal Comprehension 92 (Average); Visual Spatial 90; Fluid Reasoning 85 (Low Average); Working Memory 88; Processing Speed 79 (Below Average, 8th percentile)…" },
              { n: 3, page: 14, snippet: "No supplementary cognitive batteries (DAS-II, KABC-II) were administered. Examiner notes that processing-speed weakness should be considered…" },
            ].map((c, i) => (
              <div key={i} className="card" style={{
                padding: 12,
                background: c.active ? "var(--bg-primary)" : "var(--bg-primary)",
                borderColor: c.active ? "var(--accent)" : "var(--border)",
                boxShadow: c.active ? "0 0 0 3px var(--accent-soft)" : "none"
              }}>
                <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 6 }}>
                  <span className="cite-chip" style={{ background: "var(--accent-soft)", color: "var(--accent)", border: "none" }}>
                    <span className="num">{c.n}</span> page {c.page}
                  </span>
                  <span className="muted tiny" style={{ marginLeft: "auto", fontFamily: "var(--font-mono)" }}>eval_2024_REDACTED.pdf</span>
                </div>
                <div className="muted small" style={{ lineHeight: 1.55, fontStyle: "italic" }}>"{c.snippet}"</div>
                <div style={{ marginTop: 8, display: "flex", gap: 6 }}>
                  <button className="btn sm">Open page</button>
                  <button className="btn sm ghost muted">Copy quote</button>
                </div>
              </div>
            ))}
          </div>
        </aside>
      </div>
    </div>
  </div>
);

// ---------- SUMMARIZER — In-progress + result ----------
const B_Summarizer = () => (
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
            <button><History size={12}/></button>
          </div>
        }
      />
      <div className="content">
        <div className="page-h">
          <div>
            <h1>Summarize</h1>
            <div className="sub">Pick a document or upload a new one. We'll generate a structured psychoeducational summary.</div>
          </div>
        </div>

        <div className="composer" style={{ marginBottom: 22 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "4px 4px 0" }}>
            <FileText size={14} style={{ color: "var(--accent)" }}/>
            <span className="bold small">eval_2024_REDACTED.pdf</span>
            <span className="muted tiny">24 pages · ~187 chunks</span>
            <span className="tag" style={{ marginLeft: "auto" }}>standard</span>
          </div>
          <div className="row" style={{ marginTop: 10 }}>
            <button className="btn sm"><FileText size={12}/> Switch document <ChevronDown size={11}/></button>
            <button className="btn sm ghost muted"><Upload size={12}/> Or upload new</button>
            <div className="right">
              <span className="muted tiny">~90s for 24 pages · saved automatically</span>
              <button className="btn primary sm"><Sparkle size={12}/> Generate summary</button>
            </div>
          </div>
        </div>

        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          <div style={{ padding: "12px 18px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", gap: 10 }}>
            <span className="bold small">Summary</span>
            <span className="tag accent">just now</span>
            <span style={{ marginLeft: "auto", display: "flex", gap: 6 }}>
              <button className="btn sm ghost muted"><Copy size={12}/> Copy</button>
              <button className="btn sm ghost muted">Export .txt</button>
            </span>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "200px 1fr", minHeight: 360 }}>
            <nav style={{ borderRight: "1px solid var(--border)", padding: "12px 8px", background: "var(--bg-secondary)" }}>
              {["Student", "Referral", "Cognitive", "Achievement", "Diagnoses", "Recommendations"].map((s, i) => (
                <a key={i} style={{
                  display: "block", padding: "7px 10px", fontSize: 12.5,
                  color: i === 2 ? "var(--accent)" : "var(--text-secondary)",
                  fontWeight: i === 2 ? 600 : 500,
                  borderRadius: 6,
                  background: i === 2 ? "var(--accent-soft)" : "transparent",
                  cursor: "pointer"
                }}>{s}</a>
              ))}
            </nav>
            <div style={{ padding: 22, fontSize: 13.5, lineHeight: 1.65 }}>
              <div className="bold" style={{ fontSize: 15, marginBottom: 4 }}>Cognitive Assessment</div>
              <div className="muted small" style={{ marginBottom: 10 }}>WISC-V · Wechsler Intelligence Scale for Children, 5th edition</div>
              <div className="mono" style={{ fontSize: 12 }}>{`Full Scale IQ           88  (Low Average,    25th %ile)
Verbal Comprehension    92  (Average)
Visual Spatial          90  (Average)
Fluid Reasoning         85  (Low Average)
Working Memory          88  (Average)
Processing Speed        79  (Below Average,   8th %ile)`}</div>
              <p style={{ marginTop: 14, marginBottom: 0 }}>
                Pattern of scores indicates relative weakness in processing speed, with otherwise broadly average cognitive ability. The Processing Speed Index falls 13 points below the FSIQ, a clinically meaningful split warranting targeted accommodations.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
);

// ---------- JARGON ----------
const B_Jargon = () => {
  const levels = [
    { n: 1, label: "Psychologist", desc: "Clinical, DSM-5 preserved" },
    { n: 2, label: "Educator", desc: "For coordinators / IEP team" },
    { n: 3, label: "Parent", desc: "Default · everyday language" },
    { n: 4, label: "High school", desc: "Plain, ~9th grade" },
    { n: 5, label: "Elementary", desc: "Conversational, age 8-10" },
  ];
  return (
    <div className="sp-app">
      <ProjectRail activeProject="Case 2026-014"/>
      <div className="workspace">
        <TopBar crumbs={["Case 2026-014", "Simplify"]}
          right={
            <div className="seg">
              <button><Folder size={12}/></button>
              <button><Message size={12}/></button>
              <button><FileText size={12}/></button>
              <button className="active"><Languages size={12}/></button>
              <button><History size={12}/></button>
            </div>
          }
        />
        <div className="content">
          <div className="page-h">
            <div>
              <h1>Simplify</h1>
              <div className="sub">Rewrite clinical language at the right reading level. Input is never stored beyond a 200-character preview.</div>
            </div>
          </div>

          <div className="card" style={{ padding: 0, overflow: "hidden" }}>
            <div style={{ padding: "10px 14px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", gap: 10 }}>
              <span className="bold small">Reading level</span>
              <div style={{ flex: 1, display: "flex", gap: 4 }}>
                {levels.map((l) => (
                  <button key={l.n} style={{
                    flex: 1,
                    padding: "8px 6px",
                    background: l.n === 3 ? "var(--accent)" : "var(--bg-primary)",
                    color: l.n === 3 ? "white" : "var(--text-secondary)",
                    border: "1px solid " + (l.n === 3 ? "var(--accent)" : "var(--border)"),
                    borderRadius: 8,
                    fontSize: 11.5,
                    fontWeight: 500,
                    display: "flex", flexDirection: "column", alignItems: "center", gap: 2,
                    cursor: "pointer"
                  }}>
                    <span style={{ fontSize: 13, fontWeight: 700 }}>L{l.n}</span>
                    <span>{l.label}</span>
                  </button>
                ))}
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr" }}>
              <div style={{ padding: 18, borderRight: "1px solid var(--border)" }}>
                <div className="rail-label" style={{ padding: "0 0 8px" }}>Clinical input</div>
                <textarea className="textarea" rows={9} defaultValue={"The examinee demonstrated significant deficits in phonological processing as measured by the CTOPP-2, with a Phonological Memory Composite of 74 (4th %ile) and a Phonological Awareness Composite of 71 (3rd %ile). Findings meet DSM-5 criteria for SLD with Impairment in Reading (315.00), consistent with developmental dyslexia."}/>
                <div className="muted tiny" style={{ marginTop: 6, display: "flex", justifyContent: "space-between" }}>
                  <span>342 characters</span>
                  <span>or <a style={{ color: "var(--accent)" }}>upload PDF</a></span>
                </div>
                <button className="btn primary" style={{ width: "100%", justifyContent: "center", marginTop: 12 }}><Sparkle size={13}/> Simplify at Level 3</button>
              </div>
              <div style={{ padding: 18, background: "var(--bg-secondary)" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <span className="rail-label" style={{ padding: 0 }}>Plain-language rewrite</span>
                  <span className="tag accent" style={{ marginLeft: "auto" }}>Level 3 · Parent</span>
                  <span className="tag">FK 7.1</span>
                </div>
                <div style={{ marginTop: 12, fontSize: 14, lineHeight: 1.7 }}>
                  The testing showed that your child has difficulty with the sound-based building blocks of reading — things like remembering the sounds in words and recognizing how words break into smaller sound parts. These scores were in the low range compared to other children the same age, which is why the evaluation found that your child has a reading learning disability (sometimes called dyslexia). This is something we can directly support with the right teaching approach.
                </div>
                <div style={{ display: "flex", gap: 6, marginTop: 14 }}>
                  <button className="btn sm"><Copy size={12}/> Copy</button>
                  <button className="btn sm ghost muted">Try another level</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

window.VariationB = { B_Login, B_Dashboard, B_PIIReview, B_Chat, B_Summarizer, B_Jargon };
