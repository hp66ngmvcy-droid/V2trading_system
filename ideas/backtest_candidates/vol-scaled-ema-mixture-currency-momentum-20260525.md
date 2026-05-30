---
idea_id: vol-scaled-ema-mixture-currency-momentum-20260525
title: Vol-Scaled EMA Mixture Currency Momentum - Rule Extraction Candidate
status: tested_rejected
source_note: online-scout-20260525-c0a0b10349
source_url: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2949379
translated_at: 2026-05-25
tested_at: 2026-05-26
test_report: reports/vol_scaled_ema_mixture_proxy/20260526T082723Z_vol_scaled_ema_mixture_proxy.md
test_verdict: KILL
test_reason: NEGATIVE_AFTER_COSTS
paper_only: true
---

# Vol-Scaled EMA Mixture Currency Momentum - Backtest Candidate

## Source Summary

The source describes a currency momentum and trend-following approach that uses
a mixture of exponential moving averages with different time horizons. It tests
time-series and cross-sectional currency portfolios and reports that
traditional fiat currencies work better with the time-series version.

The source is different from the already rejected plain EMA crossover tests:
this candidate is about a smooth multi-horizon momentum signal, volatility
normalization, and response clipping rather than a single fast/slow crossover.

## Hypothesis

A multi-horizon EMA mixture, normalized by longer-horizon volatility and gated
by costs, may produce a more stable time-series momentum signal than single
EMA crossover rules on liquid FX pairs.

## V2 Mapping

- Paper-only proxy first.
- Use available local FX data before requesting new data.
- Start with H1 because D1 coverage is missing locally for several pairs.
- Treat H1 as a proxy, not an academic replication.
- Do not reuse the rejected static EMA crossover verdict as the final answer;
  this is a different signal family.

## Instruments

Initial local basket:

- EURUSD H1
- GBPUSD H1
- AUDUSD H1
- USDJPY H1
- USDCAD H1

Do not add crypto or emerging-market currencies until the local fiat basket
has a clean proxy result.

## Entry

For each symbol:

1. Compute multiple EMA-difference momentum components from close prices.
2. Normalize each component by a long-horizon volatility estimate.
3. Pass each normalized component through a bounded response function so very
   large signals do not create runaway exposure.
4. Average component responses into one time-series signal.
5. Go long when the signal is positive.
6. Go short when the signal is negative.
7. Shift positions by one bar before calculating returns.

## Exit

- Exit or reverse when the shifted signal changes sign.
- Flat only if the absolute signal is below the implementation threshold.

## Filters

- source_quality_high
- time_series_momentum_first
- multi_horizon_ema_mixture
- volatility_normalized
- bounded_response_required
- cost_model_required
- walk_forward_required

## Risk

- no_live_promotion
- no_mt5_export
- paper_only
- cost_sensitive
- require_out_of_sample
- reject_if_same_as_plain_ema_crossover

## Assumptions

- Exact component horizons still need implementation review before testing.
- H1 local data is a proxy for daily/futures research.
- Transaction costs must be applied per position change.
- Any positive result must be checked against the already rejected single-EMA
  crossover baselines.

## Backtest Plan

1. Confirm H1 readiness for the five-symbol local FX basket.
2. Build a paper-only vol-scaled EMA mixture proxy.
3. Compare against:
   - static bounded EMA crossover
   - rolling walk-forward EMA crossover
   - flat/no-position baseline
4. Apply 2 bps cost per position change.
5. Review per-symbol and equal-weight basket results.
6. Run walk-forward/stability check only if first proxy is not killed.

## Kill Conditions

- cumulative return <= 0 after costs
- basket Sharpe < 0.3
- max drawdown > 20%
- fewer than 30 trades per tested liquid pair
- result is only positive before costs
- result duplicates the already failed plain EMA crossover behavior

## Success Gate

- basket Sharpe >= 0.5 after costs
- cumulative return > 0 after costs
- at least 4 of 5 symbols not negative after costs
- max drawdown <= 20%
- signal remains useful under neighboring horizon choices

## Review Gate

- [x] Source is credible enough to keep.
- [x] Rules are specific enough for a proxy implementation, not production.
- [x] Cost, spread, and slippage sensitivity are required.
- [x] No promotion before out-of-sample and walk-forward review.

## Decision

Reject this candidate for implementation. Do not create strategy code, MT5
exports, or live trading paths from this note.

## Test Result

Ran the paper-only H1 proxy on EURUSD, GBPUSD, AUDUSD, USDJPY, and USDCAD with
EMA pairs 8/24, 16/48, 32/96, and 64/192, volatility window 200, threshold
0.05, and 2 bps cost per position change.

Basket result:

- Cumulative return: -36.6529%
- Annualized return: -8.0498%
- Sharpe: -1.5157
- Max drawdown: 37.8049%
- Verdict: KILL
- Reason: NEGATIVE_AFTER_COSTS

All five tested symbols were negative after costs.

Report:

- `reports/vol_scaled_ema_mixture_proxy/20260526T082723Z_vol_scaled_ema_mixture_proxy.md`
