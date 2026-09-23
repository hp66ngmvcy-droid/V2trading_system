# Daily BTC/Gold Strategy Reviewer: Plan and Collab Audit

Date: 2026-09-23
Status: PROPOSED - planning complete; implementation and independent review pending
REVIEW_SOURCE: FALLBACK_REVIEW
Task ID: daily-brief-strategy-review-plan-2026-09-23

Interpreting as: plan a local, paper-only daily brief/strategy reviewer and identify unfinished collaboration work that affects it. No live orders, automatic tuning, promotion, scheduler activation or external agent invocation is authorised by this plan.

## Intended result

For BTCUSD and XAUUSD, compare the daily brief with each selected strategy's actual entry rules. Show eligible hypothetical entries, reasons for rejection, subsequent movement and cost-aware simulated outcomes. Review yesterday without hindsight, observe today as data becomes available, and compare candidate changes on later unseen data.

This is a research instrument, not a trade recommendation service. A touched level is not a strategy entry; a strategy confidence score is not a calibrated probability.

## Reuse before building

- Existing `src/tar_system/reporting/post_import_review.py` provides a synthetic manifest-to-report prototype with lineage hashes, readiness checks, same-bar ambiguity and repeat-run protection. Its current contract accepts SYNTHETIC only and does not evaluate trades. Preserve those boundaries and tests; add a separately reviewed real-data adapter rather than relabelling synthetic outputs as real evidence.
- Existing `docs/runbooks/POST_IMPORT_REVIEW_PROTOTYPE.md` describes the missing real-data, session and provenance integration. Its reported 25-test result is historical, not rerun for this plan.
- Reuse the existing strategy interfaces, feature pipeline, broker cost model, data store and reporting conventions. Start with `key_level_sweep_v1` for both instruments. Add other existing strategies only after checking their symbol/timeframe support and input requirements. Do not revive KILLED strategies or imply RESEARCH candidates are approved.
- Use the existing UI framework after inspecting its route and data-loading patterns. Do not build a second dashboard or a new database simply for this feature.
- Keep brief observations and strategy trade outcomes distinct. The current synthetic upper/lower-first observation is not a target-before-stop trade result.

## Stage 0: agree the evidence contract

Suggested owner: lead implementer; human review of timing, targets and scope.

1. Preserve original brief files. Identify each version by content hash, symbol, session, strategy/configuration version and actual availability time. Amendments are new versions effective only after their recorded time.
2. Treat after-session pasted briefs and uncertain publication times as RETROSPECTIVE or UNKNOWN, never prospective. A filename date cannot establish advance knowledge.
3. Define three modes: SYNTHETIC, HISTORICAL_REPLAY and PROSPECTIVE_PAPER. Keep their sample counts and statistics separate.
4. Agree explicit side-specific entry/stop/target rules, expiry horizon, eligible sessions and instrument contract specifications. Do not silently choose a favourable target from a range to make R:R pass.
5. Define forecast probability, if supplied, as a specific event and horizon. Directional confidence and conditional trade success must not share a label without an explicit mapping.

Acceptance: a small reviewed schema and fixtures cover both symbols, revised briefs, missing provenance, ambiguous targets and expired forecasts. Existing immutable inputs remain unchanged.

## Stage 1: reliable replay and append-only outcomes

Suggested owner: one implementer, with a separate review before integration.

Build the smallest CLI/report slice first, using existing local bars. MT5 is not a prerequisite for historical replay or fixture tests.

Required engineering prerequisites:

