# App Flow: TAR V2 Trading Research System

Status: Working Draft
Date: 2026-05-24

## Primary Research Flow

```text
1. Import CSV
   -> data/raw/{SYMBOL}_{TIMEFRAME}.csv

2. Validate Data
   -> data/validated/{SYMBOL}_{TIMEFRAME}.parquet

3. Build Features
   -> data/features/{SYMBOL}_{TIMEFRAME}.parquet

4. Queue Research Job
   -> runtime/job_queue.jsonl
   -> data/tar_system.duckdb: research_jobs

5. Worker Claims Job
   -> status RUNNING
   -> runtime/dashboard_run_status.json

6. Backtest / Full Pipeline
   -> data/results/*_metrics.json
   -> reports/*.md

7. Walk-Forward / Robustness Checks
   -> data/results/*_walk_forward.json
   -> data/results/*_monte_carlo.json
   -> data/results/*_parameter_sensitivity.json

8. Scoring And Gates
   -> KEEP / REVIEW / KILL
   -> reason codes
   -> result index / memory records

9. Forward Test / Paper Signal
   -> data/results/*_forward_test.json
   -> runtime/latest_paper_signal.json

10. Manual Review
   -> research committee packet
   -> promotion board
   -> manual MT5 review only
```

## Integrated UI Flow

```text
Open http://127.0.0.1:8601
  -> index.html
  -> runtime-data.js
    -> build_snapshot()
      -> strategies from data/results
      -> jobs from runtime/job_queue.jsonl
      -> signals from runtime/latest_paper_signal.json
      -> audit rows from logs/audit/audit.jsonl
      -> raw data inventory from data/raw
  -> React shell renders dashboard/explorer/detail
  -> polls /api/snapshot every 5s
```

## Legacy Streamlit Operational Flow

```text
streamlit run src/tar_system/dashboard/app.py
  -> Run Backtest / Forward Test / Paper Signals pages
  -> queue jobs or invoke safe runtime helpers
  -> writes runtime status/activity
```

## Future Safe Action Flow

```text
Integrated UI button
  -> POST local endpoint
  -> validate paper-only request
  -> add_job(...)
  -> append audit/activity
  -> UI sees queued job on next 5s snapshot
```

Allowed future actions:

- Queue paper research job.
- Queue paper signal job.
- Queue run-all-tests batch.
- Request stop active task.
- Refresh snapshot.

Forbidden actions:

- Place trade.
- Broker login.
- Promote live.
- Edit strategy parameters in browser.
- Delete raw data.
- Delete audit/job history.

