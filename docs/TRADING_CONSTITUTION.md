# Trading Constitution

Purpose: binding principles for all V2 TAR paper-only strategy research; any violation blocks promotion.

1. No gate-gaming: strategies must not be tuned against the scoring gates themselves, including by narrowing sweep bounds after seeing results.
   Test: rerun scoring with gate thresholds perturbed ±20%; verdict must not flip. Sweep bounds may only widen, never narrow, without a new pre-registered hypothesis.

2. Minimum trade count: no KEEP verdict below 30 trades in the evaluation window.
   Test: trade count in the report is ≥30; otherwise verdict is auto-INSUFFICIENT.

3. Pre-registration: hypothesis, parameters, and success criteria are written to ideas/ before any backtest runs.
   Test: idea file commit timestamp precedes the first backtest artifact timestamp.

4. No post-hoc parameter search: parameters may not be changed after seeing out-of-sample results.
   Test: config file hash at OOS run matches the pre-registered config hash.

5. Report negatives: every KILL and failed variant is logged with the same detail as winners.
   Test: research notes contain one entry per registered idea, including all failures.

6. Statistical power: results must clear bootstrap confidence intervals, not point estimates.
   Test: bootstrap CI lower bound on the key metric excludes zero at 95%.

7. No overfit compounding: each derived variant counts against a family-wise trial budget; declare N before the family starts.
   Test: N declared in pre-registration note; reported thresholds adjusted for that N (e.g. Bonferroni or stated equivalent).

8. Regime coverage: evaluation window must span at least two distinct detected regimes.
   Test: regime detector output shows ≥2 regimes each covering ≥20% of the window.

9. Cost modelling: all backtests include spread, commission, and slippage assumptions.
   Test: report lists cost parameters, and zero-cost runs are labelled DIAGNOSTIC only.

10. Promotion gates: paper→next-stage moves require every gate green plus human sign-off.
    Test: promotion record shows all gate results and an explicit human approval entry.

11. Parameter stability floor: walk-forward parameter stability must reach ≥0.50 for REVIEW, ≥0.70 for KEEP.
    Test: scorer reports param_stability ≥ threshold; strategies below 0.50 are auto-INSUFFICIENT regardless of other metrics.
