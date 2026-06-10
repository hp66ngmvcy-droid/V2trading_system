# Translation Blockers Review

- Generated: 2026-05-26T09:41:25+00:00
- Input: `ideas/translation_blocked`
- Blocked sources: 1

## Items

### Multi-Strategy FX Futures - Formula Extracted, Data Blocked

- Path: `ideas/translation_blocked/multi-strategy-fx-futures-20260525.md`
- Status: formula_extracted_data_blocked
- Source: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3322717
- Next action: Resolve data coverage or document a reduced proxy before candidate conversion.

Missing rules:

- Daily rolled FX futures data or a documented spot-FX proxy decision
- 1-year and 10-year yield data for each currency geography
- Linked equity index data for each currency
- Commodity index data: GSCI, Brent crude, gold, agriculture
- A local data mapping from futures symbols to available V2 symbols
- A cost model suitable for futures or documented spot-FX approximation
- A decision on whether to start with single-indicator proxies before portfolio

## Guardrails

- This review does not create candidates.
- Do not invent missing formulas.
- Keep blocked sources out of proxy/backtest work until formulas and data are explicit.
