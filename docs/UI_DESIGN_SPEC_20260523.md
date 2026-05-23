# V2 TAR Trading System — Web UI Design Specification

## System Overview

**What it is:** Paper-only quantitative trading research system. Ingests MT5 CSV data, runs backtests/walk-forward validation, scores strategies, generates paper signals, manages a research pipeline via async job queue.

**What it is NOT:** No live trading. No external APIs. No cloud dependencies. Local-only. Read results from JSON/JSONL/Parquet files.

**Primary user:** Solo quant researcher running multi-step strategy validation pipeline.

---

## Tech Constraints (inform API layer design)

- Backend: Python CLI (`tar` commands), outputs to JSON/JSONL files in `runtime/`, `data/`, `reports/`
- No real-time broker feed — data is static CSV snapshots from MT5
- Paper mode hard-enforced: `PAPER_MODE=True`, `LIVE_TRADING_ALLOWED=False`
- No Docker, no Ray, no Polars — lightweight deps only
- Existing Streamlit dashboard (`src/tar_system/dashboard/app.py`) is current reference
- File locations: `runtime/*.json`, `data/results/*.json`, `data/paper_strategies/*.json`, `reports/*.md`

---

## Screens Required

### 1. Pipeline Dashboard (Home)

**Purpose:** Single-glance status of entire research pipeline.

**Data sources:**
- `runtime/dashboard_run_status.json` — current task (job name, progress %, bars, equity, DD)
- `runtime/automation_schedule.json` — recurring jobs
- `runtime/tested_data_registry.json` — how many strategy/symbol/TF combos tested

**Display:**
- Active job card: name, progress bar, current equity, current drawdown
- Pipeline stage tracker: `CSV Import → Features → Backtest → Walk-Forward → Score → Forward Test`
- Tested combo count (dedup guard counter)
- Quick-launch buttons for common CLI commands (queue a job, not execute directly)

**Known issues to avoid:**
- Do NOT show a "run live" or "activate" button — paper-only, must be explicit
- Do NOT auto-refresh faster than 5s — file I/O is heavy
- Progress % from `dashboard_run_status.json` can be stale — show last-updated timestamp
- No real-time equity feed — equity shown is from last completed backtest, not live

---

### 2. Strategy Explorer

**Purpose:** Browse all validated strategies with scores and gate verdicts.

**Data sources:**
- `data/results/{strategy}_{symbol}_{TF}_metrics.json` — backtest metrics
- `data/results/{strategy}_{symbol}_{TF}_walk_forward.json` — OOS Sharpe, parameter stability, bootstrap CI
- `runtime/research_committee_{strategy}_{symbol}_{TF}.json` — multi-agent verdict
- `data/memory/strategy_memory.jsonl` — append-only run log

**Display:**
- Filterable table: strategy, symbol, timeframe, score, verdict (KEEP/REVIEW/KILL), trade count, Sharpe, win rate, PF, max DD
- Row click → detail view
- Verdict badge colour: KEEP=green, REVIEW=amber, KILL=red
- Sort by score descending by default

**Known issues to avoid:**
- Do NOT show strategies with < 30 trades as viable — hard kill gate, grey out or hide
- Do NOT show one-trade "winners" — one-trade optimiser winners are hard KILL
- DD column: >20% = amber, >40% = red
- PF column: label "pre-cost" — broker costs not yet deducted (Stage 1 incomplete)
- Do NOT conflate backtest score with forward-test score — these are separate

---

### 3. Strategy Detail View

**Purpose:** Full metrics, equity curve, walk-forward splits, agent verdicts for one strategy.

**Data sources:**
- `data/results/{strategy}_{symbol}_{TF}_metrics.json`
- `data/results/{strategy}_{symbol}_{TF}_walk_forward.json`
- `runtime/research_committee_{strategy}_{symbol}_{TF}.md` / `.json`
- `data/paper_strategies/{strategy}_{symbol}_{TF}_paper.json`
- `reports/{symbol}_{TF}_{strategy}_report.md`

**Display sections:**

**A. Key Metrics Panel**
- Sharpe, Sortino, Win Rate, Profit Factor (pre-cost), Max DD, Trade Count, Recovery Factor
- OOS Sharpe, Parameter Stability score, Bootstrap CI — spans_zero=True = hard warning

**B. Equity Curve Chart**
- Backtest equity (blue)
- Walk-forward OOS equity overlay (orange)
- Paper equity if available (green)
- Drawdown periods shaded

**C. Walk-Forward Splits Table**
- Each split: train start/end, test start/end, OOS Sharpe, IS Sharpe, IS/OOS ratio
- IS/OOS ratio < 0.5 = red flag

**D. Multi-Agent Committee Panel**
- 3 agents: Quant Analyst, Risk Manager, Trading Advisor
- Each: stance, confidence, key concern
- Consensus verdict + dissent flag if disagreement
- Committee markdown report (collapsible)

