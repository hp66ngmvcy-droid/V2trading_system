REVIEW_SOURCE: CLAUDE_REVIEW
APPROVAL_ID: user-request-20260907-session-learning-review
CLASSIFICATION: PUBLIC_TECHNICAL_ONLY

1. Verdict

KEEP. The learning cycle is structurally sound for its stated purpose, which is disciplined pattern discovery rather than edge proof. Immutable snapshots, mandatory retention of losing and no-trigger days, explicit separation of hypothesis from established relationship, and the freeze-before-test rule all address the most common early-stage research failures. The 10-to-20-day window is honestly labelled as a cadence, not evidence. The six open questions are appropriately framed as unknowns. No material revision is needed before starting collection.

2. Additions

First, add a pre-session commitment step. Before each session opens, write the scenario in one sentence and state what price action would confirm or invalidate it. This prevents post-hoc rationalisation and strengthens the immutable snapshot discipline.

Second, add a brief session-quality tag to every record. Rate each observation window as clean, noisy, or data-absent. This lets you filter baseline comparison results by condition without changing the underlying rules, which keeps analysis honest.

Third, track time-to-trigger alongside net R. Many structural questions in this methodology, particularly around London sweeps carrying into the US session, depend on timing as much as direction. Recording minutes from confirmation to entry and from entry to first target separates fast-resolution setups from slow ones without adding a new rule change.

3. Pitfalls

Look-ahead leakage is the primary risk. When reviewing day-10 behaviour to propose a change, it is easy to select a rule that fits the same ten days used to motivate it. The fix already present in the methodology, freezing the candidate and testing on subsequent days alongside the unchanged baseline, must be applied without exception. Any softening of that rule invalidates the comparison.

Overlapping-window inflation is identified in the methodology but bears emphasis. If you observe days 1-20, then days 11-30, those windows share ten days. Treat each shared day as counted once, not twice, when assessing independent evidence.

Confirmation bias in session-quality tagging is possible if tags are assigned retrospectively after the outcome is known. Assign the quality tag at observation time, not at review time.

Small-sample judgement drift is subtle. After ten days, a two-trade sample with one winner looks like 50 percent. Resist converting ratios into probabilities. The methodology correctly uses the phrase learning cadence rather than proof, and that framing must be actively maintained in written reviews, not only in the rules.

Instrument conflation is a risk if Gold and Bitcoin records are informally compared before each instrument has its own stable baseline. Keep the two series fully separate until day 20 at the earliest.

4. Daily Template

Date and session covered.
Scenario written before session open, one sentence.
Confirmation level, invalidation level, expiry time. All fixed before open.
Sources referenced, noted at observation time.
Trigger reached: yes or no.
If yes: entry price, stop, target, spread and slippage estimate, net R, maximum favourable excursion, maximum adverse excursion.
If no: reason, classify as no-setup, no-trigger, or missing observation.
Session quality tag assigned before outcome is known: clean, noisy, or data-absent.
Fact section ends here.
Judgement section: one or two sentences on what the session suggests, clearly labelled as interpretation, not data.

5. Day 10 and Day 20 Template

At day 10, count total sessions recorded, sessions with usable observations, sessions with a trigger, net R sum, and number of no-trigger days retained. State whether each of the six open questions has enough observations to form even a provisional view. If any question has fewer than three independent trigger days, mark it sparse and continue collection to day 20 without change. If coverage is adequate, propose at most one rule change, state the exact rationale, write the frozen candidate definition, and record the start date for parallel tracking. Continue the unchanged baseline alongside the candidate. Do not test more than one change simultaneously.

At day 20, perform baseline comparison on candidate versus unchanged baseline using the same metrics: coverage, independent trigger days, average net R, drawdown, and missed opportunities. If the candidate shows a clear directional difference, retain it and restart the cycle with that version as the new baseline. If results are ambiguous, extend collection by ten days and revisit. If the candidate underperforms, revert and record the full rationale. Every version, every decision, and every evaluation criterion must remain in the log permanently.

Rules for continuing observation: continue without change whenever the trigger count for the primary question is below three, whenever session quality is predominantly noisy, or whenever a data or implementation correction is still being resolved. Corrections are tracked separately from rule changes and never count as a review cycle.

6. Deferred Work and First Experiment

Defer live sizing, instrument correlation analysis, macro overlay integration, and any comparison across overlapping windows until at least two full 20-day cycles are complete on separate instruments. Weekend Bitcoin records should be collected but not analysed until weekday baseline comparison is stable. Cross-instrument rule sharing should remain deferred indefinitely until each instrument has demonstrated independent baseline behaviour.

The first paper experiment is this: for ten consecutive trading days, record whether the London session sweeps the prior Asian session high or low before the London close, and whether the US session then extends in the same direction as that sweep. Assign a binary outcome to each day where a sweep occurred. At day 10, count direction-consistent extensions against reversals. This directly addresses the first open question, requires no rule change, uses the immutable snapshot format already defined, and produces a small but cleanly bounded result that illustrates the baseline comparison process before any hypothesis refinement begins.
