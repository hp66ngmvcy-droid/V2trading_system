# Codex Handoff — 2026-09-08

## What was done this session

### 1. rsi_trend_v4 Full Parameter Sweep (XAUUSD M15)

Ran two sweeps to find KEEP-worthy configuration:
- **280-combo big sweep** — RSI 30-45, ATR 1.5-3.0, RR 2.0-4.0, EMA gate on/off
- **50-combo high-ATR probe** — ATR 3.0-5.0, RSI 33-43

**Key finding:** ATR 3.0 + RSI 35/65 + RR 2.0 + EMA gate True = best config.
Win rate 45%, PF 1.92, score 82.87. Zero KEEP hits across all 280 combos.

**Blocker:** Bootstrap CI gate correctly blocks — RSI 35/65 generates only 5 OOS
trades in WF windows. Insufficient statistical evidence. Gate is working correctly.

**Resolution:** Registered `rsi_trend_v4_35_65_atr3` as ACTIVE RESEARCH entity (metric=1.921).
Paper collection required before promotion. See `claude_notes/2026-09-08_rsi-trend-v4-research-candidate.md`.

Scripts: `scripts/rsi_big_sweep_xauusd_m15.py`, `scripts/rsi_atr_high_probe_xauusd_m15.py`

### 2. Stability Gate Bug Fixed

`derive_stable_parameter_ranges` returned `0.0` for fixed-param strategies
(identical params every fold = "unmeasurable"). Changed to `100.0` — identical
params is perfect stability. Also added `rsi_buy_level`/`rsi_sell_level` to
`_strategy_parameters()` key list alongside legacy `rsi_buy_threshold` names.

**Commit:** `6d60ee9` | **Tests:** 405/405 pass | **Adversarial review:** no HIGH/CRITICAL

### 3. Daily Brief Pipeline Started

Three-session learning cycle active (from Codex handoff 2026-09-08 three-session note):
- Asia Open brief → `data/daily_briefs/YYYY-MM-DD.md` + `_levels.json`
- London handover → `data/daily_briefs/YYYY-MM-DD_london.md` (with outcome template)
- US Open → paste into session, saved same way

Briefs saved: Sep 7 retro, Sep 8 Asia, Sep 8 London (with Day 1/2 learning cycle outcome template).
Day 1 (Sep 7): no-trigger, XAU unresolved at 4,435-4,455.

### 4. Ideas from "Ideas to add" folder logged

- `IDEA-EXT-REPO-001` — staged external repo import (Freqtrade, PyPortfolioOpt, Agent Framework)
- `IDEA-LIVE-LIB-001` — live/ stub seal + Local Librarian Skill (Part B needs Greg sign-off)
- Involio integration → PARKED (AVD/mitmproxy setup uncertain)

## Active State

| Entity | Status | Metric | Notes |
|--------|--------|--------|-------|
| atr_breakout_v3 | ACTIVE | 1.49 | WF PF=1.49, 153 trades |
| ema_volume_fixed | ACTIVE | 1.45 | WF PF=1.45, 689 trades |
| goldv2_v2 | ACTIVE | 1.44 | WF PF=1.44, 571 trades |
| ema_volume_v3 | ACTIVE | 1.43 | WF PF=1.43, 199 trades |
| gold_orb_v1 | ACTIVE | 1.18 | WF PF=1.18, 64 trades |
| vol_filtered_momentum_v1 | ACTIVE | 1.13 | WF PF=1.13, 66 trades |
| rsi_trend_v4_35_65_atr3 | ACTIVE | 1.921 | RESEARCH — needs paper collection |
| vwmr_v1 | PARKED | 1.61 | 14 trades only, retest at 30+ |

## Pending Tasks (human-owned, no Codex action needed)

- `IDEA-EXT-REPO-001` — assign to Codex when ready to start Week 1 of import strategy
- `IDEA-LIVE-LIB-001` Part A (live/ stubs) — safe to build, small bounded task
- `IDEA-LIVE-LIB-001` Part B (Librarian Skill) — needs Greg sign-off on Obsidian endpoint first

## Next Codex Work (when assigned)

None currently queued. Await human instruction via `state_cli.py add-task`.
