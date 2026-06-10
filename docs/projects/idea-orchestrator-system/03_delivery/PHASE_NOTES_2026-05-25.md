# Phase Notes - 2026-05-25

## Phase 1 - Online Helper Reinstated

Status: complete

- Restored the Exa helper path.
- Installed `exa-py` into the project venv.
- Added parallel topic search.
- Added multi-agent search lenses for risk, performance, and robustness.

Audit:

- `pip check`: pass
- focused tests: pass

Blocker:

- `EXA_API_KEY` is not set, so live online search remains disabled.

## Phase 2 - Source Quality And Saved Scout Output

Status: complete

- Added source quality scoring.
- Added strict/balanced/off source filters.
- Added saved scout JSON output.
- Added CLI controls for result count, workers, source quality, output path, and hypothesis generation.

Audit:

- focused tests: pass
- compile check: pass

## Phase 3 - Hypothesis Notes For Backtester Review

Status: complete

- Added structured markdown hypothesis note generation.
- Notes are written to `ideas/research_queue/` by default.
- Notes include parseable `Entry`, `Exit`, `Filters`, `Risk`, and `Assumptions` lines.
- Notes are compatible with the existing `add-strategy-idea --file ...` candidate path.

Audit:

- focused tests: pass
- security warning fixed by replacing SHA1 filename digests with SHA256.

## Phase 4 - UI Online Scout Path

Status: complete

- Added `/api/research/scout`.
- Added `ONLINE_RESEARCH` status to the UI snapshot.
- Added an online scout quick action in the dashboard.
- UI action is disabled until `EXA_API_KEY` is available.

Audit:

- web UI integration tests: pass
- `security-check`: pass
- `run-local-construction-audit --fail-on-findings`: pass, zero findings

## Next Phase - Daily Idea Loop

Goal:

- Create a daily local review command that records the state of online scout readiness, hypothesis queues, candidate queues, and next review actions.
- It must stay paper-only.
- It must not auto-promote, live trade, or create strategy code.
- Online scout should run only when explicitly requested and when `EXA_API_KEY` is set.

Status: complete

- Added `run-daily-idea-loop`.
- Wrote the first daily review files under `idea_reviews/`.
- Added queue, online readiness, and guardrail summaries.
- Made queue health non-blocking so daily notes can still be written if the queue database is unavailable.

Audit:

- focused tests: pass
- `pip check`: pass
- `security-check`: pass
- construction audit: pass, zero findings

## Next Phase - Controlled Online Key Use

When to add the key:

- Add `EXA_API_KEY` after local tests, security check, construction audit, and daily idea loop all pass.
- This condition is currently met.

How to add the key:

```text
EXA_API_KEY=your_key_here
```

Add that line to `.env`. Do not commit `.env`.

First controlled online run:

```bash
PYTHONPATH=src venv/bin/python -m tar_system.cli run-daily-idea-loop \
  --run-online \
  --online-query "gold intraday momentum volatility filter walk forward"
```

Token/call efficiency rules:

- Use one focused query at a time.
- Default to `--num-results 3`.
- Default to `--source-quality strict`.
- Use cache unless a fresh search is explicitly needed.
- Save results first, then generate hypotheses from saved results.
- Online sources become notes in `ideas/research_queue/`; they do not become strategy code.

## Next Phase - Hypothesis Review Gate

Goal:

- Review extracted online hypothesis notes before candidate conversion.
- Separate ready, needs-rule-translation, and reject/archive items.
- Keep human approval in control.

Status: complete

- Added `review-hypotheses`.
- Review output writes to `idea_reviews/hypothesis_review_YYYY-MM-DD.md`.
- The command does not move notes, create strategy code, or promote candidates.
- Ran the first review against `ideas/research_queue/`.
- Reviewed 5 notes: 0 ready, 5 need rule translation, 0 rejected.

Default command:

```bash
PYTHONPATH=src venv/bin/python -m tar_system.cli review-hypotheses
```

Audit:

