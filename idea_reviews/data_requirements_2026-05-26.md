# Data Requirements Review

- Generated: 2026-05-26T10:42:01+00:00
- Requirements dir: `ideas/data_requirements`
- Raw dir: `data/raw`
- Items: 1
- Fully ready: 0
- Blocked: 1

## Multi-Strategy FX Futures - Data Requirements

- Path: `ideas/data_requirements/multi-strategy-fx-futures-20260526.md`
- Status: data_required
- Source: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3322717

| Requirement | Status | Local Evidence | Action |
| --- | --- | --- | --- |
| FX futures or documented spot-FX proxy | PARTIAL | spot symbols present: AUDUSD, EURUSD, GBPUSD, USDCAD, USDJPY; missing core spot symbols: none | Document spot-FX proxy limits and missing MXN/NZD/CHF futures coverage. |
| 1-year and 10-year yield history | MISSING | no yield symbols found in data/raw | Add approved yield datasets or remove carry from any reduced proxy. |
| Linked equity index history | MISSING | no linked equity index symbols found in data/raw | Add index datasets before testing equity-momentum components. |
| Commodity index/assets history | PARTIAL | XAUUSD can proxy gold; USOUSD can proxy oil, not Brent | Add GSCI, Brent, and agriculture data or explicitly omit commodity momentum. |
| Futures cost model or spot-FX approximation | DECISION_REQUIRED | strategy-specific cost model not documented for this source | Document futures costs or spot-FX approximation before candidate conversion. |

## Guardrails

- Data requirement readiness is not a strategy result.
- Partial local proxies must be labelled incomplete before backtesting.
- Do not promote data-blocked sources to live or paper trading.
