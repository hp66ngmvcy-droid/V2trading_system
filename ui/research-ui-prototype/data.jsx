// Synthetic data for TAR Trading System UI
// Matches schemas from spec: dashboard_run_status, metrics, latest_paper_signal, job_queue

const STRATEGIES = window.TAR_SNAPSHOT?.STRATEGIES || [
  // KEEP candidates
  { strategy: "ema_pullback_v3", symbol: "EURUSD", tf: "H1", score: 0.82, verdict: "KEEP", trades: 287, sharpe: 1.42, sortino: 1.98, win_rate: 0.541, pf: 1.61, max_dd: 11.4, net_pnl: 18420, oos_sharpe: 1.18, spans_zero: false, param_stab: 0.78, has_wf: true, regime: "trend" },
  { strategy: "atr_breakout_v2", symbol: "XAUUSD", tf: "H4", score: 0.79, verdict: "KEEP", trades: 142, sharpe: 1.31, sortino: 1.85, win_rate: 0.486, pf: 1.74, max_dd: 14.8, net_pnl: 22100, oos_sharpe: 1.02, spans_zero: false, param_stab: 0.71, has_wf: true, regime: "volatile" },
  { strategy: "donchian_revert_v1", symbol: "GBPUSD", tf: "H1", score: 0.74, verdict: "KEEP", trades: 198, sharpe: 1.18, sortino: 1.62, win_rate: 0.512, pf: 1.48, max_dd: 13.2, net_pnl: 11240, oos_sharpe: 0.91, spans_zero: false, param_stab: 0.69, has_wf: true, regime: "ranging" },
  { strategy: "ema_pullback_v3", symbol: "USDJPY", tf: "H1", score: 0.71, verdict: "KEEP", trades: 156, sharpe: 1.09, sortino: 1.45, win_rate: 0.532, pf: 1.42, max_dd: 15.1, net_pnl: 8910, oos_sharpe: 0.78, spans_zero: false, param_stab: 0.62, has_wf: true, regime: "trend" },

  // REVIEW
  { strategy: "rsi_div_v4", symbol: "EURUSD", tf: "M15", score: 0.61, verdict: "REVIEW", trades: 412, sharpe: 0.92, sortino: 1.24, win_rate: 0.498, pf: 1.21, max_dd: 18.6, net_pnl: 4280, oos_sharpe: 0.31, spans_zero: true, param_stab: 0.42, has_wf: true, regime: "ranging", reason_codes: ["BOOTSTRAP_CI_SPANS_ZERO"] },
  { strategy: "macd_cross_v2", symbol: "USDJPY", tf: "H4", score: 0.58, verdict: "REVIEW", trades: 87, sharpe: 0.81, sortino: 1.08, win_rate: 0.471, pf: 1.34, max_dd: 19.2, net_pnl: 6120, oos_sharpe: 0.42, spans_zero: false, param_stab: 0.31, has_wf: true, regime: "trend", reason_codes: ["PARAM_UNSTABLE"] },
  { strategy: "bb_squeeze_v1", symbol: "GBPUSD", tf: "M30", score: 0.54, verdict: "REVIEW", trades: 268, sharpe: 0.76, sortino: 0.98, win_rate: 0.481, pf: 1.18, max_dd: 17.4, net_pnl: 3140, oos_sharpe: 0.18, spans_zero: true, param_stab: 0.51, has_wf: true, regime: "ranging", reason_codes: ["LOW_OOS_SHARPE", "BOOTSTRAP_CI_SPANS_ZERO"] },
  { strategy: "atr_breakout_v2", symbol: "EURUSD", tf: "H1", score: 0.52, verdict: "REVIEW", trades: 94, sharpe: 0.71, sortino: 0.92, win_rate: 0.479, pf: 1.22, max_dd: 16.8, net_pnl: 2840, oos_sharpe: 0.29, spans_zero: false, param_stab: 0.48, has_wf: true, regime: "trend", reason_codes: ["LOW_OOS_SHARPE"] },

  // KILL
  { strategy: "trend_follower_v0", symbol: "XAUUSD", tf: "M15", score: 0.21, verdict: "KILL", trades: 18, sharpe: 0.42, sortino: 0.51, win_rate: 0.556, pf: 1.12, max_dd: 28.4, net_pnl: -1240, oos_sharpe: -0.18, spans_zero: true, param_stab: 0.22, has_wf: true, regime: "volatile", reason_codes: ["RISK_MAX_DD", "INSUFFICIENT_TRADES"] },
  { strategy: "rsi_div_v4", symbol: "GBPJPY", tf: "H4", score: 0.18, verdict: "KILL", trades: 64, sharpe: 0.31, sortino: 0.41, win_rate: 0.469, pf: 0.94, max_dd: 42.1, net_pnl: -4820, oos_sharpe: -0.42, spans_zero: true, param_stab: 0.18, has_wf: true, regime: "volatile", reason_codes: ["RISK_MAX_DD"] },
  { strategy: "naive_ma_v1", symbol: "EURUSD", tf: "H4", score: 0.14, verdict: "KILL", trades: 41, sharpe: 0.18, sortino: 0.24, win_rate: 0.488, pf: 0.91, max_dd: 31.2, net_pnl: -2140, oos_sharpe: -0.21, spans_zero: true, param_stab: 0.28, has_wf: true, regime: "ranging", reason_codes: ["RISK_MAX_DD", "DIRECTIONAL_FAIL"] },
  { strategy: "fib_bounce_v1", symbol: "AUDUSD", tf: "H1", score: 0.09, verdict: "KILL", trades: 0, sharpe: null, sortino: null, win_rate: null, pf: null, max_dd: null, net_pnl: null, oos_sharpe: null, spans_zero: null, param_stab: null, has_wf: false, regime: null, reason_codes: ["MISSING_WF", "INSUFFICIENT_TRADES"] },
];

