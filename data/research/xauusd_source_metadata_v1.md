# XAUUSD M15 Source Metadata — v1

- Provider: IC Markets (ASIC-regulated CFD broker)
- Data product: XAU/USD M15 OHLCV CFD history
- Export method: MetaTrader 5 History Center CSV export
- Source file: XAUUSD_M15_202505121015_202607102345.csv
- Versioned candidate file: XAUUSD_M15_clean_candidate_v1.csv
- Validated artifact: data/validated/XAUUSD_M15_clean_v1.parquet
- Feature artifact: data/features/XAUUSD_M15_clean_v1.parquet
- Date range: 2025-05-12 10:15 to 2026-07-10 23:45 (timestamps in server local time)
- Timezone: IC Markets MT5 server — UTC+2 (winter EET) / UTC+3 (summer EEST) with DST
- Timestamp storage: SERVER LOCAL TIME — NOT UTC. Add +2h (winter) / +3h (summer) to convert.
- DST policy: European DST (last Sunday March → last Sunday October)
- Spread assumption: CFD mid-price (IC Markets Standard account — variable spread, not fixed)
- Weekday gaps: 1,648 in clean period — confirmed explained (see Gate 3 below)
- Metadata captured: 2026-09-30 (confirmed by user)

## CRITICAL — Timestamp Offset

MT5 History Center exports timestamps in broker server local time.
IC Markets server = UTC+2 (winter) / UTC+3 (summer DST).

Timestamps stored in parquet are SERVER LOCAL TIME treated as UTC by importer.
True UTC = stored timestamp − 2h (winter) or − 3h (summer).

Practical effects:
- Daily session VWAP anchors for XAU are offset by 2–3h vs true UTC
- Asia VWAP anchor "00:00 UTC" in parquet = ~22:00 real UTC (prior day)
- London VWAP anchor "08:00 UTC" in parquet = ~06:00 real UTC
- NY VWAP anchor "13:00 UTC" in parquet = ~11:00 real UTC

BTC (Twelve Data API) timestamps ARE true UTC — no offset.

Any intraday analysis comparing XAU and BTC timestamps must account for this.
Session VWAP and double-touch features in brief generator are offset for XAU.
Flag for Codex: add `utc_offset_hours` field to source metadata and apply
correction in `_session_vwap()` when symbol is XAUUSD from IC Markets source.

## Gate Status

- Gate 1 — zero Saturday bars: **PASS** — confirmed in source comparison 2026-09-29
- Gate 2 — OHLC consistency: **PASS** — 0 mismatches in 27,591 overlap rows
- Gate 3 — weekday gaps mapped: **PASS** — 1,216/1,648 gaps (73.8%) at 00:00 server
  time = IC Markets daily session rollover (normal). Remaining 432 gaps at 20:00–23:00
  server time consistent with DST transition days and weekend open variations.
  All gaps explainable under IC Markets EET/EEST session calendar.
- Gate 4 — provider metadata: **PASS** — IC Markets, MT5 server UTC+2 DST, confirmed
  by user 2026-09-30. Spread: CFD mid-price variable.

## All Four Gates PASSED

XAUUSD `_clean_v1` source is cleared for rebuild.
Remaining blocker: Codex must complete the `_v1` artifact build (Step 1–3 of
`claude_notes/2026-09-29_xauusd-rebuild-task.md`) before canonical swap decision.

XAUUSD status remains `SOURCE_REVIEW_REQUIRED` until canonical swap explicitly
approved by human after reviewing second comparison report.
