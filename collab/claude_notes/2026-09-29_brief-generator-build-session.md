# Brief Generator Build Session — Session Notes

Date: 2026-09-29
Author: Claude
Refs:
- `claude_notes/2026-09-28_xauusd-provenance-debate-response.md`
- `claude_notes/2026-09-28_stability-provenance-response.md`
- `scripts/generate_daily_brief.py`
- `tests/test_generate_daily_brief.py`

Tests verified:
`PYTHONPATH=src venv/bin/python -m pytest tests/test_generate_daily_brief.py -q`
→ **47 passed in 1.61s**

Full suite:
`PYTHONPATH=src venv/bin/python -m pytest tests/test_core.py tests/test_multi_agent_scorer.py tests/test_dashboard_promotion_layer.py tests/test_research_committee.py tests/test_walk_forward_inputs.py tests/test_cli_backtest_inputs.py tests/test_gold_orb_v1.py tests/test_xauusd_provenance_report.py tests/test_generate_daily_brief.py tests/test_daily_brief_loader.py -q`
→ **165 passed in 2.93s**

No strategy code changed. No data altered. No TAR system scoring modified.

---

## What was built

All changes are in `scripts/generate_daily_brief.py` and
`tests/test_generate_daily_brief.py`. The TAR strategy pipeline is untouched.

### Round 1 — Multi-day levels + timeframe structure + scenario maps

**`_multi_day_levels(bars, today_str, n_days=5)`**

Computes from M15 parquet:
- `prev_day`: O/H/L/C of last completed trading day
- `prev_3d_high` / `prev_3d_low`: 3-day range
- `prev_5d_high` / `prev_5d_low`: 5-day range
- `week_high` / `week_low`: current Mon–Fri range
- `recent_days`: list of last n_days daily candles

**`_timeframe_structure(bars)`**

Resamples M15 to 1H. Counts HH/HL vs LH/LL across last 10 1H bars.
Returns:
- `h1_structure`: `BULLISH` / `BEARISH` / `NEUTRAL`
- `m15_pattern`: `RANGE` / `BREAKOUT` / `REJECTION` / `CONTINUATION` (last 32 bars)
- `combined_verdict`: `SELL_BIAS` / `BUY_BIAS` / `SELL_WATCH` / `BUY_WATCH` / `WAIT`

**`_scenario_maps(current_price, multi_day, sell_setup, buy_setup, atr)`**

Four pre-built conditional entry maps. Each has: condition string, entry zone,
stop, T1, T2, RR-T1, RR-T2, risk pts, confidence base, invalidation note.

| Scenario | Trigger |
|---|---|
| `SELL_RETEST` | M15 rejection at sell zone + 5m lower high |
| `BUY_EXHAUST` | M15 higher low at buy zone + 5m break above |
| `BREAKDOWN_CONT` | <prev-day-low + 30m acceptance + failed reclaim |
| `BREAKOUT_CONT` | >prev-day-high + 30m acceptance + successful retest |

T1/T2 anchored to prev-day levels when available; falls back to ATR multiples.

---

### Round 2 — IV walls

**`_iv_walls(price, iv_pct)`** — pure function, testable independently.

Formula: `daily_em = price × (iv_pct/100) × √(1/252)`

Returns: `iv_expected_move_daily`, `iv_high_90`/`iv_low_90` (1.645σ, 90%
probability), `iv_high_68`/`iv_low_68` (1σ, 68%).

**`_fetch_btc_atm_iv(btc_price)`** — Deribit no-auth endpoint. Finds nearest
expiry, ATM strike, averages call + put `mark_iv`. Returns annualised IV % or
`None`. Reuses same endpoint as `_btc_derivatives` — no extra rate-limit cost.

**`--xau-iv FLOAT`** CLI argument. XAU has no free IV source. User provides
annualised GVZ reading from TradingView (e.g. `--xau-iv 14.2`). The brief uses
it if present; omit it and XAU `iv_walls` is null.

Session MD shows IV walls table with the mean-reversion rule: "10% of sessions
break through — size accordingly."

---

### Round 3 — 200 EMA + session VWAP + double-touch alerts

**`_ema200(bars)`** — 200-period EMA on M15 close. `None` if fewer than 200
bars.

**`_session_vwap(bars, today_str)`** — anchored VWAP per session:

| Session | UTC anchor |
|---|---|
| Asia | 00:00 |
| London | 08:00 |
| NY | 13:00 |

Volume-weighted when column available; equal-weight fallback for test fixtures
or data without volume.

**`_double_touch_alerts(bars, today_str, resist_levels, support_levels, atr)`**

Detects double-top / double-bottom patterns in today's session bars.

Touch tolerance: ATR × 0.15.

Two or more bar touches within tolerance = alert.

Level hierarchy (passed by `build_symbol_block`):
1. `PDH` / `PDL` — previous day high / low (strongest signal)
2. `PM_HIGH` / `PM_LOW` — premarket = today's Asia session H/L
3. `ID_HIGH` / `ID_LOW` — intraday overall high / low

Each alert: `level_name`, `level_price`, `touch_type`, `touch_count`,
`last_touch_time`, `signal`.

Session MD shows `⚡ DOUBLE-TOUCH ALERTS` block at the top of each symbol
section when any alerts are active.

---

## Session MD output (what a brief now shows per symbol)

```
## XAUUSD — SELL lean

Current price ~4158 | ATR ~28 | Bias: SELL | Anti-bias: BUY ★ ANTI-BIAS (2.92R)

**Structure:** 1H `BEARISH` | M15 `REJECTION` | → **SELL_BIAS**
**Levels:** EMA200 `4242` | Asia VWAP `4131` | London VWAP `4149`

### ⚡ DOUBLE-TOUCH ALERTS

🔴 DOUBLE TOP at `PDH` = 4285 (2x touches) → SELL on rejection — stop above level

**Multi-day reference levels**
| Level | Value |
| Prev day high | **4285** |
| Prev day low  | **4110** |
...

**IV walls (options-implied expected range)**
| IV high (90%) | **4207** | 90% stay below |
| IV low  (90%) | **4109** | 90% stay above |

**Scenario decision tree**
| SELL_RETEST | M15 rejection at 4240–4260 + 5m lower high | 4240–4260 | 4280 | 4110 | 4085 | 2.2R | 3.1R |
| BREAKDOWN_CONT | <4110 (prev day low) + 30m acceptance... | ...
```

---

## Data dependency note

XAUUSD M15 validated data ends 2026-09-25 (Saturday bar provenance unresolved).
BTCUSD M15 validated data ends 2026-09-25.

The brief generator will produce stale levels until the data extension runs:

```bash
secrets_run_trading -- venv/bin/python scripts/extend_m15_data.py
```

XAUUSD will still be `SOURCE_REVIEW_REQUIRED` in `check_strategy.py` even after
extension — that gate is separate from the brief generator.

After extension:

```bash
secrets_run_trading -- venv/bin/python scripts/generate_daily_brief.py \
    --xau-iv 14.2 --dry-run
```

---

## No debate needed

These are standalone additions to the brief generator. They do not touch the
TAR scoring pipeline, walk-forward, gates, multi-agent scorer, or any validated
strategy. Codex can review the new functions at will.

The XAUUSD provenance debate response (`claude_notes/2026-09-28_xauusd-provenance-debate-response.md`)
remains open. Next Codex task there: read-only source comparison report.
That work is independent of the brief generator.
