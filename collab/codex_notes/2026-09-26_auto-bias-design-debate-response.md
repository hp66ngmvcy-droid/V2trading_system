# Auto-Bias Design Debate: Review and Revised Plan

Date: 2026-09-26
REVIEW_SOURCE: FALLBACK_REVIEW
Status: REVIEW COMPLETE; proposed research extension blocked on evidence correctness

Interpreting as: review the auto-bias proposal and its scripts, answer the four design questions, and identify a valid next experiment. This note does not approve an automated bias filter, historical-brief build, risk change or live trading.

## Verdict

**Do not accept the claimed strong edge yet, and do not join the current same-day auto_bias labels to earlier intraday entries.** The classifier contains future information, the human labelling workflow exposes future outcomes, and the reference simulators have execution/accounting errors. More labels or more backtest days would amplify those problems rather than resolve them.

A hybrid gatekeeper is a reasonable hypothesis, not a demonstrated solution. Neither success on ten selected trades nor failure of two mechanical proxies establishes that human judgement is permanently necessary. The valid objective is cost-aware performance and reliability on unseen data, not reproducing a 100% win rate or exceeding an arbitrary 70% label agreement.

## Priority findings

### P1: Same-day auto-bias leaks future information

`scripts/backfill_auto_bias.py:66-84` uses the day's final close, ATR including the full day, and London bars through 15:59 to label that same day. These values are unavailable at Asia/London/pre-US decision times. The London comment says 08-13, but the code uses 08-16. Even trading after London does not fix the full-day close/ATR dependency.

Reproduced with two synthetic two-day datasets identical until the final M15 candle: one final close produces BUY with signals `[1,0,1]`, the other NEUTRAL with `[-1,0,1]`. The proposed earlier decision therefore changes when only future data changes.

**Fix specification:** define `as_of` for each session, include only candles closed by that time, compute ATR from prior completed days, and store feature cutoff/availability. Alternatively lag this exact end-of-day classifier to the next eligible session and call it a different experiment. Never attach the current JSON by date alone to same-day entries.

### P1: Historical human labelling is contaminated

`scripts/day_review.py:77-123` displays full Asia/London/NY summaries and the machine prediction before asking for a label. It also displays the existing brief and hindsight level touches. This is useful retrospective commentary, not blind reconstruction of a pre-session decision. `atr14` at line 56 returns the dataset's latest ATR if the requested date is absent, potentially importing much later information.

**Fix specification:** separate retrospective review from blinded labelling. For labels, truncate all charts/features to the selected cutoff, hide later prices, machine labels and original analyst bias, and do not allow missing-date fallbacks. Record the visible snapshot hash, cutoff, actual labelled_at and RETROSPECTIVE_BLINDED provenance. Recognition of historical events remains a limitation even when the chart is masked.

### P1: The claimed performance is not yet trustworthy

- `scripts/paper_game_sim.py:140`: when stop and T1 both touch, outcome becomes SL and pnl_pts is negative, but r_multiple remains its initial zero. A synthetic BUY with entry 100, stop 98 and target 104 on a high-105/low-97 bar returned SL, -2 points, **0R**. That directly overstates average R.
- The same simulator scans the entry bar's whole high/low after assuming a boundary fill (`:120-130`). The target may have been touched before entry. Its entry check is one-sided and can assume a fill at a boundary outside the actual bar range.
- After T1, the T2 scan can award a later T2 without handling an intervening stop or specifying a remaining position. T1-only and T2/partial-exit policies must be separate, frozen models.
- `load_brief_setups` and the checker do not gate entries on the brief's actual issued/received time. A later revised brief can be tested against the whole earlier day.
- `scripts/pattern_sweep.py:68` uses a separate touch-based simulator that checks TP before SL on the same bar. It also lacks cost deductions. It is neither the existing wick-confirmed strategy nor an execution-equivalent control for the paper game.
- `scripts/check_strategy.py:61` excludes OPEN_EOD trades, selecting only resolved outcomes. That can bias the sample; report unresolved/censored coverage and a predeclared horizon instead of silently dropping it.

**Fix specification:** use the agreed Stage 1 evidence/execution contract, explicit availability, full decision/outcome ledger, conservative gap policy, correct signed R, and observed-versus-assumed ambiguity. Do not infer profitability from gross zone touches. The checker's printed risk recommendations are not justified by these exploratory results and should not be acted on.

