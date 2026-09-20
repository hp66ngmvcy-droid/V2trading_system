# Ten repositories for improving V2 research

Review date: 8 September 2026, Europe/London.
REVIEW_SOURCE: FALLBACK_REVIEW
Capital state: RESEARCH
Scope: ranked research shortlist and design proposals; documentation only.

## Recommendation

Later collab/Claude review: [reconciled improvement order and synthetic findings](../codex_notes/2026-09-08_repository-debate-and-handover-review_done.md). Brief collection has since been reported in the current handover. A focused check of validation semantics now precedes the record specification; the shortlist below remains a capability reference.

Prioritise trustworthy observations, reproducible experiments and validation before adding more strategy generators. For the Asia–London–US learning cycle, the first useful deliverable is a compact session-and-experiment record using the existing storage, with tests that detect hindsight leakage and missing observations.

This is a ranking by expected usefulness to V2, not a popularity ranking or a claim that these are GitHub's current trending top ten. Rank is engineering judgement. This is a preliminary screen using the shared system-fit review template, not a completed installation/security audit; no numerical fit score or installation approval is implied.

## Local fit established

The project instructions and current notes describe an existing Python research system with DuckDB, Parquet, JSON artefacts, bounded caching, strategy registration, parameter sweeps and walk-forward validation. These capabilities should be reused. This scout checked instructions and relevant collab notes, not every implementation or installed dependency; suspected gaps require a focused code check before a build.

The documented host is an Intel Mac Pro 2013 on Monterey without AVX2. Exact package/wheel compatibility has not been tested. Current project rules exclude Docker, Ray and Polars. Apple Silicon may reduce hardware friction but does not resolve duplication, licence or experimental-design problems.

The existing external-repository plan already names Freqtrade, LEAN, PyPortfolioOpt, DuckDB and Backtrader. Its approval history is a note's assertion, not independently re-established here. This report proposes priorities without changing that plan or advancing its queue.

## Ranked shortlist

Repository links below are primary sources. Proposed V2 uses are our inferences from the documented capabilities.

