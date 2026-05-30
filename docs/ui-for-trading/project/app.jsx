// Main app shell: env banner + sidebar + router

const NAV = [
  { id: "dashboard", label: "Pipeline", icon: "▸", kbd: "1", enabled: true },
  { id: "explorer", label: "Strategies", icon: "▤", kbd: "2", enabled: true },
  { id: "jobs", label: "Jobs", icon: "⌷", kbd: "3", enabled: false },
  { id: "signals", label: "Signals", icon: "↯", kbd: "4", enabled: false },
  { id: "optim", label: "Optimisation", icon: "◫", kbd: "5", enabled: false },
  { id: "research", label: "Research", icon: "✎", kbd: "6", enabled: false },
  { id: "audit", label: "Data & Audit", icon: "❡", kbd: "7", enabled: false },
];

const ENV_STATES = {
  SAFE_TO_TEST: { cls: "safe", text: "No high-impact events in window. System cleared for signal generation." },
  CAUTION: { cls: "caution", text: "Event scheduled within 4h window. Monitor closely; reduce position sizing." },
  HOLD_TRADING: { cls: "hold", text: "Active high-impact window in progress. New signals paused until window closes." },
  BLOCK_TRADING: { cls: "block", text: "Hard block active. Signal generation disabled. Cannot be overridden from UI." },
};

