---
idea_id: multi-strategy-fx-futures-20260525
title: Multi-Strategy FX Futures - Formula Extraction
status: formula_extracted
source_note: online-scout-20260525-bcc4b0d614
source_url: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3322717
extracted_at: 2026-05-26
paper_only: true
---

# Formula Extraction

This file records formula-level details extracted from the paper so future work
does not have to restart from the abstract.

## Data Scope

- CME current-month FX futures.
- Daily OHLC.
- T-3 rollover.
- Eight instruments in the paper: AUD, GBP, CAD, EUR, JPY, MXN, NZD, CHF
  futures.

## Indicator Formulas

Interest-rate carry:

- Compute yield-difference indicators from 10-year and 1-year yields across the
  two geographies.

Momentum:

- Short-term momentum: 3-month log return.
- Long-term momentum: 12-month log return.

Mean reversion:

- Short-term mean reversion: return relative to 3-month moving average.
- Long-term mean reversion: return relative to 12-month moving average.

Equity momentum:

- 3-month and 12-month momentum of each currency's linked equity index.

Commodity momentum:

- 3-month and 12-month momentum of GSCI, Brent crude, gold, and agriculture
  indices.

Volatility:

- 3-month and 12-month realized volatility of each security's returns.

## Normalization And Sizing

- For each instrument and indicator, compute walk-forward percentile score using
  only previous indicator values.
- Shift percentile by `-0.5` to map to a signed range around zero.
- Allocate risk budget proportional to absolute normalized signal.
- Target 10% annualized volatility per single-indicator strategy.
- Preserve signal sign so allocations can be long or short.

## Combination Methods

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

## Local V2 Decision

Do not build a backtest candidate yet. First create a data availability plan for
yield, equity index, commodity index, and futures/spot proxy coverage.