- focused tests: pass
- review artifact written: `idea_reviews/hypothesis_review_2026-05-25.md`

Next step:

- Open the best high-quality source note and translate it into exact Entry, Exit,
  Filters, Risk, and Assumptions before using `add-strategy-idea`.

## Next Phase - Repeatable Phase Gate Loop

Goal:

- Create a reusable loop for every main stage.
- Each stage must run tests, compile checks, dependency checks, security checks,
  and construction audit before moving on.
- Each stage must write a review artifact.

Status: complete

- Added `run-phase-gate`.
- Reports write to `idea_reviews/phase_gates/`.
- The command exits non-zero if any gate fails.

Default command:

```bash
PYTHONPATH=src venv/bin/python -m tar_system.cli run-phase-gate \
  --phase-name "phase name" \
  --tests tests/test_relevant_file.py
```

## Next Phase - First Rule Translation Candidate

Goal:

- Translate the best high-quality source into an exact paper-only backtest
  candidate packet.

Status: complete

- Added `ideas/backtest_candidates/currency-cross-sectional-momentum-20260525.md`.
- The candidate is multi-asset, monthly, paper-only, cost-sensitive, and blocked
  from live trading or MT5 export.
- It is not strategy code.

Review:

- This is a medium-horizon cross-sectional FX hypothesis.
- It should use D1 data if available, H1 only as a proxy.
- It should not start with M15 because costs and noise would likely swamp the
  source hypothesis.

Next step:

- Check data readiness for the required FX basket before any backtest work.

## Next Phase - Currency Basket Data Readiness

Goal:

- Check whether the translated cross-sectional currency momentum candidate has
  enough local data before any backtest work.

Status: complete

- Added `check-data-readiness`.
- Added MT5 `<DATE>` and `<TIME>` timestamp support.
- Ran readiness for `EURUSD,GBPUSD,AUDUSD,USDJPY,USDCAD` on `D1,H1`.

Review:

- D1 files are missing for all five symbols.
- H1 files are ready for all five symbols.
- H1 history is about 65 months, enough for a proxy test.
- The candidate must be treated as an H1 proxy, not a direct daily-paper match.

Artifacts:

- `reports/data_readiness/20260525T114825Z_data_readiness.md`
- `reports/data_readiness/20260525T114825Z_data_readiness.json`

Next step:

- Build a paper-only multi-asset H1 proxy backtest packet for this candidate.

## Next Phase - Currency Momentum H1 Proxy Backtest

Goal:

- Run a paper-only H1 proxy test for the translated cross-sectional currency
  momentum candidate using the five ready FX symbols.

Status: complete

- Added `run-currency-momentum-proxy`.
- Ran the H1 proxy test on `EURUSD,GBPUSD,AUDUSD,USDJPY,USDCAD`.
- Used 12-month lookback, skipped most recent month, and applied 2 bps cost.

Result:

- Months tested: 50
- Cumulative return: -10.1765%
- Annualized return: -2.5429%
- Sharpe: -0.0668
- Max drawdown: 39.2735%
- Verdict: KILL
- Reason: NEGATIVE_AFTER_COSTS

Artifacts:

- `reports/currency_momentum_proxy/20260525T202256Z_currency_momentum_proxy.md`
- `reports/currency_momentum_proxy/20260525T202256Z_currency_momentum_proxy.json`

Review:

- The H1 proxy does not support promoting this candidate.
- The result is not a final academic replication because D1 data is missing.
- Keep the source note for research history, but do not move this candidate to
  strategy code or MT5 export.

Next step:

- Mark this candidate as tested/rejected or archive it after operator review.
- Move to the next high-quality hypothesis source only after this result is
  acknowledged.

## Next Phase - Candidate Closure And Second Source Translation

Goal:

- Close the failed currency momentum candidate cleanly.
- Translate the next high-quality source into a constrained, paper-only
  backtest candidate.

Status: complete

- Updated `ideas/backtest_candidates/currency-cross-sectional-momentum-20260525.md`
  to `tested_rejected`.