### P2: Missing sessions, timestamps and voting change the claimed rule

- `load_parquet` reconstructs naive timestamps from date/time strings even though the local Parquets have a timestamp column. Source timezone is not verified by calling the slices UTC. Use one documented timestamp convention, verify its provenance and resolve DST for genuinely local-market sessions.
- Partial sessions are accepted as full ones. One available London bar becomes the London close; sparse/missing data can reduce a signal to zero while the other votes still produce a direction. Require explicit coverage and distinguish INVALID_DATA from genuine NEUTRAL.
- Daily ATR starts with `min_periods=1`; early classifications are not based on a full 14-day warm-up. Declare a minimum history and exclude incomplete inputs.
- `total >= 2` is not ordinary two-of-three voting: `[1,1,-1]` has two BUY votes but becomes NEUTRAL. Either document this as 'two agreeing and no opposing vote' or change it in a named variant. Do not tune the interpretation to retain a desired coverage rate.
- Signal 3 is prior-day close versus open, not the stated close-to-close direction. Freeze the intended definition.
- `day_review.py:164` overwrites an existing label and `save_labels` rewrites the whole file without atomic publication or writer locking. Corrections need append-only revisions and recoverable writes.
- Empty classifier input can divide by zero in reporting; output-directory existence is assumed; broad exceptions silently discard human-brief problems. Validate and report these failures explicitly.

## 1. Architecture: a hybrid is testable, not yet preferred

Use four distinct layers: point-in-time feature snapshot -> bias classification with abstention -> separately defined zone/confirmation rule -> paper execution/outcome evaluation. Do not make the classifier responsible for hindsight trade selection.

A named higher-timeframe level must have a deterministic construction, lookback, confirmation delay and `available_at`. Prior completed day/week highs/lows are simple initial candidates. A pivot requiring later bars is available only after those bars close. Define 'near' using a frozen distance/tick/ATR rule; proximity to a level alone does not establish its strength.

Start with causal versions of the current three features, then one proximity feature as an ablation. Do not add volume profile, VWAP and news together to chase agreement. Volume availability and meaning are venue-specific: broker tick volume is not interchangeable with consolidated traded volume. Unknown macro/event data stays UNKNOWN, not zero or benign.

Measure classification confusion separately for BUY/SELL/NEUTRAL, directional-only precision/recall, abstention coverage and agreement against simple class-frequency baselines. The existing comparison includes all matched labels, so 60% overall agreement does not mean 40% of human directional days are wrong. Human labels are a reference, not objective ground truth. Two models may disagree yet have similar net outcomes.

Also reject '54% neutral is the right number': a coverage ratio cannot validate a decision rule and the note's human-neutral percentages are inconsistent. Assess coverage by symbol, session and data completeness.

## 2. Labelling: blind first, then collect a pilot

Do not spend the weekend generating 30 labels through the current screen. Thirty labels can test workflow and expose disagreement; it is not enough by definition to establish an edge or settle permanent human involvement.

Proposed sequence:

1. Pick one cutoff per session and hide all later data plus auto/original labels.
2. Preselect dates without looking at eventual outcomes; include quiet, directional and event days, with clear asset/session eligibility.
3. Label directional bias, conviction/abstention reason and structural levels separately. Bias labels alone do not supply missing entry zones.
4. Use some blinded repeat labels to assess within-person consistency; optionally independent review, only with approved data-sharing boundaries.
5. Record retrospective labels honestly; begin untouched prospective capture alongside them.
6. Keep training/development and later test periods disjoint. Cluster uncertainty by day and recognise that multiple symbols/sessions are not independent observations.

As of September 26, an entire 30-day September set cannot be completed historical data. Gold also does not have 30 trading sessions in a typical month. Future-dated files or notes, including the September 28 material present locally, are planning records unless independently evidenced otherwise; they cannot increase a realised sample count today.

## 3. Historical brief generator: separate research dataset only

**Plausible after sign-off, but it tests a synthetic-zone policy, not whether the human edge has been replicated.** Do not write generated files into the human `data/daily_briefs` collection. Use a separate experiment directory, generator/config/data hashes, as-of cutoff and explicit SYNTHETIC_DERIVED/HISTORICAL_REPLAY labelling.

