# Pre-Registration: ARSB v1 Plateau Sweep

Date: 2026-07-06
Status: PRE-REGISTERED — do not run backtest before this file is committed

## Hypothesis

ARSB v1 on XAUUSD M15 has genuine edge but compression_atr_mult and buffer_mult
show param_stability=0.0 across walk-forward splits. Before constraining bounds,
we must verify whether the objective function is flat (genuine edge, any value works)
or sharp-peaked (overfit, one value works by luck).

## Sweep Specification

- Parameter 1: compression_atr_mult — range 8 to 25, step 1
- Parameter 2: buffer_mult — range 0.05 to 0.30, step 0.05
- All other params: locked to current tuned config (XAUUSD_M15_arsb_v1.json)
- Symbol/timeframe: XAUUSD M15
- Evaluation: in-sample score only at this stage; OOS/WF in follow-up

## Pre-Registered Pass Criteria (all must hold)

1. bootstrap CI lower bound > 0 at 95% confidence
2. Walk-forward param_stability >= 0.50
3. Minimum 30 trades in evaluation window
4. Result candidate must pass these gates BEFORE any bounds narrowing is considered

## Interpretation Rules (pre-registered)

- Flat plateau (score variance < 5 points across ≥50% of grid): bounds-narrowing
  defensible, proceed to WF retest with narrowed range.
- Sharp peak (score >5 points above median in <20% of cells): KILL — do not retune.
- Partial (mixed): one narrow retest allowed, new hypothesis required.

## Family-wise Budget

N = 1 for this family (no prior variants of this specific sweep).
Bonferroni threshold not applicable to single test; CI gate substitutes.

## Blocked Until

This file committed. Backtest artifact timestamp must be after this file's commit timestamp.