const JOBS = window.TAR_SNAPSHOT?.JOBS || [
  { job_id: "j_8af2c1", job_type: "walk_forward", strategy: "ema_pullback_v3", symbol: "EURUSD", tf: "H1", status: "running", reason_code: null, queued_at: "2026-05-23T14:18:02Z", completed_at: null, duration_s: 142, progress: 64 },
  { job_id: "j_8af2c0", job_type: "backtest", strategy: "atr_breakout_v2", symbol: "XAUUSD", tf: "H4", status: "queued", reason_code: null, queued_at: "2026-05-23T14:19:11Z", completed_at: null, duration_s: null, progress: 0 },
  { job_id: "j_8af2bf", job_type: "score", strategy: "donchian_revert_v1", symbol: "GBPUSD", tf: "H1", status: "queued", reason_code: null, queued_at: "2026-05-23T14:19:14Z", completed_at: null, duration_s: null, progress: 0 },
  { job_id: "j_8af2be", job_type: "backtest", strategy: "ema_pullback_v3", symbol: "USDJPY", tf: "H1", status: "completed", reason_code: null, queued_at: "2026-05-23T13:42:18Z", completed_at: "2026-05-23T13:51:04Z", duration_s: 526, progress: 100 },
  { job_id: "j_8af2bd", job_type: "walk_forward", strategy: "rsi_div_v4", symbol: "EURUSD", tf: "M15", status: "completed", reason_code: null, queued_at: "2026-05-23T13:24:01Z", completed_at: "2026-05-23T13:41:22Z", duration_s: 1041, progress: 100 },
  { job_id: "j_8af2bc", job_type: "paper_signal", strategy: "trend_follower_v0", symbol: "XAUUSD", tf: "M15", status: "failed", reason_code: "ENV_BLOCK_TRADING", queued_at: "2026-05-23T13:18:42Z", completed_at: "2026-05-23T13:18:43Z", duration_s: 1, progress: 0 },
  { job_id: "j_8af2bb", job_type: "score", strategy: "fib_bounce_v1", symbol: "AUDUSD", tf: "H1", status: "failed", reason_code: "DATA_MISSING", queued_at: "2026-05-23T13:12:11Z", completed_at: "2026-05-23T13:12:14Z", duration_s: 3, progress: 0 },
  { job_id: "j_8af2ba", job_type: "backtest", strategy: "macd_cross_v2", symbol: "USDJPY", tf: "H4", status: "completed", reason_code: null, queued_at: "2026-05-23T12:58:02Z", completed_at: "2026-05-23T13:09:48Z", duration_s: 706, progress: 100 },
  { job_id: "j_8af2b9", job_type: "optimise", strategy: "ema_pullback_v3", symbol: "EURUSD", tf: "H1", status: "completed", reason_code: null, queued_at: "2026-05-23T11:42:18Z", completed_at: "2026-05-23T12:54:31Z", duration_s: 4333, progress: 100 },
  { job_id: "j_8af2b8", job_type: "forward_test", strategy: "donchian_revert_v1", symbol: "GBPUSD", tf: "H1", status: "completed", reason_code: null, queued_at: "2026-05-23T11:32:00Z", completed_at: "2026-05-23T11:39:14Z", duration_s: 434, progress: 100 },
  { job_id: "j_8af2b7", job_type: "backtest", strategy: "naive_ma_v1", symbol: "EURUSD", tf: "H4", status: "failed", reason_code: "RISK_GATE_FAIL", queued_at: "2026-05-23T10:42:11Z", completed_at: "2026-05-23T10:48:02Z", duration_s: 351, progress: 100 },
  { job_id: "j_8af2b6", job_type: "walk_forward", strategy: "bb_squeeze_v1", symbol: "GBPUSD", tf: "M30", status: "completed", reason_code: null, queued_at: "2026-05-23T10:14:22Z", completed_at: "2026-05-23T10:38:12Z", duration_s: 1430, progress: 100 },
];

