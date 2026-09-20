# Agent Memory — arsb_v1 KILLED
Date parked: 2026-07-31
Date killed: 2026-08-15
Status: KILLED — D1 filter made WF PF worse (0.36 → 0.05)
Strategy: arsb_v1 — Asian Range Session Breakout

## Evidence trail
- WF PF=0.36, param stability=0.0, CI spans zero (2026-07-31)
- D1 EMA alignment filter implemented (PER-28, 2026-08-02)
- WF PF with filter = 0.05 — kill gate triggered

## Kill gate
"If WF PF doesn't improve above 0.5 with D1 filter → KILL arsb_v1 entirely." Gate met.

## What failed
Asian range compression breakout has no recoverable edge in current Gold trending regime.
D1 filter suppressed valid signals as much as bad ones — not a surgical fix.
Plateau sweep: FLAT — no param combo rescues PF.

## Hard rules
- Do not retune
- Do not retest without 6+ months M15 data AND new structural hypothesis
- Strategy file at `src/tar_system/strategies/arsb_v1.py` — keep, do not modify
- Kill note: `collab/codex_notes/2026-08-15_arsb_v1_killed.md`