- Added rejection record:
  `ideas/rejected/currency-cross-sectional-momentum-20260525.md`.
- Added second candidate:
  `ideas/backtest_candidates/ga-optimised-trend-forex-20260525.md`.

Review:

- The first source is closed after a failed H1 proxy test.
- The second source should be treated as bounded parameter-search governance,
  not permission to run an unconstrained genetic algorithm.
- Start with GBPUSD H1, then EURUSD H1.

Next step:

- Check data readiness for GBPUSD H1 and EURUSD H1.
- Run bounded trend parameter tests only if readiness passes.

## Next Phase - GA Trend Data Readiness

Goal:

- Confirm that the second translated source has enough local H1 data for a
  bounded first-pass proxy test.

Status: complete

- Ran readiness for `GBPUSD,EURUSD` on `H1`.
- GBPUSD H1 ready: 33,958 rows from 2020-11-16 to 2026-05-01.
- EURUSD H1 ready: 33,742 rows from 2020-09-28 to 2026-02-27.

Artifacts:

- `reports/data_readiness/20260525T204253Z_data_readiness.md`
- `reports/data_readiness/20260525T204253Z_data_readiness.json`

Review:

- Both pairs have about 65 months of H1 data.
- It is valid to run a local H1 proxy.
- This remains a proxy, not a live strategy or an academic replication.

## Next Phase - Bounded Trend Proxy

Goal:

- Test the second translated source as a bounded, paper-only EMA trend proxy
  before any deeper implementation.

Status: complete

- Added `run-bounded-trend-proxy`.
- Tested GBPUSD and EURUSD H1.
- Used fast EMA values 10, 20, 50 and slow EMA values 50, 100, 200.
- Applied a 2 bps cost per position change.

Result:

- Best row: EURUSD EMA 50/200.
- Trades: 198
- Cumulative return: -0.5798%
- Sharpe: 0.0245
- Max drawdown: 13.9139%
- Verdict: KILL
- Reason: NEGATIVE_AFTER_COSTS

Artifacts:

- `reports/bounded_trend_proxy/20260525T204934Z_bounded_trend_proxy.md`
- `reports/bounded_trend_proxy/20260525T204934Z_bounded_trend_proxy.json`

Review:

- Every bounded EMA pair failed after costs.
- The source is useful for process design, especially bounded tuning and cost
  gates, but this strategy expression is not useful enough to implement.
- Marked the candidate as `tested_rejected`.
- Added rejection record:
  `ideas/rejected/ga-optimised-trend-forex-20260525.md`.

Next step:

- Run the phase gate audit for the bounded trend proxy phase.
- Then select the next online hypothesis only if it has exact rules or can be
  translated without inventing signals.

Audit:

- Phase gate: pass
- Focused tests: 7 passed
- `pip check`: pass
- `security-check`: pass
- construction audit: pass, zero findings
- Gate artifact:
  `idea_reviews/phase_gates/20260525T205337Z_bounded-trend-proxy-for-ga-source.md`

## Next Phase - Candidate Selection Rule

Goal:

- Prevent weak online notes from becoming strategy work.

Status: queued

- Select the next source only if it has explicit tradable rules or a clear
  mapping to existing V2 strategy families.
- Prefer ideas that improve filters, cost handling, walk-forward design, or
  parameter stability over ideas that require inventing a brand-new signal.
- Keep the default action as reject or needs-translation until the rule packet
  is exact enough for a paper-only proxy test.

## Next Phase - Walk-Forward EMA Robustness Proxy

Goal:

- Test whether source-style rolling EMA selection improves the failed static
  bounded EMA result.

Status: complete

- Added `run-walk-forward-trend-proxy`.
- Added a rolling validation/test selector for EMA values 10, 20, 50, 100, 200.
- Ran GBPUSD and EURUSD H1 with 24-month training context, 6-month validation,
  6-month test, and 6-month step.
- Applied 2 bps cost per position change.

Result:

- Best row: EURUSD.
- Windows: 5
- Trades: 578
- Cumulative return: -3.3096%
- Sharpe: -0.1737
- Max drawdown: 10.9202%
- Verdict: KILL
- Reason: NEGATIVE_AFTER_COSTS

Artifacts:

- `reports/walk_forward_trend_proxy/20260525T210238Z_walk_forward_trend_proxy.md`
- `reports/walk_forward_trend_proxy/20260525T210238Z_walk_forward_trend_proxy.json`
- `ideas/backtest_candidates/walk-forward-ema-robustness-20260525.md`
- `ideas/rejected/walk-forward-ema-robustness-20260525.md`

Review:

- Rolling parameter selection did not rescue the EMA trend idea after costs.
- The implementation is still useful infrastructure for future hypotheses that
  require walk-forward validation.

Next step:

- Run the phase gate audit for the walk-forward proxy phase.

Audit:

- Phase gate: pass
- Focused tests: 6 passed
- `pip check`: pass
- `security-check`: pass
- construction audit: pass, zero findings
- Gate artifact:
  `idea_reviews/phase_gates/20260525T210435Z_walk-forward-trend-proxy.md`

Clean checkpoint:

- Static bounded EMA trend proxy: rejected.
- Rolling walk-forward EMA trend proxy: rejected.
- Reusable data readiness, bounded proxy, and walk-forward proxy tools remain
  available for future hypotheses.

## Next Phase - Candidate Selection And Duplicate Closure

Goal:

- Stop already-tested sources and duplicate active candidates from re-entering
  the strategy pipeline.
- Rank remaining research notes without creating strategy code.

Status: complete

- Added `select-next-candidates`.
- Added a candidate selector report that checks research notes, active backtest
  candidates, and rejected records together.
- Closed stale `ema-wf-crossover-20260525.md` as `tested_rejected` because it
  uses the same WNE source already tested by the walk-forward proxy.
- Ran selector over the live queue.

Result:

- Reviewed: 9 items
- Translate next: 0
- Blocked/hold: 9
- Already tested/rejected sources blocked: 3
- Closed rejected candidates recognized: 4
- Highest remaining notes:
  - `A Multi Strategy Approach to Trading Foreign Exchange Futures`
  - `Momentum and Trend Following Trading Strategies for Currencies Revisited`
- Both highest remaining notes need exact rule translation before candidate
  conversion.

Artifacts:

- `idea_reviews/candidate_selection_2026-05-25.md`
- `idea_reviews/candidate_selection_2026-05-25.json`

Review:

- No new strategy should be created from the already failed EMA/momentum source
  notes.
- The next useful work is not another plain trend proxy; it is exact extraction
  of portfolio construction, carry, mean-reversion, cost, or regime-filter rules
  from the two remaining high-scoring notes.

Next step:

- Run the phase gate audit for candidate selection.

Audit:

- Phase gate: pass
- Focused tests: 6 passed
- `pip check`: pass
- `security-check`: pass
- construction audit: pass, zero findings
- Gate artifact:
  `idea_reviews/phase_gates/20260525T221113Z_candidate-selection-and-duplicate-closure.md`

Clean checkpoint:

- No remaining note is ready for automatic conversion.
- Two sources remain worth manual rule extraction:
  - multi-strategy FX futures portfolio construction
  - momentum/trend-following currencies revisited
- Any next candidate must start from exact rules and should target filters,
  carry/mean-reversion combination, cost handling, or regime design.

## Next Phase - Raw Data Intake Guardrail

Goal:

- Make it obvious where new CSV files belong.
- Flag raw data filenames that will confuse readiness checks, backtests, or UI
  defaults.

Status: complete

- Added `audit-raw-data`.
- Added raw data intake documentation:
  `docs/project/RAW_DATA_INTAKE.md`.
- The expected drop zone is `data/raw/`.
- The expected filename format is `SYMBOL_TIMEFRAME.csv`.

Live inventory result:

- CSV files: 36
- OK: 34
- Issues: 2
- Flagged files:
  - `XAUUSD_M15_New 26.csv`
  - `XAUUSD_M15_merged.csv`