function App() {
  const t = useTweaks(/*EDITMODE-BEGIN*/{
    "theme": "dark",
    "density": "normal",
    "env_state": "SAFE_TO_TEST",
    "accent": "blue"
  }/*EDITMODE-END*/);

  // Apply theme + density to root
  React.useEffect(() => {
    document.documentElement.setAttribute("data-theme", t.theme);
    document.documentElement.setAttribute("data-density", t.density);
    document.documentElement.style.setProperty(
      "--accent",
      t.accent === "amber" ? "var(--amber)" : t.accent === "green" ? "var(--green)" : t.accent === "violet" ? "var(--violet)" : "var(--blue)"
    );
    document.documentElement.style.setProperty(
      "--accent-bg",
      t.accent === "amber" ? "var(--amber-bg)" : t.accent === "green" ? "var(--green-bg)" : t.accent === "violet" ? "oklch(70% 0.15 295 / 0.12)" : "var(--blue-bg)"
    );
  }, [t.theme, t.density, t.accent]);

  const [page, setPage] = React.useState("dashboard");
  const [selectedStrategy, setSelectedStrategy] = React.useState(null);

  function navigate(target, payload) {
    if (target === "detail") setSelectedStrategy(payload || STRATEGIES[0]);
    setPage(target);
    window.scrollTo({ top: 0, behavior: "instant" });
  }

  // Keyboard nav
  React.useEffect(() => {
    function onKey(e) {
      if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA" || e.target.tagName === "SELECT") return;
      const item = NAV.find(n => n.kbd === e.key);
      if (item && item.enabled) navigate(item.id);
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const envState = t.env_state;
  const env = ENV_STATES[envState];

  const pageTitle = {
    dashboard: { title: "Pipeline Dashboard", crumb: "home / pipeline" },
    explorer: { title: "Strategy Explorer", crumb: "strategies / explorer" },
    detail: { title: selectedStrategy ? `${selectedStrategy.strategy}` : "Strategy Detail", crumb: `strategies / ${selectedStrategy ? `${selectedStrategy.strategy}_${selectedStrategy.symbol}_${selectedStrategy.tf}` : "—"}` },
  }[page] || { title: "Not implemented", crumb: page };

  return (
    <div className="app">
      {/* Env banner — top of every page */}
      <div className={`env-banner ${env.cls}`}>
        <span className="pulse" />
        <span className="state-code">{envState}</span>
        <span style={{ opacity: 0.9 }}>{env.text}</span>
        <span className="right">
          <span>paper_mode=<strong>true</strong></span>
          <span>live_trading_allowed=<strong>false</strong></span>
          <span>{new Date().toISOString().replace(/\.\d+Z$/, "Z")}</span>
        </span>
      </div>

      {/* Sidebar */}
      <nav className="sidebar">
        <div className="brand">
          <div className="mark">T</div>
          <div className="name">TAR</div>
          <div className="ver">v2.4</div>
        </div>

        <div className="section-label">Research</div>
        {NAV.map(n => (
          <div
            key={n.id}
            className={`nav-item ${page === n.id || (page === "detail" && n.id === "explorer") ? "active" : ""}`}
            onClick={() => n.enabled && navigate(n.id)}
            style={{ opacity: n.enabled ? 1 : 0.4, cursor: n.enabled ? "pointer" : "not-allowed" }}
            title={n.enabled ? "" : "Not implemented in this prototype"}
          >
            <span className="nav-icon mono">{n.icon}</span>
            <span>{n.label}</span>
            <span className="nav-kbd">{n.kbd}</span>
          </div>
        ))}

        <div className="spacer" />

        <div className="footer">
          <div className="row"><span>daemon</span><span className="ok">● running</span></div>
          <div className="row"><span>queue</span><span>{JOBS.filter(j => j.status === "queued").length} queued</span></div>
          <div className="row"><span>poll</span><span>5s</span></div>
          <div className="row"><span>build</span><span>a92f1c8</span></div>
        </div>
      </nav>

      {/* Main */}
      <main className="main">
        <div className="page-head">
          <div>
            <div className="crumb">{pageTitle.crumb}</div>
            <h1>{pageTitle.title}</h1>
          </div>
          <div className="actions">
            <span className="timestamp"><span className="dot" />last sync · 4s ago</span>
            <button className="icon" title="Refresh">↻</button>
          </div>
        </div>

        {page === "dashboard" && <PageDashboard tweaks={t} onNavigate={navigate} />}
        {page === "explorer" && <PageExplorer onNavigate={navigate} />}
        {page === "detail" && <PageDetail strategy={selectedStrategy} onNavigate={navigate} />}
        {!["dashboard", "explorer", "detail"].includes(page) && (
          <Card title="Not implemented">
            <div style={{ padding: 24, textAlign: "center" }} className="muted">
              <p>This screen is not part of the current prototype scope.</p>
              <p className="dim mono" style={{ fontSize: 11 }}>scope: Pipeline Dashboard · Strategy Explorer · Strategy Detail</p>
            </div>
          </Card>
        )}
      </main>

      {/* Tweaks */}
      <TweaksPanel title="Tweaks">
        <TweakSection title="Appearance">
          <TweakRadio
            label="Theme"
            value={t.theme}
            onChange={(v) => t.setTweak("theme", v)}
            options={[{ value: "dark", label: "Dark" }, { value: "light", label: "Light" }]}
          />
          <TweakRadio
            label="Density"
            value={t.density}
            onChange={(v) => t.setTweak("density", v)}
            options={[
              { value: "compact", label: "Compact" },
              { value: "normal", label: "Normal" },
              { value: "comfortable", label: "Roomy" },
            ]}
          />
          <TweakColor
            label="Accent"
            value={t.accent}
            onChange={(v) => t.setTweak("accent", v)}
            options={[
              { value: "blue", color: "oklch(70% 0.14 235)" },
              { value: "green", color: "oklch(70% 0.15 150)" },
              { value: "amber", color: "oklch(78% 0.15 75)" },
              { value: "violet", color: "oklch(70% 0.15 295)" },
            ]}
          />
        </TweakSection>
        <TweakSection title="Environment Risk (simulate)">
          <TweakSelect
            label="State"
            value={t.env_state}
            onChange={(v) => t.setTweak("env_state", v)}
            options={[
              { value: "SAFE_TO_TEST", label: "SAFE_TO_TEST" },
              { value: "CAUTION", label: "CAUTION" },
              { value: "HOLD_TRADING", label: "HOLD_TRADING" },
              { value: "BLOCK_TRADING", label: "BLOCK_TRADING (red banner)" },
            ]}
          />
          <div className="mono dim" style={{ fontSize: 10, marginTop: 6, lineHeight: 1.5 }}>
            Spec rule: BLOCK_TRADING cannot be overridden from UI in production.
            This tweak exists only to preview banner states.
          </div>
        </TweakSection>
      </TweaksPanel>
    </div>
  );
}

// Custom TweakColor variant accepting {value, color} objects
function TweakColor({ label, value, onChange, options }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 6, marginBottom: 10 }}>
      <div className="mono" style={{ fontSize: 10, color: "var(--text-3)", textTransform: "uppercase", letterSpacing: "0.08em" }}>{label}</div>
      <div style={{ display: "flex", gap: 6 }}>
        {options.map(o => (
          <button
            key={o.value}
            onClick={() => onChange(o.value)}
            style={{
              width: 28, height: 28,
              borderRadius: 4,
              background: o.color,
              border: value === o.value ? "2px solid var(--text)" : "1px solid var(--border)",
              padding: 0,
              cursor: "pointer",
            }}
            title={o.value}
          />
        ))}
      </div>
    </div>
  );
}

