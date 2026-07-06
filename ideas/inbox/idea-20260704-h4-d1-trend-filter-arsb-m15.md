# Idea: H4/D1 Trend Filter for arsb_v1 M15 Entries

**Date:** 2026-07-04
**Status:** RESEARCH COMPLETE — ready to implement, blocked on M15 data (PER-22)
**Ticket:** PER-28

---

## Problem

arsb_v1 takes breakout entries in both directions (BUY above Asian high, SELL below Asian low)
with no higher-timeframe trend alignment. In choppy/mixed D1 regimes, counter-trend breakouts
produce false starts — price breaks the box then retraces back through it.

---

## Data Audit

| Source | Available | Range | Bars |
|--------|-----------|-------|------|
| XAUUSD_D1 | ✅ | 2019-06-10 → 2026-06-10 | 1,763 |
| XAUUSD_H1 | ✅ | 2020-09-28 → 2026-04-30 | 33,029 |
| XAUUSD_H4 | ❌ no parquet | — resample from H1 | 8,642 (derived) |
| XAUUSD_M15 | ⚠️ short | 2026-02-11 → 2026-05-26 | 100,000 (~3.5 months) |

**M15 backtest window is too short for significance.** Wait for PER-22 (July 2026 import).

---

## D1 Trend Structure (2019–2026)

Gold on D1 is not a choppy market — it trends:

| Condition | % of time |
|-----------|-----------|
| EMA20 > EMA50 and 5-day slope > 0 (trend UP) | 53.2% |
| EMA20 < EMA50 and 5-day slope < 0 (trend DOWN) | 21.8% |
| Mixed / choppy | 25.0% |
| ADX > 25 (strong directional) | 66.4% |
| Median ADX | 31.8 |

**Implication:** A D1 trend filter would suppress ~25% of sessions (choppy) and
flip signal direction the remaining ~22% (downtrend). Combined, this changes the
entry decision on ~47% of signals — meaningful filter, not cosmetic.

---

## Recommended Filter Design

### Option A — D1 EMA alignment (preferred)

```
BUY signal allowed when:  D1 EMA20 > EMA50
SELL signal allowed when: D1 EMA20 < EMA50
Both signals blocked when: neither condition holds (choppy range)
```

**Why D1 over H4:**
- D1 data available back to 2019 (7 years vs 5.5 years from H1)
- No resampling step needed — parquet already exists
- Trend on D1 is slower → fewer whipsaws → fewer false filter switches
- Consistent with how cross_asset_correlation_v1 loads external D1 series

### Option B — D1 + H4 confirmation (tighter, fewer signals)

```
BUY allowed when:  D1 EMA20 > EMA50  AND  H4 EMA20 > H4 EMA50
SELL allowed when: D1 EMA20 < EMA50  AND  H4 EMA20 < H4 EMA50
```

H4 adds an intermediate gate — catches cases where D1 is trending but H4 has
reversed (e.g. a pullback week within a larger uptrend). More selective; fewer
trades; stronger expected quality.

**H4 implementation:** Resample from XAUUSD_H1 at runtime using
`pd.read_parquet(...).resample("4h").last()`. No new parquet file needed.
Cache the resample result in `__post_init__`.

---

## Implementation Pattern

Follow the existing `cross_asset_correlation_v1` pattern — load external series
in `__post_init__`, look up current-bar date in the series index.

```python
# In arsb_v1 __post_init__:
self._d1_ema20, self._d1_ema50 = _load_d1_emas("XAUUSD_D1", span_fast=20, span_slow=50)

# In generate_signal, after session window check:
date_key = pd.Timestamp(row["timestamp"]).normalize()
if date_key in self._d1_ema20.index:
    ema_fast = self._d1_ema20[date_key]
    ema_slow = self._d1_ema50[date_key]
    d1_bullish = ema_fast > ema_slow
    d1_bearish = ema_fast < ema_slow
    # Gate: block counter-trend signals
    if entry > breakout_long and not d1_bullish:
        return hold_with(rc.TREND_FILTER_BLOCK)
    if entry < breakout_short and not d1_bearish:
        return hold_with(rc.TREND_FILTER_BLOCK)
```

Requires: add `TREND_FILTER_BLOCK` to `reason_codes.py`.

---

## Parameters to Backtest

Once M15 data covers ≥ 12 months (after PER-22):

| Parameter | Values to test |
|-----------|---------------|
| D1 fast EMA span | 10, 20, 50 |
| D1 slow EMA span | 50, 100, 200 |
| ADX threshold (optional gate) | off, 20, 25, 30 |
| H4 confirmation | off, on |

Primary metric: profit factor on filtered signals vs unfiltered baseline.
Minimum 30 trades per variant required before scoring.

---

## Next Steps

1. ✅ Research complete
2. ⏳ **Wait for PER-22** — July 2026 M15 data import (otherwise backtest window too short)
3. After import: add `TREND_FILTER_BLOCK` reason code
4. Implement Option A in arsb_v1 (D1 EMA gate)
5. Backtest filtered vs baseline — report in `reports/`
6. If results positive: run adversarial review before promoting

---

## References

- Schwager, J. (1993) *Market Wizards* — trend filter consensus
- Elder, A. (1993) *Trading for a Living* — triple screen system (D1 filter, H4 trigger, M15 entry)
- Academic: Erb & Harvey (2006) gold as trend-following asset — strong trending characteristics confirmed

---

*Research by Claude Sonnet 4.6. Implement after PER-22 data import.*