const PAPER_SIGNAL = window.TAR_SNAPSHOT?.PAPER_SIGNAL || {
  strategy: "ema_pullback_v3",
  symbol: "EURUSD",
  timeframe: "H1",
  side: "LONG",
  entry_price: 1.08412,
  stop_loss: 1.07984,
  take_profit: 1.09268,
  confidence: 0.68,
  generated_at: "2026-05-23T14:00:00Z",
  env_risk_state: "SAFE_TO_TEST",
  bar_age: 0,
};

const FORWARD_TESTS = window.TAR_SNAPSHOT?.FORWARD_TESTS || [
  { strategy: "ema_pullback_v3", symbol: "EURUSD", tf: "H1", last_bar: "2026-05-23T14:00Z", paper_equity: 10412, paper_dd: 2.1, trades: 14 },
  { strategy: "atr_breakout_v2", symbol: "XAUUSD", tf: "H4", last_bar: "2026-05-23T12:00Z", paper_equity: 10284, paper_dd: 1.4, trades: 6 },
  { strategy: "donchian_revert_v1", symbol: "GBPUSD", tf: "H1", last_bar: "2026-05-23T14:00Z", paper_equity: 10092, paper_dd: 3.8, trades: 11 },
  { strategy: "ema_pullback_v3", symbol: "USDJPY", tf: "H1", last_bar: "2026-05-23T08:00Z", paper_equity: 10018, paper_dd: 2.6, trades: 9 },
];

const AGENTS = [
  { name: "Quant Analyst", stance: "KEEP", confidence: 0.78, concern: "OOS Sharpe 1.18 holds across 5/6 splits. Bootstrap CI strictly positive [0.42, 1.84]. No regime decay observed." },
  { name: "Risk Manager", stance: "KEEP", confidence: 0.64, concern: "Max DD 11.4% within tolerance, but recovery factor 0.92 is borderline. Suggest position size cap at 0.5% equity per trade." },
  { name: "Trading Advisor", stance: "REVIEW", confidence: 0.52, concern: "Parameter stability 0.78 acceptable but EMA_FAST shows sensitivity at boundary (12 ↔ 14). Recommend forward test 200+ bars before promote." },
];

const WF_SPLITS = [
  { idx: 1, train: "2022-01 / 2022-09", test: "2022-10 / 2022-12", is_sharpe: 1.62, oos_sharpe: 1.31, ratio: 0.81 },
  { idx: 2, train: "2022-04 / 2022-12", test: "2023-01 / 2023-03", is_sharpe: 1.54, oos_sharpe: 1.22, ratio: 0.79 },
  { idx: 3, train: "2022-07 / 2023-03", test: "2023-04 / 2023-06", is_sharpe: 1.71, oos_sharpe: 1.18, ratio: 0.69 },
  { idx: 4, train: "2022-10 / 2023-06", test: "2023-07 / 2023-09", is_sharpe: 1.44, oos_sharpe: 0.94, ratio: 0.65 },
  { idx: 5, train: "2023-01 / 2023-09", test: "2023-10 / 2023-12", is_sharpe: 1.58, oos_sharpe: 1.42, ratio: 0.90 },
  { idx: 6, train: "2023-04 / 2023-12", test: "2024-01 / 2024-03", is_sharpe: 1.62, oos_sharpe: 1.08, ratio: 0.67 },
];

