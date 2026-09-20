# Asia–London–US: 10–20 day strategy learning cycle

Interpreting as: record the user's idea to learn from daily session outcomes
over a 10–20 day window, develop new hypotheses, and gradually refine a strategy
together.

Status: IDEA_RECORDED — proposed research workflow.
Scope: paper research for gold and Bitcoin; documentation only.

## Core idea

The daily brief should be both a forward-looking market review and a record
that helps us learn. Compare what Asia suggested, how London responded, what
changed into the US session, and what actually happened afterwards. Over
10–20 trading days, look for repeated relationships, failures and exceptions.
Use that evidence to propose a small improvement or a new strategy idea, then
test it on subsequent days and refine it gradually with the user and agents.

The aim is to discover which parts of the review add useful information,
including when waiting is the better decision. key_level_sweep_v1 is one
candidate emerging from this process, rather than the only possible outcome.

## Daily record

Preserve each session snapshot with its issue time, observation time, data
sources, levels, conditional scenarios, confirmation rules and expiry. Later
updates must not replace what was known earlier.

For each scenario record:

- What was expected, and what would confirm or invalidate it.
- Whether the level was reached and the trigger actually completed.
- What London changed about the Asian picture, and what the US session changed
  about London's picture.
- Any relevant scheduled event, volatility change or missing/stale observation.
- The hypothetical entry after confirmation, stop, targets, expiry and assumed
  spread/slippage, defined before judging the outcome.
- The observed outcome: target, stop, expired, cancelled, no trigger or unknown.
- Net result in R where a valid paper trade exists, maximum favourable/adverse
  movement, and whether a losing or missed setup suggests a testable question.

Keep all scenarios, losses and no-trade days. Missing observations remain
unknown rather than being counted as successful avoidance. Keep gold and
Bitcoin results separate; record Bitcoin weekends separately from the shared
weekday session comparison.

## Review window and gradual refinement

1. Days 1–10: collect a consistent baseline. Review data quality daily, but keep
   candidate trading rules fixed so outcomes can be compared fairly.
2. Around day 10: examine the evidence together. Identify a small number of
   repeated behaviours and choose at most one rule change for the next trial.
   If coverage or observations are too sparse, continue collecting to day 20.
3. Freeze the revised candidate and its expected benefit before the next
   observation window. Run it alongside the unchanged baseline on subsequent
   days where practical, using the same cost assumptions.
4. Around day 20, or after the next complete window: compare baseline and
   candidate. Keep, revise, discard or continue observing, with written reasons.
5. Repeat in 10–20 day windows. Each revision has a version, rationale, start
   date, evaluation criteria and a record of all earlier variants tried.

If the first 20 days were used to invent a change, those same days cannot be
its independent validation. A rolling dashboard is useful for monitoring, but
overlapping windows do not count as fresh independent evidence.

## Questions that could generate new ideas

- Does a London sweep and reclaim of Asia's range tend to continue into the US
  session, or reverse under particular observed conditions?
- Does waiting for the US data release improve entry quality enough to offset
  missed moves and a less favourable entry price?
- Does London follow-through carry more information than the initial Asian bias?
- Do no-trade zones prevent losses, or block otherwise valid confirmations?
- Does macro context improve a simple level-and-price-action baseline?
- Do gold and Bitcoin need different confirmation and expiry rules?

These are hypotheses to investigate, not established market relationships.

## How to judge a candidate

Compare trade count, independent days, coverage, average net R, losses and
drawdown, missed opportunities, and results with/without the proposed change.
Include a simple baseline and the option of making no change. Do not optimise
only for win rate or use judgement-confidence scores as measured probabilities.

Ten to twenty days is a learning cadence, not proof of a durable trading edge.
Collect more evidence when the sample is sparse or dominated by one unusual day.
Correct implementation/data errors separately from strategy tweaks and identify
which historical results need to be invalidated or recomputed.

## Relationship to the existing build plan

Clarifies the earlier ten-brief trigger: ten saved files should trigger a
learning review, not an automatic strategy build. The existing specification's
timestamp, overlapping-zone, instrument-schema and execution ambiguities still
need resolution. A concrete candidate can be proposed after the learning review
with explicit rules and a test plan.

Next collaboration step: Claude and Codex review this workflow, agree a compact
daily outcome template, then use completed observations to propose the first
small experiment. No scheduler, strategy implementation or trading action is
created by this note.

## Claude review outcome — 2026-09-08

Claude returned `KEEP`. The response passed the inbound provenance guard with
all six required sections and three topic anchors. Response SHA-256:
`2be3e732db8a1f071e281a9daecaa941f0a3814f1efb99db1bc90d20215226ea`.

Accepted additions:

- Before each session, commit to one sentence describing the scenario and its
  confirmation, invalidation and expiry.
- Assign `clean`, `noisy` or `data-absent` at observation time, before the
  result is known.
- Record time from the session start to confirmation, confirmation to paper
  entry, and entry to the first target or expiry.
- Separate measurable facts, execution assumptions and interpretation in the
  outcome record.
- Record why no scenario or trigger occurred so coverage is not overstated.
- At day 10, treat fewer than three independent trigger days for the primary
  question as sparse and continue observing. Propose no more than one change.
- Evaluate a frozen change against the unchanged baseline at day 20 using new
  observations. Extend the window when results remain sparse or ambiguous.

First observational experiment: for gold, record whether London sweeps the
Asian high or low before the London close, then whether the US session extends
beyond the swept side, reverses away from it, or remains unresolved. Define
the measurement before the first observation and retain every day, including
no-sweep and missing-data days. This is pattern collection, not a trade rule.

Claude's full response is saved at
`../claude_notes/2026-09-08_three-session-learning-cycle-review.md`.
