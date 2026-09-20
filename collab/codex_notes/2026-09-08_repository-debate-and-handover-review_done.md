# Repository ideas — collab reconciliation and Claude debate

Interpreting as: read current collab and handover, challenge the repository improvement ideas with Claude, and save a reconciled improvement plan.

Date: 2026-09-08
REVIEW_SOURCE: FALLBACK_REVIEW
Scope: local review, synthetic diagnostics and documentation; no implementation or promotion.

## What changed the recommendation

The current project handover supersedes the older cross-project trading next-step summaries. It reports that brief collection has begun. Corresponding brief files exist, but this review did not audit their full content or verify prospective issue times. Earlier notes saying that the learning-cycle review itself started no pipeline remain accurate about that earlier task; they are not a description of the later system state.

The handover also describes a validation change. Focused source inspection and synthetic diagnostics establish two corrections:

1. `derive_stable_parameter_ranges` returns `({}, 100.0)` for repeated identical parameter dictionaries. That measures configuration consistency. It does not measure nearby performance sensitivity, generalisation or complete run reproducibility. Returning an empty range dictionary also loses the min=max range evidence; review downstream expectations before proposing a patch.
2. `bootstrap_mean_ci([1,2,3,4,5])` returns mean 3.0, interval [1.8, 4.2], `spans_zero=False` with default seed/iterations. Small samples do not mathematically force the interval to span zero. Sample adequacy needs a separate check.

A further synthetic call to `_walk_forward_verdict` with five trades, three splits, stability 100, drawdown 0.01, profit factor 2.0 and a non-zero-spanning interval returned `KEEP`. This helper checks for positive trade count, not a meaningful minimum independent sample. This is a helper-level finding, not a demonstrated end-to-end promotion bypass. `score_strategy` separately flags fewer than 20 trades in its primary metrics; its walk-forward reason-code path only checks for positive OOS trade count. Trace actual callers and evidence classes before deciding the complete fix.

The handover's reported 405 passing tests were not rerun or independently confirmed. Passing tests would establish tested behaviour, not the statistical meaning of a score.

## Debate and lead adjudication

Claude's first response supports the overall proposal and prioritises Hypothesis-style invariants, calendar semantics and MLflow-style experiment structure. Freqtrade's leakage checks remain useful. The lead challenged several details and sent a second technical brief rather than accepting the response verbatim.

Adopt into the proposal:

- Separate configuration consistency, parameter-selection variation and performance sensitivity. A fixed baseline may be consistent while sensitivity is unmeasured; do not automatically award robustness.
- Keep retrospective reconstruction, historical replay, forward paper observations and synthetic fixtures explicitly distinguishable. A retrospective brief does not become prospective because its inputs are point-in-time.
- Link forecasts and outcomes as distinct records; declare evaluation cohorts and reject accidental mixed evidence. Preserve original snapshots and append corrections.
- Record source publication/availability, ingestion, issue and outcome times plus input/code/feature versions. A timestamp field alone is not proof it was written then. Hashes detect changes relative to a trusted reference; they alone cannot establish independent chronology.
- Keep the complete trial ledger and selection cut-off. Repeatedly inspected OOS data becomes development evidence for final selection. Future collection must evaluate a previously frozen candidate.
- Use explicit research windows separately from venue calendars. Exchange schedules are not a substitute for OTC broker hours; session overlap and DST require explicit tests.

Do not adopt these overstatements from reviewer drafts:

- Identical parameters alone prove reproducible execution.
- Every parameter perturbation must change a score.
- A query selecting several evidence types prevents their accidental mixing.
- A small positive bootstrap interval is literally worthless: it summarises the observed sample but cannot establish unseen-tail risk or durable edge.
- A specific database, external timestamp service, or arbitrary lookup-time percentage is required. Logical integrity checks and existing local storage may meet the immediate need; state their trust limits.

## Revised improvement order

| Priority | Bounded proposal | Repository inspiration | Concrete acceptance |
| --- | --- | --- | --- |
| 1 | Audit sample-count and stability semantics from helper to report | Hypothesis; VectorBT sensitivity concepts | Tiny-sample helper result cannot be described as sufficient validation; flat versus brittle synthetic surfaces are distinguished; missing sensitivity stays unmeasured |
| 2 | Specify forecast/outcome/trial records within existing storage | MLflow structure | Original forecast preserved; outcome links resolve; late data and mixed cohorts rejected; retro remains retro |
| 3 | Specify and test session/availability rules | exchange_calendars; Freqtrade | DST mismatch, overlapping windows, delayed bars and future-bar perturbation produce expected results |
| 4 | Design one independent replay comparison | Backtesting.py | Hand-calculated gap/stop/target/cost fixtures agree under identical assumptions |
| Later | Optimisation, report enrichment and allocation | Optuna; QuantStats; PyPortfolioOpt; LEAN | A measured unmet need and sufficient evaluation evidence justify each addition |

