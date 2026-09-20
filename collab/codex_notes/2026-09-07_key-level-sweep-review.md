# Asia / London / US daily-level strategy review

Interpreting as: review the new key_level_sweep_v1 proposal and its daily brief
for logic, session handover and test readiness.

REVIEW_SOURCE: FALLBACK_REVIEW
Verdict: REVISE specification before implementation.
Scope: saved plan, build specification and first daily brief; no code executed
or changed, no trading jobs interrupted, no live price validation performed.

## Evidence

One dated levels JSON exists. Asia and London are present; US is absent.
The build specification explicitly defers implementation until ten briefs.
No key_level_sweep source or tests were found under src/ or tests/.

## Findings

1. HIGH — Look-ahead risk. The specification overwrites the daily levels with
   the latest session and loads them by bar date only. Historical morning bars
   could therefore receive afternoon information. Preserve immutable session
   snapshots with issued_at, data_as_of, valid_from, expires_at and revision.
   Load only a snapshot actually available at the decision time; use the next
   tradable bar for execution after confirmation.
2. HIGH — Conflicting filters. Gold's no-trade range overlaps its buy watch
   range. A buy must close above the buy range, yet many such closes are in the
   no-trade range and are rejected first. The same conflict affects sell
   rejections below the sell range. Specify whether the no-trade zone forbids
   all entries or permits a confirmed reclaim/rejection exception.
3. HIGH — BTC schema mismatch. The proposed buy logic requires
   asia_liquidity_low, which the BTC sample lacks. Targets and invalidation
   also need separate per-direction scenarios; top_scenario_targets cannot
   safely serve the opposite direction. Validate stop < entry < targets for
   buys and targets < entry < stop for sells.
4. MEDIUM — Confirmation mismatch. The brief uses 5-minute confirmation but
   the strategy uses M15 wicks. These are different rules. A wick restricted to
   remain inside the zone also excludes genuine excursions beyond it. Define
   the boundary, allowed overshoot and reclaim explicitly.
5. MEDIUM — Risk and fill ambiguity. Gold buys use an ATR-extended stop but
   separately invalidate at the Asia low. Define the effective exit, sizing,
   costs, gaps, same-bar stop/target ordering and repeat-entry prevention.
   Recalculate reward/risk from the executable entry: a gold sell at 4430 with
   stop 4470 and targets 4410/4390 is 0.5R/1R before costs, materially different
   from the zone-based headline ratios.
6. MEDIUM — Confidence is uncalibrated judgement. Do not treat the decimal
   scores as win probabilities or use 0.65 as a validated threshold. Compare
   a level-only baseline with the confidence-filtered variant prospectively.
7. MEDIUM — Ten briefs and five trades are development checks, not evidence
   of profitability. Track independent days, coverage, no-trade outcomes,
   realistic costs and held-out results; do not tune until five trades appear.
8. MEDIUM — Session timing and provenance. Distinguish the US data release
   window from the cash-equity open. Use America/New_York and Europe/London
   timezone conversions and market-specific holiday status. Store source URLs
   and observation times for macro values, including stale/missing markers.
9. LOW — The example JSON path in Context Files incorrectly adds src/tar_system
   before data/daily_briefs. Correct it before handing the spec to a builder.

## Recommended daily review

Asia: record the range and initial conditional scenarios.
London: record whether Asia's range held, broke or was swept, and update scenarios.
US: refresh available macro observations, explicitly retain/cancel/change each
scenario, and record an expiry. Missing US observations must not look confirmed.
Close: record what was knowable, which trigger occurred and the paper outcome.

Retain each snapshot; never replace historical inputs with later knowledge.
First revise the data and execution contract, then continue collecting briefs.
No strategy build or promotion has been approved by this review.
