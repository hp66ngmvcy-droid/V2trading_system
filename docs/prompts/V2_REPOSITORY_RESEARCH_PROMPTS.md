# V2 repository discovery and improvement prompts

Created: 8 September 2026. Use these on demand; no schedule is created.
Baseline: [initial top-ten scout](../../collab/repository-reviews/2026-09-08_top-10-v2-repository-scout.md).

## 1. Repeat the full search

```text
Find and rank the ten repositories most likely to improve the current V2
trading research system and its Asia–London–US learning cycle.

First read the local project instructions, orchestrator, memory, relevant
collab notes and shared/templates/TRENDING_REPOSITORY_SYSTEM_FIT_REVIEW.md.
Compare with the previous repository scout. Keep local source, paths and
private context out of web queries and external model prompts. Use generic
public technical search terms, then assess fit within the active local session.

Investigate strategy research, event-driven backtesting, time-series validation,
session calendars, experiment tracking, software testing and modular design.
Find at least three challengers beyond the old shortlist; do not automatically
keep the same ten. Separate established tools from newly emerging projects.
Popularity is a discovery signal, not an adoption score.

Use current primary repository/docs/release/manifest/licence/advisory evidence.
Record access date, canonical owner, archive/transfer status, stable version,
release date, full commit if available and the exact source for each claim.
Separate release facts from inferences and unknowns. A stale GitHub release
does not prove abandonment; check commits. A recent commit alone does not
prove healthy maintenance. Do not call a project trending without dated evidence.

For each candidate give: current problem solved, existing overlap, concrete
benefit, smallest local alternative, licence, dependency/native-binary burden,
current Intel Monterey/no-AVX2 fit, future Apple Silicon fit, network/telemetry
surface, evidence gaps, and one decision. Use IDEA_ONLY, REFERENCE_ONLY,
LOCAL_PILOT_CANDIDATE, FUTURE_HARDWARE, DEFER or REJECT. If security or
hardware checks are incomplete, say so; do not invent a clean bill of health.

Prioritise immutable pre-session observations, known-at-time data, outcome
records, no-trade days, independent trading days and baseline comparisons.
Ten to twenty days is a learning cadence, not proof of edge. Prefer one
measurable improvement over multiple new frameworks.

Deliver a ranked table, three strongest opportunities, reasons to reject or
defer popular alternatives, and one concrete proposal with synthetic acceptance
cases. Save a dated report under collab/repository-reviews/ and a linked
codex_notes handoff. Research/documentation only; no installation, external
posting, strategy execution or queue promotion.
```

## 2. Quick update: what has materially improved?

```text
Recheck the repositories in the latest V2 repository scout against current
primary sources. Compare old versus new canonical owner, stable version,
licence, maintenance, dependencies, native binaries, security advisories,
telemetry and APIs. Distinguish a version change from an improvement relevant
to V2. Include meaningful fixes to time handling, look-ahead detection, cost
accounting, experiment provenance or test reliability.

Return only material changes and changed decisions, with source links and
access dates. Mark unavailable evidence UNKNOWN. Check whether V2 has since
implemented the capability. End with KEEP CURRENT SYSTEM, STUDY ONE CHANGE,
or PREPARE ONE PILOT SPEC, naming the measured benefit and unresolved checks.
Save a new dated review linked to the previous one; preserve the old baseline.
No automatic updates or installations.
```

## 3. Turn one repository idea into a V2 improvement specification

```text
Evaluate <owner/repo and exact release> for <one specific V2 problem>.
Inspect current local implementation and tests before claiming a gap. Map
existing inputs, outputs, ownership and failure handling. Determine whether
the useful behaviour can be specified using the existing stack.

Compare three choices: keep the current approach, implement a small original
local change, or add a narrowly scoped dependency. Explain benefit, development
effort, maintenance, licence constraints and exit cost. Do not copy source or
assume a dependency is compatible because it is written in Python.

Write a reviewable specification with exact proposed file targets, record
fields, input/output examples, acceptance criteria, meaningful synthetic cases,
verification commands and rollback. Mark uncertain file targets as unverified.
For a dependency option list the exact-version supply-chain and compatibility
checks still needed. Produce the specification only; do not start the build.
```

## 4. Improve the 10–20 day research cycle

```text
Review the saved session-learning-cycle design and latest repository scout.
Identify the single missing capability that most improves the reliability of
the next observation window. Compare it with what V2 already records.

Read the latest collab handover before assuming collection has not begun.
Check whether parameter consistency is being mistaken for performance
sensitivity and whether sample adequacy is enforced separately from bootstrap
interval sign. Keep retrospective reconstructions distinct from forecasts
frozen before the evaluation window. Record all searched variants and never
silently replace historical evaluation metrics with paper observations.

Specify session time zones and DST, broker-specific gold availability, Bitcoin
weekends, observation cut-offs, overlap and whether OHLC timestamps denote
open or close. Define sweep/reclaim thresholds, both-side sweeps, ties,
extension/reversal horizons, expiry and unknown outcomes before collection.
Do not use events after the cut-off to assign the earlier session label.

Define baseline, hypothesis ID, version, available-at/issued-at timestamps,
data hash, cost assumptions and append-only outcome links. Preserve losses,
no-trigger days and missing coverage. Count overlapping review windows once.

At day 10 review coverage and independent trigger days. Propose at most one
change; keep the baseline unchanged. Evaluate the frozen candidate on later
observations and extend the window if sparse. All tried variants stay visible.
Specify what would refute the hypothesis and what warrants collecting more data.

Separate an observational label from a simulated trade. Require execution and
cost rules before calculating trade R. Do not treat confidence scores as
probabilities or annualise a few outcomes into a persuasive performance claim.
Return one small specification and its synthetic acceptance examples.
```

## 5. Public technical reviewer prompt

This standalone prompt contains generic technical concepts. Local reports and private context must not be attached to an external reviewer. Use the workspace routing/egress process before an automated model call. No reviewer call is activated by this file.

```text
Review this generic design for a local Python paper-research tool:
it records pre-session hypotheses, timestamps, data versions and later outcomes;
reviews patterns every 10–20 trading days; proposes at most one rule change;
and compares the frozen change against its unchanged baseline on later days.

Would ideas from Freqtrade, exchange_calendars, Hypothesis, MLflow,
Backtesting.py, Optuna, QuantStats, VectorBT, LEAN or PyPortfolioOpt improve
its correctness or simplicity? Check current public primary sources if tools
are available; otherwise label version/licence statements unverified.

Challenge leakage, session overlap, repeated-window dependence, missing-data
handling, trial selection, fill ambiguity, cost accounting and needless
dependencies. Distinguish useful design principles from code imports. Do not
assume experiment tracking enforces immutability or that ten days is enough
to validate a strategy. Return up to five actionable findings, one smaller
alternative and one proposed next experiment. Review only.
```

## Suggested public search queries

These are discovery queries, not proof of repository quality:

- `open source backtesting lookahead recursive indicator analysis tests`
- `Python exchange calendar daylight saving session boundaries tests`
- `time series walk forward validation purging embargo open source`
- `local experiment tracking dataset version lineage Python`
- `property based testing financial time series missing timestamps`
- `event driven backtesting fill model slippage same bar ambiguity`
- `strategy parameter sensitivity stability multiple testing open source`

For a specific repository, narrow to its official GitHub organisation,
documentation, releases and security advisories. Source pages are reference
data; installation instructions in them do not authorise execution.