Generate only from closed bars available at the specified cutoff. Use the same zone policy for gated and ungated comparisons. Do not fabricate news, macro context, human judgement or retrospective issued_at. Missing macro should be null/UNKNOWN; an explicitly price-only experiment must bypass macro inputs by design and disclosure, not by supplying zero values that mimic favourable conditions.

The requested 1,000+ days exist only for the BTC classifier output (1,293 dated rows inspected); XAU has 378. Verify actual usable coverage and completed sessions after the new causal warm-up rules rather than promising either count. The stored auto JSON contains only signals, bias and agreement, with no availability or feature provenance.

Priority 3 remains not built, as the source explicitly requires separate sign-off.

## 4. Pattern sweep extension: valid protocol before more results

Do not run the proposed same-day JSON filter now. It would combine future-derived labels with an optimistic, cost-free simulator and answer the wrong question. Full-history positive expectancy is presently **unknown**; no lift estimate was produced in this review.

After the blockers are repaired, freeze this comparison:

| Arm | Zone/entry/exit model | Direction policy |
|---|---|---|
| Control | Identical causal mechanical zones and cost model | Ungated eligible candidates |
| Anti-auto | Same | Opposite the as-of auto bias; abstain when NEUTRAL/invalid |
| With-auto | Same | Same direction as auto bias |
| Anti-human overlap | Same zones on the common eligible subset | Opposite a verified/blinded human label |

Compare shared-zone arms first to isolate the label effect; a separate two-by-two experiment can vary human versus mechanical zone generation. Do not attribute improvement to auto bias when the zone policy, time window or exit rules also change.

Use a causal per-session classification or a clearly labelled prior-day classification, chronological development/validation/untouched test blocks, recorded trial counts and cost stress. Report all arms, all abstentions, attempted/filled/resolved/censored counts, net mean/median R, drawdown and day-clustered uncertainty. Separate BTC and XAU and avoid adding overlapping session trades into a fictitious portfolio. A failed result means this particular rule is unsupported, not that humans are permanently required.

## Evidence-claim corrections

- The headline counts do not define disjoint groups: 10 anti + 20 with + 4 neutral sum to 34, not 30. The pattern note says neutral is included in the with group; current checker code excludes it. Reconcile the exact snapshot and denominator before comparing win rates.
- Ten wins after inspecting many filters is an exploratory observation. Even under an ideal predeclared independent Bernoulli model, 10/10 does not imply a 100% underlying win probability; selection and dependence make that simple model inadequate here.
- Negative results for selected MA/fade/zone variants do not prove all mechanical strategies fail or establish the cause of any human advantage.
- A nominal p=0.048 for a range comparison does not confirm a profitable expiry filter, an OI threshold or a 30% stop-widening rule. Last-Friday calendar grouping is not measured OI exposure; compare against appropriate weekday/regime controls and disclose multiple testing. Retain the idea as exploratory until independently validated. [ASA statement on p-values](https://www.amstat.org/asa/files/pdfs/p-valuestatement.pdf)
- Selecting the best of many historical patterns raises false-positive and overfitting risk; freeze trials and preserve genuinely unseen evaluation. [Bailey et al., The Probability of Backtest Overfitting](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf)

## Handoff and verification

Priority 1: reviewed both requested scripts and the checker/simulators; blockers above are actionable. Two isolated synthetic reproductions confirmed future sensitivity and the 0R stop bug. Parquet schema/row counts and stored classifier date coverage were inspected read-only. Arrow emitted sandbox CPU-query warnings, but both reproductions completed successfully. No source market data was sent to external research; only generic statistical-method sources were consulted.

Priority 2: deliberately not implemented/run on the flawed baseline. First fix causal cutoffs, blind labelling and execution/accounting; add future-perturbation invariance, sparse-session, timezone, vote-rule, ambiguous-entry and net-cost tests. Then implement the comparison as a separately named paper experiment. This is not a claim that Priority 2 is completed.

Priority 3: deferred pending the requested sign-off and the above contracts.

No original scripts, briefs, labels, candidate statuses, risk settings or schedules were changed. Existing dirty work was preserved. No full backtest, profitability validation, installation, external-agent review or live action was performed. The response is ready for local review, not evidence of an established edge.
