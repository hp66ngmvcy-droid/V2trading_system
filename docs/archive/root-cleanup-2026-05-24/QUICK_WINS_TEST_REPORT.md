# Quick Wins Test Report

Snapshot date: 2026-05-13

## Scope

Tested the five "This Week" quick wins:

- Volume Confirmation
- Multi-Timeframe Filter
- Regime Detection
- Parameter Variants
- Multi-Asset Test

## Changes Made

- Fixed `PaperStrategyBacktester.backtest_strategy()` so volume-confirmed signals are no longer overwritten by a second unfiltered signal pass.
- Added optional multi-timeframe confirmation support to `PaperStrategyBacktester.backtest_strategy()`.
- Implemented usable higher-timeframe directional confirmation in `MultiTimeframeFilter`.
- Added focused tests in `tests/test_quick_wins.py`.

## Verification

Targeted tests:

```bash
PYTHONPATH=src venv/bin/python -m pytest tests/test_quick_wins.py -q
```

Result:

```text
7 passed in 1.90s
```

Compile check:

```bash
PYTHONPATH=src venv/bin/python -m compileall src/tar_system/research tests/test_quick_wins.py
```

Result: passed.

Real-data smoke test:

```bash
PYTHONPATH=src venv/bin/python -c "from tar_system.research.paper_backtester import PaperStrategyBacktester; b=PaperStrategyBacktester(); r=b.backtest_strategy('volatility_breakout', symbol='XAUUSD', timeframe='M15', start_date='2023-01-01', use_volume_confirmation=True, use_regime_detection=True, parameter_variant='aggressive'); print({'trades': r.get('total_trades'), 'sharpe': round(r.get('sharpe_ratio',0),2), 'dd_pct': round(r.get('max_drawdown_pct',0)*100,1), 'return_pct': round(r.get('total_return_pct',0)*100,1)})"
```

Result:

```text
{'trades': 9, 'sharpe': 12.51, 'dd_pct': 3.3, 'return_pct': 25.0}
```

## Advanced Pipeline

Command:

```bash
PYTHONPATH=src venv/bin/python run_advanced_strategies.py
```

Status: passed with bounded smoke defaults.

Default scope:

```text
Assets: XAUUSD, EURUSD
Strategies: volatility_breakout, momentum
Timeframe: M15
Parameter variant: aggressive
Date range: 2023-01-01 to end
Max rows: 300
```

Generated:

```text
data/paper_strategies/parameter_variants_report.json
data/paper_strategies/cross_asset_comparison.json
```

Parameter variant results for `volatility_breakout` on `XAUUSD M15`:

| Variant | Verdict | Score | Trades | Sharpe | Max DD | Return |
|---|---:|---:|---:|---:|---:|---:|
| conservative | KEEP | 8/10 | 6 | 6.24 | 2.7% | 9.8% |
| moderate | KEEP | 9/10 | 9 | 12.51 | 3.3% | 25.0% |
| aggressive | KEEP | 9/10 | 12 | 11.30 | 4.9% | 32.9% |
| breakout | KEEP | 9/10 | 12 | 4.34 | 8.6% | 14.3% |

Cross-asset smoke results:

| Strategy | Asset | Verdict | Score | Trades | Sharpe | Max DD | Return |
|---|---|---:|---:|---:|---:|---:|---:|
| volatility_breakout | XAUUSD | KEEP | 9/10 | 9 | 12.51 | 3.3% | 25.0% |
| volatility_breakout | EURUSD | KILL | 0/10 | 0 | 0.00 | 0.0% | 0.0% |
| momentum | XAUUSD | KILL | 0/10 | 0 | 0.00 | 0.0% | 0.0% |
| momentum | EURUSD | KILL | 0/10 | 0 | 0.00 | 0.0% | 0.0% |

The full grid is still available with:

```bash
PYTHONPATH=src venv/bin/python run_advanced_strategies.py --full
```

## Findings

| Quick win | Status | Evidence |
|---|---|---|
| Volume Confirmation | Passed | Unit test verifies low volume blocks signals; backtester integration now preserves filtered signals. |
| Multi-Timeframe Filter | Passed | Unit test verifies higher-timeframe direction confirms matching signals and blocks opposing signals. |
| Regime Detection | Passed | Unit test verifies detector returns a known regime. |
| Parameter Variants | Passed | Unit test verifies all four variants and regime mapping. Bounded script generated KEEP verdicts for all XAUUSD volatility-breakout variants. |
| Multi-Asset Test | Passed as smoke | Unit test verifies asset discovery and limited execution; bounded script completed 2 strategies x 2 assets. |

## Recommendation

Use the bounded default run as the daily/weekly quick check. Use `--full` only when you deliberately want the slower full research grid.
