---
idea_id: currency-cross-sectional-momentum-20260525
title: Currency Cross-Sectional Momentum - Rejected After H1 Proxy Test
status: rejected_after_proxy_backtest
source_note: online-scout-20260525-05ab51a462
source_url: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1809776
candidate_note: ideas/backtest_candidates/currency-cross-sectional-momentum-20260525.md
test_report: reports/currency_momentum_proxy/20260525T202256Z_currency_momentum_proxy.md
decided_at: 2026-05-25
paper_only: true
---

# Currency Cross-Sectional Momentum - Rejection Record

## Decision

Reject for implementation and further candidate promotion.

## Reason

The available H1 proxy basket test failed after costs:

- Verdict: KILL
- Reason: NEGATIVE_AFTER_COSTS
- Cumulative return: -10.1765%
- Annualized return: -2.5429%
- Sharpe: -0.0668
- Max drawdown: 39.2735%

## Notes

- The source remains credible and should stay in research history.
- The local dataset does not include D1 files, so this is not a direct daily
  replication of the academic source.
- Do not create strategy code or MT5 export from this candidate.
- Revisit only if D1 data is added and a true daily replication is requested.
