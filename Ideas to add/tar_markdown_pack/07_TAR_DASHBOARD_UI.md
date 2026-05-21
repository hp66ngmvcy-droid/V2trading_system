# TAR Dashboard UI

## Objective

Create a clear Streamlit dashboard so the user always knows:

- what is running
- what is stopped
- what data is selected
- what strategy is being tested
- what the system is doing
- whether live trading is disabled

---

## Pages

```text
Overview
Backtests
Memory
GitHub Review
Run Backtest
Audit Log
Security
Librarian
```

---

## Overview Page

Show:

- system status
- paper mode status
- live trading disabled status
- latest score
- phase gates
- risk alerts
- current running task

---

## Run Backtest Page

Must include:

- start button
- stop button
- auto-run toggle
- symbol dropdown
- timeframe dropdown
- strategy dropdown
- date picker
- terminal/log viewer
- progress status
- current stage label

---

## Backtests Page

Show:

- result table
- equity curve
- drawdown chart
- win rate
- expectancy
- Sharpe or simplified risk score
- KEEP / REVISE / KILL workflow

---

## Memory Page

Show:

- strategy memory records
- filters by asset
- filters by timeframe
- filters by verdict
- promotion status

---

## Audit Log Page

Show:

- JSONL event viewer
- reason code filters
- timestamp filter
- strategy filter
- security events

---

## Security Page

Show:

- paper mode enforced
- live disabled
- .env ignored
- external repo status
- secrets checklist

---

## UI Rule

Every button must have one clear function.

No duplicated button behaviour.