// Custom radio that uses our segmented style
function TweakRadio({ label, value, onChange, options }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 6, marginBottom: 10 }}>
      <div className="mono" style={{ fontSize: 10, color: "var(--text-3)", textTransform: "uppercase", letterSpacing: "0.08em" }}>{label}</div>
      <div className="segmented" style={{ width: "fit-content" }}>
        {options.map(o => (
          <button key={o.value} className={value === o.value ? "active" : ""} onClick={() => onChange(o.value)}>
            {o.label}
          </button>
        ))}
      </div>
    </div>
  );
}

function TweakSelect({ label, value, onChange, options }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 6, marginBottom: 10 }}>
      <div className="mono" style={{ fontSize: 10, color: "var(--text-3)", textTransform: "uppercase", letterSpacing: "0.08em" }}>{label}</div>
      <select value={value} onChange={(e) => onChange(e.target.value)}>
        {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>
    </div>
  );
}

function TweakSection({ title, children }) {
  return (
    <div style={{ marginBottom: 16 }}>
      <div className="mono" style={{
        fontSize: 10,
        textTransform: "uppercase",
        letterSpacing: "0.1em",
        color: "var(--text-2)",
        marginBottom: 10,
        paddingBottom: 6,
        borderBottom: "1px solid var(--border)",
      }}>{title}</div>
      {children}
    </div>
  );
}

function useTweaks(defaults) {
  const [state, setState] = React.useState(defaults);

  React.useEffect(() => {
    function onMsg(e) {
      if (e.data?.type === "__edit_mode_set_keys") {
        setState(s => ({ ...s, ...e.data.edits }));
      }
    }
    window.addEventListener("message", onMsg);
    return () => window.removeEventListener("message", onMsg);
  }, []);

  function setTweak(key, value) {
    setState(s => ({ ...s, [key]: value }));
    window.parent.postMessage({ type: "__edit_mode_set_keys", edits: { [key]: value } }, "*");
  }

  return { ...state, setTweak };
}

// Minimal TweaksPanel that wires the host protocol
function TweaksPanel({ title = "Tweaks", children }) {
  const [open, setOpen] = React.useState(false);

  React.useEffect(() => {
    function onMsg(e) {
      if (e.data?.type === "__activate_edit_mode") setOpen(true);
      if (e.data?.type === "__deactivate_edit_mode") setOpen(false);
    }
    window.addEventListener("message", onMsg);
    window.parent.postMessage({ type: "__edit_mode_available" }, "*");
    return () => window.removeEventListener("message", onMsg);
  }, []);

  function close() {
    setOpen(false);
    window.parent.postMessage({ type: "__edit_mode_dismissed" }, "*");
  }

  if (!open) return null;
  return (
    <div style={{
      position: "fixed",
      right: 20, bottom: 20,
      width: 320,
      maxHeight: "80vh",
      background: "var(--panel)",
      border: "1px solid var(--border-strong)",
      borderRadius: 6,
      boxShadow: "0 8px 32px rgba(0,0,0,0.5)",
      padding: 16,
      overflow: "auto",
      zIndex: 9999,
      fontFamily: "var(--sans)",
    }}>
      <div style={{
        display: "flex",
        alignItems: "center",
        marginBottom: 14,
        paddingBottom: 10,
        borderBottom: "1px solid var(--border)",
      }}>
        <span className="mono" style={{ fontSize: 12, fontWeight: 600, letterSpacing: "0.04em" }}>{title}</span>
        <button className="icon" onClick={close} style={{ marginLeft: "auto", padding: "2px 8px" }}>✕</button>
      </div>
      {children}
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
