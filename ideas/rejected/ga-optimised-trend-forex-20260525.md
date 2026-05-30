---
idea_id: ga-optimised-trend-forex-20260525
title: GA Optimised Trend Forex - Rejected After Bounded Trend Proxy
status: rejected
source_note: online-scout-20260525-60ebef8e01
source_url: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4515471
rejected_at: 2026-05-25
test_report: reports/bounded_trend_proxy/20260525T204934Z_bounded_trend_proxy.md
reason: NEGATIVE_AFTER_COSTS
paper_only: true
---

# Rejection Record

The source was translated into a bounded, paper-only EMA trend proxy for GBPUSD
H1 and EURUSD H1. The test intentionally avoided an unconstrained genetic
algorithm and used a small parameter grid to reduce overfit risk.

## Result

- Best symbol: EURUSD
- Best EMA pair: 50/200
- Best cumulative return: -0.5798%
- Best Sharpe: 0.0245
- Best max drawdown: 13.9139%
- Best verdict: KILL
- Best reason: NEGATIVE_AFTER_COSTS

All tested EMA pairs were negative after the cost model. No strategy code, MT5
export, live trading path, or automatic promotion should be created from this
candidate.

## Useful Lesson

The research value is in the process control: bounded parameter search,
walk-forward requirements, and cost gates should stay in the idea pipeline. The
specific EMA trend expression tested here should not move forward.
