---
idea_id: currency-cross-sectional-momentum-20260525
title: Currency Cross-Sectional Momentum - Translated From SSRN Source
status: tested_rejected
source_note: online-scout-20260525-05ab51a462
source_url: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1809776
translated_at: 2026-05-25
paper_only: true
tested_at: 2026-05-25
test_report: reports/currency_momentum_proxy/20260525T202256Z_currency_momentum_proxy.md
test_verdict: KILL
test_reason: NEGATIVE_AFTER_COSTS
---

# Currency Cross-Sectional Momentum - Backtest Candidate

## Source Summary

The source reports a cross-sectional currency momentum effect: currencies with
stronger prior performance tend to outperform prior losers, but transaction
costs and limits to arbitrage materially reduce exploitability.

## Hypothesis

A monthly cross-sectional momentum basket across major FX pairs can produce a
positive out-of-sample spread after transaction costs when the lookback window
is long enough to avoid noise and when high-volatility/cost-fragile regimes are
filtered.

## V2 Mapping

This is not a single-symbol intraday signal yet. It should enter V2 as a
multi-asset research packet first.

Primary research path:

- Use `tar_system.research.multi_asset_backtester` or a dedicated basket test.
- Do not map directly to one live strategy.
- Do not export MT5 code from this candidate.

## Instruments

Initial basket:

- EURUSD
- GBPUSD
- AUDUSD
- USDJPY
- BTCUSD only as a non-FX stress comparison if local data is already clean

Skip any symbol without enough clean local history.

## Timeframes

- Primary: D1 if available
- Secondary proxy: H1 if D1 is unavailable
- Do not start with M15; the source hypothesis is medium horizon and likely
  cost-sensitive at intraday frequency.

## Entry

At each monthly rebalance:

1. Compute trailing return for each available instrument over 252 trading days.
2. Exclude the most recent 21 trading days to reduce short-term reversal noise.
3. Rank instruments by prior return.
4. Long the top third.
5. Short the bottom third.
6. Equal weight positions within long and short sleeves.

If fewer than 4 instruments have enough data, do not run the candidate.

## Exit

- Close positions at the next monthly rebalance.
- Re-rank and rebuild the basket.
- Exit any instrument immediately if data becomes stale or invalid.

## Filters

- source_quality_high
- cross_sectional_required
- monthly_rebalance
- exclude_recent_month
- require_cost_model
- require_walk_forward
- volatility_filter_candidate

## Risk

- no_live_promotion
- no_mt5_export
- cost_sensitive
- equal_weight_only_first_pass
- max_single_symbol_weight_33_pct
- require_out_of_sample

## Assumptions

- Local data has enough history for medium-horizon FX momentum.
- Pair returns are acceptable first-pass proxies for currency momentum.
- Transaction costs must be applied before scoring.
- Any profitable result without costs is not useful enough.

## Backtest Plan

1. Validate available FX data and history length.
2. Build monthly return/ranking table.
3. Run equal-weight long/short basket.
4. Compare against:
   - equal-weight FX basket
   - time-series momentum per pair
   - current best V2 strategy on the same symbols
5. Run walk-forward by calendar blocks.
6. Add volatility/cost filters only after baseline is measured.

## Kill Conditions

- fewer than 4 tradable instruments
- fewer than 36 monthly rebalance observations
- transaction costs flip net return negative
- out-of-sample Sharpe below 0.3
- max drawdown above 20%
- performance concentrated in one symbol or one short period

## Success Gate

- positive net return after costs
- out-of-sample Sharpe at least 0.5
- walk-forward result does not rely on one market regime
- basket spread remains positive after excluding the strongest single symbol

## Review Gate

- [x] Confirm D1 or H1 data availability.
- [x] Confirm pair-return mapping is acceptable for first-pass research.
- [x] Build as paper-only multi-asset test.
- [x] No live trading, no MT5 export, no automatic promotion.

## Test Result

- Report: `reports/currency_momentum_proxy/20260525T202256Z_currency_momentum_proxy.md`
- Verdict: KILL
- Reason: NEGATIVE_AFTER_COSTS
- Cumulative return: -10.1765%
- Annualized return: -2.5429%
- Sharpe: -0.0668
- Max drawdown: 39.2735%

## Decision

Reject as a strategy candidate for now. Keep as a research history item because
the source is high quality, but the available H1 proxy does not support further
implementation. A true D1 replication would require D1 data first.
