// Pipeline Dashboard — single-glance status of entire research pipeline

function PageDashboard({ tweaks, onNavigate, onAction, actionState }) {
  const activeJob = JOBS.find(j => j.status === "running");
  const completed = JOBS.filter(j => j.status === "completed");
  const failed = JOBS.filter(j => j.status === "failed");
  const queued = JOBS.filter(j => j.status === "queued");
  const onlineResearch = window.TAR_SNAPSHOT?.ONLINE_RESEARCH || {};
  const tokenUsage = window.TAR_SNAPSHOT?.TOKEN_USAGE || {};

  const stages = [
    { num: 1, name: "Data Import", state: "done", meta: "8 datasets" },
    { num: 2, name: "Feature Build", state: "done", meta: "ATR · EMA · RSI · ADX" },
    { num: "3a", name: "Backtest", state: "done", meta: "47 runs" },
    { num: "3b", name: "Walk-Forward", state: "active", meta: "1 running · 64%" },
    { num: 4, name: "Score", state: "todo", meta: "queued · 1" },
    { num: 5, name: "Forward Test", state: "todo", meta: "4 tracked" },
    { num: 6, name: "Export", state: "todo", meta: "manual" },
  ];

  // sparkline equity for active job — synthetic
  const equitySpark = [10000, 10024, 10012, 10038, 10052, 10041, 10068, 10082, 10094, 10078, 10101, 10118, 10142, 10131, 10164, 10182];

  // Tested combos counter
  const testedCount = 47;
  const uniqueStrategies = 9;
  const uniqueSymbols = 6;
  const uniqueTFs = 4;

  return (
    <>
      {/* Top metrics */}
      <div className="grid grid-4" style={{ marginBottom: 16 }}>
        <Metric
          label="Active Job"
          value={activeJob ? activeJob.job_type.replace("_", " ") : "Idle"}
          sub={activeJob ? `${activeJob.strategy} · ${activeJob.symbol} · ${activeJob.tf}` : "No job running"}
        />
        <Metric
          label="Current Equity"
          value={`$10,182`}
          sub="from last backtest · not live"
          tone="good"
        />
        <Metric
          label="Current Drawdown"
          value="-2.1%"
          sub="pre-vol-gate"
        />
        <Metric
          label="Tested Combos"
          value={testedCount}
          sub={`${uniqueStrategies} strat × ${uniqueSymbols} sym × ${uniqueTFs} TF · dedup on`}
        />
      </div>

      {/* Active job card */}
      {activeJob && (
        <Card
          title="Active Job"
          right={
            <>
              <span className="muted mono" style={{ fontSize: 10 }}>job_id</span>
              <code className="mono" style={{ fontSize: 11 }}>{activeJob.job_id}</code>
              <Badge kind="RUNNING" pulse>RUNNING</Badge>
            </>
          }
          style={{ marginBottom: 16 }}
        >
          <div style={{ display: "grid", gridTemplateColumns: "1fr auto", gap: 24, alignItems: "center" }}>
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 8 }}>
                <div>
                  <div className="mono" style={{ fontSize: 14 }}>
                    <strong>{activeJob.job_type}</strong>
                    <span className="dim" style={{ margin: "0 8px" }}>›</span>
                    <span>{activeJob.strategy}</span>
                    <span className="dim" style={{ margin: "0 6px" }}>·</span>
                    <span>{activeJob.symbol}</span>
                    <span className="dim" style={{ margin: "0 6px" }}>·</span>
                    <span>{activeJob.tf}</span>
                  </div>
                  <div className="mono dim" style={{ fontSize: 10.5, marginTop: 4 }}>
                    bars processed: 142,841 / 223,191 · started {timeAgo(activeJob.queued_at)}
                  </div>
                </div>
                <div className="mono" style={{ fontSize: 13 }}>{activeJob.progress}%</div>
              </div>
              <Progress pct={activeJob.progress} />
              <div className="mono dim" style={{ fontSize: 10.5, marginTop: 8 }}>
                last_updated: 2026-05-23T14:20:38Z · refresh ≥ 5s · progress may be stale
              </div>
            </div>
            <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 8 }}>
              <Sparkline data={equitySpark} color="oklch(70% 0.14 235)" width={140} height={36} />
              <div className="mono dim" style={{ fontSize: 10 }}>equity (synthetic, in-flight)</div>
            </div>
          </div>
        </Card>
      )}

      {/* Pipeline stages */}
      <div className="card-head" style={{ marginTop: 8, marginBottom: 8, padding: "0 4px", border: "none" }}>
        <span className="title">Pipeline Stages</span>
        <span className="right muted" style={{ fontSize: 10 }}>CSV → Features → Backtest → Walk-Forward → Score → Forward Test → Export</span>
      </div>
      <div className="stages" style={{ marginBottom: 16 }}>
        {stages.map(s => (
          <div key={s.num} className={`stage ${s.state}`}>
            <div className="num">stage {s.num}</div>
            <div className="name">{s.name}</div>
            <div className="meta">{s.meta}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-2" style={{ marginBottom: 16 }}>
        {/* Quick launch */}
        <Card
          title="Quick Launch"
          right={<span className="muted" style={{ fontSize: 10 }}>{actionState?.busy ? "working..." : "queues only · paper mode"}</span>}
        >
          <div className="grid grid-2" style={{ gap: 8 }}>
            <QuickAction
              code="queue research"
              desc="gold_v2 · XAUUSD · M15"
              disabled={actionState?.busy}
              onClick={() => onAction("/api/jobs/queue-paper-research", { strategy: "gold_v2", symbol: "XAUUSD", timeframe: "M15" }, "Paper research")}
            />
            <QuickAction
              code="queue signal"
              desc="paper_signal · no live trade"
              disabled={actionState?.busy}
              onClick={() => onAction("/api/jobs/queue-paper-signal", { strategy: "gold_v2", symbol: "XAUUSD", timeframe: "M15" }, "Paper signal")}
            />
            <QuickAction
              code="queue all"
              desc="raw CSV sweep · max 24"
              disabled={actionState?.busy}
              onClick={() => onAction("/api/jobs/queue-all-tests", { max_jobs: 24 }, "All tests")}
            />
            <QuickAction
              code="online scout"
              desc={onlineResearch.exa_api_key_set ? "strict · saves hypotheses" : "needs EXA_API_KEY"}
              disabled={actionState?.busy || !onlineResearch.exa_api_key_set}
              onClick={() => onAction("/api/research/scout", {
                query: "gold intraday momentum filter strategy",
                num_results: 3,
                max_workers: 3,
                source_quality: "strict",
                generate_hypotheses: true,
                save_output: true,
              }, "Online scout")}
            />
            <QuickAction
              code="stop active"
              desc="sets stop flags"
              disabled={actionState?.busy}
              onClick={() => onAction("/api/tasks/stop-active", {}, "Stop active")}
            />
          </div>
          {(actionState?.message || actionState?.error) && (
            <div className={`mono ${actionState?.error ? "red" : "dim"}`} style={{ fontSize: 10.5, marginTop: 10 }}>
              {actionState.error || actionState.message}
            </div>
          )}
        </Card>

        {/* Recent jobs */}
        <Card
          title="Recent Jobs"
          right={
            <button onClick={() => onNavigate("jobs")} className="muted" style={{ fontSize: 11 }}>
              View queue →
            </button>
          }
        >
          <table className="table" style={{ marginTop: -8 }}>
            <thead>
              <tr><th>Job</th><th>Strategy</th><th>Status</th><th className="num">Dur</th></tr>
            </thead>
            <tbody>
              {JOBS.slice(0, 6).map(j => (
                <tr key={j.job_id}>
                  <td className="mono">{j.job_type}</td>
                  <td className="mono dim" style={{ fontSize: 11 }}>{j.strategy} <span className="faint">·</span> {j.symbol} <span className="faint">·</span> {j.tf}</td>
                  <td>
                    {j.status === "running" && <Badge kind="RUNNING" pulse>RUNNING</Badge>}
                    {j.status === "queued" && <Badge kind="QUEUED">QUEUED</Badge>}
                    {j.status === "completed" && <Badge kind="COMPLETED">DONE</Badge>}
                    {j.status === "failed" && (
                      <span style={{ display: "inline-flex", gap: 6, alignItems: "center" }}>
                        <Badge kind="FAILED">FAILED</Badge>
                        <ReasonCode code={j.reason_code} />
                      </span>
                    )}
                  </td>
                  <td className="num">{fmtDuration(j.duration_s)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      </div>

      <Card
        title="Token Usage"
        right={<span className="muted" style={{ fontSize: 10 }}>{tokenUsage.tracked ? "tracked locally" : "not tracked"}</span>}
        style={{ marginBottom: 16 }}
      >
        <textarea
          className="token-usage-box mono"
          readOnly
          value={tokenUsage.summary_text || "Token usage is not tracked locally yet."}
          aria-label="Token usage"
        />
      </Card>

      <div className="grid grid-2">
        {/* Top strategies */}
        <Card
          title="Top Strategies by Score"
          right={
            <button onClick={() => onNavigate("explorer")} className="muted" style={{ fontSize: 11 }}>
              Open explorer →
            </button>
          }
        >
          <table className="table" style={{ marginTop: -8 }}>
            <thead>
              <tr>
                <th>Strategy</th>
                <th className="num">Score</th>
                <th className="num">Sharpe</th>
                <th className="num">DD</th>
                <th>Verdict</th>
              </tr>
            </thead>
            <tbody>
              {STRATEGIES.filter(s => s.trades >= 30).slice(0, 6).map((s, i) => (
                <tr key={i} className="clickable" onClick={() => onNavigate("detail", s)}>
                  <td className="mono" style={{ fontSize: 11.5 }}>
                    {s.strategy}
                    <span className="dim" style={{ marginLeft: 6 }}>· {s.symbol} · {s.tf}</span>
                  </td>
                  <td className="num mono">{s.score.toFixed(2)}</td>
                  <td className="num mono">{s.sharpe ? s.sharpe.toFixed(2) : "—"}</td>
                  <td className={`num mono ${ddTone(s.max_dd)}`}>{s.max_dd ? `${s.max_dd.toFixed(1)}%` : "—"}</td>
                  <td><Badge kind={s.verdict} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>

        {/* Automation + Forward tests */}
        <Card title="Forward Tests" right={<span className="muted" style={{ fontSize: 10 }}>paper · last bar shown</span>}>
          <table className="table" style={{ marginTop: -8 }}>
            <thead>
              <tr>
                <th>Strategy</th>
                <th>Last Bar</th>
                <th className="num">P-Equity</th>
                <th className="num">DD</th>
                <th className="num">Trades</th>
              </tr>
            </thead>
            <tbody>
              {FORWARD_TESTS.map((f, i) => (
                <tr key={i}>
                  <td className="mono" style={{ fontSize: 11.5 }}>
                    {f.strategy} <span className="dim">· {f.symbol} · {f.tf}</span>
                  </td>
                  <td className="mono dim" style={{ fontSize: 11 }}>{timeAgo(f.last_bar)}</td>
                  <td className="num mono">${f.paper_equity.toLocaleString()}</td>
                  <td className={`num mono ${ddTone(f.paper_dd)}`}>{f.paper_dd.toFixed(1)}%</td>
                  <td className="num mono">{f.trades}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      </div>
    </>
  );
}

function QuickAction({ code, desc, onClick, disabled }) {
  return (
    <button style={{
      flexDirection: "column",
      alignItems: "flex-start",
      gap: 4,
      padding: "10px 12px",
      textAlign: "left",
      opacity: disabled ? 0.55 : 1,
    }} onClick={onClick} disabled={disabled}>
      <span className="mono" style={{ fontSize: 12, color: "var(--blue)" }}>{code}</span>
      <span className="dim" style={{ fontSize: 10.5 }}>{desc}</span>
    </button>
  );
}

window.PageDashboard = PageDashboard;
