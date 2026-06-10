# Backend Schema: TAR V2 Trading Research System

Status: Working Draft
Date: 2026-05-24

## Storage Overview

| Area | Path / Table | Purpose |
|---|---|---|
| Raw data | `data/raw/{SYMBOL}_{TIMEFRAME}.csv` | Imported CSV/tick-derived OHLCV source |
| Validated data | `data/validated/{SYMBOL}_{TIMEFRAME}.parquet` | Clean validated bars |
| Features | `data/features/{SYMBOL}_{TIMEFRAME}.parquet` | Indicator/features for strategies |
| Results | `data/results/*.json` | Metrics, walk-forward, forward-test artifacts |
| Queue DB | `data/tar_system.duckdb: research_jobs` | Operational job queue |
| Queue mirror | `runtime/job_queue.jsonl` | Human/audit-readable queue mirror |
| Dashboard status | `runtime/dashboard_run_status.json` | Current task state |
| Paper signal | `runtime/latest_paper_signal.json` | Latest paper-only signal |
| Audit log | `logs/audit/audit.jsonl` | Append-only reason-code audit |
| Reports | `reports/*.md` | Human-readable research output |

## Queue Schema

DuckDB table: `research_jobs`

Important columns:

- `job_id`
- `type`
- `strategy`
- `symbol`
- `timeframe`
- `file`
- `broker`
- `status`
- `priority`
- `data_hash`
- `params_hash`
- `created_at`
- `started_at`
- `completed_at`
- `result_path`
- `recommendation`
- `cost_sensitive`
- `swap_drag`
- `session_filter_used`
- `from_date`
- `to_date`
- `forward_from_date`
- `skip_walk_forward`
- `skip_forward_test`
- `max_walk_forward_splits`
- `research_stage`
- `no_live`
- `no_mt5_promotion`
- `require_walk_forward`
- `require_min_trades`
- `min_trades`

Statuses:

- `QUEUED`
- `RUNNING`
- `COMPLETED`
- `FAILED`
- `SKIPPED`

Active statuses:

- `QUEUED`
- `RUNNING`

Deduplication key:

```text
strategy + symbol + timeframe + type + COALESCE(data_hash, file)
+ from_date + to_date + research_stage
```

## Snapshot Schema

Endpoint: `GET /api/snapshot`

```json
{
  "generated_at": "ISO8601",
  "STRATEGIES": [],
  "JOBS": [],
  "PAPER_SIGNAL": {},
  "FORWARD_TESTS": [],
  "COMMITTEE_REPORTS": [],
  "STATIC_FINDINGS": [],
  "IMPORTED_DATA": [],
  "AUDIT_LOG": []
}
```

The browser also loads the same payload through:

```text
GET /runtime-data.js
```

## Strategy Row Shape

```json
{
  "strategy": "gold_v2",
  "symbol": "XAUUSD",
  "tf": "M15",
  "score": 70.0,
  "verdict": "KEEP|REVIEW|KILL",
  "trades": 240,
  "sharpe": 1.2,
  "sortino": 1.4,
  "win_rate": 0.55,
  "pf": 1.6,
  "max_dd": 8.0,
  "net_pnl": 100.0,
  "oos_sharpe": 0.8,
  "spans_zero": false,
  "param_stab": 0.7,
  "has_wf": true,
  "regime": "unknown",
  "reason_codes": [],
  "live_chart_url": "https://www.tradingview.com/chart/..."
}
```

## Forward Test Row Shape

```json
{
  "strategy": "gold_v2",
  "symbol": "XAUUSD",
  "tf": "M15",
  "last_bar": "ISO8601 or timestamp string",
  "paper_equity": 10000.0,
  "paper_dd": 0.0,
  "trades": 0
}
```

Values must be numeric where the UI calls numeric formatting methods.

## Paper Signal Shape

```json
{
  "strategy": "gold_v2",
  "symbol": "XAUUSD",
  "timeframe": "M15",
  "side": "LONG|SHORT|FLAT",
  "entry": 0.0,
  "entry_price": 0.0,
  "stop_loss": 0.0,
  "take_profit": 0.0,
  "confidence": 0.0,
  "risk_approved": false,
  "risk_reason": "SIGNAL_HOLD",
  "environment_state": "SAFE_TO_TEST",
  "paper_only": true
}
```

## Audit Row Shape

```json
{
  "ts": "ISO8601",
  "event": "event_type",
  "code": "REASON_CODE",
  "strategy": "gold_v2",
  "result": "COMPLETED|FAILED|SKIPPED"
}
```

## Invariants

- Raw files are immutable from UI.
- JSONL audit/job history is not deleted from UI.
- Snapshot reads are bounded and must not scan full raw CSV files.
- Browser payloads should normalize nulls before rendering.

