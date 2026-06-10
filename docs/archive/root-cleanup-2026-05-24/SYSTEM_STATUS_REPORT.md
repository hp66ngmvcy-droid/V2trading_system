# V2 Trading System Status Report

Snapshot date: 2026-05-13  
Root: `/Users/whs1/Dev/V2trading_system`  
Mode: local-first, paper-only trading research system

## Executive Summary

This repository is a Python package named `tar-system` with a broad local research stack for market CSV import, data validation, feature engineering, backtesting, risk checks, strategy scoring, walk-forward validation, paper broker simulation, dashboard controls, research-loop automation, and manual MT5 review exports.

The system is not a clean committed baseline. The git repository has one commit (`591a9e0 Clean gitignore`) and a large dirty working tree containing modified runtime/source files and many untracked project files, data artifacts, reports, and strategy modules.

The main packaged code lives under `src/tar_system`. There is also a separate `src/master_system` helper layer and an experimental `src/v2trading` namespace. The `src/v2trading` files currently contain syntax-corrupted code and should be treated as broken/experimental until repaired.

The repo contains a populated data lake:

- 35 raw CSV files in `data/raw`
- 34 validated Parquet files in `data/validated`
- 34 feature Parquet files in `data/features`
- 182 direct result files in `data/results`
- a 51 MB DuckDB database at `data/tar_system.duckdb`
- generated paper strategy review artifacts under `data/paper_strategies`

## Requested Read Checklist

The exact inventory command was run:

```bash
find /Users/whs1/Dev/V2trading_system -type f -name "*.py" -o -name "*.md" -o -name "*.txt" | sort
```

Result: 8,975 matching files. This includes the local `venv` site-packages, so the raw output is mostly dependency internals. Excluding `.git`, `venv`, and `__pycache__`, there are 332 project-owned `.py`, `.md`, and `.txt` files.

Requested core files:

| Requested file | Status |
|---|---|
| `START_HERE.md` | Missing |
| `CLAUDE.MD` | Missing by exact case; `CLAUDE.md` exists and was read |
| `CODEX.MD` | Missing |
| `SESSION_MEMORY.md` | Missing |
| `START_IDEA_ORCHESTRATOR.txt` | Missing |
| `IDEA_ORCHESTRATOR_INTEGRATION.md` | Missing |
| `idea_orchestrator.py` | Missing |
| `run_paper_strategies.py` | Exists and was read |

The repo search found no direct idea-orchestrator files. The nearest orchestrator files are:

- `src/master_system/orchestrator.py`
- `src/tar_system/validation/walk_forward_orchestrator.py`
- `src/tar_system/controller/research_controller.py`
- `src/tar_system/controller/research_loop.py`

## Folder Structure

Project directories, excluding `.git` and `venv` dependency internals:

```text
.
|- .vscode/
|- Ideas to add/
|  `- tar_markdown_pack/
|- configs/
|  |- brokers/
|  `- legacy_presets/
|- data/
|  |- features/
|  |- paper_strategies/
|  |- raw/
|  |- results/
|  |  `- cache/
|  `- validated/
|- exports/
|  `- mt5/
|- logs/
|  `- audit/
|- master_system/
|  `- memory/
|- reports/
|- research/
|  `- external_repos/
|     |- backtrader/
|     |- freqtrade/
|     |- lean/
|     `- pypfopt/
|- runtime/
|  `- dashboard_runs/
|- scripts/
|- skills/
|- src/
|  |- master_system/
|  |  |- domains/
|  |  |- integrations/
|  |  |- reporting/
|  |  `- vault/
|  |- tar_system/
|  |  |- agents/
|  |  |- analysis/
|  |  |- assets/
|  |  |- audit/
|  |  |- backtest/
|  |  |- brokers/
|  |  |- cache/
|  |  |- controller/
|  |  |- dashboard/
|  |  |  |- components/
|  |  |  `- pages/
|  |  |- data/
|  |  |- discovery/
|  |  |- environment/
|  |  |- execution/
|  |  |- exports/
|  |  |- features/
|  |  |- forward_test/
|  |  |- legacy/
|  |  |- live/
|  |  |- memory/
|  |  |- obsidian/
|  |  |- optimisation/
|  |  |- pipeline/
|  |  |- portfolio/
|  |  |- positioning/
|  |  |- regime/
|  |  |- reporting/
|  |  |- research/
|  |  |- risk/
|  |  |- scoring/
|  |  |- security/
|  |  |- strategies/
|  |  `- validation/
|  `- v2trading/
|     |- execution/
|     |- memory/
|     `- validation/
`- tests/
```