- Keep the full market-data timeline, including days without briefs. Missing briefs block new entries, not stop/target processing for existing positions.
- Use one canonical feature calculation in replay and prospective collection; resolve the runner's EWM ATR versus feature pipeline's rolling ATR mismatch.
- Separate bar-open timestamp, bar-close availability, decision time, observation time and executable entry time. Proposed new baseline: next available bar open after a closed-bar decision, with costs and a defined gap policy. Retain existing close-fill results only as a separately labelled variant until a baseline change is reviewed.
- Resolve bar-path ambiguity conservatively: a candle touching stop and target cannot establish their order. Finer data must have valid provenance; otherwise show AMBIGUOUS and any conservative assumed result separately.
- Reject malformed/non-finite data, unknown instruments, stale or incomplete input and invalid stop distances. A missing/expired event calendar is UNKNOWN, not confirmation of no events.
- Keep the two symbols in isolated paper ledgers initially. Do not combine their equity until per-symbol marking, sizing and shared exposure limits are verified. Likewise, strategy comparisons use isolated accounts rather than summing overlapping hypothetical profits.

Proposed linked records, adapted to existing local storage conventions:

| Record | Minimum information |
|---|---|
| Input manifest | Brief/data/config hashes, feature version, symbol/venue/timeframe, availability, coverage, evidence class |
| Decision | Stable ID, brief version, strategy version, decision timestamp, BUY/SELL/WAIT/REJECTED and reason codes, proposed entry/stop/target |
| Simulated fill | Decision link, executable timestamp, quantity/units, bid/ask or stated assumption, spread/slippage/commission model |
| Outcome event | Trade link, OPEN/RESOLVED/EXPIRED/CENSORED/AMBIGUOUS, exit reason/time, realised net P&L and net R when meaningful |
| Amendment | Prior record link, corrected fields, recorded time and reason; never overwrite the previous event |

Log NO_BRIEF, NO_TRIGGER, LOW_RR, SESSION_BLOCK, EVENT_BLOCK, COOLDOWN, INVALID_DATA and RISK_BLOCK separately. No record is not evidence of no trade. Record maximum favourable/adverse excursion only over the actual exposure window, with OHLC limitations disclosed.

Use deterministic IDs and restart-safe cursors; repeated input must not duplicate trades or sample counts. Partial batches produce operational status, not completed outcome scores. Write reports atomically using existing conventions and keep outputs out of source briefs.

Acceptance: one complete replay report for each symbol, repeat-run identity, traceable decisions/outcomes and explicit missing-data status. No profitability claim is required or implied.

## Stage 2: daily local interface

Suggested owner: UI implementer after report contract is stable.

Three compact views inside the existing local application:

- **Today:** date/symbol/strategy selection; input freshness and evidence badge; original brief/version; chart with levels and hypothetical entries; filter results; open paper positions. WAIT and unavailable-data states must be explicit.
- **Yesterday:** frozen brief alongside actual movement; entry/exit markers; rejected opportunities; net outcomes and assumptions. Explain why an entry was accepted or rejected without inventing a narrative from future prices.
- **Compare:** frozen baseline versus named experimental versions on the same eligible data, with sample counts, net results, uncertainty and trial history. Clearly separate training and unseen evaluation periods.

Input workflow: draft -> validate -> preview -> save version -> explicit Run Paper Review. Confirm the local save path and record ID, reload the saved version, and preserve prior versions. Edited notes do not silently rerun or alter the baseline. Optional hypothetical opposite-side tests need their own predeclared rule/version; never select the winning direction after seeing the day.

Local-only requirements: bind a future server to loopback by default, validate all imported content as data, constrain read/write paths to approved directories, escape rendered notes, and exclude credentials/account identifiers. No remote analytics, LLM calls, broker calls or filesystem-wide access. Local storage is not a promise of encryption or backup; document permissions and recovery separately.

Acceptance: desktop/mobile browser checks, keyboard access, all controls working, no chart/label overlaps, persistent-save/reload tests, empty/error/partial-data states and explicit absence of live-order controls. Implement charts using the existing library where possible.

## Stage 3: probability, then controlled experiments

Before sufficient evidence, display **Insufficient evidence**. Do not display the strategy's confidence field as a measured win probability.

Historical estimates must include the exact event definition, sample size, period, symbol/strategy version, uncertainty interval and treatment of unresolved/ambiguous outcomes. Separate retrospective and prospective populations. Multiple correlated trades on one brief/day do not provide equivalent independent evidence.

