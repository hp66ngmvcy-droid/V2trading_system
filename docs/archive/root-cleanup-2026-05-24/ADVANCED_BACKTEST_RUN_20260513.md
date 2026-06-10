# Advanced Backtest Run - 2026-05-13

Generated: 2026-05-13T09:18:12

## Command

```bash
PYTHONPATH=src venv/bin/python run_advanced_strategies.py --full --max-rows 300 --start-date 2023-01-01
```

## Scope

- Mode: full strategy/asset grid with row cap
- Timeframe: M15
- Start date: 2023-01-01
- Max rows per backtest: 300
- Parameter variant for cross-asset phase: aggressive

## Parameter Variant Results

| Variant | Verdict | Score | Trades | Sharpe | Max DD | Return |
|---|---:|---:|---:|---:|---:|---:|
| conservative | KEEP | 8/10 | 6 | 6.24 | 2.7% | 9.8% |
| moderate | KEEP | 9/10 | 9 | 12.51 | 3.3% | 25.0% |
| aggressive | KEEP | 9/10 | 12 | 11.30 | 4.9% | 32.9% |
| breakout | KEEP | 9/10 | 12 | 4.34 | 8.6% | 14.3% |

## Cross-Asset KEEP Results

| Strategy | Asset | Score | Trades | Sharpe | Max DD | Return |
|---|---|---:|---:|---:|---:|---:|
| volatility_breakout | XAUUSD | 9/10 | 9 | 12.51 | 3.3% | 25.0% |
| mean_reversion | XAUUSD | 9/10 | 5 | 10.81 | 0.0% | 13.3% |
| orb | XAUUSD | 9/10 | 15 | 3.65 | 14.1% | 16.2% |

## Notes

- The only asset producing KEEP verdicts in this bounded run was XAUUSD.
- Volatility breakout was the strongest XAUUSD candidate by Sharpe and return.
- Most non-XAUUSD assets produced zero trades under the aggressive paper-parameter settings.
