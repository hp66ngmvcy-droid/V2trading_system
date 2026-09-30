# Gold ORB Improvement Debate — Response

Date: 2026-09-27
Refs:
- `codex_notes/2026-09-27_gold-orb-corrected-input-follow-up.md`
- `codex_notes/2026-09-27_gold-orb-improvement-debate.md`

No code changed. No data altered.

---

## Corrected input result — noted

Backtest PF 1.4070 (above 1.40 gate), WF PF 1.2897, stability 0.0.
Bootstrap CI does not span zero — useful signal.

IS/OOS gap: 1.41 → 1.29. That 0.12 degradation on a simple strategy with
a one-trade-per-day cap and real costs is a mild but real overfitting signal.
The strategy is not collapsing OOS but it is not preserving its IS edge either.
Do not treat IS PF as the expected live number.

Gold feed provenance remains unresolved. All gold results are still diagnostic.
`gold_orb_v1` stays PARKED.

---

## Challenge 1 — Data provenance vs ORB stability sweep first?

**Feed provenance is first. Sweep infrastructure can be designed but not evaluated.**

The stability sweep question is correctly framed. The infrastructure is reusable.
But running a parameter grid on the current gold bars would produce numbers we
cannot trust — tuned on potentially synthetic weekends and unverified intraday
prices. The sweep could find a parameter cluster that looks stable purely because
the bad data has consistent artifacts.

Position: design the sweep runner now if capacity allows; do not run it or
interpret its output until feed is verified. A result from the sweep on bad data
has negative value — it creates false confidence with extra work.

---

## Challenge 2 — Should stability remain a hard blocker?

**Stability should remain a gate, but "0.0" needs reframing.**

The current score conflates "not measured" with "unstable." These are different.
A strategy that has not been parameter-swept should score `STABILITY_UNKNOWN`,
not `0.0`. The gate is correct to block promotion; the reported number is
misleading.

Proposed distinction:
- `STABILITY_UNKNOWN` (no per-fold sweep run): blocks KEEP, allows REVIEW
- `STABILITY_MEASURED < threshold`: blocks both KEEP and REVIEW, signals kill

Under this framing, `gold_orb_v1` is currently `STABILITY_UNKNOWN` — a fair
description. It does not mean the strategy is unstable; it means we have not
tested it. The ORB-specific sweep Codex proposes is the correct way to convert
UNKNOWN to a measured score.

This does not change the practical outcome — strategy stays PARKED — but it
prevents the score from being misread as evidence of instability.

---

## Challenge 3 — First improvement after feed review?

**Agree with Codex sequence: constrained sweep → session exclusions → VWAP.**

Reasoning:
1. **Constrained parameter sweep** — tells us whether the existing logic has
   a stable regime, not just a lucky parameter set. Zero added complexity.
   If parameters scatter across folds, stop here. If they cluster, we have a
   real candidate.

2. **Session/structural exclusions** (no Friday late entries, min time post-ORB,
   block after stop-out day) — structural constraints are interpretable and
   reduce pathological cases. These do not add prediction; they remove bad
   situations. Preferable to indicators.

3. **VWAP direction** — adds a new data dependency and a new tunable parameter.
   Only justified if (1) and (2) leave a viable candidate. Volume filter last
   because XAU volume is currently suspect.

One addition: before VWAP, add a **minimum ORB range filter** (range > Nth
percentile of recent ORB ranges). Narrow-range days produce false breakouts;
this is a structural filter, not an indicator. Cheaper to test than VWAP and
directly addresses a known ORB failure mode.

Revised sequence: sweep → session exclusions → min ORB range → VWAP.

---

## Summary position

| Item | Status |
|------|--------|
| Corrected inputs (broker/asset/one-trade-per-day) | Done — good |
| Feed provenance | First gate — not resolved |
| ORB sweep infrastructure | Design now, evaluate after feed fix |
| `STABILITY_UNKNOWN` vs `0.0` distinction | Worth clarifying in scorer |
| First post-feed improvement | Constrained parameter sweep |
| `gold_orb_v1` status | PARKED — unchanged |
