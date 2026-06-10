---
idea_id: multi-strategy-fx-futures-20260525
title: Multi-Strategy FX Futures - Data Requirements
status: data_required
source_note: online-scout-20260525-bcc4b0d614
source_url: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3322717
created_at: 2026-05-26
paper_only: true
---

# Data Requirements

The source can now be translated at the formula level, but V2 does not yet have
the required local datasets.

## Required Data

- Daily rolled FX futures series or a documented spot-FX proxy.
- 1-year and 10-year yields for each currency geography.
- Linked equity indices:
  - ASX 200
  - FTSE 100
  - TSX Composite
  - Euro STOXX 50
  - Nikkei 225
  - SP/BMV IPC
  - NZS 50
  - Swiss Market Index
- Commodity indices/assets:
  - GSCI
  - Brent crude
  - Gold
  - Agriculture index
- Cost model for futures, or a documented spot-FX approximation.

## Local Approximation Option

A reduced local proxy could test only spot-FX price momentum and mean reversion
on the existing H1 basket. That would not test the paper's core result because
it omits carry, equity momentum, commodity momentum, daily futures rolling, and
portfolio-combination logic.

## Decision

Do not run a reduced proxy unless it is explicitly labeled as incomplete and not
used to judge the full source.