const ANCHOR_PARAMS = [
  { name: "ema_fast", min: 8, max: 21, current: 12, notes: "Standard fast EMA range. Below 8 = noise." },
  { name: "ema_slow", min: 26, max: 89, current: 34, notes: "Must be ≥2× ema_fast." },
  { name: "atr_period", min: 10, max: 28, current: 14, notes: "Bound to bar count for stable stop calc." },
  { name: "atr_mult_stop", min: 1.2, max: 3.5, current: 2.2, notes: "Stop-loss = entry ± N × ATR." },
  { name: "atr_mult_target", min: 1.5, max: 5.0, current: 3.0, notes: "Should yield RR > 1.3." },
  { name: "session_filter", min: 0, max: 1, current: 1, notes: "0=24h, 1=LDN+NY only." },
  { name: "min_trades_gate", min: 30, max: 30, current: 30, notes: "Locked. Hard gate, cannot reduce." },
];

const SWEEP_RESULTS = [
  { params: "ema_fast=10 ema_slow=30 atr=14", score: 0.79, verdict: "KEEP", trades: 312 },
  { params: "ema_fast=12 ema_slow=34 atr=14", score: 0.82, verdict: "KEEP", trades: 287 },
  { params: "ema_fast=14 ema_slow=42 atr=14", score: 0.78, verdict: "KEEP", trades: 241 },
  { params: "ema_fast=12 ema_slow=34 atr=18", score: 0.74, verdict: "KEEP", trades: 268 },
  { params: "ema_fast=10 ema_slow=34 atr=14", score: 0.71, verdict: "KEEP", trades: 294 },
  { params: "ema_fast=16 ema_slow=50 atr=14", score: 0.62, verdict: "REVIEW", trades: 194 },
  { params: "ema_fast=8 ema_slow=26 atr=14", score: 0.58, verdict: "REVIEW", trades: 384 },
  { params: "ema_fast=12 ema_slow=34 atr=10", score: 0.41, verdict: "KILL", trades: 412 },
  { params: "ema_fast=20 ema_slow=60 atr=14", score: 0.38, verdict: "KILL", trades: 78 },
];

const REGIME_HEATMAP = [
  // rows: regime  /  cols: WF split 1..6
  { regime: "trend", values: [1.42, 1.31, 1.28, 0.94, 1.51, 1.18] },
  { regime: "ranging", values: [0.61, 0.42, 0.58, 0.31, 0.71, 0.48] },
  { regime: "volatile", values: [-0.18, 0.12, 0.41, -0.32, 0.28, 0.18] },
  { regime: "low-vol", values: [0.81, 0.92, 0.68, 0.74, 1.04, 0.82] },
];

const COMMITTEE_REPORTS = window.TAR_SNAPSHOT?.COMMITTEE_REPORTS || [
  { strategy: "ema_pullback_v3", symbol: "EURUSD", tf: "H1", verdict: "KEEP", dissent: true, agents: AGENTS, summary: "Strategy demonstrates consistent OOS performance across multiple regimes with acceptable drawdown profile. Trading Advisor flags parameter sensitivity at boundary; recommend extended forward test." },
  { strategy: "atr_breakout_v2", symbol: "XAUUSD", tf: "H4", verdict: "KEEP", dissent: false, agents: [
    { name: "Quant Analyst", stance: "KEEP", confidence: 0.71, concern: "PF 1.74 strong, but pre-cost. Estimate 8-12% PF degradation after broker costs applied." },
    { name: "Risk Manager", stance: "KEEP", confidence: 0.68, concern: "DD 14.8% acceptable for XAU volatility regime. Concentration risk low." },
    { name: "Trading Advisor", stance: "KEEP", confidence: 0.74, concern: "Clean ATR breakout logic, no overfit signal. Proceed to forward test." },
  ], summary: "Unanimous KEEP. Conservative ATR-based breakout with adequate trade count and stable params across splits." },
  { strategy: "rsi_div_v4", symbol: "EURUSD", tf: "M15", verdict: "REVIEW", dissent: true, agents: [
    { name: "Quant Analyst", stance: "REVIEW", confidence: 0.42, concern: "Bootstrap CI [-0.18, 0.84] spans zero — statistical significance not established." },
    { name: "Risk Manager", stance: "KILL", confidence: 0.71, concern: "DD trajectory in WF split 4 hit -22% peak. Recovery factor 0.41 inadequate." },
    { name: "Trading Advisor", stance: "REVIEW", confidence: 0.38, concern: "M15 timeframe noisy for divergence signals. Consider H1 retest before kill." },
  ], summary: "Dissent: Risk recommends KILL. Bootstrap CI spans zero and intra-WF drawdown exceeds tolerance. Recommend H1 retest before kill." },
];

