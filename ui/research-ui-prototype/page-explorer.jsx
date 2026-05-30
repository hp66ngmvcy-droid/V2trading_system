// Strategy Explorer — filterable table of all validated strategies

function PageExplorer({ onNavigate }) {
  const [verdict, setVerdict] = React.useState("ALL");
  const [symbol, setSymbol] = React.useState("ALL");
  const [tf, setTf] = React.useState("ALL");
  const [showLowTrades, setShowLowTrades] = React.useState(false); // <30 trades = hard kill, hidden by default
  const [sort, setSort] = React.useState({ key: "score", dir: "desc" });
  const [search, setSearch] = React.useState("");

  const symbols = ["ALL", ...new Set(STRATEGIES.map(s => s.symbol))];
  const tfs = ["ALL", ...new Set(STRATEGIES.map(s => s.tf))];

  const filtered = STRATEGIES.filter(s => {
    if (verdict !== "ALL" && s.verdict !== verdict) return false;
    if (symbol !== "ALL" && s.symbol !== symbol) return false;
    if (tf !== "ALL" && s.tf !== tf) return false;
    // Hide < 30 trades unless toggle is on (one-trade winners = hard KILL by spec)
    if (!showLowTrades && (s.trades == null || s.trades < 30)) return false;
    if (search && !s.strategy.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  }).sort((a, b) => {
    const av = a[sort.key] ?? -999;
    const bv = b[sort.key] ?? -999;
    return sort.dir === "asc" ? av - bv : bv - av;
  });

  const hiddenCount = STRATEGIES.length - STRATEGIES.filter(s => s.trades != null && s.trades >= 30).length;

  function toggleSort(key) {
    if (sort.key === key) setSort({ key, dir: sort.dir === "asc" ? "desc" : "asc" });
    else setSort({ key, dir: "desc" });
  }

  function SortableHead({ k, children, className }) {
    const active = sort.key === k;
    return (
      <th className={className} onClick={() => toggleSort(k)} style={{ cursor: "pointer", userSelect: "none" }}>
        <span style={{ display: "inline-flex", alignItems: "center", gap: 4 }}>
          {children}
          <span style={{ opacity: active ? 1 : 0.3, fontSize: 9 }}>
            {active ? (sort.dir === "asc" ? "▲" : "▼") : "↕"}
          </span>
        </span>
      </th>
    );
  }

  return (
    <>
      <div className="filter-bar">
        <div className="filter-group">
          <label>Search</label>
          <input
            type="search"
            placeholder="strategy name..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            style={{ width: 180 }}
          />
        </div>

        <div className="filter-group">
          <label>Verdict</label>
          <div className="segmented">
            {["ALL", "KEEP", "REVIEW", "KILL"].map(v => (
              <button key={v} className={verdict === v ? "active" : ""} onClick={() => setVerdict(v)}>{v}</button>
            ))}
          </div>
        </div>

        <div className="filter-group">
          <label>Symbol</label>
          <select value={symbol} onChange={e => setSymbol(e.target.value)}>
            {symbols.map(s => <option key={s}>{s}</option>)}
          </select>
        </div>

        <div className="filter-group">
          <label>TF</label>
          <select value={tf} onChange={e => setTf(e.target.value)}>
            {tfs.map(t => <option key={t}>{t}</option>)}
          </select>
        </div>

        <div className="filter-group">
          <label style={{ cursor: "pointer" }}>
            <input
              type="checkbox"
              checked={showLowTrades}
              onChange={e => setShowLowTrades(e.target.checked)}
              style={{ verticalAlign: "middle", marginRight: 4 }}
            />
            Show &lt;30 trades (hard-KILL, hidden by default)
          </label>
        </div>

        <div className="spacer" />
        <span className="count">
          {filtered.length} / {STRATEGIES.length} strategies
          {!showLowTrades && hiddenCount > 0 && <span className="dim"> · {hiddenCount} hidden by trade gate</span>}
        </span>
      </div>

      <Callout kind="info" ico="i">
        All <strong>profit factor</strong> and <strong>P&amp;L</strong> values are <strong>pre-cost</strong>. Stage 1 broker costs not yet applied.
        <strong> Max DD</strong> values are <strong>pre-vol-gate</strong> (Stage 2). Backtest scores ≠ forward-test scores.
      </Callout>

      <div className="table-wrap" style={{ marginTop: 12 }}>
        <table className="table">
          <thead>
            <tr>
              <SortableHead k="strategy">Strategy</SortableHead>
              <th>Symbol</th>
              <th>TF</th>
              <SortableHead k="score" className="num">Score</SortableHead>
              <th>Verdict</th>
              <SortableHead k="trades" className="num">Trades</SortableHead>
              <SortableHead k="sharpe" className="num">Sharpe</SortableHead>
              <SortableHead k="oos_sharpe" className="num">OOS Sharpe</SortableHead>
              <SortableHead k="win_rate" className="num">Win %</SortableHead>
              <SortableHead k="pf" className="num">PF<sup className="dim" style={{fontSize:8, marginLeft:2}}>*pre-cost</sup></SortableHead>
              <SortableHead k="max_dd" className="num">Max DD</SortableHead>
              <th>Flags</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((s, i) => {
              const greyed = s.trades != null && s.trades < 30;
              const ddT = ddTone(s.max_dd);
              return (
                <tr
                  key={i}
                  className={`clickable ${greyed ? "greyed" : ""} ${s.verdict === "KILL" ? "killed" : ""}`}
                  onClick={() => onNavigate("detail", s)}
                >
                  <td className="mono">{s.strategy}</td>
                  <td className="mono">{s.symbol}</td>
                  <td className="mono">{s.tf}</td>
                  <td className="num mono">{s.score.toFixed(2)}</td>
                  <td><Badge kind={s.verdict} /></td>
                  <td className="num mono">{s.trades ?? "—"}</td>
                  <td className="num mono">{s.sharpe != null ? s.sharpe.toFixed(2) : "—"}</td>
                  <td className="num mono">
                    {s.oos_sharpe != null ? s.oos_sharpe.toFixed(2) : "—"}
                    {s.spans_zero && <span title="bootstrap CI spans zero" style={{ color: "var(--red)", marginLeft: 4 }}>⚠</span>}
                  </td>
                  <td className="num mono">{s.win_rate != null ? `${(s.win_rate * 100).toFixed(1)}%` : "—"}</td>
                  <td className="num mono">{s.pf != null ? s.pf.toFixed(2) : "—"}</td>
                  <td className={`num mono ${ddT}`}>{s.max_dd != null ? `${s.max_dd.toFixed(1)}%` : "—"}</td>
                  <td style={{ maxWidth: 200 }}>
                    {!s.has_wf && <ReasonCode code="MISSING_WF" />}
                    {s.reason_codes && s.reason_codes.map(c => (
                      <ReasonCode key={c} code={c} kind={s.verdict === "REVIEW" ? "warn" : ""} />
                    ))}
                  </td>
                </tr>
              );
            })}
            {filtered.length === 0 && (
              <tr><td colSpan="12" style={{ padding: 40, textAlign: "center", color: "var(--text-3)" }}>No strategies match current filters.</td></tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="row-flex" style={{ marginTop: 14, gap: 16, fontSize: 11 }}>
        <span className="muted mono" style={{ textTransform: "uppercase", letterSpacing: "0.08em", fontSize: 10 }}>Legend</span>
        <span><Badge kind="KEEP" /> <span className="dim">≥30 trades · OOS Sharpe &gt; 0 · WF exists · all hard gates pass</span></span>
        <span><Badge kind="REVIEW" /> <span className="dim">soft gate breach</span></span>
        <span><Badge kind="KILL" /> <span className="dim">hard gate fail</span></span>
        <span className="dim">·</span>
        <span className="dim mono" style={{ fontSize: 10 }}>DD: amber &gt;20% · red &gt;40%</span>
        <span className="dim">·</span>
        <span className="dim mono" style={{ fontSize: 10 }}>⚠ bootstrap CI spans zero</span>
      </div>
    </>
  );
}

window.PageExplorer = PageExplorer;
