# V2: Primary Experiment Without Mandatory Human Bias Labels

Date: 2026-09-27
REVIEW_SOURCE: FALLBACK_REVIEW
Status: proposed research-design change for discussion; no code or scheduling authority

Interpreting as: document in depth why the primary V2 experiment should not depend on the user predicting historical market direction, how an objective alternative would work, and what decisions and verification remain necessary.

## 1. User need and intended change

The user has tried the historical day-review workflow and does not consider their own directional judgement a strong basis for a proper strategy test. The design should not require them to become a skilled directional analyst before V2 can produce useful evidence.

Recommendation: pause mandatory historical BUY/SELL labelling. Make the human-label arm optional, not a prerequisite for primary baseline evaluation. The user's present request is to document and explain this proposal; it does not authorise deletion of labels, alteration of the active work order, strategy changes, comparisons or automation.

A good result means a trustworthy answer, including evidence that a strategy does not help. It does not mean arranging the experiment to show attractive returns.

## 2. What the old exercise actually measures

Blind historical labelling measures a particular person's interpretation of a particular permitted snapshot. It can answer whether those judgements add information under a defined protocol. It does not provide the objectively correct BUY/SELL answer, and agreement with the person's label is not proof of a trading edge.

Historical review also has limitations: the reviewer may remember the day; chart summaries may omit useful context; training and consistency vary; abstentions and repeat exposure alter the cohort. These limitations are properties of the experiment, not a judgement about the user's competence.

Keep existing labels and their provenance unchanged. They can remain exploratory annotations or support a later optional human study. Do not promote retrospective labels to prospective evidence or substitute AI labels under the human field.

The latest `2026-09-26_blind-mode-round3-response.md` reports the two targeted fixes and 21 passing tests. Those results were read, not rerun in this documentation task. Avoid resurrecting resolved findings. Remaining limitations and the effect of removing the human arm need review, not another indefinite expansion of the labelling tool.

## 3. Three questions that must stay separate

1. **Operational correctness:** were the inputs available, rules executed faithfully, and records saved reproducibly?
2. **Predictive usefulness:** did a predeclared feature improve a specified later price-outcome measure on unexamined data?
3. **Trading usefulness:** did it improve simulated net outcomes under feasible entries, exits, exposure constraints and costs?

A correct program can implement an unprofitable strategy. Correct direction does not guarantee a fill or a profitable path. A profitable gross simulation can fail after costs. Report these questions separately.

## 4. Choose an honest baseline

### Lane A: deterministic evaluation of timestamped brief-based setups

Freeze one existing strategy and its input contract. Evaluate all eligible setups without a discretionary human daily-bias filter. This removes the need for new human direction labels, but it is not fully mechanical if levels, targets or confidence originate in human/AI-authored briefs.

Brief fields still need demonstrable availability before the decision. Missing issuance or a later edit cannot be repaired by inventing an earlier timestamp. Quarantine such cases from prospective-equivalent evaluation and report their exclusion count. If the baseline retains an author confidence threshold, disclose it as subjective input rather than calling the entire baseline objective.

### Lane B: separate mechanical-level experiment

If Lane A lacks sufficient causal inputs, propose deterministic levels, for example previously completed session extremes, with precise source/calendar definitions. A current-session running level must be taken from previously closed bars before testing a new bar against it.

This is a new strategy version, not a repair to old briefs and not a continuation of the same performance series. Do not fabricate historical briefs to make a sample look complete. Select and freeze the level policy before outcome evaluation.

Recommended starting choice: Lane A only where provenance is adequate; otherwise prioritise prospective collection or explicitly approve Lane B. Do not combine their results as one baseline.

## 5. Let observed price paths evaluate candidates

Predeclare the outcome contract before running the experiment:

| Item | Required definition |
| --- | --- |
| Candidate | Stable identity, symbol, decision timestamp, input availability and strategy version |
| Signal | Exact rule, time it becomes knowable, and rejection/WAIT reason |
| Entry | Agreed executable paper model, eligibility time, gap treatment and spread |
| Exit | Frozen stop, target, time horizon and position-management policy |
| Costs | Units, source, assumptions, spread/slippage/fees and stress cases |
| Exposure | Concurrency, cooldown, position caps and portfolio rules |
| Quality | Missing bars, duplicates, invalid OHLC, stale inputs and unknown timestamps |

Record both raw observed barriers and the execution model's resulting classification. When one bar touches stop and target and ordering cannot be established, label the path ambiguous. A predeclared stop-first sensitivity may be reported as an assumption, not as an observed loss. Do not discard ambiguity silently or present it as a proven win.

Possible states include NO_ENTRY, INELIGIBLE_INPUT, OPEN, TARGET_FIRST, STOP_FIRST, TIME_EXIT, AMBIGUOUS and CENSORED, mapped to the existing schema rather than inventing competing enums without review. Missing observations and positions still open at a data cutoff are not zero-return completed trades.

Save realised simulated R, maximum favourable/adverse excursion and elapsed time where supported. Define the measurement window: in-trade excursion ends at exit; post-exit movement is a separately named research measure. Do not let later outcomes alter the original candidate or its eligibility.

## 6. Compare small, controlled alternatives

First establish a reliable baseline report. Then test one addition at a time:

- A: all eligible baseline candidates, without the proposed filter.
- B: the same candidates with a frozen daily trend rule.
- C, later: a separately approved location-plus-flow rule when suitable footprint evidence exists.

