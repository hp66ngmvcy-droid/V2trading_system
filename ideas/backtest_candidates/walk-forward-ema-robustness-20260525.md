---
idea_id: walk-forward-ema-robustness-20260525
title: Walk-Forward EMA Robustness Proxy - Translated From WNE Source
status: tested_rejected
source_note: online-scout-20260525-6c71c4f887
source_url: https://www.wne.uw.edu.pl/download_file/4308/2141
translated_at: 2026-05-25
tested_at: 2026-05-25
test_report: reports/walk_forward_trend_proxy/20260525T210238Z_walk_forward_trend_proxy.md
test_verdict: KILL
test_reason: NEGATIVE_AFTER_COSTS
paper_only: true
---

# Walk-Forward EMA Robustness Proxy - Backtest Candidate

## Source Summary

The source describes EMA crossover trend-following with EMA values 10, 20, 50,
100, and 200, selected through rolling walk-forward optimization. The useful
V2 idea is robustness governance: parameters should be selected on validation
windows and judged on later test windows with costs included.

## Hypothesis

A rolling walk-forward EMA selector on GBPUSD and EURUSD H1 may outperform a
static bounded EMA grid by adapting the fast/slow EMA pair to recent validation
conditions.

## V2 Mapping

- Use a bounded EMA pair set only.
- Select parameters on validation windows by Sharpe.
- Apply selected pair only to the next test window.
- Keep this as paper-only research with no live trading or MT5 export.

## Instruments

- GBPUSD H1
- EURUSD H1

## Entry

- BUY when the selected fast EMA is above the selected slow EMA.
- SELL when the selected fast EMA is below the selected slow EMA.
- Position is shifted by one bar to avoid same-bar lookahead.

## Exit

- Opposite EMA signal.

## Filters

- source_quality_high
- context_robustness
- bounded_parameter_search
- rolling_walk_forward
- cost_model_required

## Risk

- no_live_promotion
- no_mt5_export
- cost_sensitive
- require_out_of_sample
- require_parameter_stability

## Test Result

Rolling walk-forward proxy was run with 24-month training context, 6-month
validation windows, 6-month test windows, and 6-month step size. EMA values were
10, 20, 50, 100, and 200. Cost was 2 bps per position change.

Best row:

- Symbol: EURUSD
- Windows: 5
- Trades: 578
- Cumulative return: -3.3096%
- Sharpe: -0.1737
- Max drawdown: 10.9202%
- Verdict: KILL
- Reason: NEGATIVE_AFTER_COSTS

Report:

- `reports/walk_forward_trend_proxy/20260525T210238Z_walk_forward_trend_proxy.md`

## Decision

Reject this candidate as a strategy. Keep the walk-forward selector as useful
testing infrastructure, because it directly supports future robustness checks.
