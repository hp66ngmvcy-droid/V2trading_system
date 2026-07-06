# rsi_reversion_v1 — NY session + tighter threshold

## Finding
Bucket analysis (2026-07-05) on XAUUSD M15:

| Bucket | Trades | WR% | PF |
|--------|--------|-----|-----|
| NY session | 935 | 48.7% | 1.17 |
| HIGH ATR | 1133 | 47.4% | 1.10 |
| LONDON | 1379 | 46.3% | 1.06 |

Gross PF 1.08 in RANGING regime — costs drag it to ~0.89. Two changes can flip this:
1. NY session filter (best bucket PF 1.17) cuts churn and improves average trade quality
2. Raise entry threshold to RSI <25 / >75 (extreme only) — cuts trades ~60%, keeps fat-tail entries

## Task
In `src/tar_system/strategies/rsi_reversion_v1.py`:
1. Add NY session gate: entry only when `hour_utc` between 13 and 20 (or `session_label == NEW_YORK`)
2. Raise RSI threshold: existing buy/sell RSI levels → confirm current values, tighten if currently <30/>70

Run:
```bash
source venv/bin/activate
PYTHONPATH=src python -m tar_system.cli run-backtest --strategy rsi_reversion_v1 --symbol XAUUSD --timeframe M15 --force
PYTHONPATH=src python -m tar_system.cli tune-strategy --strategy rsi_reversion_v1 --symbol XAUUSD --timeframe M15
PYTHONPATH=src python -m tar_system.cli score-strategy --strategy rsi_reversion_v1 --symbol XAUUSD --timeframe M15
```

## Success criteria
- Trades reduced from 3440 to ~400-800
- Costed PF >= 1.2
- Sharpe >= 1.5
