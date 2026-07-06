---
type: "optimiser"
strategy: "rsi_reversion_v1"
asset: "XAUUSD"
timeframe: "M15"
score: 0.0
decision: "REDUCE_RISK"
tags: ["#type/optimiser", "#decision/reduce_risk", "#risk/reduce"]
---

# Optimiser rsi_reversion_v1 XAUUSD M15

- Strategy note: [[rsi_reversion_v1_XAUUSD_M15]]
- GO / NO-GO: NO_GO
- Risk adjustment: REDUCE_RISK
- Positioning context: NEUTRAL score=0.0

## Improvement Plan
- Reduce position size, add a volatility cap, and widen the validation window.
- KILL or RETEST with simpler parameters because walk-forward is weak.
- Reduce optimisation range or simplify the strategy parameters.
- Pivot required: TAIL_RISK. Recommended action: ASSUMPTION_INVERSION.
