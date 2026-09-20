---
id: SESSION-2026-09-20b
type: session-handoff
status: DONE
logged: 2026-09-20
author: claude-sonnet-4-6
CLASSIFICATION: PUBLIC_TECHNICAL_ONLY
---

# Session — Codex Review Fixes + Brief Validator — 2026-09-20

## What was built

### 1. Three correctness fixes in `key_level_sweep_v1.py` (commit `1ed79c5`)

**Fix 1 — fail-closed on malformed `issued_at`** (`key_level_sweep_v1.py:44`)
- Before: `except Exception: pass` → gate silently passed malformed timestamps
- After: `except Exception: return None` — fail-closed, brief blocked
- New tests: `test_malformed_issued_at_returns_none`, `test_empty_issued_at_uses_default_gate`

**Fix 2 — raw R:R comparison** (`key_level_sweep_v1.py:166, 210`)
- Before: `rr = round(reward / risk, 2); if rr < self.min_reward_risk` — `0.994` rounded to `0.99` passed a `1.0` gate
- After: compare `rr_raw` (unrounded), round only for metadata reporting
- New tests: `test_rr_just_below_threshold_returns_hold`, `test_rr_exactly_at_threshold_fires`

**Fix 3 — BUY reads `top_scenario_targets`** (`key_level_sweep_v1.py:203–207`)
- Before: BUY take-profit hardcoded to `sell_zone_low`, ignoring `top_scenario_targets`
- After: reads `targets[0]` when available and above entry; falls back to `sell_zone_low`
- New tests: `test_buy_uses_top_scenario_targets`, `test_buy_falls_back_to_szl_when_targets_below_entry`

### 2. `scripts/validate_brief.py` — read-only brief validator

- Input: `_levels.json` path or directory
- Output: table of SELL/BUY candidates with entry, stop, target, risk, reward, raw R:R, rejection reason
- Shares calculation logic with strategy (imports nothing from strategy — parallel impl to avoid circular import, but uses same formulas)
- Handles: `asia_liquidity_low` / `breakdown_trigger` / ATR fallback for BUY stop anchor
- CLI: `python scripts/validate_brief.py data/daily_briefs/ --atr 20 --min-rr 1.0`

### 3. Validator output — all 10 historical briefs

```
5 PASS  31 FAIL  (min_rr=1.0, atr=20.0)
```

Passing briefs: Sep-07 BTCUSD BUY, Sep-08 XAUUSD SELL, Sep-11 BTCUSD BUY, Sep-17 XAUUSD SELL, Sep-18 XAUUSD SELL.

Root cause of FAIL: T1 placed too close to entry in most briefs (0.1–0.9 R:R). Two BTC briefs have negative R:R (target on wrong side of entry). Briefs were written before R:R gate existed.

### 4. Research this session

- FVG formula read from `joshyattridge/smart-money-concepts`: uses `shift(-1)` — **look-ahead leak**. Cannot be used row-by-row. Confirmed inline would need to check prior bar's confirmed 3-candle pattern only.
- 10 repos catalogued for future reference (SMC, WF backtesting, gold signal, systematic trading index)
- London session filter confirmed optimal 07:00–12:00 UTC for XAUUSD sweeps

### 5. Codex counterproposal reviewed and debated

Codex found 3 bugs (all now fixed), challenged zero-trade claim as insufficient evidence, and proposed 5-step implementation order (validator → target rules → session cutoff → regime provenance → FVG experiment). Claude agreed with all findings.

Open debate topic sent via `debate print`: whether historical brief T1 correction is legitimate calibration or look-ahead bias. Pending Codex response.

## Research findings and conflict synthesis

Conducted adversarial research — searched for evidence **against** each proposed improvement.

**Critical finding — ICT/SMC mechanical edge:**
StatOasis ran 648 mechanical backtests of core ICT entries (order blocks, FVGs, liquidity sweeps, OTE) across SPY/QQQ/DIA/IWM. 0/648 beat buy-and-hold. No statistically significant forward-return edge. XAUUSD may differ (physical commodity, genuine institutional hedging) but brief zone quality is unverified without outcome data.

**Revised priority order from synthesis:**

| Rank | Item | Evidence |
|------|------|----------|
| 1 | Brief outcome logging (`hit_target`/`hit_stop`) | Required before any filter improvement is verifiable |
| 2 | Brief JSON schema hook | Pure integrity — no statistical assumptions |
| 3 | Brier score (after 10 outcomes) | Validates confidence values are meaningful |
| 4 | NY session window (13:30–15:00 UTC) | Current 12:00 cutoff blocks documented clean Gold setups |
| 5 | ATR-percentile regime classifier | Safer than FRED tracker; validate after outcomes |
| 6 | FVG experiment | Weakest evidence; defer to 50+ signals |

**R:R gate reassessment:**
Gate is correct as brief-writing discipline (forces T1 placement). As a live filter it conflates geometry with expectancy — a 0.7 R:R setup at 65% WR beats 1.2 R:R at 42% WR. Revisit min_reward_risk after 30+ outcomes.

**Session filter reassessment:**
`session_end_utc=12:00` correct for London AM. Blocks NY killzone (13:30–15:00 UTC) which research confirms produces clean Gold sweeps. Add as second window param, not a replacement.

## Open decisions

1. **Historical brief T1** — leave unchanged (Path A) or lower min_rr threshold for historical period (Path B)? Do NOT edit brief files. Debate prompt sent to Codex.
2. **BUY take-profit policy** — `top_scenario_targets[0]` now used (implemented Fix 3). Fallback to `sell_zone_low`.

## Remaining approved steps (not yet built)

| Priority | Task | Notes |
|----------|------|-------|
| 4 | Regime provenance — `regime_observed_at` on new briefs only | No historical backfill — human action |
| 5 | FVG inline helper — `require_fvg: bool = False` | Needs 30+ trades first; no external dependency |

### 5. Session cutoff param (commit `dee553f`)

Added `session_end_utc: str | None = "12:00"` to `KeyLevelSweepV1` dataclass.

- Parsed at `__post_init__` to `_session_end_minutes: int | None`
- Checked in `generate_signal()` before zone logic — bar open time (UTC naive) `>= cutoff` → `SESSION_FILTER_BLOCK`
- Default `"12:00"` UTC for XAUUSD (London AM). Set `None` for BTCUSD or any 24h instrument.
- Bar timestamps confirmed as opening times (checked `XAUUSD_M15.parquet` — naive UTC)
- 4 new tests: before cutoff passes, at cutoff blocked, after cutoff blocked, `None` allows all hours
- **499/499 tests passing**

## Test state

**499/499 passing** (up from 489 at start of this session — 10 new tests total).

## Brief writing rule going forward

Run `python scripts/validate_brief.py <new_brief.json> --atr <current_atr> --min-rr 1.0` before saving any new brief. T1 must PASS before the brief is used for signals.
