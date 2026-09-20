REVIEW_SOURCE: CLAUDE_REVIEW
APPROVAL_ID: user-request-20260908-repository-learning-debate
CLASSIFICATION: PUBLIC_TECHNICAL_ONLY

1. Lead Proposal Verdict

KEEP, with one revision: instrument edge-case handling before adding any framework dependency. The strongest objection is ordering cost — installing MLflow, VectorBT and Optuna before validating that session observations are clean introduces framework-shaped assumptions into the record structure. A native record format that captures data lineage, session boundaries and trigger metadata is cheaper to own and easier to audit. Once that baseline is stable, selectively adopt libraries where the marginal correctness gain exceeds the integration surface.

2. Stability and Small-Sample Counterexamples

Parameter stability is not the same as configuration consistency. A strategy run with identical parameters across every fold demonstrates reproducible execution, not robustness. Robustness requires that small parameter perturbations produce only small performance changes — that is local sensitivity. A configuration can be perfectly consistent and still sit on a ridge where a one-tick threshold shift collapses the edge. Assigning a perfect robustness score for consistency alone conflates the property being measured. Counterexample: a strategy whose sole parameter is an integer threshold; identical across folds, but changing by one unit moves it outside a narrow liquidity window and removes all edge.

For the bootstrap interval: a five-trade bootstrap does not necessarily span zero by any mathematical property. Whether the interval spans zero depends on the distribution of those five outcomes. An algorithmic fallback — such as returning a fixed wide interval when sample size falls below a threshold — is a software convention, not a theorem. Even a positive small-sample interval is insufficient because the interval width is dominated by sample variance, not signal. A single lucky streak across five trades can produce a spuriously positive lower bound. Prospective evidence from additional out-of-sample trades is required before treating a positive interval as meaningful.

3. Provenance and Retrospective/Prospective Separation

Minimum lineage fields for each record: data_available_as_of (the timestamp of the latest data accessible at decision time), reconstruction_time (when the analysis was performed), issue_time (when the record was written or frozen), and evaluation_period_start. A retrospectively reconstructed brief cannot count as prospective prediction unless issue_time strictly precedes evaluation_period_start and data_available_as_of is bounded to exclude data from that period. All three timestamps must be present and independently verifiable. Without them, a retrospective analysis relabelled after observing outcomes is indistinguishable from a genuine forecast. Lineage fields also prevent accidental pooling: a validation query can filter on record_type IN ('prospective', 'paper', 'historical') and reject mixed joins.

Substituting forward-paper metrics into a historical validation structure is unsafe without explicit lineage. The proposed additional fields: record_type, source_mode (live-paper vs. historical-replay), fill_model (assumed vs. observed), and a parent_experiment_id that links back to the original frozen baseline. These prevent silent relabelling when results are aggregated.

4. Repository Ranking

Most useful now: Hypothesis. Property-based tests for session boundary logic, timezone transitions and OHLC fill ambiguity are cheap to write and catch invariant violations that example-based tests miss. These correctness properties must hold before any experiment record is trusted.

Second: exchange_calendars. Calendar semantics — half-days, delayed opens, overlapping sessions — are a known source of look-ahead errors and silent data misalignment. A thin wrapper that validates session timestamps against canonical exchange schedules is high-value and low-coupling.

Third: MLflow experiment structure (schema only, not full deployment). The record structure for capturing pre-session hypotheses and appended outcomes maps naturally onto MLflow's run/param/metric model. Using the schema as a design reference — without installing the full stack — gives a proven template without the dependency cost.

Defer: Optuna, VectorBT, PyPortfolioOpt and LEAN. These are useful only after the correctness and record infrastructure is stable, and each adds a substantial integration surface. The trial ledger should be a simple append-only file until the record format is validated.

5. Small Design with Acceptance Tests

Design: a SessionRecord dataclass with fields hypothesis (written before session), outcome (appended after), and the four lineage timestamps above. A validation function rejects records where issue_time >= evaluation_period_start or data_available_as_of overlaps the evaluation window.

Synthetic acceptance tests:
- A record with issue_time one second before evaluation_period_start and a data cutoff two days prior passes validation.
- A record with issue_time equal to evaluation_period_start is rejected with a provenance error.
- A record with data_available_as_of inside the evaluation window is rejected even if issue_time is valid.
- A bootstrap call on five trades with all positive outcomes returns a positive interval; a separate assertion checks that this interval is flagged as insufficient pending prospective evidence.
- A parameter stability check perturbs the sole threshold by one unit and asserts that the score changes, confirming the configuration-consistency/robustness distinction.

6. Remaining Disagreement and Next Step

Remaining disagreement: whether a small native record format can remain adequate as the trial ledger grows, or whether it will require a queryable store before the review cadence (every 10–20 days) becomes burdensome. Evidence that could settle this: run the 10-day review cycle manually for two periods and measure time spent on record lookup versus analysis. If lookup exceeds twenty percent of review time, adopt a lightweight store. Next step: write the SessionRecord schema and the five acceptance tests; run one synthetic review cycle before evaluating any external library.
