# Eight Debate Dispositions

Date: 2026-09-23
REVIEW_SOURCE: FALLBACK_REVIEW
Status: recommendations delivered; not queue closure or strategy approval

Interpreting as: deliver Group 1 dispositions from the work order, applying the earlier review without repeating the debate. Group 3 fix specifications are superseded by the user's latest instruction and current completed entries.

Authority for reasoning: [nine-debate review](2026-09-21-nine-debate-review.md). Current implementation status: `_state.yaml` version 8 and focused read-only source inspection. No tests, code changes, installs or queue updates in this task.

## 1. debate-historical-brief-t1

**Decision:** Path A: preserve original briefs and hashes; lower-threshold replays are separately labelled experiments only.

**Rationale:** Changing historical forecasts or selecting targets after observing outcomes destroys a fair baseline.

**Next:** Freeze input versions and experiment parameters; keep historical files unchanged and evaluate variants on an untouched later period.

## 2. debate-buy-stop-atr-vs-structure

**Decision:** Specify an experimental sweep-extreme policy, leaving the current baseline unchanged.

**Rationale:** Consistent stop geometry is testable but does not establish an edge.

**Next:** Proposed ticket `EXP-SWEEP-STOP-001`: BUY = min(sweep_low - buffer, entry - k*ATR); SELL = max(sweep_high + buffer, entry + k*ATR). Freeze k, price-unit buffer, outward tick rounding, data availability and costs before testing; recompute loss-at-stop sizing. Promotion requires outcome evidence and human review. This note does not register or activate that ticket.

## 3. debate-wf-overfitting

**Decision:** Freeze splits, parameters, costs and trial history now; retain chronological walk-forward and treat CPCV as an optional supplement.

**Rationale:** Repeatedly selecting favourable validation windows invalidates the holdout, and reusing observations across CPCV paths does not create independent samples.

**Next:** Document train/test boundaries, overlap purging and an untouched prospective period. Around 100-200 resolved trades is only a feasibility checkpoint for additional analysis, not a pass threshold; coverage and dependence determine adequacy.

## 4. debate-paper-live-gap

**Decision:** Retire the stale 'no spread model' premise; require regenerated results and explicit execution assumptions.

**Rationale:** September 22 cost/profile repairs and September 23 replay continuity change the tested implementation, while stop-gap and intrabar assumptions still matter.

**Next:** Compare new versioned results under measured or clearly assumed costs and adverse scenarios. The current runner is not itself a walk-forward pass. Do not deduct spread twice or re-label older reports as corrected evidence.

## 5. debate-external-data-feeds

**Decision:** Defer optional macro-feed integration; local replay and outcome logging need not wait for it.

**Rationale:** New data sources cannot repair missing outcome provenance or execution semantics.

**Next:** Define source, venue, entitlement, observation/publication/fetch times, revisions and staleness before any adapter. An unknown calendar remains UNKNOWN; read-only event-safety design is not prohibited merely because optional macro integration is deferred.

## 6. debate-confidence-sizing-ruin

**Decision:** Keep uncalibrated confidence out of sizing; do not treat a Brier threshold alone as permission to use Kelly.

**Rationale:** Calibration, payoff distribution, estimation error and loss controls are different requirements.

**Next:** Validate the declared probability event out of sample and stress sizing before any change. Current inspection finds sealed live broker/runner/router stubs and no executable live path there. The paper caller exposes a selectable sizing model, so HALF_KELLY is not universally unreachable; forward testing uses ATR_BASED, and these inspected callers do not supply brief confidence as win_rate. The September 23 sizing fix is recorded as completed, not independently re-certified here. The reviewer MVP must select capped fixed-risk paper sizing explicitly.

## 7. debate-xauusd-btcusd-concentration

**Decision:** Use isolated per-symbol paper ledgers for the MVP; any shared account needs an explicit aggregate risk cap and concurrency policy.

**Rationale:** Repairing the mark-price interface alone does not prove complete multi-symbol marks or portfolio loss control.

**Next:** For a combined account, initially allow at most one open position across this strategy's symbols or share one documented loss budget, logging rejected candidates. The current tracker accepts a symbol-price map, but the inspected engine supplies the current symbol only and missing marks are skipped; do not claim a fully valued combined portfolio from that call. This is a remaining integration condition, not a request to redo Group 3.

## 8. debate-human-brief-bias

**Decision:** Preserve immutable input versions and verified availability; defer statistical bias claims.

**Rationale:** A syntactically valid issued_at or a hash made today cannot prove that a historical forecast existed before the move.

**Next:** Read-only JSON inspection found 13 current `_levels.json` files, all with parseable offset-aware issued_at values matching their filename dates. This does NOT verify absence of backdating or establish the date each content version became available. Require original run/export/receipt evidence; mark unverified historical versions accordingly. Store future hashes at ingestion and append amendments. Thirty outcomes is at most a review checkpoint, not proof that a round-number bias test has adequate power.

## Installation answer

**No new installation.** Read-only environment inspection found `jsonschema 4.26.0` and `check-jsonschema 0.38.2` already installed in V2's venv. This establishes presence, not a supply-chain audit or permission to upgrade. Stage 0 can use existing tools; any hook activation and dependency pinning remain separate changes. JSON Schema handles structure; zone ordering, timing and record links also need semantic validation.
