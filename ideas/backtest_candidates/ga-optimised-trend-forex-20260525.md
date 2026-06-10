---
idea_id: ga-optimised-trend-forex-20260525
title: GA Optimised Trend Forex - Translated From SSRN Source
status: tested_rejected
source_note: online-scout-20260525-60ebef8e01
source_url: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4515471
translated_at: 2026-05-25
tested_at: 2026-05-25
test_report: reports/bounded_trend_proxy/20260525T204934Z_bounded_trend_proxy.md
test_verdict: KILL
test_reason: NEGATIVE_AFTER_COSTS
paper_only: true
---

# GA Optimised Trend Forex - Backtest Candidate

## Source Summary

The source compares technical trading strategies in major Forex markets using a
genetic algorithm. The strongest clue for V2 is not "use a GA blindly"; it is
that trend indicators did better than common default parameters before costs,
while spreads and commissions substantially deteriorated returns.

## Hypothesis

Trend-following rules on EURUSD and GBPUSD can improve versus default parameter
sets when parameter search is constrained, walk-forwarded, and cost-gated. Any
edge that disappears after spread/commission assumptions should be rejected.

## V2 Mapping

Use existing V2 strategy/tuning machinery before creating new code:

- Primary strategy family: `ema_volume_v3` with volume gate disabled first pass.
- Comparison family: `atr_breakout_v3` only after EMA baseline review.
- Use `tune-strategy` or bounded parameter variants, not unconstrained GA.
- Treat this as parameter-search governance, not a new live strategy.

## Instruments

- Primary: GBPUSD H1
- Secondary: EURUSD H1
- Do not test broad symbols until these two pass.

## Entry

First pass:

- BUY when fast EMA crosses above slow EMA.
- SELL when fast EMA crosses below slow EMA.
- Candidate fast EMA values: 10, 20, 50.
- Candidate slow EMA values: 50, 100, 200.
- Require fast EMA < slow EMA.

## Exit

- Opposite EMA crossover.
- ATR stop first pass: `atr_multiplier=1.5`.
- Reward/risk first pass: `reward_risk=2.0`.

## Filters

- source_quality_high
- trend_indicator_first
- bounded_parameter_search
- walk_forward_required
- cost_model_required
- gbpusd_primary

## Risk

- no_live_promotion
- no_mt5_export
- cost_sensitive
- no_unbounded_ga
- require_out_of_sample
- require_parameter_stability

## Assumptions

- Local H1 data is enough for first-pass validation.
- GA-style search must be approximated with bounded parameter grids to avoid
  overfit.
- A result before costs is not actionable.

## Backtest Plan

1. Confirm GBPUSD H1 and EURUSD H1 data readiness.
2. Run bounded EMA parameter candidates.
3. Score after broker cost model.
4. Run walk-forward with limited splits.
5. Compare best bounded candidate against default EMA settings.
6. If GBPUSD passes but EURUSD fails, mark market-specific and do not generalize.

## Kill Conditions

- profit_factor < 1.1 after costs
- walk-forward Sharpe < 0.3
- total_trades < 30
- max_drawdown > 20%
- best result only exists in one narrow parameter combination
- cost model flips KEEP/REVIEW into KILL

## Success Gate

- profit_factor >= 1.25 after costs
- walk-forward Sharpe >= 0.5
- at least 30 trades
- stable neighboring parameter combinations
- GBPUSD H1 passes first; EURUSD H1 is confirmatory

## Review Gate

- [x] Confirm data readiness for GBPUSD H1 and EURUSD H1.
- [x] Run bounded parameter search only.
- [x] Review costs before any candidate promotion.
- [x] No live trading, no MT5 export, no automatic promotion.

## Test Result

Bounded H1 EMA trend proxy was run on GBPUSD and EURUSD with fast EMA values
10, 20, 50 and slow EMA values 50, 100, 200. Every tested combination failed
after a 2 bps position-change cost.

Best row:

- Symbol: EURUSD
- EMA pair: 50/200
- Trades: 198
- Cumulative return: -0.5798%
- Sharpe: 0.0245
- Max drawdown: 13.9139%
- Verdict: KILL
- Reason: NEGATIVE_AFTER_COSTS

Report:

- `reports/bounded_trend_proxy/20260525T204934Z_bounded_trend_proxy.md`

## Decision

Reject this candidate for V2 implementation. The source remains useful as a
research lesson: bounded parameter search and cost gates are valuable controls,
but the tested EMA trend expression did not produce a usable local edge.