Artifacts:

- `reports/raw_data_inventory/20260525T221426Z_raw_data_inventory.md`
- `reports/raw_data_inventory/20260525T221426Z_raw_data_inventory.json`

Review:

- The folder choice is correct: new market CSVs should go into `data/raw/`.
- Standard files such as `EURUSD_H1.csv` and `XAUUSD_M15.csv` are ready for
  existing tools.
- Nonstandard files can stay temporarily as source/reference files, but they
  should not be used as canonical strategy inputs unless renamed or imported
  into a standard canonical file.

Next step:

- Run the phase gate audit for raw data intake.

Audit:

- Phase gate: pass
- Focused tests: 7 passed
- `pip check`: pass
- `security-check`: pass
- construction audit: pass, zero findings
- Gate artifact:
  `idea_reviews/phase_gates/20260525T221546Z_raw-data-intake-guardrail.md`

Clean checkpoint:

- New CSV files should be added to `data/raw/`.
- Canonical filenames should use `SYMBOL_TIMEFRAME.csv`.
- Run `audit-raw-data` after adding files.
- Run `check-data-readiness` for the symbols/timeframes before any backtest or
  hypothesis proxy test.

## Next Phase - Raw Data Cleanup Suggestions

Goal:

- Make raw-data audit results actionable without moving or deleting files
  automatically.

Status: complete

- Added `suggested_action` to each raw data inventory row.
- Updated `RAW_DATA_INTAKE.md` to explain the optional
  `data/raw/source_exports/` reference area.
- Regenerated the live raw data inventory report.

Result:

- CSV files: 36
- OK: 34
- Issues: 2
- Suggested action for both flagged XAUUSD files:
  keep as reference or move to `data/raw/source_exports/`, then use/create a
  canonical `SYMBOL_TIMEFRAME.csv` before testing.

Artifacts:

- `reports/raw_data_inventory/20260525T221715Z_raw_data_inventory.md`
- `reports/raw_data_inventory/20260525T221715Z_raw_data_inventory.json`

Review:

- No files were moved or deleted.
- The canonical `XAUUSD_M15.csv` remains the strategy input.
- The nonstandard files now have a clear cleanup path.

Next step:

- Run the phase gate audit for raw data cleanup suggestions.

Audit:

- Phase gate: pass
- Focused tests: 7 passed
- `pip check`: pass
- `security-check`: pass
- construction audit: pass, zero findings
- Gate artifact:
  `idea_reviews/phase_gates/20260525T221833Z_raw-data-cleanup-suggestions.md`

Clean checkpoint:

- Raw data audit now reports both issues and suggested actions.
- Nonstandard CSVs are not renamed, moved, or deleted automatically.
- The safe manual cleanup path is `data/raw/source_exports/`.

## Next Phase - Source Export Holding Area

Goal:

- Give noncanonical broker exports and merged drafts a clear local place to
  live without becoming strategy inputs.

Status: complete

- Created local ignored folder: `data/raw/source_exports/`.
- Added a local README inside that folder.
- Added a test confirming `audit-raw-data` ignores CSVs inside
  `data/raw/source_exports/`.
- Updated `RAW_DATA_INTAKE.md` to explain that only top-level `data/raw/*.csv`
  files are canonical inventory inputs.

Result:

- Fresh inventory still sees 36 top-level CSV files.
- Source export folder exists and is ignored by canonical inventory.
- The two existing nonstandard top-level XAUUSD files are still flagged until
  manually moved or resolved.

Artifacts:

- `reports/raw_data_inventory/20260525T222027Z_raw_data_inventory.md`
- `reports/raw_data_inventory/20260525T222027Z_raw_data_inventory.json`

Review:

- No market data files were moved or deleted.
- The folder is ready for manual cleanup when desired.
- Because `data/raw/` is ignored by git, this holding area is local workspace
  structure, not tracked project source.

Next step:

- Run the phase gate audit for the source export holding area.

Audit:

- Phase gate: pass
- Focused tests: 8 passed
- `pip check`: pass
- `security-check`: pass
- construction audit: pass, zero findings
- Gate artifact:
  `idea_reviews/phase_gates/20260525T222144Z_source-export-holding-area.md`

Clean checkpoint:

- Canonical market CSVs live directly in `data/raw/`.
- Reference exports can live in `data/raw/source_exports/`.
- `audit-raw-data` checks only top-level canonical CSVs.

## Next Phase - Raw Data Cleanup Plan

Goal:

- Produce a reviewable dry-run plan for moving noncanonical top-level raw CSVs
  into the source export holding area.

Status: complete

- Added `plan-raw-data-cleanup`.
- Added tests proving the plan is dry-run and leaves files in place.
- Updated `RAW_DATA_INTAKE.md` with the cleanup-plan command.
- Generated the live cleanup plan.

Result:

- Proposed moves: 2
- Dry run: true
- Proposed:
  - `data/raw/XAUUSD_M15_New 26.csv` ->
    `data/raw/source_exports/XAUUSD_M15_New 26.csv`
  - `data/raw/XAUUSD_M15_merged.csv` ->
    `data/raw/source_exports/XAUUSD_M15_merged.csv`

Artifacts:

- `reports/raw_data_inventory/20260525T222338Z_raw_data_cleanup_plan.md`
- `reports/raw_data_inventory/20260525T222338Z_raw_data_cleanup_plan.json`

Review:

- No files were moved, renamed, or deleted.
- The plan is safe to review before manual cleanup.
- The canonical `XAUUSD_M15.csv` remains untouched.

Next step:

- Run the phase gate audit for the raw data cleanup plan.

Audit:

- Phase gate: pass
- Focused tests: 9 passed
- `pip check`: pass
- `security-check`: pass
- construction audit: pass, zero findings
- Gate artifact:
  `idea_reviews/phase_gates/20260525T222459Z_raw-data-cleanup-plan.md`

Clean checkpoint:

- `plan-raw-data-cleanup` is available and dry-run only.
- Current plan proposes moving the two noncanonical XAUUSD files into
  `data/raw/source_exports/`.
- No files were moved, renamed, or deleted.

## Next Phase - Guarded Raw Data Cleanup Apply

Goal:

- Add a safe manual apply command for reviewed raw-data cleanup plans.

Status: complete

- Added `apply-raw-data-cleanup`.
- The command refuses to run without `--confirm-reviewed-plan`.
- It moves only noncanonical top-level CSVs into `data/raw/source_exports/`.
- It refuses to overwrite existing files.
- Added tests for confirmation, moving, overwrite protection, and preserving
  canonical files.

Review:

- The live apply command was not run against real data.
- No files were moved, renamed, or deleted.
- The command is ready for manual use after reviewing
  `plan-raw-data-cleanup`.

Next step:

- Run the phase gate audit for guarded raw data cleanup apply.

Audit:

- Phase gate: pass
- Focused tests: 12 passed
- `pip check`: pass
- `security-check`: pass
- construction audit: pass, zero findings
- Gate artifact:
  `idea_reviews/phase_gates/20260525T222806Z_guarded-raw-data-cleanup-apply.md`

Clean checkpoint:

- `apply-raw-data-cleanup` is available.
- It requires `--confirm-reviewed-plan`.
- It refuses to overwrite existing files.
- The live apply command has not been run against real data.

## Next Phase - Applied Raw Data Cleanup

Goal:

- Finish the reviewed raw-data cleanup by moving noncanonical top-level CSVs
  into the source export holding area.

Status: complete

- Ran `apply-raw-data-cleanup --confirm-reviewed-plan`.
- Moved 2 files.
- Skipped 0 files.
- Verified canonical raw-data inventory afterward.
- Verified `XAUUSD_M15.csv` readiness afterward.

Moved:

- `data/raw/XAUUSD_M15_New 26.csv` ->
  `data/raw/source_exports/XAUUSD_M15_New 26.csv`
