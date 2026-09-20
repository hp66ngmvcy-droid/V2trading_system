# Codex Task: key_level_sweep_v1 Strategy Build
Date: 2026-09-07
Author: Claude
Status: DEFERRED — collect 10+ daily briefs first, then build
Priority: Medium

---

## Objective

Build `key_level_sweep_v1`, a new paper-mode strategy for XAUUSD (and optionally BTCUSD)
that trades daily key levels sourced from an external morning brief JSON file, confirmed
by price-action sweep/rejection signals on M15 bars.

DO NOT build until `data/daily_briefs/` contains at least 10 dated `_levels.json` files.
Check count first: `ls data/daily_briefs/*_levels.json | wc -l`

---

## Background

The V2 system currently uses rsi_trend_v4 (XAUUSD M15, RSI 38/62, ATR 2.0).
That strategy detects momentum from price data alone. It has no knowledge of:
- Where institutional supply/demand zones are each day
- What the macro regime is (yields, USD, Fed bias)
- Which direction the day's analysis favours

A daily brief (saved to `data/daily_briefs/YYYY-MM-DD_levels.json`) captures
exactly this information. The brief defines sell zones, buy zones, no-trade zones,
invalidation levels, and a directional confidence score.

## Three-Session Structure (from 2026-09-07)

Each trading day now produces up to three brief sections:

| Session | Time (UK) | Purpose |
|---------|-----------|---------|
| Asia Open | ~00:30 | Overnight structure, likely ranges, initial bias |
| London Handover | ~06:30 | Asia H/L, liquidity sweeps, best conditional setup into Europe |
| US Open | ~13:15–13:30 | Refresh yields/DXY/VIX/equities, confirm or invalidate London move |

The US session is most important for XAUUSD and BTCUSD on days with US macro releases
or Fed speakers. On quiet days the US review is short (~500 tokens).

The `_levels.json` should reflect the **most recent session's levels** for that day.
The `sessions_present` array records which sessions were included.
The strategy loader should prefer US-open levels when available (most confirmed),
fall back to London, then Asia if that is all that exists.

`key_level_sweep_v1` uses these levels as entry filters rather than computing them
dynamically from rolling price data.

---

## Daily Brief JSON Format

Reference file: `data/daily_briefs/2026-09-07_levels.json`

Relevant fields per symbol:
```json
{
  "date": "YYYY-MM-DD",
  "XAUUSD": {
    "daily_bias": "SELL",
    "sell_confidence": 0.67,
    "buy_confidence": 0.63,
    "key_levels": {
      "bearish_invalidation": 4470,
      "sell_zone_high": 4455,
      "sell_zone_low": 4435,
      "no_trade_high": 4435,
      "no_trade_low": 4415,
      "buy_zone_high": 4420,
      "buy_zone_low": 4410,
      "asia_liquidity_low": 4395,
      "sell_continuation_trigger": 4390
    },
    "top_scenario": "SELL_REJECTION",
    "top_scenario_targets": [4410, 4390],
    "top_scenario_invalidation": 4470
  }
}
```

---

## Files to Create

### 1. `src/tar_system/data/daily_brief_loader.py`

Single function: `load_daily_levels(date: str, symbol: str, briefs_dir: Path) -> dict | None`

- Accepts date string `"YYYY-MM-DD"` and symbol `"XAUUSD"`
- Looks for `briefs_dir / f"{date}_levels.json"`
- Returns the symbol sub-dict or `None` if file missing
- No fallback to previous day — missing = no signal that day
- Must not raise on missing file

```python
def load_daily_levels(date: str, symbol: str, briefs_dir: Path) -> dict | None:
    path = briefs_dir / f"{date}_levels.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    return data.get(symbol)
```

### 2. `src/tar_system/strategies/key_level_sweep_v1.py`

Dataclass strategy. Parameters:

```python
@dataclass
class KeyLevelSweepV1:
    symbol: str = "XAUUSD"
    min_confidence: float = 0.65      # minimum brief confidence to act
    atr_multiplier: float = 2.0       # stop distance in ATR
    wick_ratio: float = 0.40          # min wick/bar-range to confirm rejection
    briefs_dir: Path = Path("data/daily_briefs")
    name: str = "key_level_sweep_v1"
    version: str = "0.1.0"
```