There are also stray top-level entries that look accidental or generated: `0`, `Agent`, `The`, `-la/`, `configsls/`, `sbrcat`, `src/tar_s`, `src/tar_system/strategicat`, and a corrupted/oddly named strategy file `src/tar_system/strategies/ATR Breakout Strategy - FIXED`.

## Top-Level Files

| File | Purpose / status |
|---|---|
| `.gitignore` | Ignore rules; latest committed file per git log. |
| `README.md` | Lean setup and CLI quickstart for CSV import, features, backtest, scoring, MT5 export, and dashboard placeholder. |
| `CLAUDE.md` | Agent/coding rules. Important project rules: paper mode only, no live trading, inspect before edit, light dependencies, safe logged failures, no memory writes from partial runs, never overwrite raw files. |
| `CHANGELOG.md` | Project change history. |
| `COMPLETION_SUMMARY.md` | Academic paper strategy system summary. Claims 5 paper strategies complete and XAUUSD M15 results generated. |
| `PAPER_STRATEGY_IMPLEMENTATION.md` | Technical documentation for the paper strategy research modules. |
| `PAPER_STRATEGY_QUICK_REFERENCE.md` | Commands for running `run_paper_strategies.py`, single strategy tests, and verdict checks. Note: it recommends live execution integration as a developer next step, which conflicts with `CLAUDE.md` paper-only policy. |
| `WEEK3_COMPLETION_REPORT.md` | Walk-forward validation and Phase 3 variant progress report. |
| `PHASE2_COMPLETION.txt` | Short Phase 2 completion note. |
| `SYSTEM_AUDIT_20260509.txt` | Audit snapshot text. |
| `requirements.txt` | Runtime dependencies: pandas, numpy, duckdb, pyarrow, python-dotenv, ta, scikit-learn, streamlit, plotly. |
| `pyproject.toml` | Package metadata for `tar-system`, Python >=3.9, setuptools package discovery under `src`. |
| `pytest.ini` | Pytest configuration. |
| `run_paper_strategies.py` | Full academic paper strategy pipeline runner. Loads strategy definitions, backtests on XAUUSD M15, reviews verdicts, exports JSON/text/graph artifacts. |
| `run_advanced_strategies.py` | Advanced strategy runner script. |
| `run_all_backtests.sh` | Shell script for batch backtesting. |
| `simple_paper_trader.py` | Small/simple paper trading script. |
| `audit_results.py`, `diagnose_strategies.py`, `quick_audit.py`, `fix_walk_forward_cli.py` | Local utility/debug scripts. |
| `fix_cli.txt` | CLI fix notes. |
| `refinement_plan.json` | Local refinement plan data. |
| `backtest_run.log` | Backtest run log. |

## Source Modules and Purposes

### `src/tar_system`

This is the primary application package.

