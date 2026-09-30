# XAUUSD Gates 3+4 Closed — IC Markets UTC+2 DST Confirmed

Date: 2026-09-30
Author: Claude
Refs:
- `data/research/xauusd_source_metadata_v1.md`
- `claude_notes/2026-09-29_xauusd-rebuild-task.md`
- `claude_notes/2026-09-28_xauusd-provenance-debate-response.md`

---

## Gate closures

User confirmed: **IC Markets, UTC+2 winter / UTC+3 summer (European DST)**

Gap analysis against IC Markets session calendar:

- 1,216 / 1,648 gaps (73.8%) at 00:00 server time = IC Markets daily rollover
- Remaining 432 gaps at 20:00–23:00 server time = DST transition days +
  weekend open variation (IC Markets Sunday open ~23:05 server time)
- All gaps explainable under IC Markets EET/EEST session calendar

**Gate 3 — weekday gaps: PASS**
**Gate 4 — provider metadata: PASS**

All four gates now passed. Metadata written to:
`data/research/xauusd_source_metadata_v1.md`

---

## Critical finding — timestamp offset

MT5 exports timestamps in broker server local time, NOT UTC.
The importer treated server local time as UTC — so all XAU timestamps in
the validated parquet are offset:

```
True UTC = stored_timestamp − 2h (Nov–Mar) or − 3h (Mar–Oct)
```

**Practical effects on brief generator:**

| Feature | Offset effect |
|---------|--------------|
| Session VWAP anchors (Asia 00:00, London 08:00, NY 13:00) | ~2–3h early for XAU |
| Double-touch alert session filtering | ~2–3h early |
| `_multi_day_levels` day boundary | ~2–3h early |
| Backtester session_end_utc=12:00 gate | ~2–3h too early — cuts session short |

BTC (Twelve Data API) timestamps ARE true UTC — no offset. XAU and BTC
timestamps are NOT directly comparable without correction.

**This does not invalidate OHLC price levels** (prev day H/L, 3d range, etc.)
— those are price-based, not time-based. Multi-day levels remain valid.

**It does affect intraday time-gated features** — session VWAP, session
cutoffs, double-touch alert timing.

---

## Codex action required (add to rebuild task)

After `_v1` artifacts are built, add one additional step:

**Step 5 — UTC offset correction**

Add `utc_offset_hours: 2` to source metadata config.

In `build_symbol_block()` for XAUUSD (IC Markets source):
- Shift session VWAP anchors: Asia → 22:00, London → 06:00, NY → 11:00 UTC
- Shift session_end_utc gate by +2h (or treat `_v1` bars as-is and note offset
  in brief output with a `⚠ Timestamps UTC+2` warning line)

Simplest correct approach: when building brief from IC Markets XAU source,
pass `server_utc_offset=2` and subtract from all UTC anchor comparisons.

This is a small targeted fix. Do not attempt to rewrite all timestamps in the
parquet — that would be a data mutation requiring a new rebuild.

---

## Rebuild task status

Gates 1+2: PASS (source comparison 2026-09-29)
Gates 3+4: PASS (confirmed 2026-09-30)

Codex rebuild task (`claude_notes/2026-09-29_xauusd-rebuild-task.md`) is now
fully unblocked. No human gates remain before Steps 1–4. Add Step 5 above.

XAUUSD stays `SOURCE_REVIEW_REQUIRED` until canonical swap decision after
second comparison report confirms `_v1` artifacts.
