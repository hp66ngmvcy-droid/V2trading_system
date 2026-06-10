---
idea_id: multi-strategy-fx-futures-20260525
title: Multi-Strategy FX Futures - Data Requirements - Proxy Decision Required
status: proxy_decision_required
source_url: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3322717
created_at: 2026-05-26
paper_only: true
---

# Proxy Decision Required

## Decision

- Current decision: DO_NOT_CONVERT_FULL_SOURCE
- Allowed local proxy scope: incomplete_local_spot_price_proxy_only
- Candidate conversion: blocked until an operator explicitly accepts the reduced scope.

## Why This Is Blocked

- FX futures or documented spot-FX proxy: PARTIAL
- 1-year and 10-year yield history: MISSING
- Linked equity index history: MISSING
- Commodity index/assets history: PARTIAL
- Futures cost model or spot-FX approximation: DECISION_REQUIRED

## If A Reduced Proxy Is Approved

- Label the candidate as incomplete and not representative of the full source.
- Exclude missing components rather than inventing them.
- Compare only against local price-action baselines.
- Do not use the result to reject or promote the full paper.
- Keep live, paper, and automation promotion disabled.

## Data Review Snapshot

| Requirement | Status | Local Evidence | Action |
| --- | --- | --- | --- |
| FX futures or documented spot-FX proxy | PARTIAL | spot symbols present: AUDUSD, EURUSD, GBPUSD, USDCAD, USDJPY; missing core spot symbols: none | Document spot-FX proxy limits and missing MXN/NZD/CHF futures coverage. |
| 1-year and 10-year yield history | MISSING | no yield symbols found in data/raw | Add approved yield datasets or remove carry from any reduced proxy. |
| Linked equity index history | MISSING | no linked equity index symbols found in data/raw | Add index datasets before testing equity-momentum components. |
| Commodity index/assets history | PARTIAL | XAUUSD can proxy gold; USOUSD can proxy oil, not Brent | Add GSCI, Brent, and agriculture data or explicitly omit commodity momentum. |
| Futures cost model or spot-FX approximation | DECISION_REQUIRED | strategy-specific cost model not documented for this source | Document futures costs or spot-FX approximation before candidate conversion. |
