# KILL Note — arsb_v1
Date: 2026-08-15
Author: Claude (post-PER-28 verdict)
Status: KILLED

## Strategy
Asian Range Session Breakout — XAUUSD M15.
File: `src/tar_system/strategies/arsb_v1.py`

## Evidence trail
| Date | Result | State |
|------|--------|-------|
| 2026-07-05 | Bug fixed | PENDING retest |
| 2026-07-31 | WF PF=0.36, param stability=0.0, CI spans zero | PARKED |
| 2026-08-02 | PER-28 D1 EMA filter implemented; WF PF=0.05 | KILL gate triggered |

## Kill gate met
Gate was explicit: "if WF PF doesn't improve above 0.5 with D1 filter → KILL arsb_v1 entirely."
PF went from 0.36 → 0.05 with filter. Filter made it worse, not better.
Root cause was not counter-trend entries. Strategy has no recoverable edge on current 2-month dataset.

## Hard rules going forward
- Do not retune arsb_v1
- Do not retest unless: (a) 6+ months of M15 data available AND (b) new structural hypothesis
- Strategy file kept at `src/tar_system/strategies/arsb_v1.py` — code reference only
- Do not remove from REGISTRY (avoids breakage); mark as RESEARCH_REGISTRY only if needed

## What was learned
- Asian range compression breakout fires too many counter-trend entries in a trending Gold regime
- D1 EMA alignment gate suppressed valid signals as much as bad ones — not a surgical fix
- Plateau sweep: FLAT — no compression_atr_mult × buffer_mult combo rescues PF
- 2-month data window insufficient for statistical confidence regardless of strategy