Signal logic per M15 bar:

```
1. Load daily levels for bar's date via load_daily_levels()
   If None → HOLD (no brief for that day)

2. Check confidence gate:
   SELL signal possible only if sell_confidence >= min_confidence
   BUY signal possible only if buy_confidence >= min_confidence

3. No-trade zone filter:
   If no_trade_low <= close <= no_trade_high → HOLD

4. SELL signal:
   If sell_confidence >= min_confidence:
     If sell_zone_low <= high <= sell_zone_high:   (price entered sell zone)
       upper_wick = high - max(open, close)
       bar_range = high - low
       If upper_wick / bar_range >= wick_ratio:    (rejection candle)
         If close < sell_zone_low:                 (closed back below zone)
           stop = bearish_invalidation
           target1 = top_scenario_targets[0]
           target2 = top_scenario_targets[1]
           → SELL signal

5. BUY signal:
   If buy_confidence >= min_confidence:
     If buy_zone_low <= low <= buy_zone_high:      (price swept buy zone)
       lower_wick = min(open, close) - low
       bar_range = high - low
       If lower_wick / bar_range >= wick_ratio:    (reclaim candle)
         If close > buy_zone_high:                 (closed back above zone)
           stop = asia_liquidity_low - (atr * atr_multiplier)
           target1 = sell_zone_low
           target2 = sell_zone_high
           → BUY signal

6. Invalidation check:
   If SELL signal active and close > bearish_invalidation → close/HOLD
   If BUY signal active and close < asia_liquidity_low → close/HOLD

7. ATR floor: if atr == 0 → HOLD (no valid ATR, skip bar)
```

Signal output must match `Signal` dataclass from `base.py`.
Include `reason_code` from `reason_codes` module for every HOLD path.

### 3. `scripts/run_key_level_sweep_backtest.py`

```python
SYMBOL = "XAUUSD"
TIMEFRAME = "M15"
BRIEFS_DIR = ROOT / "data/daily_briefs"

# Load features, run backtest with KeyLevelSweepV1
# Print: trades, win_rate, profit_factor, max_drawdown, score, verdict
# Save to data/results/key_level_sweep_v1_XAUUSD_M15.json
```

---

## Success Criteria

- [ ] `daily_brief_loader.py` has unit test: missing file returns None, valid file returns dict
- [ ] Strategy generates at least 5 trades across the available brief dates
- [ ] No crash on days with missing brief file (graceful HOLD)
- [ ] Backtest runs without error: `python scripts/run_key_level_sweep_backtest.py`
- [ ] Score and verdict printed to stdout
- [ ] Results saved to `data/results/key_level_sweep_v1_XAUUSD_M15.json`
- [ ] All existing tests still pass: `python -m pytest tests/ -q`

---

## Hard Constraints (V2 Rules)

- Paper mode only — no live trading wiring
- No Docker, Ray, Polars
- Do not overwrite `rsi_trend_v4.py` or any existing strategy
- Do not add live trading imports or broker connections
- Keep deps light — stdlib + pandas + existing V2 imports only
- Inspect files before editing, never recreate working modules
- Write a `codex_notes/YYYY-MM-DD_key-level-sweep-v1-build.md` done file on completion

---

## Pre-Build Check

Before writing any code:
```bash
ls data/daily_briefs/*_levels.json | wc -l
```
If result < 10, stop and write a note explaining why build was deferred.
Do not build a partial strategy against insufficient data.

---

## Context Files to Read First

- `src/tar_system/strategies/liquidity_sweep_v1.py` — similar sweep logic for reference
- `src/tar_system/strategies/rsi_trend_v4.py` — existing top strategy, do not break
- `src/tar_system/strategies/base.py` — Signal dataclass
- `src/tar_system/data/daily_briefs/2026-09-07_levels.json` — example brief JSON
- `collab/STATUS.md` — current system state