| Area | Key files | Purpose / status |
|---|---|---|
| CLI | `cli.py`, `cli_walk_forward.py` | Main command surface. Supports import, tick conversion, validation, feature build, backtest, scoring, MT5 export, environment checks, walk-forward, ranking, Obsidian export, idea/candidate generation, dashboard, forward test, reports, security, optimisation, broker/cost tools, scheduled runs, queue/controller/worker, research loop, positioning, and full pipeline. |
| Settings | `settings.py` | Hard-coded paper-only defaults. `PAPER_MODE=True`, `LIVE_TRADING_ALLOWED=False`, default capital and risk caps. |
| Data | `data/csv_importer.py`, `data/store.py`, `data/tick_converter.py`, `data/validator.py` | CSV/tick ingestion, original raw copy preservation, OHLCV validation, Parquet storage, date filtering, DuckDB query helper. |
| Features | `features/engineering.py` | Builds technical feature tables from validated data. |
| Backtest | `backtest/engine.py`, `backtest/metrics.py` | Event-driven backtest with strategy signal generation, regime detection, risk gate, paper broker execution, portfolio tracking, metrics, and stop handling from dashboard runtime status. Currently contains debug prints in the loop. |
| Strategies | `strategies/base.py`, `gold_v2.py`, `rsi_reversion_v1.py`, `goldv2_v2.py`, `rsi_only_v3.py`, `ema_volume_v3.py`, `atr_breakout_v3.py`, `momentum_crossover_v3.py`, `multi_timeframe_v3.py`, fixed variants, `registry.py`, `resolver.py`, `asset_variants.py`, `regime_selector.py` | Strategy implementations and variant resolution. Current registry exposes `STRATEGIES` and `get_strategy`; some controller code expects `REGISTRY`, causing pytest collection failure. |
| Risk | `risk/engine.py`, `risk/position_sizer.py` | Signal approval, drawdown/exposure/volatility gates, position sizing using broker/asset profiles. |
| Broker/execution | `execution/paper_broker.py`, `brokers/profiles.py`, `brokers/registry.py`, `brokers/paper_broker.py` | Paper-only broker model, spreads, slippage/commission/swap/margin estimates, broker profiles. |
| Portfolio | `portfolio/tracker.py` | Position and trade tracking, equity curve export. |
| Assets | `assets/profiles.py`, `assets/registry.py` | Asset profile lookup and audit integration. |
| Regime | `regime/detector.py` | Market regime enum and row-level regime classification. |
| Environment | `environment/*` | Economic event calendar, risk state evaluation, shock detection, asset impact mapping, environment report generation. |
| Validation | `validation/*` | Walk-forward splits, Monte Carlo, parameter sensitivity, cost analysis, blind OOS testing, failed-window logs, equity stitching, OOS aggregation, walk-forward orchestrator. |
| Optimisation | `optimisation/*` | Parameter spaces, optimizer, risk strategy optimiser, regime heatmap, go/no-go gate, artifacts, improvement planning. |
| Scoring | `scoring/scorer.py` | Converts metrics to score/verdict/reason codes. |
| Reporting | `reporting/reporter.py`, `reporting/review_log.py` | Markdown reports, variant comparison reports, review summaries/logs. |
| Dashboard | `dashboard/app.py`, `dashboard/runtime_control.py`, components, pages | Streamlit dashboard with overview, run control, strategy detail, leaderboard, promotion board, asset data, environment, positioning, daily summary, and security pages. |
| Controller | `controller/job_queue.py`, `data_watcher.py`, `research_controller.py`, `worker.py`, `research_loop.py`, `load_test.py` | Queue-backed automation layer using JSONL/DuckDB, raw-data scanning, controller/worker execution, load tests, and research loop summaries. |
| Research | `research/strategy_importer.py`, `paper_backtester.py`, `finance_reviewer.py`, `strategy_enhancements.py`, `multi_asset_backtester.py` | Academic paper strategy subsystem. Contains five strategy families, adaptive parameters, volume/regime filters, standalone backtesting, finance verdict scoring, and graph/report export. |
| Forward test | `forward_test/engine.py` | Forward-test state/result generation with review-only guards. |
| Discovery | `discovery/*` | Strategy idea parsing, blueprint mutation, candidate registry, promotion gates. |
| Memory | `memory/*` | Strategy memory and master-system bridge/client. Must not write memory for partial/blocked runs per project rules. |
| Obsidian | `obsidian/exporter.py` | Exports research/memory notes. |
| Positioning | `positioning/*` | COT/manual note import and positioning score storage. |
| Security | `security/checks.py` | Local security checks. |
| Live | `live/broker_adapter.py`, `live/execution_interface.py` | Present as interfaces, but project policy says live trading must remain disabled/sealed. |
| Agents | `agents/*` | Thin agent classes for audit, backtest, dashboard, data validation, features, memory, optimisation, oversight, reporting, risk, scoring, strategy, and walk-forward roles. |
| Cache/pipeline/audit | `cache/*`, `pipeline/checkpoint.py`, `audit/writer.py`, `reason_codes.py` | Result/artifact caching, checkpointing, audit events, reason-code vocabulary. |

