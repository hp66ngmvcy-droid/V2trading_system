---
id: RESEARCH-RSI35-001
type: research_candidate
status: ACTIVE
entity: rsi_trend_v4_35_65_atr3
logged: 2026-09-08
---

# rsi_trend_v4 — RSI 35/65 ATR 3.0 RR 2.0 — Research Candidate

## Parameters

| Param | Value |
|-------|-------|
| rsi_buy_level | 35 |
| rsi_sell_level | 65 |
| atr_multiplier | 3.0 |
| reward_risk | 2.0 |
| ema_cross_gate | True |
| liquid_sessions_only | True |

## Backtest Results (XAUUSD M15, full dataset 103,053 bars)

| Metric | Value |
|--------|-------|
| Trades | 91 |
| Win rate | 45% |
| Profit factor | 1.921 |
| Score | 82.87 (REVIEW) |

## Why REVIEW not KEEP

Bootstrap CI gate correctly blocked promotion. With IS=10000/OOS=2000/splits=5,
only 5 OOS trades accumulated. A 95% bootstrap CI with n=5 always spans zero
regardless of PF — insufficient statistical evidence, not a strategy failure.

Gate changes made during this investigation:
- Fixed stability gate bug: fixed-param strategies now return 100.0 (was 0.0).
  Commit: 6d60ee9. 405/405 tests pass. Adversarial review: no HIGH/CRITICAL.

Bootstrap CI gate was NOT changed — it is working correctly.

## Promotion Path

Paper collect 50+ real trades on XAUUSD M15 paper mode.
When 50 trades accumulated: re-run score_strategy with paper data as stitched_metrics.
If CI clears and PF ≥ 1.10 OOS: run full promotion gate check.

Do NOT promote to KEEP from backtest alone — bootstrap CI gate exists for this reason.

## Context

Discovered during big sweep (2026-09-08). ATR 3.0 is the key lever —
previous sweeps used ATR ≤ 2.75 which clipped stops on normal volatility,
reducing win rate to 27-29%. ATR 3.0 lifts win rate to 45%, PF to 1.92.

Existing ACTIVE strategies for comparison:
- atr_breakout_v3: PF 1.49, 153 trades — has sufficient OOS density
- ema_volume_fixed: PF 1.45, 689 trades — high frequency, clears all gates