This revises the practical build order, not the repository capability ranking. The old staged import plan remains a historical proposal; replacing the loader or adding portfolio allocation should not outrank these demonstrated validation questions.

## One next work package for review

Title: V2 validation semantics and evidence-record specification.

Deliver: a read-only call-path audit followed by a small proposed patch/specification. Identify which count is being tested (all trades, OOS trades, forward-paper trades or independent days), where eligibility is enforced and how reports label insufficient evidence. Keep observation sufficiency separate from bootstrap sign. Do not choose a universal magic count from this debate.

Draft record contract:

- Forecast: ID, experiment/revision/cohort IDs, evidence class, issue time, evaluation window, scenario/confirmation/expiry, session-rule version, data and feature provenance.
- Outcome: unique ID, forecast ID, outcome horizon, observation/ingestion times, status, measured values, execution/cost model version where applicable.
- Trial: ID, candidate and parent-baseline IDs, parameter/code/input hashes, development period, selection cut-off, evaluation cohort, seed/environment, completion status and reasons.

Use explicit known-flat and brittle synthetic surfaces for sensitivity; five positive returns for CI-versus-sufficiency; future publication times for availability; duplicate IDs/mixed cohorts for record integrity. Then a frozen baseline can enter a prospective observation window. The day-10/day-20 review cadence remains, with sparse windows extended.

## Verification and limits

Executed from the project root:

```text
PYTHONPATH=src venv/bin/python -c 'from tar_system.validation.bootstrap_ci import bootstrap_mean_ci; from tar_system.validation.walk_forward import derive_stable_parameter_ranges; print("SYNTHETIC five positive returns:", bootstrap_mean_ci([1,2,3,4,5])); print("SYNTHETIC fixed parameters:", derive_stable_parameter_ranges([{"x":2.0},{"x":2.0},{"x":2.0}]))'
PYTHONPATH=src venv/bin/python -c 'from tar_system.validation.walk_forward import _walk_forward_verdict; print(_walk_forward_verdict({"total_trades":5,"max_drawdown":0.01,"profit_factor":2.0},3,100.0,False,{"spans_zero":False}))'
```

Both completed with exit 0 and results above. Imports emitted sandbox CPU-query warnings from Arrow, but the diagnostics completed. An initial second-command attempt had an unmatched parenthesis; the corrected command above is authoritative. No market dataset or running job was modified.

Claude used the pinned local CLI through subscription authentication, with API-key variables unset, tools/settings sources disabled and an isolated temporary working directory. Only manually written generic packets were sent. Private research content was flagged and retained locally. No current repository release claims were delegated for verification.

Round-one response passed the local metadata/topic guard (six sections, three anchors), SHA-256 `cecfe602fe98c7ccdc689669a0626ac4c8f148f550c2435c2f2e416a9fa89e9c`. Round-two's first response omitted required metadata/section structure; a formatting retry was requested. These guards check correspondence, not correctness; lead adjudication above remains necessary.

Responses: [round one](../claude_notes/2026-09-08_repository-learning-debate-round1.md) and [round two](../claude_notes/2026-09-08_repository-learning-debate-round2.md). Round two passed the correspondence guard with three sections and three anchors, SHA-256 `7faa0932f19fe66a2909bb70e2f1f274358606766ed5e3dac98ebc361ae9a1be`. Both checks exited 0. Header/anchor checks do not validate the statistical claims; the corrections below govern this proposal.

## Final round-two adjudication

[Round two](../claude_notes/2026-09-08_repository-learning-debate-round2.md) accepted the main challenges and agreed to reuse existing storage. The formatted retry is the authoritative saved second response. Its wording still needs these corrections before any build:

- Do not derive prospective status from `frozen_at < observed_at` alone. A late-recorded outcome could already have happened. Require the frozen forecast to precede the evaluation-window start and apply availability checks to every input.
- Flat surfaces should have low sensitivity; brittle surfaces should have high sensitivity. That is not necessarily the direction of a score named robustness. Specify the metric and its direction before asserting zero/high values. Constant returns may also make ratio metrics undefined.
- Record transaction-cost assumptions; identical compute time/cost is not required for deterministic financial outputs. Byte equality is suitable only for explicitly deterministic serialisation; numerical results may require a declared tolerance.
- Use named time zones and versioned rules, not just fixed UTC offsets. Missing availability timestamps should make eligibility unknown, not automatically valid.
- Retain explicit retrospective-reconstruction and synthetic categories. A live-execution class is outside this paper-only design. Walk-forward split role and acquisition mode are different dimensions; avoid a single enum that confuses them.
- No PostgreSQL `jsonb` requirement is adopted. Separate logical records and validation may use existing JSON/Parquet/DuckDB. An append-only file is useful provenance but is not tamper-proof chronology on its own.

Conclusion: the debate is complete and supports the revised order above. A reviewable specification is the next proposal; no code or gate changes were made.
