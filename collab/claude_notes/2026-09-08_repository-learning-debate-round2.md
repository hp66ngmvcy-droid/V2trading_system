REVIEW_SOURCE: CLAUDE_REVIEW
APPROVAL_ID: user-request-20260908-repository-learning-debate
CLASSIFICATION: PUBLIC_TECHNICAL_ONLY

1. Decisions on A-I

A. Accept. Parameter stability confirms configuration identity, not execution identity. Full reproducibility requires matching code commit, input hashes, random seeds, and recorded compute costs as separate tracked fields.

B. Accept. A flat performance surface tests that perturbation correctly returns no signal; a brittle surface with known sensitivity tests that perturbation detects signal when present. Both are necessary to validate the robustness metric itself, not just the system under test.

C. Accept. Named exchange calendars are a convenience alias, not a general solution. Research windows and venue hours must be stored as explicit time intervals with timezone offsets and must not share a single calendar object.

D. Accept with clarification. Point-in-time datasets remove look-ahead bias from features but do not convert a retrospective reconstruction into prospective evidence. Prospective evidence requires the forecast record to be frozen and timestamped before any outcome is observed. Timestamps must be cross-referenced against an append-only trial ledger to have evidential weight.

E. Accept. An IN clause is a necessary but insufficient guard. Each evaluation row must carry a single evidence class, an explicit cohort membership key, a unique observation ID, and foreign keys to separate parent forecast and outcome records. Mixed joins must be a schema violation, not merely a query-time filter.

F. Accept. A single ingestion timestamp is ambiguous. Each feature column requires its source publication time, ingestion time, and transformation version. These are independent nullable fields, not a single composite timestamp.

G. Accept. Return-only bootstraps recycle observed outcomes and cannot generate unseen tail events. Minimum independent observation counts are a separate rule. Five positive returns can yield a positive confidence interval while hiding catastrophic left-tail risk entirely.

H. Accept. Any dataset consulted during variant selection is development data regardless of its label. Full search history, variant scores, and the selection cutoff date must all be recorded. The trial ledger entry for the chosen variant must reference this history.

I. Contest partially. Twenty percent is an unsupported threshold. The correct rule is: reuse existing storage by default; introduce a separate database only when a measurable access-pattern requirement, such as query latency or concurrent-write volume, cannot be met by the current store. No numeric threshold belongs in schema design.

2. Schema

Forecast: forecast_id, cohort_id, evidence_class (single enum value), feature_snapshot (jsonb including publication_time, ingestion_time, transform_version per feature), frozen_at (append-only, set once), code_commit, input_hash, seed.

Outcome: outcome_id, forecast_id (FK), observed_at, value, evidence_class (must equal parent forecast evidence_class, enforced by constraint).

Trial: trial_id, trial_ledger_entry (append-only log reference), search_history_ref, selection_cutoff_date, selected_forecast_id (FK), status (prospective or retrospective, derived from whether frozen_at precedes observed_at).

Evidence classes: HISTORICAL_SIMULATION, WALK_FORWARD_OOS, PROSPECTIVE_LIVE, PAPER_TRADE. Each class permits only its own outcome records. Cross-class joins are a schema constraint violation.

3. Tests and next step

Test 1 (parameter stability): Run identical configuration twice with fixed seed and input hash. Assert all parameter values, costs, and output hashes match byte-for-byte.

Test 2 (flat surface robustness): Perturb parameters on a synthetic constant-return series. Assert robustness score returns zero, confirming no spurious signal.

Test 3 (brittle surface robustness): Perturb a known sensitive parameter on a synthetic threshold-dependent series. Assert robustness score exceeds a documented expected bound.

Test 4 (prospective evidence guard): Attempt to insert an outcome record before frozen_at is set on the parent forecast. Assert schema constraint rejects the insert.

Next design task: implement the append-only trial ledger with referential constraints before any optimiser work begins. All other integrity guarantees depend on it.
