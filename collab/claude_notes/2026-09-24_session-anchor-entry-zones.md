---
type: update
date: 2026-09-24
author: claude
subject: generate_daily_brief.py — session-anchored intraday entry zones
status: complete
---

## What changed

`scripts/generate_daily_brief.py` now produces intraday entry zones anchored to
real session structure (yesterday's Asia/London/NY highs and lows) instead of
2-day percentile bands.

### Why

Old method: entry zones from 88th/12th percentile of last 192 M15 bars.
Problem: zones were 4–7 ATR wide, not tradeable (e.g. BTC entry 86527–87279 = 752pt wide).

New method: "best anchor" selected from session highs/lows nearest to current price.
Result: zones are ~1.3 ATR wide, stops are 2 ATR beyond anchor, R:R ~1.1–1.5 for
the structural fade setups.

### New functions (scripts/generate_daily_brief.py)

`_best_anchor(side, current_price, today_asia, yest_asia, yest_london, yest_ny, swing_levels)`
- Returns (anchor_price, label) — the nearest qualifying session extreme
- SELL: nearest session HIGH above current price; BUY: nearest session LOW below
- Falls back to swing percentile if no session data qualifies

`_compute_levels()` — updated with `anchor` param
- If anchor provided: zone = [anchor ± 1.0 ATR], stop = anchor ± 2.0 ATR
- T1 = swing support/resistance floor if directionally valid, else anchor ± 3 ATR
- T2 = swing extreme if valid, else anchor ± 5 ATR
- Fallback (anchor=None): original percentile-based logic unchanged

`build_symbol_block()` — now computes yest_asia, passes anchors to `_compute_levels()`
- Exposes `session_context` block in brief JSON (anchor, label, Asia range pts)

Session MD now shows Session context line:
```
**Session context:** Asia range: 4274 – 4304 (30 pts) | SELL anchor: 4284.94 (yest_london_high) | ...
```

### Sample output (2026-09-25)

```
XAUUSD  SELL anchor 4284.94 (yest_london_high)  zone [4279, 4287]  stop 4296  T1 4260  R:R 1.1
XAUUSD  BUY  anchor 4274.05 (yest_asia_low)     zone [4272, 4280]  stop 4263  T1 4344  R:R 3.75
BTCUSD  SELL anchor 84612 (yest_asia_high)       zone [84420, 84670] stop 84996 T1 83726 R:R 1.2
BTCUSD  BUY  anchor 83745 (yest_asia_low)        zone [83687, 83937] stop 83360 T1 86527 R:R 4.49
```

## Status

Live — generator uses this for all future briefs. Sep-25 brief should be re-run to
update the JSON and session MD with the new zones.

No changes to `paper_game_sim.py` needed — it reads from `_levels.json` fields which
are still named `sell_zone_low`, `sell_zone_high`, `bearish_invalidation`, `top_scenario_targets`.
Those fields are populated correctly from the new `_compute_levels()` output.

## For Codex

No action needed. This is an FYI handoff. The generator is stable.

If backtesting shows the 2 ATR stop is too wide or too tight relative to historical
outcomes, the multipliers are in `_compute_levels()` lines:
  `stop = round(anchor + atr * 2.00, 2)` — SELL stop
  `stop = round(anchor - atr * 2.00, 2)` — BUY stop
Adjust these based on sim data when 20+ anchor-based trades are logged.
