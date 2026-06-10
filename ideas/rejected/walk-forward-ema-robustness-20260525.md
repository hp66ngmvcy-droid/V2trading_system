---
idea_id: walk-forward-ema-robustness-20260525
title: Walk-Forward EMA Robustness Proxy - Rejected
status: rejected
source_note: online-scout-20260525-6c71c4f887
source_url: https://www.wne.uw.edu.pl/download_file/4308/2141
rejected_at: 2026-05-25
test_report: reports/walk_forward_trend_proxy/20260525T210238Z_walk_forward_trend_proxy.md
reason: NEGATIVE_AFTER_COSTS
paper_only: true
---

# Rejection Record

The source was translated into a rolling walk-forward EMA selector for GBPUSD
H1 and EURUSD H1. Parameters were selected on validation windows and applied to
future test windows only.

## Result

- Best symbol: EURUSD
- Windows: 5
- Cumulative return: -3.3096%
- Sharpe: -0.1737
- Max drawdown: 10.9202%
- Verdict: KILL
- Reason: NEGATIVE_AFTER_COSTS

The result does not justify strategy implementation. The walk-forward proxy
itself remains useful as reusable validation infrastructure.
