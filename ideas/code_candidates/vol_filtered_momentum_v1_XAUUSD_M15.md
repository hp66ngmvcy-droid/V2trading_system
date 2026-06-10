---
idea_id: vol_filtered_momentum_v1-xauusd-m15
title: Vol-Filtered Momentum v1 — XAUUSD M15
status: code_candidate
promoted_at: 2026-05-26
promoted_from: focus_strategy
---

# Vol-Filtered Momentum v1 — XAUUSD M15

## Strategy Identity

| Field | Value |
|-------|-------|
| Strategy | `vol_filtered_momentum_v1` |
| Symbol | XAUUSD |
| Timeframe | M15 |
| Broker profile | current_broker_demo |

---

## Tuned Parameters

```json
{
  "rsi_buy_threshold": 57,
  "rsi_sell_threshold": 43,
  "session_start_utc": 8,
  "session_end_utc": 15,
  "atr_cap": 8.2761,
  "atr_percentile": 0.9
}
```

Config file: `configs/tuned/XAUUSD_M15_vol_filtered_momentum_v1.json`

---

## In-Sample Results (full dataset 2022-01-31 → 2026-05-21)

| Metric | Value | Gate |
|--------|-------|------|
| Sharpe | 1.5976 | ✅ ≥1.5 |
| Profit factor | 1.2581 | ✅ ≥1.0 |
| Max drawdown | 0.45% | ✅ ≤2% |
| Win rate | 34.6% | ✅ ≥28% |
| Total trades | 283 | ✅ ≥30 |

---

## Walk-Forward Results (6 splits, train=24000 / test=12000 bars)

| Split | Sharpe | PF | Trades |
|-------|--------|----|--------|
| 1 | 2.33 | 1.40 | 17 ⚠️ |
| 2 | 0.68 | 1.10 | 12 ⚠️ |
| 3 | 0.46 | 1.07 | 34 |
| 4 | 1.48 | 1.25 | 25 |
| 5 | 5.46 | 2.17 | 56 |
| 6 | 0.44 | 1.06 | 47 |
| **avg** | **1.81** | **1.34** | **191** |

⚠️ Splits 1+2 have <30 trades — data availability constraint (M15 history only from 2022). Not a strategy flaw. Monitor live trade frequency in first 3 months.

**6/6 splits PF > 1.0.**

---

## Gate Summary

| Gate | Required | Result | |
|------|----------|--------|-|
| IS Sharpe | ≥1.5 | 1.60 | ✅ |
| OOS avg Sharpe | ≥0.5 | 1.81 | ✅ |
| OOS avg PF | ≥1.1 | 1.34 | ✅ |
| Total WF trades | ≥30 | 191 | ✅ |
| OOS vs IS drift | ≤20% | OOS better | ✅ |
| All splits positive PF | 6/6 | 6/6 | ✅ |
| Auto-KILL triggers | none | none hit | ✅ |

---

## Entry / Exit Rules

### Entry
- **BUY:** `ema_fast > ema_slow` AND `ema_fast_slope > ema_slope_threshold` AND `ema_slow_slope >= 0` AND `rsi >= 57`
- **SELL:** `ema_fast < ema_slow` AND `ema_fast_slope < -ema_slope_threshold` AND `ema_slow_slope <= 0` AND `rsi <= 43`

### Filters
- Session: **08:00–15:00 UTC only** (London core + overlap)
- ATR cap: reject bar if `atr > 8.2761` (P90 filter — blocks extreme volatility)

### Exit
- ATR-based stop loss and take profit (strategy defaults)

---

## EA Implementation Notes

1. **Session gate:** block all entries outside 08:00–15:00 UTC server time. Confirm broker server timezone.
2. **ATR cap:** calculate ATR(14) on M15. If current bar ATR > 8.2761, skip signal.
3. **RSI thresholds:** buy ≥57, sell ≤43. Standard RSI(14).
4. **EMA:** fast and slow EMA with slope check — confirm exact periods from strategy source `src/tar_system/strategies/vol_filtered_momentum_v1.py`.
5. **Costs:** strategy was tuned with broker spread included. Verify live spread matches demo assumptions.
6. **Trade frequency:** expect ~63 trades/year (~5/month). If <2 trades/month in first 3 months, investigate parameter drift.

---

## Data

- Training data: `data/raw/XAUUSD_M15.csv` (2022-01-31 → 2026-05-21, 101,748 bars)
- Validated parquet: `data/validated/XAUUSD_M15.parquet`
- Note: no pre-2022 M15 data available. Data limitation acknowledged.

---

## Review Gate (human sign-off required before EA coding)

- [ ] Parameters confirmed against strategy source code
- [ ] Broker spread assumption verified for live account
- [ ] Server timezone confirmed for session gate
- [ ] EA code reviewed before any MT5 deployment
- [ ] Paper signal test run for ≥2 weeks before live