const STATIC_FINDINGS = window.TAR_SNAPSHOT?.STATIC_FINDINGS || [
  { severity: "HIGH", file: "src/tar_system/optimisation/sweep.py", line: 142, desc: "Mutable default argument in `run_sweep(params=[])`", fix: "Use `None` sentinel and create new list inside function." },
  { severity: "HIGH", file: "src/tar_system/backtest/engine.py", line: 84, desc: "Possible division by zero when total_trades == 0", fix: "Guard ratio computations with explicit zero check." },
  { severity: "MEDIUM", file: "src/tar_system/forward/loop.py", line: 211, desc: "Catch-all `except Exception` swallows error context", fix: "Catch specific exceptions; log with reason_code." },
  { severity: "MEDIUM", file: "src/tar_system/data/validate.py", line: 56, desc: "Pandas chained indexing — SettingWithCopyWarning risk", fix: "Use `.loc[row, col] = ...` form." },
  { severity: "LOW", file: "src/tar_system/dashboard/app.py", line: 312, desc: "Unused import: `from typing import Optional`", fix: "Remove unused import." },
  { severity: "LOW", file: "src/tar_system/scoring/composite.py", line: 91, desc: "f-string missing placeholders", fix: "Use regular string or add interpolation." },
];

const FILTER_PLAN = {
  proposed: [
    { name: "EMA slope gate", current: "none", proposed: "EMA_50 slope > 0 for LONG, < 0 for SHORT", impact: "+0.18 OOS Sharpe est." },
    { name: "ATR bounds", current: "none", proposed: "0.4× ATR_30d ≤ ATR_now ≤ 2.0× ATR_30d", impact: "Filters extreme regimes" },
    { name: "Session window", current: "24h", proposed: "08:00 - 17:00 LDN+NY overlap", impact: "Reduces spread, -28% trade count" },
    { name: "News blackout", current: "none", proposed: "Block ± 30min around HIGH-impact events", impact: "Removes 8 worst-DD trades in WF" },
  ],
};

const IMPORTED_DATA = window.TAR_SNAPSHOT?.IMPORTED_DATA || [
  { symbol: "EURUSD", tf: "H1", file: "EURUSD_H1_2022_2026.csv", date_range: "2022-01-03 → 2026-05-22", bars: 27144, status: "validated", hash: "sha:9a82c1" },
  { symbol: "EURUSD", tf: "M15", file: "EURUSD_M15_2023_2026.csv", date_range: "2023-01-02 → 2026-05-22", bars: 87412, status: "validated", hash: "sha:7c12fe" },
  { symbol: "GBPUSD", tf: "H1", file: "GBPUSD_H1_2022_2026.csv", date_range: "2022-01-03 → 2026-05-22", bars: 27144, status: "validated", hash: "sha:24b9aa" },
  { symbol: "USDJPY", tf: "H1", file: "USDJPY_H1_2022_2026.csv", date_range: "2022-01-03 → 2026-05-22", bars: 27082, status: "validated", hash: "sha:cf18ee" },
  { symbol: "XAUUSD", tf: "H4", file: "XAUUSD_H4_2020_2026.csv", date_range: "2020-01-02 → 2026-05-22", bars: 9876, status: "validated", hash: "sha:18a4f1" },
  { symbol: "XAUUSD", tf: "M15", file: "XAUUSD_M15_2024_2026.csv", date_range: "2024-01-01 → 2026-05-22", bars: 48720, status: "validated", hash: "sha:42de98" },
  { symbol: "AUDUSD", tf: "H1", file: "AUDUSD_H1_2023_2024.csv", date_range: "2023-01-03 → 2024-08-12", bars: 9842, status: "failed", reason: "DATA_SPIKE", hash: "sha:e1f0aa" },
  { symbol: "GBPJPY", tf: "H4", file: "GBPJPY_H4_2022_2026.csv", date_range: "2022-01-03 → 2026-05-22", bars: 6786, status: "validated", hash: "sha:ba14cd" },
];

