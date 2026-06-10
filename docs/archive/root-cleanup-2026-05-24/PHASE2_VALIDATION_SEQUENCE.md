# Phase 2 Validation Sequence

Decision: use a staged Phase 2 path. Do not let macro-regime research block the core tester, optimiser, and paper-trading validation loop.

## Sequence

### Stage 1 - Phase 2 Standard

Goal: prove the strategy search and validation engine can find robust paper candidates.

Build and run:
- Continuous parameter search
- Walk-forward validation
- Blind out-of-sample checks
- Parameter stability scoring
- KEEP / REVIEW / KILL gates
- Minimum trade-count gate
- Drawdown and profit-factor gates

Promotion rule:
- Only move candidates forward if they pass enough-trades, drawdown, profit-factor, and stability checks.
- One-trade lucky winners are REVIEW only, never KEEP.

Primary outputs:
- `runtime/optimizer_candidate_queue.jsonl`
- `data/results/parameter_search/continuous_parameter_search_summary.json`
- `data/results/*_walk_forward.json`
- `reports/*_report.md`

### Stage 2 - Paper Trading Collection

Goal: collect real paper behavior while research continues locally.

Run:
- Paper signal generation
- Strategy health monitor
- Paper-only risk gates
- Local signal logs
- Quant reports for shortlisted candidates

No live trading. No broker execution.

Primary outputs:
- `runtime/latest_paper_signal.json`
- `runtime/paper_signal_alerts.jsonl`
- `runtime/strategy_health_status.json`
- `reports/*_quant_report.md`
- `reports/*_quant_report.pdf`

### Stage 3 - Phase 2 Extended Regime Retrofit

Goal: add macro/regime intelligence after Phase 2 Standard is working and paper data is being collected.

Add later:
- DXY, rates, and VIX local data cache
- Macro data validation
- Regime labels for historical windows
- Regime-specific Sharpe / drawdown / trade counts
- Correlation stability scoring
- Regime-aware validation report

Gate addition:
- Parameter stability score must pass.
- Correlation stability score must pass.
- If either fails, candidate stays REVIEW or KILL.

This stage is valuable, but it must not block Stage 1 or Stage 2.

### Stage 4 - Phase 3 Multi-Asset Planning

Goal: use the regime retrofit to design a multi-asset portfolio intelligently.

Use:
- Regime-specific performance
- Cross-asset correlation by regime
- Candidate robustness by asset
- Paper-trading behavior

Only after:
- At least one candidate survives Phase 2 Standard
- Paper trading has produced usable evidence
- Regime retrofit has been completed or explicitly deferred

## Current Priority

1. Make continuous parameter search reliable.
2. Find candidates with enough trades.
3. Validate survivors with walk-forward and OOS.
4. Start paper-only monitoring for survivors.
5. Retrofit macro/regime analysis.
6. Plan Phase 3 multi-asset.

## Do Not Do Yet

- Do not build cloud dependencies.
- Do not add live trading.
- Do not promote one-trade winners.
- Do not build the full macro UI before the core optimiser works.
- Do not treat aggregate Sharpe as enough without stability checks.
