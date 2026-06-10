---
idea_id: vol-scaled-ema-mixture-currency-momentum-20260525
title: Vol-Scaled EMA Mixture Currency Momentum - Rejected
status: rejected
source_note: online-scout-20260525-c0a0b10349
source_url: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2949379
rejected_at: 2026-05-26
test_report: reports/vol_scaled_ema_mixture_proxy/20260526T082723Z_vol_scaled_ema_mixture_proxy.md
reason: NEGATIVE_AFTER_COSTS
paper_only: true
---

# Rejection Record

The source was translated into a paper-only H1 proxy using a multi-horizon EMA
mixture, volatility normalization, bounded signal response, one-bar position
shift, and 2 bps cost per position change.

## Result

- Basket cumulative return: -36.6529%
- Basket annualized return: -8.0498%
- Basket Sharpe: -1.5157
- Basket max drawdown: 37.8049%
- Verdict: KILL
- Reason: NEGATIVE_AFTER_COSTS

All five tested symbols were negative after costs:

- EURUSD
- GBPUSD
- AUDUSD
- USDJPY
- USDCAD

## Decision

Do not implement this as strategy code. Do not export to MT5 or promote to live
or paper signal paths. Keep the record as evidence that this proxy expression
did not improve on the already rejected plain EMA family.
