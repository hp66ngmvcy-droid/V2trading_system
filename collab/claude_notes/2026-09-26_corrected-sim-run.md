# Corrected Sim Run — Steps 2a–2g Applied
**Date:** 2026-09-26
**From:** Claude
**Status:** REVISED — SELL fill fix + classifier fixes applied. Previous run STALE.

## CORRECTION 2026-09-26 (second pass)

Previous "Step 1 COMPLETE" run (earlier today) missed:
- SELL fill validity bug (lo > ezl → INVALID_FILL)
- Classifier: target-date eligibility, closed-bar check, MIN_BARS_COMPLETE=88
- issued_at gate (was counted but not excluded from completed)

All fixed. 9/9 fixtures PASS (incl. 3 new SELL fixtures).
Invariance test: CHECK 1 + CHECK 2 both PASS.
ISSUED_AT_UNKNOWN in current dataset: 0 (gate ready for future briefs).

## Current authoritative results (2026-09-26, all fixes 2a–2g applied)

### All R:R

| Group | N | WR | AvgR gross | AvgR net | TotalR |
|---|---|---|---|---|---|
| All (excl neutral) | 17 | 88.2% | +0.65R | +0.61R | +11.01R |
| **Anti-bias ★** | **9** | **100.0%** | **+0.72R** | **+0.66R** | **+6.48R** |
| With-bias | 8 | 75.0% | +0.57R | +0.55R | +4.53R |
| Neutral (informational) | 4 | 0.0% | -1.00R | -1.03R | -4.00R |

Anti-bias sub-split:

| Sub-group | N | WR | AvgR gross |
|---|---|---|---|
| Anti-bias + R:R ≥ 1.0 | 4 | 100% | +1.28R |
| Anti-bias + R:R < 1.0 | 5 | 100% | +0.27R |

## Delta from pre-bug numbers (cumulative, all fixes applied)

| Metric | Original claim | This run | Change |
|---|---|---|---|
| Anti-bias N | 10 | 9 | −1 (SELL INVALID_FILL) |
| Anti-bias WR | 100% | 100% | Unchanged |
| Anti-bias AvgR gross | +0.71R | +0.72R | +0.01R |
| With-bias N | 16→14 | 8 | −6 (SELL INVALID_FILL) |
| INVALID_FILL total | 0→2 | 9 | SELL fix reclassed 7 more |
| ISSUED_AT_UNKNOWN | reported not gated | gated (0 in current data) | Gate live |

SELL fill fix: 9 INVALID_FILL trades total (7 SELL + 2 BUY). Most are WITH-BIAS SELL
entries where the entry bar's low > sell_zone_low (bar never traded at fill price). One
anti-bias SELL (Sep-17 BTCUSD) also INVALID.

Note: Sep-24 BTCUSD SELL (WITH-BIAS, previously TP_T1 +1.38R) is now INVALID_FILL —
SELL fix reclassified a former winner. With-bias numbers not directly comparable to
pre-fix runs.

## Coverage

- Briefs: Sep 7–29 (16 files)
- Sep 25: Options expiry — NEUTRAL bias, 4 NEUTRAL completions WR=0%
- Sep 28–29: NEUTRAL bias or NO_ENTRY — no completions yet
- OPEN_EOD: 1 (BTCUSD SELL Sep-12)
- INVALID_FILL: 9 (7 SELL entries, 2 BUY entries)

## Status

Steps 2a–2g complete. Remaining before four-arm comparison:
- Step 3: `day_review.py` blind labelling mode
- Step 4: Run corrected four-arm comparison after Step 3