const AUDIT_LOG = window.TAR_SNAPSHOT?.AUDIT_LOG || [
  { ts: "2026-05-23T14:18:42Z", event: "job_failed", code: "ENV_BLOCK_TRADING", strategy: "trend_follower_v0", result: "Signal generation blocked — events.yaml flagged FOMC window" },
  { ts: "2026-05-23T14:12:11Z", event: "job_failed", code: "DATA_MISSING", strategy: "fib_bounce_v1", result: "AUDUSD H1 dataset validation status: failed (DATA_SPIKE)" },
  { ts: "2026-05-23T13:51:04Z", event: "job_completed", code: null, strategy: "ema_pullback_v3", result: "Backtest USDJPY H1 — 156 trades, verdict KEEP" },
  { ts: "2026-05-23T13:41:22Z", event: "verdict_assigned", code: "BOOTSTRAP_CI_SPANS_ZERO", strategy: "rsi_div_v4", result: "REVIEW — bootstrap CI [-0.18, 0.84]" },
  { ts: "2026-05-23T13:18:43Z", event: "signal_blocked", code: "ENV_BLOCK_TRADING", strategy: "trend_follower_v0", result: "Reason: high-impact event within active window" },
  { ts: "2026-05-23T12:54:31Z", event: "optimise_completed", code: null, strategy: "ema_pullback_v3", result: "324 param combos evaluated, top-K=9 promoted to score" },
  { ts: "2026-05-23T10:48:02Z", event: "verdict_assigned", code: "RISK_MAX_DD", strategy: "naive_ma_v1", result: "KILL — Max DD 31.2% exceeds 20% hard gate" },
  { ts: "2026-05-23T10:38:12Z", event: "wf_completed", code: null, strategy: "bb_squeeze_v1", result: "6 splits, OOS Sharpe mean 0.18, spans_zero=True" },
  { ts: "2026-05-23T09:14:08Z", event: "data_imported", code: null, strategy: null, result: "XAUUSD_H4_2020_2026.csv — 9876 bars, validated" },
  { ts: "2026-05-23T08:42:11Z", event: "system_start", code: null, strategy: null, result: "tar daemon initialised, paper_mode=true" },
];

const REASON_CODE_LEGEND = [
  { prefix: "DATA_*", codes: ["DATA_MISSING", "DATA_DUPLICATE", "DATA_SPIKE", "DATA_GAP", "DATA_HASH_MISMATCH"] },
  { prefix: "SIGNAL_*", codes: ["SIGNAL_NO_CONFIDENCE", "SIGNAL_ENV_BLOCKED", "SIGNAL_STALE_BAR"] },
  { prefix: "RISK_*", codes: ["RISK_MAX_DD", "RISK_EXPOSURE_LIMIT", "RISK_CONSECUTIVE_LOSSES", "RISK_GATE_FAIL"] },
  { prefix: "ENV_*", codes: ["ENV_BLOCK_TRADING", "ENV_HOLD_TRADING", "ENV_SHOCK_DETECTED", "ENV_CAUTION"] },
];

// expose
Object.assign(window, {
  STRATEGIES, JOBS, PAPER_SIGNAL, FORWARD_TESTS, AGENTS, WF_SPLITS,
  ANCHOR_PARAMS, SWEEP_RESULTS, REGIME_HEATMAP, COMMITTEE_REPORTS,
  STATIC_FINDINGS, FILTER_PLAN, IMPORTED_DATA, AUDIT_LOG, REASON_CODE_LEGEND,
});