**E. Gate Status**
- Hard gates (pass/fail): ≥30 trades, max DD <20%, not directionally failed
- Soft gates (pass/warn): OOS Sharpe >0, parameter stability, PF, win rate
- Final verdict badge

**F. Parameter Block**
- Current params read-only
- Show diff from locked baseline if available

**Known issues to avoid:**
- No parameter editing from this screen — changes via CLI only (one-at-a-time rule)
- No "promote to live" button anywhere
- `spans_zero=True` = hard warning, not subtle badge
- Missing WF data = show "Missing WF — KEEP blocked" explicitly

---

### 4. Job Queue Manager

**Purpose:** Submit, monitor, cancel async research jobs.

**Data sources:**
- `runtime/job_queue.jsonl` — append-only job log
- `runtime/dashboard_run_status.json` — active job status

**Display:**
- Job list: ID, type, strategy/symbol/TF, status badge, queued time, duration, result
- Status badges: QUEUED (grey), RUNNING (blue pulse), COMPLETED (green), FAILED (red)
- Failed jobs: show reason code (e.g. `DATA_MISSING`, `RISK_GATE_FAIL`, `ENV_BLOCK_TRADING`)
- Submit new job form: select job type, strategy, symbol, TF
- Cancel button for QUEUED jobs only

**Known issues to avoid:**
- Block duplicate submission for same strategy/symbol/TF/data_hash
- FAILED jobs must show reason code — no generic "failed"
- Re-running failed job requires acknowledgment of what failed
- Job history is append-only — no delete, no edit

---

### 5. Paper Signal Monitor

**Purpose:** View latest paper signal, forward-test status, environment risk state.

**Data sources:**
- `runtime/latest_paper_signal.json`
- `runtime/forward_test_{strategy}_{symbol}_{TF}.json`
- Environment risk state (derived from `configs/events.yaml`)

**Display:**
- Latest Signal Card: symbol, direction (LONG/SHORT/FLAT), entry, SL, TP, confidence, timestamp
- Environment Risk Banner: SAFE_TO_TEST / CAUTION / HOLD_TRADING / BLOCK_TRADING
  - `BLOCK_TRADING` = full-width red banner at top of page
  - `HOLD_TRADING` = amber warning
- Forward Test Status table: strategy, symbol, TF, last bar, paper equity, paper DD, trade count
- "Generate Signal Now" → queues `run-paper-signal` job (does not execute directly)

**Known issues to avoid:**
- `BLOCK_TRADING` cannot be overridden from UI
- Stale signals (>1 bar old) must show staleness warning
- Label as "signal confidence" not "probability of profit"

---

### 6. Optimisation Explorer

**Purpose:** Review parameter sweep results, approved anchors, regime heatmap.

**Data sources:**
- `data/results/optimisation_*.json`
- `src/tar_system/optimisation/parameter_anchors.py` (static reference)
- Regime heatmap outputs

**Display:**
- Anchor parameter table: name, approved range (min/max), notes
- Sweep results table: parameter combo, score, verdict, trade count
- Static callout: "One parameter change at a time"
- Regime heatmap (regime × WF split → Sharpe colour grid)

**Known issues to avoid:**
- UI is read-only — no multi-parameter changes
- Filter single-trade winners from all results views
- Label all results "pre-cost" (Stage 1 broker costs not yet applied)
- Label all DD values "pre-vol-gate" (Stage 2 volatility gates not yet applied)

---

### 7. Research Committee Report Viewer

**Purpose:** Read committee reports, filter fitter output, AI review packet.

**Data sources:**
- `runtime/research_committee_*.md` / `*.json`
- `runtime/strategy_filter_plan.md` / `*.json`
- `runtime/ai_review_packet.md`
- `runtime/static_analysis/opengrep.json`

**Display:**
- Committee report cards: strategy, agents, stances, key concerns, recommendation
- Filter plan: proposed thresholds (EMA slope gate, ATR bounds, session window)
- AI Review Packet: top-K candidates (read-only)
- Static analysis findings: severity (HIGH/MEDIUM/LOW), file, line, fix

**Known issues to avoid:**
- No "approve for live" action anywhere
- HIGH severity static analysis findings must be visually prominent — not buried
- Filter plan thresholds are proposals, not active config

---

### 8. Data & Audit Log

**Purpose:** Track imported data, validation results, audit trail.

**Data sources:**
- `runtime/tested_data_registry.json`
- `data/validated/` file list
- Audit JSONL (reason code events)

**Display:**
- Imported datasets table: symbol, TF, file, date range, bar count, validation status
- Audit event log: timestamp, event type, reason code, strategy, result
- Reason code legend

**Known issues to avoid:**
- Raw files in `data/raw/` are immutable — no delete/edit buttons near them
- Validation failures must show specific reason code
- Re-import blocked without explicit hash check

---

## Pipeline Stage Glossary

