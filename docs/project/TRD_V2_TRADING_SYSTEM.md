# TRD: TAR V2 Trading Research System

Status: Working Draft
Date: 2026-05-24
Template basis: `docs/templates/source/spec-kit-plan-template.md`

## Summary

The TAR V2 technical design is a local Python research system with a lightweight
browser UI. The backend owns all trading research logic. The browser UI reads a
snapshot bridge and, when write actions are added, must only call narrow
queue/status endpoints.

## Technical Context

| Area | Decision |
|---|---|
| Language | Python 3.14 in current environment |
| Backend package | `src/tar_system` |
| UI | Integrated local HTML/React-style prototype served by stdlib HTTP server |
| Legacy UI | Streamlit dashboard under `src/tar_system/dashboard` |
| Storage | Local files plus DuckDB at `data/tar_system.duckdb` |
| Queue | DuckDB `research_jobs` with JSONL mirror at `runtime/job_queue.jsonl` |
| Tests | pytest |
| Static audit | `tar_system.cli run-local-construction-audit` using opengrep/semgrep wrapper |
| External data | Manual CSV import only; TradingView link is human reference only |

## Architecture

```text
operator
  -> integrated web UI on 127.0.0.1:8601
    -> GET /runtime-data.js
    -> GET /api/snapshot
      -> local runtime JSON/JSONL
      -> local data/results JSON
      -> local data/raw inventory
  -> CLI commands
    -> import/validate/build/backtest/walk-forward/score/queue
      -> data/, runtime/, logs/, reports/
  -> worker/controller
    -> claims queued jobs
    -> writes results and audit records
```

## Runtime Components

- `src/tar_system/cli.py`: command entrypoint.
- `src/tar_system/web_ui/server.py`: integrated V2 web UI server and snapshot bridge.
- `src/tar_system/controller/job_queue.py`: queue, dedupe, DuckDB/JSONL mirror.
- `src/tar_system/controller/research_controller.py`: queued job executor.
- `src/tar_system/dashboard/runtime_control.py`: status, schedule, activity helpers.
- `src/tar_system/data/csv_importer.py`: CSV/tick schema detection and normalization.
- `src/tar_system/scoring/*`: gate and score logic.
- `src/tar_system/dashboard/pages/*`: legacy Streamlit operational views.

## Hard Technical Constraints

- Browser UI must not import backend trading logic into client-side code.
- Browser UI must not place orders or call broker adapters.
- UI write actions, when implemented, must call backend endpoints that only queue jobs or set stop flags.
- Raw data and audit JSONL must remain append-only or immutable from UI.
- Poll interval must be 5 seconds or slower by default.
- Snapshot endpoint must be fast and bounded: no full raw CSV scans on page load.

## API Surface

Current integrated web UI:

- `GET /`: serves `ui/research-ui/index.html`
- `GET /runtime-data.js`: writes `window.TAR_SNAPSHOT = ...`
- `GET /api/snapshot`: returns JSON snapshot
- `GET /prototype/*`: serves prototype JS/CSS assets

Planned write endpoints:

- `POST /api/jobs/queue-paper-research`
- `POST /api/jobs/queue-paper-signal`
- `POST /api/jobs/run-all-tests`
- `POST /api/tasks/stop-active`

All planned writes must be paper-only, local-only, and auditable.

## Security And Safety Requirements

- `PAPER_MODE=True`
- `LIVE_TRADING_ALLOWED=False`
- MT5 export is manual review only.
- No secrets in browser output.
- No arbitrary shell command endpoint.
- No endpoint accepts a raw filesystem path outside approved data roots.

## Testing Requirements

- Web bridge unit tests for snapshot and CLI parser.
- Controller tests for paper signal job branching.
- Dashboard safety tests for queue and promotion behavior.
- Construction audit before major UI/backend merges.

## Known Technical Debt

- Integrated UI still uses CDN React/Babel/Chart.js inherited from prototype.
- Operational controls are not yet wired into integrated UI.
- Existing docs contain older 30-trade wording while promotion gate is moving toward 200-trade manual review.
- Some runtime files are large; snapshot code must keep using bounded reads.

