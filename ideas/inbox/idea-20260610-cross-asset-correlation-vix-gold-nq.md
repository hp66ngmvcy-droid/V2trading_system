---
idea_id: idea-20260610-cross-asset-correlation-vix-gold-nq
title: Cross-Asset Correlation Model — VIX/Gold/NQ Downturn Alpha
status: hypothesis_extracted
source_url: manual
source_label: User idea — 2026-06-10
category: strategy_idea
tags: ["cross-asset", "correlation", "gold", "vix", "NQ", "statistical", "regime"]
created_from: manual_entry
created_at: 2026-06-10T22:00:00+00:00
---

# Cross-Asset Correlation Model — VIX/Gold/NQ Downturn Alpha

## Hypothesis

Statistical correlation between VIX, Gold (XAUUSD), and NQ (Nasdaq futures) provides
a non-price-action signal for capturing alpha during market downturns.

When VIX spikes and NQ sells off, Gold historically diverges positively (flight-to-safety).
The correlation breakdown between NQ and Gold during high-VIX regimes is the tradeable signal.

## Rules (to be defined)

- **Entry:** Statistical regime shift detected — rolling correlation between Gold and NQ
  crosses below threshold AND VIX exceeds regime threshold
- **Exit:** Correlation reverts to baseline OR VIX normalises
- **Filters:** No price action, no ICT, no ORB — pure statistical signal only
- **Direction:** Long Gold / Short NQ on downturn signal (or Gold-only if multi-asset not ready)
- **Risk:** Fixed ATR-based SL, no pyramiding

## Statistical Approach

- Rolling 20/60 bar correlation: Gold vs NQ
- VIX z-score as regime gate (not raw level)
- Signal: correlation < -0.3 AND VIX z-score > 1.5 → entry
- No curve-fitting on correlation window — validate on OOS only

## Data Requirements

- XAUUSD (already have)
- NQ continuous futures or NQ proxy (need to check)
- VIX index data (need to check — may need proxy)

## Success Criteria

- Stage 1 costed PF > 1.2
- Sharpe > 1.5 OOS
- Trades >= 30 (avoid lucky-winner gate)
- Walk-forward KEEP verdict

## Notes

- High-conviction idea — correlation between these assets is well-documented academically
- Downturn focus means low trade frequency but high per-trade quality
- Check `ideas/data_requirements/` for VIX and NQ data availability before backtesting
- Do NOT promote on < 30 trades — min trade gate is hard