| Stage | Label | What it does |
|-------|-------|-------------|
| 1 | Data Import | MT5 CSV → validated Parquet |
| 2 | Feature Build | Parquet → technical indicators Parquet |
| 3a | Backtest | Event-driven simulated trades on history |
| 3b | Walk-Forward | Rolling OOS splits, param stability, bootstrap CI |
| 4 | Score | Composite score + hard/soft gates + multi-agent verdict |
| 5 | Forward Test | Incremental paper-only bar loop, paper equity |
| 6 | Export | MT5 CSV/JSON bundle for manual review |

---

## Environment Risk States

| State | Colour | Meaning |
|-------|--------|---------|
| `SAFE_TO_TEST` | Green | No high-impact events |
| `CAUTION` | Yellow | Event within 4h window |
| `HOLD_TRADING` | Amber | Active high-impact window |
| `BLOCK_TRADING` | Red full-banner | Hard block — no signals generated |

---

## Verdict Badge Reference

| Verdict | Colour | Conditions |
|---------|--------|-----------|
| KEEP | Green | All hard gates pass, OOS Sharpe >0, WF exists, ≥30 trades |
| REVIEW | Amber | Soft gate breach (low OOS Sharpe, unstable params, bootstrap CI spans zero) |
| KILL | Red | Hard gate fail: <30 trades, DD >20%, 100% directional, 1-trade winner, missing WF |

---

## Reason Code Reference

| Prefix | Examples |
|--------|---------|
| `DATA_*` | `DATA_MISSING`, `DATA_DUPLICATE`, `DATA_SPIKE` |
| `SIGNAL_*` | `SIGNAL_NO_CONFIDENCE`, `SIGNAL_ENV_BLOCKED` |
| `RISK_*` | `RISK_MAX_DD`, `RISK_EXPOSURE_LIMIT`, `RISK_CONSECUTIVE_LOSSES` |
| `ENV_*` | `ENV_BLOCK_TRADING`, `ENV_HOLD_TRADING`, `ENV_SHOCK_DETECTED` |

Always display full code — never collapse to "failed."

---

## Key Data Schemas

### `runtime/dashboard_run_status.json`
```json
{
  "task_name": "string",
  "progress_pct": 0,
  "bars_processed": 0,
  "current_equity": 0.0,
  "current_drawdown_pct": 0.0,
  "last_updated": "ISO8601"
}
```

### `data/results/{strategy}_{symbol}_{TF}_metrics.json`
```json
{
  "strategy": "string",
  "symbol": "string",
  "timeframe": "string",
  "sharpe_ratio": 0.0,
  "sortino_ratio": 0.0,
  "win_rate": 0.0,
  "profit_factor": 0.0,
  "max_drawdown_pct": 0.0,
  "total_trades": 0,
  "net_pnl": 0.0,
  "verdict": "KEEP|REVIEW|KILL",
  "reason_codes": ["string"]
}
```

### `runtime/latest_paper_signal.json`
```json
{
  "strategy": "string",
  "symbol": "string",
  "timeframe": "string",
  "side": "LONG|SHORT|FLAT",
  "entry_price": 0.0,
  "stop_loss": 0.0,
  "take_profit": 0.0,
  "confidence": 0.0,
  "generated_at": "ISO8601",
  "env_risk_state": "SAFE_TO_TEST|CAUTION|HOLD_TRADING|BLOCK_TRADING"
}
```

### `runtime/job_queue.jsonl`
```json
{
  "job_id": "string",
  "job_type": "backtest|walk_forward|score|forward_test|paper_signal|optimise",
  "strategy": "string",
  "symbol": "string",
  "timeframe": "string",
  "status": "queued|running|completed|failed",
  "reason_code": "string|null",
  "queued_at": "ISO8601",
  "completed_at": "ISO8601|null"
}
```

---

## Navigation Structure

```
Home (Pipeline Dashboard)
├── Strategies
│   ├── Explorer (table)
│   └── [strategy] Detail
├── Jobs (Queue Manager)
├── Signals (Paper Monitor)
├── Optimisation
├── Research (Committee + Filter Plans)
└── Data & Audit
```

---

## Global Rules — What the UI Must Never Do

- Show a "go live" / "activate" / "trade now" button
- Allow parameter editing in-browser
- Delete or overwrite any file in `data/raw/`, memory JSONL, or job JSONL
- Hide reason codes on failures
- Show KEEP verdict when walk-forward data is missing
- Display one-trade results as viable candidates

## Visual Hierarchy Priorities

1. Environment risk state (BLOCK_TRADING) — always visible, top of every page
2. Gate verdict (KEEP/REVIEW/KILL) — prominent badge, colour coded
3. Reason codes on failures — never collapsed by default
4. Drawdown — always visible alongside Sharpe, never hidden
5. Timestamp on all signal/result displays — stale data clearly marked

## Data Refresh

- Poll interval: 5s minimum for job status
- All metrics: static until job completes — no fake real-time
- Show last-updated timestamp on every data card
