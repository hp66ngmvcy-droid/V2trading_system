# Session Close Handoff

Date: 2026-09-30
From: Claude
To: Codex

---

## Session summary

Data extension, brief generation, outcome logging, ideas registry built,
data requirements mapped, XAUUSD all four gates now passed.

---

## Data state

**BTCUSD M15**: extended to 2026-09-30 04:45 UTC — 122,387 rows. Current.

**XAUUSD M15**: still ends 2026-09-25. Extension blocked by Saturday-bar gate.
`_v1` rebuild not yet run — awaiting Codex.

**Sep 30 brief generated**: `data/daily_briefs/2026-09-30_levels.json`
```
XAUUSD SELL  entry 4293-4298  stop 4305  T1 4258  R:R 2.92  PASS  (stale levels)
XAUUSD BUY   R:R 0.671  FAIL
BTCUSD SELL  entry 84084-84235  stop 84431  T1 82911  R:R 3.39  PASS
BTCUSD BUY   entry 83016  stop 82629  T1 84190  R:R 3.04  PASS
```
Anti-bias: XAUUSD SELL + BTCUSD SELL.
XAU levels identical to Sep 29 — stale until `_v1` rebuild clears.

---

## Outcomes logged

| Date | Symbol | Side | Result |
|------|--------|------|--------|
| Sep 29 | XAUUSD | SELL | AMBIGUOUS (no data) |
| Sep 29 | XAUUSD | BUY | NO_SIGNAL (validator fail) |
| Sep 29 | BTCUSD | SELL | PENDING — sell zone 84,256+ not reached by 04:45 Sep 30 |
| Sep 29 | BTCUSD | BUY | PENDING — buy zone 82,667− not reached by 04:45 Sep 30 |

Sep 29 BTC PENDING entries need resolving after London/NY session.
Extend data + re-run outcome checker to close them.

---

## XAUUSD — all four gates now passed

User confirmed broker: **IC Markets, UTC+2 winter / UTC+3 summer (European DST)**

Gap analysis completed:
- 1,216/1,648 gaps (73.8%) = IC Markets daily rollover at server midnight
- Remaining 432 = DST transitions + Sunday open variation
- All explainable under IC Markets EET/EEST calendar

Gate status:
- Gate 1 — zero Saturday bars: PASS
- Gate 2 — OHLC consistency: PASS (0 mismatches, 27,591 rows)
- Gate 3 — weekday gaps: PASS (IC Markets calendar confirmed)
- Gate 4 — provider metadata: PASS (IC Markets, UTC+2 DST, CFD mid-price)

Metadata written: `data/research/xauusd_source_metadata_v1.md`
Gate closure note: `claude_notes/2026-09-30_xauusd-gates-3-4-closed.md`

**Rebuild task fully unblocked. Codex can proceed immediately.**

### Critical timestamp finding

MT5 exports server local time (UTC+2/+3), NOT UTC.
Importer treated it as UTC — all XAU timestamps are 2–3h ahead of true UTC.

Price levels (OHLC, H/L, multi-day ranges) — VALID, unaffected.
Session-time features (VWAP anchors, session cutoffs) — OFFSET by 2–3h.

Codex rebuild task Step 5 (added in gate closure note):
- Add `server_utc_offset=2` to source metadata
- In `build_symbol_block()` for XAU: shift VWAP anchors and session_end_utc
  by +2h to compensate (Asia → 22:00, London → 06:00, NY → 11:00 UTC)
- Do NOT rewrite parquet timestamps — runtime correction only

---

## New ideas written this session

All ideas isolated. Nothing combined until individually tested.

**`claude_notes/2026-09-30_ideas-registry.md`** — full catalogue of 11 ideas
across strategy / feature / infrastructure with status, data requirements,
and gate to next action. Read this before starting any new build.

**`claude_notes/2026-09-30_data-requirements-map.md`** — maps each blocked
idea to exact data needed. Priority table:

| Action | Cost | Unblocks |
|--------|------|----------|
| XAUUSD `_v1` rebuild (unblocked) | £0 | All XAU work |
| GVZ auto-fetch from FRED `GVZCLS` | £0 | XAU IV walls automation |
| Deribit full strike chain → BTC GEX proxy | £0 | IDEA-F-009 |
| QQQ data via Twelve Data (needs human yes/no) | £0 | IDEA-S-005, I-001 |
| Options chain data (SpotGamma etc.) | £25–150/mo | IDEA-S-002 full build |

**`claude_notes/2026-09-30_gex-volume-profile-strategy-debate.md`** — GEX +
volume profile strategy (QQQ). Blocked by GEX data + DOM/tape. Volume profile
LVN detection (IDEA-F-003) buildable now as brief feature — no backtest until
GEX confirmed.

---

## Codex task priority order

1. **XAUUSD `_v1` rebuild** — fully unblocked, all four gates passed
   → `claude_notes/2026-09-29_xauusd-rebuild-task.md`
   → Add Step 5 from `claude_notes/2026-09-30_xauusd-gates-3-4-closed.md`

2. **`--intraday` flag** for brief generator — small, independent
   → `claude_notes/2026-09-29_collab-run-debate-response.md`

3. **GVZ auto-fetch** from FRED `GVZCLS` — small, no new data source
   → add `_fetch_xau_iv()` to `generate_daily_brief.py`; fallback to `--xau-iv`

4. **`pd_array_rejection_v1`** — new strategy build
   → `claude_notes/2026-09-29_pd-array-rejection-v1-debate.md`

5. **Volume profile LVN detection** — brief feature, no backtest
   → `claude_notes/2026-09-30_ideas-registry.md` IDEA-F-003

---

## Do not do

- Do not overwrite existing canonical XAU parquet files
- Do not delete Saturday rows from canonical
- Do not run ORB sweep or any backtest on `_v1` data before human swap approval
- Do not combine strategy ideas until each individually tested
- Do not backtest GEX + volume profile without GEX data in hand
- Do not treat Sep 25/28 SL run as evidence for or against any strategy — N too small
- Do not approve QQQ data addition without human sign-off (pending)
- No live trading, schedules, external API writes
