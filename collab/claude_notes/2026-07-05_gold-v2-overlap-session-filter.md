# gold_v2 — OVERLAP session filter

## Finding
Bucket analysis (2026-07-05) on XAUUSD M15 shows edge is concentrated in London/NY overlap:

| Session | Trades | WR% | PF |
|---------|--------|-----|-----|
| OVERLAP | 52 | 44.2% | 1.54 |
| LONDON | 59 | 32.2% | 0.99 |
| NEW_YORK | 100 | 28.0% | 0.74 |

Filtering to OVERLAP only reduces trades from 211 to 52 but lifts PF from 0.99 → 1.54.

## Task
In `src/tar_system/strategies/gold_v2.py`, add session filter:
- Entry allowed only when session label is OVERLAP (08:00–12:00 UTC)
- Use existing `session_label` feature column (already in validated parquets)
- If `session_label` not available, gate on `hour_utc` between 8 and 12

Then run:
```bash
source venv/bin/activate
PYTHONPATH=src python -m tar_system.cli run-backtest --strategy gold_v2 --symbol XAUUSD --timeframe M15 --force
PYTHONPATH=src python -m tar_system.cli score-strategy --strategy gold_v2 --symbol XAUUSD --timeframe M15
```

## Success criteria
- Trades >= 30 (previously 211, OVERLAP subset ~52 — if below 30 after full rerun, widen to LONDON+OVERLAP)
- Costed PF >= 1.2
- Score >= 65