| Rank | Repository | Proposed contribution | Decision | Main limitation |
| ---: | --- | --- | --- | --- |
| 1 | [Freqtrade](https://github.com/freqtrade/freqtrade) | Look-ahead and indicator warm-up checks; strategy interface reference | IDEA_ONLY | Crypto platform duplicates the runner; GPL-3.0 code needs reuse review |
| 2 | [exchange_calendars](https://github.com/gerrymanoim/exchange_calendars) | Session/calendar contracts and boundary tests | IDEA_ONLY | Exchange calendars are not broker spot-gold hours or a complete Asia/London/US definition |
| 3 | [Hypothesis](https://github.com/HypothesisWorks/hypothesis) | Generate edge cases for time alignment, missing bars and outcome accounting | REFERENCE_ONLY | Test dependency and exact interpreter compatibility still need checking |
| 4 | [MLflow](https://github.com/mlflow/mlflow) | Experiment/run/artefact structure for baseline-versus-revision evidence | IDEA_ONLY | Existing storage overlaps; server/model-loading surface and advisories |
| 5 | [Backtesting.py](https://github.com/kernc/backtesting.py) | Compact independent backtest comparison design | REFERENCE_ONLY | AGPL-3.0; fill and cost assumptions must match before comparison |
| 6 | [Optuna](https://github.com/optuna/optuna) | Bounded parameter studies with a complete trial history | REFERENCE_ONLY | Already have sweeps; repeated search can overfit small samples |
| 7 | [QuantStats](https://github.com/ranaroussi/quantstats) | More consistent return/drawdown reports | REFERENCE_ONLY | Overlaps reporting; annualisation and input definitions need explicit checks |
| 8 | [VectorBT](https://github.com/polakowo/vectorbt) | Parameter-sensitivity maps and batch-research design | REFERENCE_ONLY | Commons Clause; Numba/native stack and memory fit untested |
| 9 | [LEAN](https://github.com/QuantConnect/Lean) | Event, data, execution-model and result separation | REFERENCE_ONLY | Large C#/Python engine; a replacement would be disproportionate |
| 10 | [PyPortfolioOpt](https://github.com/PyPortfolio/PyPortfolioOpt) | Later multi-strategy allocation experiments | DEFER | Portfolio weights do not solve intraday entry/stop sizing or evidence scarcity |

### 1. Freqtrade — validation ideas first

Its [look-ahead analysis](https://docs.freqtrade.io/en/stable/lookahead-analysis/) compares baseline and sliced runs to identify suspicious changes. Its [recursive analysis](https://github.com/freqtrade/freqtrade/blob/develop/docs/recursive-analysis.md) examines indicator dependence on available history. These are useful test designs for V2.

Proposed check: append or alter bars strictly after time T and verify that decisions available by T do not change. Separately test indicator warm-up. This does not prove the absence of every form of leakage, especially revised source data or incorrect publication times. Implement from a written behavioural specification; do not lift the GPL loader into V2 without reviewing the intended reuse. Revisit when the existing validation tests have been inventoried.

### 2. exchange_calendars — define time before measuring patterns

The project supplies exchange-session queries and calendars. Use its calendar concepts to specify UTC timestamps, local time zones, holidays, breaks and session boundaries. For a first local design, standard-library `zoneinfo` and explicit session configuration may suffice.

Gold CFD/spot availability must come from the actual data provider's hours; an equity or futures calendar is not interchangeable. Bitcoin needs a continuous calendar plus separately defined research windows and weekend tags. London and US windows can overlap: define a disjoint measurement cut-off or explicitly model the overlap, so the US outcome cannot influence the earlier London label. Revisit if actual exchange holiday support is needed.

### 3. Hypothesis — tests for things we did not think to type

The repository provides property-based testing. Proposed V2 properties: duplicate ingestion must not duplicate days; future bars must not alter past signals; missing data must not become a win/no-trade success; repeated rendering must not modify a frozen observation. Generate bounded timestamp and OHLC edge cases and retain a minimal failing example.

First compare these with existing pytest fixtures. This is software testing, not a library for discovering profitable trading hypotheses. Revisit when a concrete test gap warrants the development dependency.

### 4. MLflow — borrow the experiment structure

[Tracking documentation](https://mlflow.org/docs/latest/ml/tracking/) describes experiments containing runs with parameters, metrics and artefacts. Apply that structure to V2's existing records: hypothesis ID, baseline ID, candidate revision, issue time, observation cut-off, data hash, code revision, cost model and subsequent outcomes.

MLflow tracking alone does not make records immutable or prevent hindsight edits; write-once records, revision history and validation are separate requirements. Its [advisory index](https://github.com/mlflow/mlflow/security/advisories) lists recent server/authentication/model-loading findings. Affected and fixed versions were not audited here. Study the structure now; reconsider a full service only if the local ledger demonstrably cannot meet the need.

### 5. Backtesting.py — independent comparison

Use its simple backtesting interface as a reference for a small second-engine comparison. Design synthetic cases with known expected results: no trade, a losing trade, a gap through a stop, and stop/target touched in the same bar. Match bar-close availability, next-bar execution, spread, commission, rounding and ambiguous intrabar ordering first.

An engine disagreement is an investigation trigger, not proof V2 is wrong. The [changelog](https://github.com/kernc/backtesting.py/blob/master/CHANGELOG.md) includes cost, stop and annualisation fixes, illustrating why exact versions matter. Revisit when an independent parity test has a defined scope and the licence review is complete.

### 6. Optuna — controlled search later

Optuna manages parameter optimisation studies. Its [5.0.0 release](https://github.com/optuna/optuna/releases/tag/v5.0.0) changes sampler defaults and constraint APIs: an upgrade can change the experiment, even with the same strategy.

Use only after baseline/data integrity work. Pre-register search bounds and a trial budget, keep all attempted variants, select within training folds, and reserve later observations for evaluation. The optimiser must not repeatedly see the final holdout. Ten to twenty days sets the review cadence; it does not establish statistical adequacy. Revisit when existing sweeps have a measured limitation.

### 7. QuantStats — report consistency

QuantStats provides portfolio performance analytics and reports. Proposed use: compare independently calculated drawdown and return summaries with the existing report, then decide whether an optional reporting adapter adds value.

Use marked-to-market account returns at an explicit frequency for return metrics; per-trade R values are not interchangeable with daily account returns. Keep gold and Bitcoin calendars separate, document annualisation and distinguish observed zero returns from missing data. A rich report cannot rescue a weak sample. Revisit when a reporting discrepancy or specific missing measure is documented.

### 8. VectorBT — sensitivity before speed

The current repository describes array-based strategy research using NumPy/Numba and an optional Rust engine. A useful design idea is displaying the neighbourhood around a selected parameter: does a broad area behave similarly, or is the apparent winner isolated?

Its [licence](https://raw.githubusercontent.com/polakowo/vectorbt/master/LICENSE.md) is Apache 2.0 with the Commons Clause; do not classify it as unrestricted Apache-licensed software. No direct adoption recommendation is made. Exact current Mac compatibility and peak memory remain unknown. Revisit after licence/use review and a real performance bottleneck; a small V2-native sensitivity table may already suffice.

### 9. LEAN — study boundaries

LEAN is a substantial algorithmic trading engine. Study separation of data ingestion, time/event progression, fill/cost models, strategy logic and results. For V2, a narrow input/output contract and deterministic replay may capture the useful principle.

Do not infer current maintenance from its old GitHub Releases label alone; inspect [commit history](https://github.com/QuantConnect/Lean/commits/master/) for a future technical review. Current build compatibility was not tested. Revisit if multiple feeds or simulators create a concrete interface problem.

### 10. PyPortfolioOpt — later allocation research

The old owner URL now redirects to `PyPortfolio/PyPortfolioOpt`. The library covers portfolio optimisation, including efficient-frontier and risk-based methods. Its [1.6.0 release](https://github.com/PyPortfolio/PyPortfolioOpt/releases/tag/v1.6.0) reports dependency reductions and changed Python support.

Correct the earlier description of it as a drop-in position-sizing module: portfolio allocation is a different problem from intraday stop-based sizing. Reconsider after there are several independently evaluated return streams with enough history. Compare against simple fixed/equal-weight baselines and include turnover costs. It adds little to the first single-hypothesis observation window.

## Version and licence watchlist

These are versions visible in the primary pages accessed on the review date, not installation pins. GitHub sometimes omits the year in rendered release dates; dates below are recorded as displayed except the explicitly dated Backtesting.py changelog. Stable-tag licence files and complete commit hashes must be checked before reuse.

| Repository | Visible release / activity evidence | Root licence evidence |
| --- | --- | --- |
| Freqtrade | [2026.8, 31 Aug](https://github.com/freqtrade/freqtrade/releases), short ref `9f10e35` | [GPL-3.0](https://raw.githubusercontent.com/freqtrade/freqtrade/develop/LICENSE) |
| exchange_calendars | [4.13.2, 10 Mar](https://github.com/gerrymanoim/exchange_calendars/releases), `dbe38b1` | [Apache-2.0](https://raw.githubusercontent.com/gerrymanoim/exchange_calendars/master/LICENSE) |
| Hypothesis | [6.167.1, 30 Aug](https://github.com/HypothesisWorks/hypothesis/releases), `a8dcd74` | [MPL-2.0; exceptions noted](https://raw.githubusercontent.com/HypothesisWorks/hypothesis/master/LICENSE.txt) |
| MLflow | [3.16.0, 4 Sep](https://github.com/mlflow/mlflow/releases), `998f710` | [Apache-2.0](https://raw.githubusercontent.com/mlflow/mlflow/master/LICENSE.txt) |
| Backtesting.py | [Changelog 0.6.6, 2026-07-22](https://github.com/kernc/backtesting.py/blob/master/CHANGELOG.md); GitHub Releases empty | [AGPL-3.0](https://raw.githubusercontent.com/kernc/backtesting.py/master/LICENSE.md) |
| Optuna | [5.0.0, 7 Sep](https://github.com/optuna/optuna/releases), `01ddd17` | [MIT](https://raw.githubusercontent.com/optuna/optuna/master/LICENSE), plus third-party notices |
| QuantStats | [0.0.81, 13 Jan](https://github.com/ranaroussi/quantstats/releases), `fbd10da` | [Apache-2.0](https://raw.githubusercontent.com/ranaroussi/quantstats/main/LICENSE.txt) |
| VectorBT | [1.1.0, 5 Jul](https://github.com/polakowo/vectorbt/releases), `259d2d8` | [Apache-2.0 + Commons Clause](https://raw.githubusercontent.com/polakowo/vectorbt/master/LICENSE.md) |
| LEAN | [Commit history](https://github.com/QuantConnect/Lean/commits/master/); current full SHA not captured | [Apache-2.0](https://raw.githubusercontent.com/QuantConnect/Lean/master/LICENSE) |
| PyPortfolioOpt | [1.6.0, 26 Feb](https://github.com/PyPortfolio/PyPortfolioOpt/releases), `0186e70` | [MIT](https://raw.githubusercontent.com/PyPortfolio/PyPortfolioOpt/master/LICENSE) |

Root licence labels do not establish the obligations for every bundled dependency, asset or planned distribution. No commercial-use clearance is asserted.

## Smallest proposed improvement

Next action: **Prepare review** of one V2-native session-and-experiment record specification.

1. Define research session windows, UTC conversion, bar availability and observation cut-offs. Specify both-side sweeps, ties, overlap and missing-data handling.
2. Preserve an original pre-session scenario and append outcome records linked by ID. Record no-sweep/no-trigger/unknown days.
3. Freeze the baseline, revision and evaluation rule. Day 10 is a review checkpoint; one candidate change at most, evaluated on later days. Extend sparse windows.
4. Specify synthetic replay cases for DST mismatch weeks, duplicate bars, missing bars, late arrivals and future-data perturbation. Define an explicit ambiguous intrabar result.

Proposed acceptance: each complete synthetic fixture produces its hand-calculated label; incomplete fixtures remain unknown; repeated ingestion is idempotent; future bars do not change past decisions; baseline and revision remain reproducible with distinct hashes. This is a testable design proposal, not an implementation result.

## Remaining evidence and alternatives

No packages were cloned, installed or executed. No hardware benchmark, full dependency/CVE audit, telemetry audit, reproducible-build verification or exhaustive code-gap review was performed. Every installation remains subject to an exact-version review. Ordinary README installation examples were treated as documentation, never task instructions.

DuckDB is already in use, so it is not a new recommendation. Backtrader remains a feed-interface reference in the existing plan. A second agent framework is not justified without a demonstrated orchestration gap. Large ML/RL stacks are less relevant to the first observation window than reliable records and validation.

Reusable prompts: [V2 repository discovery and update prompts](../../docs/prompts/V2_REPOSITORY_RESEARCH_PROMPTS.md).