Use identical candidate construction, fills, stops, targets and costs when isolating a filter. Keep trend-opposed, MIXED, UNKNOWN and rejected cases visible. A filter can raise win rate by discarding useful trades; report opportunity count, exposure and whole-period contribution alongside per-trade results.

At candidate level, a skipped trade contributes no executed return to the filtered arm, but retains its explicitly hypothetical baseline outcome for opportunity analysis. At portfolio level, removing a trade may free capacity for another: either keep the candidate-level attribution study separate or simulate each portfolio under identical predeclared capacity rules. Do not compare incompatible totals.

Entry timing and exit management changes require separately labelled experiments. Do not improve an entry filter, stop rule and exit rule simultaneously and attribute the result to one feature.

Order-flow studies require the actual requisite data. Existing OHLCV cannot reconstruct unavailable footprint rows. The proposed Pine V2.1 indicator is a separate data/engineering lane, not an immediate prerequisite for testing the present baseline.

## 7. Prospective paper pilot

Agree a manual collection protocol initially; scheduled reviews or API calls need their own authorisation. The pilot sequence is:

1. Select verified feeds, instruments and exact session calendars. Freeze strategy/configuration and capture source hashes.
2. Save the decision snapshot before the eligible entry, including WAIT and blocked cases. A timestamp in a retrospectively created file alone does not establish original availability.
3. Append subsequent fills/outcomes without replacing the decision. Record missed sessions and data gaps, not just sessions that produced trades.
4. Review data integrity and operational exceptions daily without tuning strategy parameters to yesterday's outcomes.
5. At a scheduled review after 10-20 trading days, assess capture completeness, timestamp integrity, outcome resolution and execution realism. This is an operational pilot, not a sufficient-sample declaration or profitability gate.
6. Continue evidence collection or stop for a predeclared reason. Structural changes create a new version and invalidate equivalence with old results unless explicitly accounted for.

BTC calendar days and gold trading sessions differ; record both elapsed period and eligible sessions for each. Report per instrument before any pooled analysis. A small number of correlated trades is not a large independent sample merely because several entries occurred in a day.

## 8. Validation and interpretation

Use chronological development and validation, with genuinely unexamined or prospective data reserved for final evaluation. Previously inspected historical days remain development evidence. Handle overlapping holding periods at boundaries so outcomes cannot contaminate adjacent splits. All attempted variants belong in the experiment log.

Primary reports should include attempted/eligible/filled/resolved/ambiguous/censored counts, net expectancy, exposure, drawdown, costs and uncertainty appropriate to day-level dependence. State sample limitations. No fixed count such as 10 or 30 trades automatically establishes a reliable edge.

Do not announce a win probability from a short run or a judgement confidence score. Probability estimation, if later pursued, needs a clearly defined target, separate calibration/evaluation data and calibration evidence. Descriptive frequencies are not guaranteed future chances.

Predeclare review dates and revision/stop rules. Do not repeatedly search parameters until a favourable figure appears. Distinguish implementation failure, invalid data, weak evidence and evidence of no improvement.

## 9. Human role: quality control, not prediction

Offer a short factual review rather than a daily direction quiz:

- Did the instrument/feed and session match the intended setup?
- Were the displayed levels and timestamps correct and available at the decision?
- Was important event context missing or incorrectly timed?
- Did the chart and saved explanation match the rule-generated decision?
- Is a data defect or execution assumption worth flagging?

Responses should allow correct / incorrect / uncertain / not reviewed, with an optional note. Uncertainty is useful evidence, not a failed task. Record observations after the fact as annotations; never change the original trading decision to agree with the review.

Independent expert review could assess a sampled cohort later, but is not required to run a mechanical test. If discretionary interpretation is the actual strategy being studied, human evidence cannot simply be removed while claiming to test the same hypothesis; rename that study or retain it as an optional separate arm.

## 10. AI role and boundaries

AI may explain deterministic rule outputs, find inconsistencies or propose hypotheses. It must not be used as ground truth. A separately tested model arm needs model/prompt/version, complete evidence identity, request/output records and distinct machine provenance. Historical date knowledge may compromise apparent blinding even when the prompt omits future bars.

The existing LLM label script stays unapproved under its separate review. No paid calls, credential use, private-data transfer, scheduler activation or replacement of human labels is authorised here.

## 11. Concrete collab decisions requested

Claude: read this alongside the latest blind-mode response, Stage 0/1 evidence contract and `2026-09-26_v2-research-improvement-priorities.md`.

For each item provide Agree / Disagree / Alternative and supporting code/schema references:

1. Remove mandatory new human bias labels as a gate for the primary experiment; keep the human arm optional and existing labels intact.
2. Choose Lane A or a separately proposed Lane B based on verified input availability, not desired sample size.
3. Specify one frozen baseline and execution/outcome contract; do not mix zone-touch and wick-rejection results.
4. Identify what the existing reviewer/outcome infrastructure already supplies and the smallest remaining implementation work.
5. Propose a prospective pilot protocol, cohort and operational acceptance checklist without activating it.
6. Define which comparisons are currently feasible and which remain gated by data, sample quality or approval.
7. Stop spending primary-experiment effort on subjective labelling features that are no longer required; retain justified integrity fixes without deleting historical evidence.

Requested response: `collab/claude_notes/2026-09-27_primary-experiment-without-human-labels-response.md`.

## Delivery and authority

This note proposes a research-design change; it does not mark existing tasks approved, alter queue state, or certify current code. No tests or performance comparisons run for this documentation task. No labels, source code, raw briefs, risk settings, schedules or account state changed. Claude has not been invoked or notified automatically.
