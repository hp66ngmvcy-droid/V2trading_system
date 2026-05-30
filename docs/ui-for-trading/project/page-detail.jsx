// Strategy Detail View — all panels A–F per spec

function PageDetail({ strategy, onNavigate }) {
  const s = strategy || STRATEGIES[0];
  const chartRef = React.useRef(null);
  const chartInstance = React.useRef(null);

  // Find committee report
  const committee = COMMITTEE_REPORTS.find(c =>
    c.strategy === s.strategy && c.symbol === s.symbol && c.tf === s.tf
  ) || COMMITTEE_REPORTS[0];

  // Generate synthetic equity curves
  const eqData = React.useMemo(() => generateEquityCurves(s), [s.strategy, s.symbol, s.tf]);

  React.useEffect(() => {
    if (!chartRef.current || !window.Chart) return;

    if (chartInstance.current) chartInstance.current.destroy();

    // Manually size the canvas (responsive: false)
    const container = chartRef.current.parentElement;
    const sizeCanvas = () => {
      if (!chartRef.current || !container) return;
      const dpr = window.devicePixelRatio || 1;
      const w = container.clientWidth;
      const h = container.clientHeight;
      chartRef.current.width = w * dpr;
      chartRef.current.height = h * dpr;
      chartRef.current.style.width = w + "px";
      chartRef.current.style.height = h + "px";
    };
    sizeCanvas();

    const getCssVar = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

    const blue = getCssVar("--blue") || "#5b8def";
    const amber = getCssVar("--amber") || "#d9a55b";
    const green = getCssVar("--green") || "#4caf78";
    const border = getCssVar("--border") || "#1f242d";
    const text3 = getCssVar("--text-3") || "#5a6170";
    const text2 = getCssVar("--text-2") || "#8b929e";

    chartInstance.current = new Chart(chartRef.current, {
      type: "line",
      data: {
        labels: eqData.labels,
        datasets: [
          {
            label: "Backtest equity",
            data: eqData.backtest,
            borderColor: blue,
            backgroundColor: blue + "1f",
            borderWidth: 1.6,
            pointRadius: 0,
            fill: { target: "origin", above: blue + "10" },
            tension: 0.15,
          },
          {
            label: "Walk-forward OOS",
            data: eqData.wf,
            borderColor: amber,
            borderWidth: 1.4,
            pointRadius: 0,
            borderDash: [4, 3],
            fill: false,
            tension: 0.15,
          },
          {
            label: "Paper equity",
            data: eqData.paper,
            borderColor: green,
            borderWidth: 1.8,
            pointRadius: 0,
            fill: false,
            tension: 0.1,
          },
        ],
      },
      options: {
        responsive: false,
        maintainAspectRatio: false,
        interaction: { intersect: false, mode: "index" },
        plugins: {
          legend: {
            position: "top",
            align: "end",
            labels: {
              color: text2,
              font: { family: "JetBrains Mono, monospace", size: 10 },
              boxWidth: 10,
              boxHeight: 2,
              padding: 14,
            },
          },
          tooltip: {
            backgroundColor: "#0a0c10",
            borderColor: border,
            borderWidth: 1,
            titleFont: { family: "JetBrains Mono, monospace", size: 10 },
            bodyFont: { family: "JetBrains Mono, monospace", size: 11 },
            padding: 10,
            titleColor: text3,
            bodyColor: "#e6e8eb",
            callbacks: {
              label: (ctx) => `${ctx.dataset.label}: $${ctx.parsed.y?.toLocaleString("en-US", { maximumFractionDigits: 0 }) ?? "—"}`,
            },
          },
        },
        scales: {
          x: {
            grid: { color: border, drawTicks: false },
            ticks: {
              color: text3,
              font: { family: "JetBrains Mono, monospace", size: 9 },
              maxRotation: 0,
              autoSkipPadding: 24,
            },
          },
          y: {
            grid: { color: border, drawTicks: false },
            ticks: {
              color: text3,
              font: { family: "JetBrains Mono, monospace", size: 9 },
              callback: (v) => `$${(v / 1000).toFixed(0)}k`,
            },
          },
        },
      },
    });

    return () => {
      if (chartInstance.current) {
        chartInstance.current.destroy();
        chartInstance.current = null;
      }
    };
  }, [eqData, s.strategy]);

  const tone = s.verdict === "KEEP" ? "good" : s.verdict === "REVIEW" ? "warn" : "bad";
  const isReviewable = s.trades != null && s.trades >= 30;
  const wfMissing = !s.has_wf;

  // Gates
  const hardGates = [
    { name: "≥ 30 trades", state: (s.trades ?? 0) >= 30 ? "pass" : "fail", value: s.trades ?? 0 },
    { name: "Max DD < 20%", state: s.max_dd != null && s.max_dd < 20 ? "pass" : s.max_dd == null ? "fail" : "fail", value: s.max_dd != null ? `${s.max_dd.toFixed(1)}%` : "—" },
    { name: "Not directionally failed", state: "pass", value: "OK" },
    { name: "WF data present", state: s.has_wf ? "pass" : "fail", value: s.has_wf ? "OK" : "missing" },
    { name: "Not 1-trade winner", state: (s.trades ?? 0) > 1 ? "pass" : "fail", value: (s.trades ?? 0) > 1 ? "OK" : "1 trade" },
  ];
  const softGates = [
    { name: "OOS Sharpe > 0", state: s.oos_sharpe != null && s.oos_sharpe > 0 ? "pass" : "warn", value: s.oos_sharpe != null ? s.oos_sharpe.toFixed(2) : "—" },
    { name: "Bootstrap CI excl. zero", state: s.spans_zero === false ? "pass" : s.spans_zero === true ? "warn" : "warn", value: s.spans_zero === false ? "[+, +]" : s.spans_zero === true ? "spans 0" : "—" },
    { name: "Param stability > 0.5", state: s.param_stab != null && s.param_stab > 0.5 ? "pass" : "warn", value: s.param_stab != null ? s.param_stab.toFixed(2) : "—" },
    { name: "Profit factor > 1.3", state: s.pf != null && s.pf > 1.3 ? "pass" : "warn", value: s.pf != null ? s.pf.toFixed(2) : "—" },
    { name: "Win rate > 45%", state: s.win_rate != null && s.win_rate > 0.45 ? "pass" : "warn", value: s.win_rate != null ? `${(s.win_rate * 100).toFixed(1)}%` : "—" },
  ];

  // Params (synthetic for selected strategy)
  const params = getParams(s);

  return (
    <>
      <div className="row-flex" style={{ marginBottom: 14, justifyContent: "space-between" }}>
        <button onClick={() => onNavigate("explorer")} style={{ fontSize: 11 }}>
          ← Back to Explorer
        </button>
        <div className="row-flex">
          <span className="mono dim" style={{ fontSize: 10 }}>last_updated</span>
          <code className="mono" style={{ fontSize: 11 }}>2026-05-23T14:18:02Z</code>
          <span className="muted">·</span>
          <span className="staleness">↻ 5s poll</span>
        </div>
      </div>

      {/* Title strip */}
      <div className="card" style={{ marginBottom: 16, padding: "18px 20px", display: "grid", gridTemplateColumns: "1fr auto", gap: 16, alignItems: "center" }}>
        <div>
          <div className="mono dim" style={{ fontSize: 10, letterSpacing: "0.08em", textTransform: "uppercase" }}>Strategy</div>
          <div className="mono" style={{ fontSize: 20, marginTop: 4 }}>
            {s.strategy}
            <span className="dim" style={{ margin: "0 10px" }}>·</span>
            <span>{s.symbol}</span>
            <span className="dim" style={{ margin: "0 10px" }}>·</span>
            <span>{s.tf}</span>
          </div>
          <div className="row-flex" style={{ marginTop: 8, gap: 8 }}>
            <span className="tag">regime: {s.regime || "—"}</span>
            <span className="tag">score {s.score?.toFixed(2) ?? "—"}</span>
            {s.spans_zero && <span className="tag" style={{ color: "var(--red)", borderColor: "var(--red-border)" }}>bootstrap CI spans zero</span>}
          </div>
        </div>
        <div style={{ textAlign: "right" }}>
          <div className="mono dim" style={{ fontSize: 10, letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 6 }}>Final Verdict</div>
          <div style={{ display: "inline-flex", alignItems: "center", gap: 10 }}>
            <span style={{
              fontFamily: "var(--mono)",
              fontWeight: 700,
              fontSize: 26,
              letterSpacing: "0.05em",
              color: s.verdict === "KEEP" ? "var(--green)" : s.verdict === "REVIEW" ? "var(--amber)" : "var(--red)",
            }}>{s.verdict}</span>
          </div>
          {committee.dissent && (
            <div className="mono" style={{ fontSize: 10.5, color: "var(--amber)", marginTop: 4 }}>
              ⚠ committee dissent
            </div>
          )}
        </div>
      </div>

      {wfMissing && (
        <Callout kind="bad" ico="✕">
          <strong>Missing WF data — KEEP blocked.</strong> Strategy cannot receive KEEP verdict without walk-forward results.
          Queue: <code className="mono">tar walk-forward --strategy {s.strategy} --symbol {s.symbol} --tf {s.tf}</code>
        </Callout>
      )}
      {s.spans_zero && (
        <Callout kind="bad" ico="!" >
          <strong>Bootstrap CI spans zero.</strong> Statistical significance of OOS Sharpe not established —
          the confidence interval includes zero. Treat results with hard caution; do not promote to forward test
          without addressing.
        </Callout>
      )}

      {/* Panel A — Key Metrics */}
      <SectionLabel>A · Key Metrics</SectionLabel>
      <div className="grid grid-4" style={{ marginBottom: 8 }}>
        <Metric label="Sharpe (Backtest)" value={s.sharpe != null ? s.sharpe.toFixed(2) : "—"} sub="risk-adjusted return" tone={tone} />
        <Metric label="OOS Sharpe (WF mean)" value={s.oos_sharpe != null ? s.oos_sharpe.toFixed(2) : "—"} sub="walk-forward · out-of-sample" tone={s.oos_sharpe > 0.8 ? "good" : s.oos_sharpe > 0 ? "warn" : "bad"} />
        <Metric label="Sortino" value={s.sortino != null ? s.sortino.toFixed(2) : "—"} sub="downside-deviation adjusted" />
        <Metric label="Win Rate" value={s.win_rate != null ? `${(s.win_rate * 100).toFixed(1)}%` : "—"} sub={`${s.trades ?? "—"} trades`} />
      </div>
      <div className="grid grid-4" style={{ marginBottom: 16 }}>
        <Metric label="Profit Factor" value={s.pf != null ? s.pf.toFixed(2) : "—"} sub="*pre-cost · Stage 1 incomplete" tone={s.pf > 1.3 ? "" : "warn"} />
        <Metric label="Max Drawdown" value={s.max_dd != null ? `${s.max_dd.toFixed(1)}%` : "—"} sub="*pre-vol-gate" tone={ddBadgeTone(s.max_dd)} />
        <Metric label="Recovery Factor" value={s.max_dd != null && s.net_pnl != null ? (s.net_pnl / (s.max_dd * 100)).toFixed(2) : "—"} sub="net P&L / max DD$" />
        <Metric label="Param Stability" value={s.param_stab != null ? s.param_stab.toFixed(2) : "—"} sub="0=unstable · 1=stable" tone={s.param_stab > 0.6 ? "good" : "warn"} />
      </div>

      {/* Panel B — Equity Curve */}
      <SectionLabel right={
        <div className="row-flex" style={{ gap: 14, fontSize: 10 }}>
          <span><LegendDot color="var(--blue)" /> backtest</span>
          <span><LegendDot color="var(--amber)" /> walk-forward OOS</span>
          <span><LegendDot color="var(--green)" /> paper</span>
        </div>
      }>B · Equity Curve</SectionLabel>
      <Card flat style={{ marginBottom: 16 }}>
        <div className="card-body" style={{ padding: 14 }}>
          <div style={{ height: 320, position: "relative" }}>
            <canvas ref={chartRef} />
          </div>
        </div>
      </Card>

      {/* Panel C — Walk-Forward Splits */}
      <SectionLabel right={
        s.has_wf
          ? <span className="muted mono" style={{ fontSize: 10 }}>{WF_SPLITS.length} splits · rolling 9m train / 3m test</span>
          : <span className="reason-code">MISSING_WF</span>
      }>C · Walk-Forward Splits</SectionLabel>
      {s.has_wf ? (
        <div className="table-wrap" style={{ marginBottom: 16 }}>
          <table className="table">
            <thead>
              <tr>
                <th>#</th>
                <th>Train period</th>
                <th>Test period</th>
                <th className="num">IS Sharpe</th>
                <th className="num">OOS Sharpe</th>
                <th className="num">IS/OOS ratio</th>
                <th>Stability</th>
              </tr>
            </thead>
            <tbody>
              {WF_SPLITS.map(w => (
                <tr key={w.idx}>
                  <td className="mono">{w.idx}</td>
                  <td className="mono dim">{w.train}</td>
                  <td className="mono">{w.test}</td>
                  <td className="num mono">{w.is_sharpe.toFixed(2)}</td>
                  <td className="num mono">{w.oos_sharpe.toFixed(2)}</td>
                  <td className={`num mono ${w.ratio < 0.5 ? "red" : w.ratio < 0.7 ? "amber" : ""}`}>{w.ratio.toFixed(2)}</td>
                  <td>
                    {w.ratio < 0.5 && <Badge kind="FAIL">UNSTABLE</Badge>}
                    {w.ratio >= 0.5 && w.ratio < 0.7 && <Badge kind="WARN">SOFT</Badge>}
                    {w.ratio >= 0.7 && <Badge kind="PASS">STABLE</Badge>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <Card flat style={{ marginBottom: 16, padding: 30, textAlign: "center" }}>
          <div className="mono dim">No walk-forward data for this strategy. Run <code>tar walk-forward</code>.</div>
        </Card>
      )}

      {/* Panel D — Multi-Agent Committee */}
      <SectionLabel right={
        <div className="row-flex" style={{ gap: 10 }}>
          {committee.dissent && <Badge kind="REVIEW">DISSENT</Badge>}
          <span className="muted mono" style={{ fontSize: 10 }}>3 agents · consensus {committee.verdict}</span>
        </div>
      }>D · Research Committee</SectionLabel>
      <div className="grid grid-3" style={{ marginBottom: 12 }}>
        {committee.agents.map((a, i) => (
          <div key={i} className="agent">
            <div className="name">{a.name}</div>
            <div className="stance">
              <Badge kind={a.stance} />
              <span className="dim mono" style={{ fontSize: 10 }}>conf {a.confidence.toFixed(2)}</span>
            </div>
            <div className="conf-bar">
              <div className="fill" style={{ width: `${a.confidence * 100}%`, background: a.stance === "KEEP" ? "var(--green)" : a.stance === "REVIEW" ? "var(--amber)" : "var(--red)" }} />
            </div>
            <div className="concern">{a.concern}</div>
          </div>
        ))}
      </div>
      <details className="collapsible" style={{ marginBottom: 16 }}>
        <summary>Committee markdown report — {s.strategy}_{s.symbol}_{s.tf}_committee.md</summary>
        <div className="content">{`# Research Committee — ${s.strategy} · ${s.symbol} · ${s.tf}

Verdict: ${committee.verdict}${committee.dissent ? " (dissent)" : ""}
Quorum: 3/3 agents responded

## Summary
${committee.summary}

## Agent stances
${committee.agents.map(a => `- **${a.name}** — ${a.stance} (conf ${a.confidence.toFixed(2)})
  > ${a.concern}`).join("\n")}

## Recommendation
${committee.verdict === "KEEP" ? "Promote to forward test (paper). Re-evaluate after 200 paper bars or 30d, whichever first." : ""}
${committee.verdict === "REVIEW" ? "Hold for human review. Address dissent and re-run committee before promotion." : ""}
${committee.verdict === "KILL" ? "Archive. Do not promote. Reason codes attached to strategy_memory.jsonl." : ""}`}</div>
      </details>

      {/* Panel E — Gate Status */}
      <SectionLabel>E · Gate Status</SectionLabel>
      <div className="grid grid-2" style={{ marginBottom: 16 }}>
        <Card title="Hard Gates" right={<span className="muted mono" style={{ fontSize: 10 }}>{hardGates.filter(g => g.state === "pass").length}/{hardGates.length} pass</span>}>
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {hardGates.map((g, i) => <Gate key={i} {...g} />)}
          </div>
        </Card>
        <Card title="Soft Gates" right={<span className="muted mono" style={{ fontSize: 10 }}>{softGates.filter(g => g.state === "pass").length}/{softGates.length} pass</span>}>
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {softGates.map((g, i) => <Gate key={i} {...g} />)}
          </div>
        </Card>
      </div>

      {/* Panel F — Parameter Block */}
      <SectionLabel right={<span className="muted mono" style={{ fontSize: 10 }}>read-only · CLI edits only · one parameter at a time</span>}>F · Parameters</SectionLabel>
      <div className="grid grid-2" style={{ marginBottom: 16 }}>
        <Card title="Current Parameters">
          <dl className="kv">
            {params.map(p => (
              <React.Fragment key={p.name}>
                <dt>{p.name}</dt>
                <dd>
                  {p.value}
                  {p.diff != null && (
                    <span className={p.diff > 0 ? "amber" : "amber"} style={{ marginLeft: 8, fontSize: 10 }}>
                      Δ {p.diff > 0 ? "+" : ""}{p.diff} vs baseline
                    </span>
                  )}
                </dd>
              </React.Fragment>
            ))}
          </dl>
        </Card>
        <Card title="Locked Baseline" right={<span className="muted mono" style={{ fontSize: 10 }}>last promote · 2026-04-12</span>}>
          <dl className="kv">
            {params.map(p => (
              <React.Fragment key={p.name}>
                <dt>{p.name}</dt>
                <dd className="dim">{p.baseline ?? p.value}</dd>
              </React.Fragment>
            ))}
          </dl>
        </Card>
      </div>

      <Callout ico="i">
        To change a parameter:&nbsp;
        <code className="mono">tar set-param --strategy {s.strategy} --symbol {s.symbol} --tf {s.tf} --param &lt;name&gt; --value &lt;v&gt;</code>
        <br />
        <span className="dim">One change per run. Multi-param edits are blocked.</span>
      </Callout>
    </>
  );
}

function SectionLabel({ children, right }) {
  return (
    <div style={{
      display: "flex",
      alignItems: "center",
      padding: "8px 4px",
      marginTop: 8,
      marginBottom: 10,
      borderBottom: "1px solid var(--border)",
    }}>
      <span className="mono" style={{ fontSize: 11, color: "var(--text-2)", textTransform: "uppercase", letterSpacing: "0.1em" }}>
        {children}
      </span>
      {right && <span style={{ marginLeft: "auto" }}>{right}</span>}
    </div>
  );
}

function LegendDot({ color }) {
  return <span style={{ display: "inline-block", width: 8, height: 2, background: color, verticalAlign: "middle", marginRight: 5 }} />;
}

// ---- synthetic generators ----

function seedFrom(s) {
  // simple string hash → seed
  const str = `${s.strategy}|${s.symbol}|${s.tf}`;
  let h = 2166136261;
  for (let i = 0; i < str.length; i++) { h ^= str.charCodeAt(i); h = (h * 16777619) >>> 0; }
  return h;
}

function mulberry32(a) {
  return function() {
    let t = (a += 0x6D2B79F5);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function generateEquityCurves(s) {
  const rand = mulberry32(seedFrom(s));
  const N = 180;
  const labels = [];
  const start = new Date(2024, 0, 1);
  for (let i = 0; i < N; i++) {
    const d = new Date(start);
    d.setDate(d.getDate() + Math.floor(i * 5.5));
    labels.push(d.toISOString().slice(0, 10));
  }

  // backtest: trend up if KEEP, sideways/down if KILL
  const direction = s.verdict === "KEEP" ? 1 : s.verdict === "REVIEW" ? 0.3 : -0.5;
  const vol = s.max_dd ? s.max_dd / 100 : 0.15;
  let bt = 10000;
  const backtest = [bt];
  for (let i = 1; i < N; i++) {
    const ret = direction * 0.0018 + (rand() - 0.5) * vol * 0.06;
    bt *= 1 + ret;
    backtest.push(bt);
  }

  // walk-forward OOS: starts at split boundary, more noisy
  const wfStart = Math.floor(N * 0.65);
  const wf = labels.map((_, i) => {
    if (i < wfStart) return null;
    const t = i - wfStart;
    let v = backtest[wfStart];
    const r2 = mulberry32(seedFrom(s) ^ 0xA5A5);
    for (let k = 0; k <= t; k++) {
      const ret = direction * 0.0011 + (r2() - 0.5) * vol * 0.08;
      v *= 1 + ret;
    }
    return v;
  });

  // paper equity: very recent only
  const paperStart = Math.floor(N * 0.88);
  const paper = labels.map((_, i) => {
    if (i < paperStart) return null;
    const t = i - paperStart;
    let v = (wf[paperStart] ?? backtest[paperStart]);
    const r3 = mulberry32(seedFrom(s) ^ 0x5A5A);
    for (let k = 0; k <= t; k++) {
      const ret = direction * 0.0009 + (r3() - 0.5) * vol * 0.05;
      v *= 1 + ret;
    }
    return v;
  });

  return { labels, backtest, wf, paper };
}

function getParams(s) {
  // synthetic param set keyed loosely by strategy family
  if (s.strategy.startsWith("ema")) {
    return [
      { name: "ema_fast", value: 12, baseline: 12 },
      { name: "ema_slow", value: 34, baseline: 30, diff: 4 },
      { name: "atr_period", value: 14, baseline: 14 },
      { name: "atr_mult_stop", value: 2.2, baseline: 2.2 },
      { name: "atr_mult_target", value: 3.0, baseline: 3.0 },
      { name: "session_filter", value: "LDN+NY", baseline: "LDN+NY" },
      { name: "min_trades_gate", value: 30, baseline: 30 },
    ];
  }
  if (s.strategy.startsWith("atr")) {
    return [
      { name: "atr_period", value: 20, baseline: 14, diff: 6 },
      { name: "atr_mult_stop", value: 2.8, baseline: 2.2 },
      { name: "breakout_lookback", value: 50, baseline: 50 },
      { name: "session_filter", value: "24h", baseline: "LDN+NY" },
      { name: "min_trades_gate", value: 30, baseline: 30 },
    ];
  }
  return [
    { name: "lookback", value: 20, baseline: 20 },
    { name: "threshold", value: 1.5, baseline: 1.5 },
    { name: "session_filter", value: "LDN+NY", baseline: "LDN+NY" },
    { name: "min_trades_gate", value: 30, baseline: 30 },
  ];
}

window.PageDetail = PageDetail;
