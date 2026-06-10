---
idea_id: multi-strategy-fx-futures-20260525
title: Multi-Strategy FX Futures - Formula Extracted, Data Blocked
status: formula_extracted_data_blocked
source_note: online-scout-20260525-bcc4b0d614
source_url: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3322717
blocked_at: 2026-05-25
updated_at: 2026-05-26
paper_only: true
---

# Formula Extracted, Data Blocked

The source is high-quality and useful. Formula-level details were extracted from
the paper text on 2026-05-26. The source should still not become a backtest
candidate yet because the required yield, equity index, commodity index, and
rolled futures datasets are not present locally.

## Extracted Rules

Instrument set:

- 8 liquid CME current-month FX futures.
- Daily OHLC.
- T-3 day rollover to build uniform futures series.

Indicators:

- Interest-rate carry:
  log difference of long-term 10-year and short-term 1-year yields between the
  two geographies.
- Momentum:
  short-term 3-month log returns and long-term 12-month log returns.
- Mean reversion:
  returns relative to short-term 3-month and long-term 12-month moving
  averages.
- Equity momentum:
  3-month and 12-month momentum of linked equity indices.
- Commodity momentum:
  3-month and 12-month momentum of GSCI, Brent crude, gold, and agriculture
  indices.
- Volatility:
  3-month and 12-month realized volatility of each security's returns.

Normalization:

- Walk-forward percentile normalization across each instrument's prior
  indicator history.
- Percentile score is mapped to `[0, 1]`, then shifted by `-0.5` to remove
  persistent long bias.

Position sizing:

- Convert normalized indicator values into risk budgets proportional to absolute
  signal magnitude.
- Target 10% annualized volatility per single-indicator strategy.
- Preserve signal sign so weights can be negative.
- Apply covariance-aware risk budgeting with practical leverage constraints.

Combination methods:

- Equal weight.
- Equal risk.
- Equal risk contribution.
- Proportional to Sharpe.
- Correlation-aware Sharpe.
- Maximum diversification.
- Volatility-scaled negative correlation.
- Negative correlation dot Sharpe.
- Optimization to maximize realized Sharpe.
- Optimization to maximize 10th percentile of rolling one-year Sharpe.

## Required Before Candidate Conversion

- Daily rolled FX futures data or a documented spot-FX proxy decision.
- 1-year and 10-year yield data for each currency geography.
- Linked equity index data for each currency.
- Commodity index data: GSCI, Brent crude, gold, agriculture.
- A local data mapping from futures symbols to available V2 symbols.
- A cost model suitable for futures or documented spot-FX approximation.
- A decision on whether to start with single-indicator proxies before portfolio
  combination.

## Decision

Do not convert into a strategy candidate yet. The formulas are no longer the
blocker; the blocker is local data coverage and the futures-to-spot proxy
decision.
