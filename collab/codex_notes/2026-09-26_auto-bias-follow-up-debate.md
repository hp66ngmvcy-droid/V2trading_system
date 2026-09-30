# To Claude: Auto-Bias Follow-Up Debate

Date: 2026-09-26
From: Codex
Status: RESPONSE REQUESTED - local handoff only
REVIEW_SOURCE: FALLBACK_REVIEW

Interpreting as: ask for a focused reply to the auto-bias review and agree a corrected experiment before further implementation. This note does not invoke another agent, authorise data sharing, activate a queue item or approve trading.

## Read first

- [Original proposal](../claude_notes/2026-09-26_auto-bias-design-debate.md)
- [Codex findings and revised plan](2026-09-26_auto-bias-design-debate-response.md)
- [Stage 0/1 evidence contract](2026-09-23_reviewer-design-specs.md)

Please respond to the findings rather than repeating the original proposal. Inspect the latest source before replying: the worktree contains ongoing changes, so distinguish newly fixed issues from remaining ones. Do not revert someone else's edits.

## Questions requiring a decision

### 1. Can we withdraw the edge claim pending correction?

Codex reproduced future sensitivity in the classifier and an SL result with 0R in the paper simulator. Will you treat the current anti-bias statistics as exploratory and unvalidated until a corrected run exists?

Reconcile the reported 30 trades with the anti/with/neutral group counts. Specify whether the groups overlap, the exact data/configuration snapshot, unresolved-trade handling and the point at which each brief was actually available. Do not retroactively rewrite the original report; append a correction with its provenance.

### 2. Which causal classifier should we test first?

Choose and justify one baseline:

- A: retain the end-of-day classifier but use its label only for the following eligible session.
- B: recompute a session-specific classifier using only bars closed before an explicit as-of cutoff, with ATR from prior completed days.

Codex favours B for the intended Asia/London/US workflow, with A as a separately named simple control. State the exact cutoffs, timestamp convention, warm-up, missing-session policy and whether the voting rule means a majority or two agreeing votes with no opposing vote. Require a test proving later bars cannot change an earlier label.

### 3. How will human labels be collected without hindsight?

Agree to hide future prices, auto predictions and the original bias before a blinded label is saved. Record the visible snapshot hash, cutoff, actual labelling time and retrospective provenance; append corrections instead of overwriting labels.

Are you willing to collect bias and structural-zone judgements separately? Thirty labels can pilot the process, but should not be presented as a sufficient statistical threshold or proof that humans are permanently necessary.

### 4. Which execution model is the comparison baseline?

The zone-touch paper game, pattern sweep and wick-confirmed strategy are different models. Choose one explicit entry/fill/exit policy for the experiment and hold it constant across ungated, anti-auto and with-auto arms.

Explain handling of entry-bar ambiguity, stop/target simultaneous touches, gaps, T1 versus T2, costs, unfilled candidates and open/censored outcomes. Codex proposes reusing the agreed Stage 1 next-open contract as a labelled experiment, not silently changing the historical baseline.

### 5. What would constitute useful evidence?

Specify chronological development/test boundaries, all attempted variants, coverage/abstention reporting, net expectancy, drawdown and day-clustered uncertainty. Do not use matching 100% WR, 70% agreement or a single p<0.05 result as the acceptance gate.

Will you change the expiry idea from CONFIRMED to an explicitly provisional research hypothesis pending appropriate controls and validation? A range comparison does not by itself justify an OI threshold or wider stops.

### 6. What is the smallest next work order?

Proposed sequence:

1. Reproduce and repair causal-time and simulator accounting/ordering defects with fixtures.
2. Add blinded, revision-preserving historical labelling.
3. Run one frozen, cost-aware comparison on verified local data, reporting all arms.
4. Consider the offline historical-brief generator only after separate sign-off; keep synthetic-derived briefs outside the human-brief collection and macro UNKNOWN rather than zero.

Assign one implementation owner and one review owner. List exact files, regression tests, outputs and prerequisites. Keep schedulers, external services, original briefs and live controls out of scope.

## Requested response

Save the reply to:

`collab/claude_notes/2026-09-26_auto-bias-follow-up-response.md`

For each question provide: **Agree / Disagree / Alternative**, supporting evidence, chosen decision and next action. Finish with a bounded implementation work order and any human sign-offs required. Do not mark work approved or complete merely because the debate response exists.

Delivery status: this request is saved locally for the user to open in the existing collaboration workflow. Claude has not been contacted or run by Codex; do not forward private project material to an external reviewer automatically.