Build Brier/reliability calculations with synthetic fixtures if useful, but do not infer calibration from ten labels. Assess held-out calibration against a training-only base-rate predictor. Do not let uncalibrated probabilities increase position size.

Tuning is an explicit research experiment: freeze baseline, preregister a small change and its evaluation rule, train on past data, evaluate on later untouched data, record every attempted variant and obtain human review. Never rewrite yesterday's brief or silently replace the baseline. Walk-forward sample adequacy and cost-stressed outcomes remain gates; there is no automatic '30 days means ready' rule.

Acceptance: future-data perturbation cannot change earlier decisions; train/test boundaries and trial registry are visible; insufficient sample and censored cases do not manufacture certainty; no automatic strategy promotion exists.

## Test plan for implementation

1. Preserve and rerun the existing reporting tests before extending the prototype.
2. Add fixtures for both symbols, contract units, target ranges, invalid values, revisions, late briefs and missing availability times.
3. Test decision/fill chronology, next-bar execution, costs, price gaps, same-bar stop/target ambiguity and positions crossing days without briefs.
4. Test UTC conversion, London/New York daylight-saving boundaries, BTC weekends and Gold closed sessions without invented bars.
5. Test duplicate imports, repeat runs, restart recovery, partial data and ledger amendments.
6. Test isolated strategy/symbol accounts; combined portfolio tests are a later prerequisite for combined statistics.
7. Test probability eligibility, outcome horizons, censoring, no-signal exclusions and training/test separation.
8. Run focused pytest first, then the full suite for shared engine/risk/UI changes; browser-test the interface and verify saved-file reloads. Record exact results in a new completion note.

## Collab audit: outstanding work and contradictions

Scope: current `_state.yaml`, generated `STATUS.md`, `TASKS.md`, recent handoffs, relevant review/prototype notes and focused source inspection. This is backlog triage, not a full code/security audit or a fresh test/backtest run.

The September 23 YAML contains **24 pending items**. `STATUS.md` shows only three active rows. Its generator reads `collab/state.db`, not `_state.yaml`; therefore regenerating the page alone will not reconcile the YAML backlog. `TASKS.md` is a separate auto-builder-facing queue with no current rows. Do not add Ready rows for this proposal or blindly merge these stores.

### Immediate prerequisites, in recommended order

| Existing work | Current disposition | Required next action |
|---|---|---|
| outcome-logging-schema | Draft and revision recommendation exist; still pending | Adopt linked append-only outcomes, not outcome fields written into original forecasts |
| brief-outcome-logging | Blocked by the agreed evidence contract | Start reliable prospective recording; historical reconstruction labelled separately |
| fix-runner-interday-position-continuity | Still present in inspected runner: date filtering uses `isin(brief_dates)` | Preserve intervening bars and gate entries separately |
| fix-half-kelly-lot-conversion | Still pending; sizing branch requires correctness review | Test actual final loss-at-stop; keep uncalibrated Kelly out of this MVP |
| fix-tracker-multi-symbol-mark-price | Inspected tracker still applies a single mark across positions | Use isolated ledgers first; repair per-symbol marking before combined reporting |
| brief-schema-hook | Pending | Agree schema, then runtime and hook validation; review any new dependency before install |
| populate-regime-opening-type-briefs | Queue still instructs historical edits and references an old count | Use separately timestamped retrospective annotations; do not fabricate original knowledge or activate sizing automatically |
| mt5-live-feed-gaps | Pending | Fixture-test feature parity, decisions, lifecycle and restart logic now; live terminal smoke test waits for a supported environment |
| mt5-macos-compatibility | Human environment decision outstanding | Needed for actual MT5 integration, not for local historical MVP |

### Existing debates and later experiments

The [nine-debate response](2026-09-21-nine-debate-review.md) already addresses the eight `debate-*` items and the outcome schema. They need reviewer disposition and implementation tickets where appropriate, rather than another identical debate. No approval or closure is implied by the response's existence.

