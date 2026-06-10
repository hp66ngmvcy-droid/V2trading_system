---
type: "optimiser"
strategy: "vol_filtered_momentum_v1"
asset: "XAUUSD"
timeframe: "M15"
score: 22.0
decision: "REDUCE_RISK"
tags: ["#type/optimiser", "#decision/reduce_risk", "#risk/reduce"]
---

# Optimiser vol_filtered_momentum_v1 XAUUSD M15

- Strategy note: [[vol_filtered_momentum_v1_XAUUSD_M15]]
- GO / NO-GO: NO_GO
- Risk adjustment: REDUCE_RISK
- Positioning context: NEUTRAL score=0.0

## Improvement Plan
- Reduce position size, add a volatility cap, and widen the validation window.
- Review timeframe selection or loosen the entry filter slightly.
- Reduce optimisation range or simplify the strategy parameters.
