# PD Array Rejection v1 — Strategy Debate

Date: 2026-09-29
Author: Claude
Refs:
- `src/tar_system/strategies/key_level_sweep_v1.py`
- `src/tar_system/strategies/gold_orb_v1.py`
- `src/tar_system/strategies/base.py`

Status: DEBATE — build pending resolution of open questions below

---

## Strategy Description (formalised)

**Name:** `pd_array_rejection_v1`

**Timeframes:** 4H (level detection) + 15M (entry trigger)

**Logic:**

1. Resample M15 → 4H. Detect unmitigated PD arrays:
   - **Bearish order block**: last bullish 4H candle immediately before a
     significant bearish displacement (≥ 1× ATR move down from that candle's close)
   - **Bullish order block**: last bearish 4H candle immediately before a
     significant bullish displacement (≥ 1× ATR move up)
   - **Bearish FVG**: 3-candle imbalance — `candle[i-1].low > candle[i+1].high`
     (gap between candle i-1 low and candle i+1 high, never filled)
   - **Bullish FVG**: `candle[i-1].high < candle[i+1].low`
   - **Mitigation**: a PD array is consumed once price closes through its
     defining level. Consumed arrays are removed from the active list.

2. On 15M bars: monitor for price trading INTO an active 4H level.
   - Into bearish OB/FVG: bar high enters the zone
   - Into bullish OB/FVG: bar low enters the zone

3. On 15M: detect a rejection block at the 4H level.
   - **Rejection block**: the 15M bar (or sequence) that enters the 4H zone
     and closes back out. Defined as: bar enters zone AND close is outside
     the zone in the direction of rejection.
   - Bearish rejection: bar high enters bearish OB zone, close < zone low
   - Bullish rejection: bar low enters bullish OB zone, close > zone high

4. **Entry**: limit order at 50% of rejection block candle range
   - Rejection block high/low → midpoint = (high + low) / 2
   - SELL limit at midpoint (bearish rejection)
   - BUY limit at midpoint (bullish rejection)

5. **Stop**: 10 points fixed (as described)

6. **Target**: 6R = entry ± 60 points

---

## Debate Questions

### Q1 — Fixed 10-point stop for XAUUSD

Recent ATR for XAUUSD is ~28–35 pts. A 10-point stop is sub-ATR.

Sub-ATR stops get hit by noise on almost every bar. On BTC (ATR ~500–800+),
a 10-point stop is meaningless — price will breach it within the first bar.

**Position**: Fixed 10-point stop is not viable as a universal parameter.
Either:
- (a) Make stop ATR-based (e.g. `stop = atr × 0.35`) and set default so
  ATR 28 → ~10 pts (multiplier ≈ 0.35), which preserves the described intent
  for current XAU while being portable to BTC.
- (b) Keep stop as 10 pts for XAUUSD explicitly, separate param for BTCUSD.

Recommend (a). 6R target stays the same — `target = stop × 6`.

### Q2 — "PD array" scope for v1

Full ICT PD array hierarchy includes: order blocks, FVGs, breaker blocks,
mitigation blocks, rejection blocks, propulsion blocks, equilibrium,
premium/discount zones, etc.

For v1 the useful subset is: **order blocks + FVGs only**.
Breaker/mitigation blocks require tracking prior OBs that were broken, adding
state complexity. Defer to v2.

Codex should implement `_detect_4h_order_blocks()` and `_detect_4h_fvgs()`.

### Q3 — Mitigation / "unmitigated" tracking

An order block that has already been traded through is no longer a valid entry.
This requires stateful tracking across bars — the strategy must mark OBs as
consumed when price closes through them.

The existing strategy pattern (`key_level_sweep_v1`, `gold_orb_v1`) is
stateless per-bar. PD array detection requires a stateful pre-processing pass
over 4H bars before the 15M signal loop begins.

**Approach**: precompute active PD array zones as a list of `(zone_low, zone_high,
direction, source_ts)` tuples from 4H bars BEFORE the signal loop. Pass this
list into each 15M bar's `generate_signal()` call. Update consumed arrays
as bars pass through them.

This is a different pattern from existing strategies. Codex must be aware.

### Q4 — Defining "significant displacement" for OB detection

"Last bullish candle before bearish displacement" needs a threshold.
Without one, any candle before any move qualifies.

Proposed: displacement ≥ 1.0 × 4H ATR from the OB candle's close.
This filters minor pullbacks from genuine order block formations.

Configurable parameter: `ob_displacement_atr_mult: float = 1.0`

### Q5 — Data availability for 4H

We have M15 bars. Resampling M15 → 4H is clean.
XAUUSD M15 validated data ends 2026-07-10 23:45 UTC (Saturday bar gate).
BTC M15 goes to 2026-09-29 (just extended).

For XAUUSD the 4H levels will be stale by ~80 days until _v1 rebuild
clears the provenance gates. This does not block building the strategy
but limits live useful output until XAUUSD data is clean.

### Q6 — R target of 6R is aggressive

6R from a sub-ATR stop means the target is ~60 pts for XAU.
Previous day range is typically 150–300 pts. A 60-pt target is reachable
within session — not aggressive in absolute terms.

But: high R targets require very precise entries. Limit order at 50% of
rejection block is appropriate — this is the designed precision mechanism.

No change to 6R. Worth flagging in backtest: expect lower win rate, higher
average winner. Need minimum 17% win rate to break even at 6R.

---

## Build Plan (pending Codex sign-off on Q1 and Q3 approach)

### Files

```
src/tar_system/strategies/pd_array_rejection_v1.py
tests/test_pd_array_rejection_v1.py
```

No new dependencies. Resampling via pandas `.resample()`.

### Key functions

```python
def _detect_4h_order_blocks(bars_4h: pd.DataFrame, atr_mult: float) -> list[dict]:
    # Returns list of {zone_low, zone_high, direction, ts, consumed: False}

def _detect_4h_fvgs(bars_4h: pd.DataFrame) -> list[dict]:
    # Returns list of {zone_low, zone_high, direction, ts, consumed: False}

def _is_rejection_block(bar: pd.Series, zone: dict, atr: float) -> bool:
    # True if bar entered zone and closed back outside in rejection direction

def _rejection_midpoint(bar: pd.Series) -> float:
    # (high + low) / 2
```

### Strategy class

```python
@dataclass
class PdArrayRejectionV1:
    symbol: str = "XAUUSD"
    ob_displacement_atr_mult: float = 1.0
    stop_atr_mult: float = 0.35      # ~10 pts at ATR 28
    reward_risk: float = 6.0
    session_end_utc: str | None = "20:00"
    one_trade_per_day: bool = True
    name: str = "pd_array_rejection_v1"
    version: str = "0.1.0"
```

### Test coverage

- OB detection: bullish OB found, bearish OB found, consumed OB not returned
- FVG detection: bullish/bearish FVG found, filled FVG not returned
- Rejection block: enter-and-close-out = True, enter-only = False
- Entry midpoint arithmetic
- Signal: SELL at bearish OB rejection, BUY at bullish OB
- No signal when no active PD array in range
- Stop = `stop_atr_mult × atr`, target = `stop × reward_risk`

---

## Codex Task

1. Resolve Q1 (stop approach) and Q3 (stateful pre-processing pattern) by
   building to the plan above.
2. Write tests first, then implement.
3. Run full suite: `PYTHONPATH=src venv/bin/python -m pytest tests/ -q`
4. Report pass count and any pre-existing failures.
5. Do not run walk-forward or promote to KEEP — this is new, untested strategy.
   Status after build: `PENDING_BACKTEST`.

Write completion note: `codex_notes/2026-09-29_pd-array-rejection-v1-done.md`