| Pending item/group | Recommended disposition |
|---|---|
| debate-historical-brief-t1 | Preserve baseline briefs; lower-threshold variants remain labelled experiments |
| debate-buy-stop-atr-vs-structure | Specify candidate stop policy; baseline change gated on outcomes |
| debate-wf-overfitting | Freeze experiments and chronological evaluation now; additional validation methods later |
| debate-paper-live-gap | Wording 'no cost model' is stale; September 22 fixes and runner profile exist. Remaining cost/gap realism and regenerated evidence need review |
| debate-external-data-feeds | Data contract and entitlement/as-of checks first; no feed integration required for first local replay |
| debate-confidence-sizing-ruin | Calibration and sizing are separate gates; no confidence-driven risk increases |
| debate-xauusd-btcusd-concentration | Combined-account risk controls required before combined portfolio claims |
| debate-human-brief-bias | Immutable provenance now; statistical bias studies later |
| brier-score-script | Fixture-based implementation can start after event definition; conclusions remain sample-gated |
| ny-session-window | Shadow comparison first; use intended local session clock with DST, not an unexplained fixed UTC window |
| regime-classifier-price-based | Shadow features only until supported by outcomes |
| fvg-experiment | Deferred candidate, not a prerequisite for this reviewer |
| phase3-macro-agent-a | Deferred decision-impact automation; not required for MVP |
| phase3-event-gate-agent-b | Reliable read-only event safety design can be separate; no scheduler or automatic permission to trade |
| business-model-path1a-pilot | Separate human-owned commercial work; not a dependency for private paper reporting |

The [business-model debate](2026-09-22_business-model-debate-response.md) is now recorded as completed in YAML. Its recommendations are not implemented merely because that debate is complete.

### Other collab work needing attention

- **Synthetic prototype independent review and real-data adapter:** explicitly outstanding in the prototype completion note. This plan extends that work rather than creating a duplicate learning loop.
- **External repository import proposal:** remains human-owned in generated status. Broad imports are not needed for this MVP; older approval must not substitute for present dependency/security review.
- **Live stubs / Librarian split task:** status mixes two deliverables. Stubs already exist; Librarian scope/sign-off is separate. Reconcile evidence and split the tracking rather than reimplementing stubs.
- **Older three-session learning tally:** earlier handoffs contain unresolved outcomes and a calendar-based day-10 review trigger. Audit availability/completeness before increasing a learning counter; no new completion count was asserted here.
- **Stale memory/orchestrator:** they still contain older focus/blocker/count claims superseded by newer notes. Reconcile durable summaries against reviewed evidence, not just the latest date.
- **Missing linked completion note:** generated status refers to `codex_notes/2026-09-19_key-level-sweep-v1-build.md`, which was not in the collab file inventory inspected. Verify the intended location and correct the state-store link; do not invent a replacement completion record.

## Next review packet and boundaries

Proposed first implementation slice: agree immutable input/outcome schemas, review the synthetic prototype, fix continuous-bar replay, then create one CLI JSON/Markdown report for each symbol. Dashboard work follows the stable report contract. MT5 collection, probability estimates and automated experiments are later slices.

Questions for the next local review: approve the event/horizon definition; confirm the next-bar execution policy for the new baseline; approve isolated-ledger MVP scope; choose one authoritative collaboration queue and its migration process. These are review questions, not blockers to saving this plan.

This note does not change queue ownership, readiness, review sign-offs or completed-task history. The generated status tables, SQLite state, YAML and auto-builder queue were deliberately left unchanged because they disagree and include existing user/agent modifications. Register this proposal as PENDING/NOT READY when the queue owner reconciles the stores. Do not run another agent or transmit private source material merely because a local handoff exists.

Verification for this planning task: relevant notes and current source locations inspected; new Markdown saved and compared against the staged file. No application tests, broker connection, backtest, new dependency, database migration, scheduler activation or trading action was performed.
