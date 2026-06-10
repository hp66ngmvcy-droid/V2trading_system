---
type: "optimiser"
strategy: "rsi_trend_v4"
asset: "EURUSD"
timeframe: "M15"
score: 16.0
decision: "REDUCE_RISK"
tags: ["#type/optimiser", "#decision/reduce_risk", "#risk/reduce"]
---

# Optimiser rsi_trend_v4 EURUSD M15

- Strategy note: [[rsi_trend_v4_EURUSD_M15]]
- GO / NO-GO: NO_GO
- Risk adjustment: REDUCE_RISK
- Positioning context: NEUTRAL score=0.0

## Improvement Plan
- Reduce position size, add a volatility cap, and widen the validation window.
- Review timeframe selection or loosen the entry filter slightly.
- KILL or RETEST with simpler parameters because walk-forward is weak.
- Reduce optimisation range or simplify the strategy parameters.