- `data/raw/XAUUSD_M15_merged.csv` ->
  `data/raw/source_exports/XAUUSD_M15_merged.csv`

Verification:

- `audit-raw-data`: 34 CSV files, 34 OK, 0 issues.
- `check-data-readiness --symbols XAUUSD --timeframes M15`: ready.
- Canonical `XAUUSD_M15.csv`: 101,748 rows, about 51.63 months.

Artifacts:

- `reports/raw_data_inventory/20260525T222941Z_raw_data_cleanup_apply.md`
- `reports/raw_data_inventory/20260525T222941Z_raw_data_cleanup_apply.json`
- `reports/raw_data_inventory/20260525T222959Z_raw_data_inventory.md`
- `reports/raw_data_inventory/20260525T222959Z_raw_data_inventory.json`
- `reports/data_readiness/20260525T223014Z_data_readiness.md`
- `reports/data_readiness/20260525T223014Z_data_readiness.json`

Review:

- Canonical market CSVs are now clean.
- Reference exports are preserved under `data/raw/source_exports/`.
- No canonical strategy input was deleted.

Next step:

- Run the phase gate audit for applied raw data cleanup.

Audit:

- Phase gate: pass
- Focused tests: 12 passed
- `pip check`: pass
- `security-check`: pass
- construction audit: pass, zero findings
- Gate artifact:
  `idea_reviews/phase_gates/20260525T223137Z_applied-raw-data-cleanup.md`

Clean checkpoint:

- Top-level `data/raw/` canonical CSV inventory is clean.
- `data/raw/source_exports/` contains the two moved reference files.
- `XAUUSD_M15.csv` remains ready for strategy tests.

## Next Phase - Momentum Source Rule Extraction

Goal:

- Complete the next research-selection task without inventing a strategy from
  weak source notes.

Status: complete

- Refreshed `select-next-candidates`.
- Converted the stronger momentum/trend source into a paper-only candidate:
  `ideas/backtest_candidates/vol-scaled-ema-mixture-currency-momentum-20260525.md`.
- Blocked the multi-strategy FX futures source because local notes only contain
  abstract-level detail:
  `ideas/translation_blocked/multi-strategy-fx-futures-20260525.md`.
- Checked H1 readiness for the candidate's five-symbol local FX basket.

Result:

- Candidate selection now sees the vol-scaled EMA mixture as an open candidate.
- The original momentum/trend note is now marked as already having a candidate.
- The multi-strategy FX futures source remains useful, but needs exact formulas
  before candidate conversion.

Data readiness:

- EURUSD H1: ready, about 65.02 months.
- GBPUSD H1: ready, about 65.45 months.
- AUDUSD H1: ready, about 65.45 months.
- USDJPY H1: ready, about 65.45 months.
- USDCAD H1: ready, about 65.45 months.

Artifacts:

- `ideas/backtest_candidates/vol-scaled-ema-mixture-currency-momentum-20260525.md`
- `ideas/translation_blocked/multi-strategy-fx-futures-20260525.md`
- `reports/data_readiness/20260525T223606Z_data_readiness.md`
- `reports/data_readiness/20260525T223606Z_data_readiness.json`
- `idea_reviews/candidate_selection_2026-05-25.md`
- `idea_reviews/candidate_selection_2026-05-25.json`

Review:

- This is not strategy code.
- It is not live trading.
- The next implementation task is a paper-only proxy for the vol-scaled EMA
  mixture, compared against the already failed plain EMA baselines.

Next step:

- Run the phase gate audit for momentum source rule extraction.

Audit:

- Phase gate: pass
- Focused tests: 7 passed
- `pip check`: pass
- `security-check`: pass
- construction audit: pass, zero findings
- Gate artifact:
  `idea_reviews/phase_gates/20260525T223750Z_momentum-source-rule-extraction.md`

Clean checkpoint:

- Data cleanup is complete.
- Candidate selection is refreshed.
- One new paper-only open candidate exists.
- One high-quality source is explicitly blocked until exact formulas are
  extracted.