### `src/master_system`

Separate helper package with a CLI, a `MasterOrchestrator`, a `SecondaryBrain`, invoice-calculator sample domain, CSV validator, position sizer, and PDF report generator. This appears to be a broader/local master-system utility layer rather than core TAR execution.

### `src/v2trading`

Experimental namespace with:

- `execution/fills.py`
- `memory/learning_engine.py`
- `validation/parameter_stability.py`

Current status: broken. `compileall` reports syntax errors in all three files.

## Data Folder Snapshot

Command run:

```bash
ls -lah /Users/whs1/Dev/V2trading_system/data/
```

Summary:

```text
data/
|- features/              34 feature Parquet files
|- paper_strategies/      5 generated paper-strategy artifacts
|- raw/                   35 raw CSV/metadata files
|- results/               182 direct result files plus cache/
|- validated/             34 validated Parquet files
|- phase2_audit.json
|- phase2_audit_final.json
`- tar_system.duckdb       51 MB
```

Market coverage visible in raw/features/validated includes AUDUSD, BTCUSD, EURUSD, GBPUSD, USDCAD, USDJPY, USOUSD, and XAUUSD across M1, M5, M15, M30, and H1 depending on asset.

Important policy: original raw files must never be overwritten. The importer preserves raw copies and writes validated/feature data separately.

## Reports and Research Files

`reports/` contains 72 report files, mainly per-asset/per-timeframe strategy reports for `gold_v2` and `rsi_reversion_v1`, plus variant comparison and research-loop summaries.

`research/external_repos/` contains synthesis notes and pattern extractions from Backtrader, DuckDB, Freqtrade, Lean, Microsoft Agent coordination, Polars, PyPortfolioOpt, TensorTrade, and Zipline. There are also small copied source references from Backtrader and Freqtrade.

`Ideas to add/tar_markdown_pack/` contains architecture/runbook/security/dashboard/data-pipeline/import strategy markdown intended as design backlog or external idea material.

## Skills and Operating Rules

`skills/` contains local project-specific rules:

- `backtest_rules.md`
- `code_skill.md`
- `csv_data_rules.md`
- `environment_risk_rules.md`
- `local_performance.md`
- `mt5_export_rules.md`
- `obsidian_rules.md`
- `risk_strategy_optimiser.md`
- `security_rules.md`
- `strategy_discovery_rules.md`
- `token_optimisation.md`

These support the same operating theme as `CLAUDE.md`: local, safe, paper-only, audit-heavy, low dependency, no raw data overwrite.

## Integration Points

### Main CLI Workflow

`src/tar_system/cli.py` is the central integration surface.

Primary flow:

1. `import-csv` loads raw/tick data, converts if needed, validates OHLCV, audits schema/environment, writes validated Parquet.
2. `validate-data` re-runs validation on stored validated data.
3. `build-features` loads validated Parquet and writes feature Parquet.
4. `run-backtest` loads feature data, resolves asset/broker/strategy variant, checks cache, runs event-driven backtest, writes metrics JSON and cache, appends review log.
5. `score-strategy` scores metrics, records memory, appends review result, writes review summary.
6. `run-walk-forward`, `cost-analysis`, `optimise-asset`, `compare-assets`, `compare-variants`, and `go-no-go` validate and rank candidate strategy variants.
7. `export-mt5` exports latest signal files for manual MT5 review only.

### Strategy Resolution

`tar_system.strategies.resolver.resolve_strategy()` connects:

- asset profiles
- broker profiles
- strategy variants
- strategy registry
- audit events

Current defect: `resolve_strategy()` calls `get_strategy(base_strategy, **variant.parameters)`, but `registry.get_strategy()` currently accepts only `name`. This path may fail when variant parameters are non-empty.

### Backtesting

`backtest.engine.run_backtest()` connects:

- feature rows
- strategy signal generation
- regime detection
- risk engine
- paper broker execution
- portfolio tracking
- audit events
- dashboard stop status
- metrics export

Backtests are designed to fail safe: if a stop is requested, partial results are marked and not cached/reviewed by `run_backtest_cmd`.

### Runtime/Dashboard Control

Dashboard pages and `dashboard/runtime_control.py` coordinate:

- backtest status
- dashboard activity
- run history
- pipeline status
- queue view
- tested-data registry
- quick actions and batch actions

Current runtime files are modified in git status, which is expected if the dashboard/backtests have been run locally.

### Queue and Research Loop

`controller/job_queue.py`, `data_watcher.py`, `research_controller.py`, and `worker.py` provide raw-data scanning and queued research jobs. Jobs can be stored/mirrored in DuckDB and JSONL. The research loop can queue smoke/full jobs, run workers, and summarize next actions.

Current defect: `data_watcher.py` imports `REGISTRY` from `tar_system.strategies.registry`, but the registry file defines `STRATEGIES`, not `REGISTRY`. This breaks pytest collection.

### Paper Strategy Research Pipeline

`run_paper_strategies.py` orchestrates:

1. Load academic paper strategies from `tar_system.research.strategy_importer`.
2. Backtest all strategies with `PaperStrategyBacktester`.
3. Export `paper_strategies_results.json`.
4. Review results with `AnthropicFinanceReviewer`.
5. Export `strategy_verdicts.json` and a timestamped finance review text file.
6. Generate `paper_strategies_comparison.png`.

Generated artifacts currently exist in `data/paper_strategies`.

### Master System / Memory

`src/master_system` and `src/tar_system/memory` are integration points for local memory, learning records, and broader orchestration. Treat these as separate from strategy results unless a run completes fully and passes scoring/review requirements.

## Current Component Status

| Component | Status | Notes |
|---|---|---|
| Repo baseline | Dirty | One commit only; many modified and untracked files. |
| Packaging | Present | `pyproject.toml` package discovery under `src`. |
| Dependencies | Present | `venv` exists and has pytest; system Python lacks pytest. |
| Core `tar_system` syntax | Mostly OK | `compileall src` reached most TAR modules successfully. |
| `src/v2trading` syntax | Broken | Three syntax errors in `fills.py`, `learning_engine.py`, and `parameter_stability.py`. |
| Test suite | Blocked | `venv/bin/python -m pytest` collects 156 items but stops on `ImportError: cannot import name 'REGISTRY'`. |
| Data pipeline | Populated | Raw, validated, feature, DuckDB, and result artifacts exist. |
| Backtest engine | Functional but noisy | Contains `DEBUG:` print inside the event loop. |
| Strategy registry | Inconsistent | Exposes `STRATEGIES`; some code/tests expect `REGISTRY`; `get_strategy` does not accept parameter overrides used by resolver. |
| Walk-forward validation | Implemented | Multiple modules and reports present. |
| Dashboard | Implemented | Streamlit pages and runtime control present. Runtime status files are dirty. |
| Paper strategy subsystem | Implemented | Docs and generated XAUUSD M15 results present. |
| Live trading | Disabled by policy | Interfaces exist, but `CLAUDE.md` and settings require paper-only operation. |
| Idea orchestrator | Missing | Requested files are absent; only other orchestrators exist. |

## Git Snapshot

Current branch: `main`  
Latest commit:

```text
591a9e0 Clean gitignore
```

Modified tracked files:

```text
runtime/backtest_status.json
runtime/dashboard_activity.jsonl
runtime/dashboard_run_history.json
runtime/dashboard_run_status.json
runtime/job_queue.jsonl
runtime/pipeline_status.json
runtime/tested_data_registry.json
src/tar_system/backtest/engine.py
src/tar_system/cli.py
src/tar_system/execution/paper_broker.py
src/tar_system/settings.py
src/tar_system/strategies/registry.py
```

Notable untracked areas:

```text
.vscode/
COMPLETION_SUMMARY.md
Ideas to add/
PAPER_STRATEGY_IMPLEMENTATION.md
PAPER_STRATEGY_QUICK_REFERENCE.md
WEEK3_COMPLETION_REPORT.md
configs/strategy_params.yaml
data/
master_system/
research/external_repos/
run_advanced_strategies.py
run_all_backtests.sh
run_paper_strategies.py
src/master_system/
src/tar_system/research/
src/tar_system/live/
src/tar_system/validation/* new walk-forward files
src/v2trading/
```

## Documentation Count

Command run:

```bash
wc -l /Users/whs1/Dev/V2trading_system/*.md /Users/whs1/Dev/V2trading_system/*.py | tail -1
```

Result:

```text
2173 total
```

This covers only top-level `.md` and `.py` files, not nested docs/code.

## Health Checks Performed

System Python pytest:

```bash
PYTHONPATH=src python -m pytest
```

Result: failed immediately because system Python has no `pytest` installed.

Venv pytest:

```bash
PYTHONPATH=src venv/bin/python -m pytest
```

Result: pytest starts under Python 3.14.4, collects 156 items, then stops during collection:

```text
ImportError: cannot import name 'REGISTRY' from 'tar_system.strategies.registry'
```

Compile check:

```bash
PYTHONPATH=src python -m compileall src
```

Result: syntax errors in:

```text
src/v2trading/execution/fills.py
src/v2trading/memory/learning_engine.py
src/v2trading/validation/parameter_stability.py
```

## Ready-To-Use Workflows

### Setup

```bash
cd /Users/whs1/Dev/V2trading_system
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

### Import CSV

```bash
PYTHONPATH=src venv/bin/python -m tar_system.cli import-csv --file data/raw/XAUUSD_M15.csv --symbol XAUUSD --timeframe M15
```

### Validate and Build Features

```bash
PYTHONPATH=src venv/bin/python -m tar_system.cli validate-data --symbol XAUUSD --timeframe M15
PYTHONPATH=src venv/bin/python -m tar_system.cli build-features --symbol XAUUSD --timeframe M15
```

### Run Backtest

```bash
PYTHONPATH=src venv/bin/python -m tar_system.cli run-backtest --strategy gold_v2 --symbol XAUUSD --timeframe M15 --broker current_broker_demo
```

### Score Strategy

```bash
PYTHONPATH=src venv/bin/python -m tar_system.cli score-strategy --strategy gold_v2 --symbol XAUUSD --timeframe M15
```

### Walk-Forward

```bash
PYTHONPATH=src venv/bin/python -m tar_system.cli run-walk-forward --strategy gold_v2 --symbol XAUUSD --timeframe M15
```

### Full Pipeline

```bash
PYTHONPATH=src venv/bin/python -m tar_system.cli run-full-pipeline --strategy gold_v2 --symbol XAUUSD --timeframe M15 --file data/raw/XAUUSD_M15.csv --broker current_broker_demo --force
```

### Paper Strategy Research

```bash
PYTHONPATH=src venv/bin/python run_paper_strategies.py
```

Outputs:

```text
data/paper_strategies/paper_strategies_results.json
data/paper_strategies/strategy_verdicts.json
data/paper_strategies/finance_review_*.txt
data/paper_strategies/paper_strategies_comparison.png
```

### Research Queue

```bash
PYTHONPATH=src venv/bin/python -m tar_system.cli queue-job --strategy gold_v2 --symbol XAUUSD --timeframe M15 --file data/raw/XAUUSD_M15.csv
PYTHONPATH=src venv/bin/python -m tar_system.cli show-queue
PYTHONPATH=src venv/bin/python -m tar_system.cli run-worker --limit 1
```

### Dashboard

```bash
PYTHONPATH=src venv/bin/streamlit run src/tar_system/dashboard/app.py
```

## Recommended Next Steps

1. Repair the strategy registry API mismatch.
   - Add a compatible `REGISTRY` alias or update `data_watcher.py` and tests to use `STRATEGIES`.
   - Update `get_strategy` to accept `**kwargs` if variant parameters should flow into strategy constructors.

2. Quarantine or repair `src/v2trading`.
   - These files currently break `compileall`.
   - If experimental, move them out of `src` or exclude them from package/test checks.
   - If intended production code, restore valid implementations.

3. Clean accidental top-level/stray files.
   - Review `0`, `Agent`, `The`, `-la/`, `configsls/`, `sbrcat`, `src/tar_s`, and `src/tar_system/strategicat`.

4. Remove event-loop debug printing from `backtest/engine.py`.
   - Replace with audit events or optional verbose logging.

5. Re-run health checks after the registry and syntax repairs.
   - `PYTHONPATH=src venv/bin/python -m pytest`
   - `PYTHONPATH=src venv/bin/python -m compileall src/tar_system src/master_system`

6. Make a deliberate checkpoint commit.
   - The current working tree is too broad to reason about casually.
   - Commit source/docs separately from runtime/data artifacts.

7. Resolve policy conflicts in docs.
   - `CLAUDE.md` says paper-only/no live trading.
   - Some quick-reference developer notes mention live execution/cloud deployment.
   - Keep the safety policy authoritative unless explicitly changed.

8. Decide whether the idea orchestrator exists as a planned feature or should be removed from startup instructions.
   - The requested idea orchestrator files do not exist in this snapshot.

## File Inventory Appendix

Project-owned `.py`, `.md`, and `.txt` files excluding `venv`, `.git`, and `__pycache__` were inventoried. The list includes:

```text
CHANGELOG.md
CLAUDE.md
COMPLETION_SUMMARY.md
Ideas to add/TAR_EXTERNAL_REPO_IMPORT_STRATEGY_REVIEW.md
Ideas to add/tar_markdown_pack/00_TAR_SYSTEM_INDEX.md
Ideas to add/tar_markdown_pack/01_TAR_ARCHITECTURE.md
Ideas to add/tar_markdown_pack/02_TAR_CODEX_MASTER_BUILD_PROMPT.md
Ideas to add/tar_markdown_pack/03_TAR_AGENTS_AND_HOOKS.md
Ideas to add/tar_markdown_pack/04_TAR_DATA_PIPELINE.md
Ideas to add/tar_markdown_pack/05_TAR_BACKTEST_AND_VALIDATION.md
Ideas to add/tar_markdown_pack/06_TAR_RISK_ENGINE.md
Ideas to add/tar_markdown_pack/07_TAR_DASHBOARD_UI.md
Ideas to add/tar_markdown_pack/08_TAR_GITHUB_REPO_IMPORT.md
Ideas to add/tar_markdown_pack/09_TAR_SECURITY_POLICY.md
Ideas to add/tar_markdown_pack/10_TAR_LOCAL_RUNBOOK.md
Ideas to add/tar_markdown_pack/11_TAR_OBSIDIAN_AND_LIBRARIAN.md
Ideas to add/tar_markdown_pack/12_TAR_LIVE_INTERFACE_DISABLED.md
Ideas to add/tar_missing_files_and_librarian_skill.md
PAPER_STRATEGY_IMPLEMENTATION.md
PAPER_STRATEGY_QUICK_REFERENCE.md
PHASE2_COMPLETION.txt
README.md
SYSTEM_AUDIT_20260509.txt
WEEK3_COMPLETION_REPORT.md
audit_results.py
diagnose_strategies.py
fix_cli.txt
fix_walk_forward_cli.py
master_system/memory/memory_client.py
master_system/memory_api.py
master_system/memory_client.py
quick_audit.py
requirements.txt
run_advanced_strategies.py
run_paper_strategies.py
simple_paper_trader.py
src/master_system/*
src/tar_system/*
src/v2trading/*
tests/*
```

Generated nested report files are heavily patterned by asset, timeframe, and strategy under `reports/` and `data/results/`. Dependency files under `venv/` are intentionally not repeated here because they are third-party package internals, even though they were included by the exact requested `find` command.
