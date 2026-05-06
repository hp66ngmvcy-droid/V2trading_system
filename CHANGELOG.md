# Changelog

## V2 Batch Asset Import Broker Coverage
- Added `scripts/import_all_assets.sh` for safe batch import and feature builds across MT5 bar CSV files.
- Updated asset profiles with availability flags, sessions, XAGUSD/ETH/XRP future stubs and USOUSD notes.
- Added XAGUSD broker specs with 5000 oz contract size and broker fallback warnings for missing symbols.
- Added `show-broker` CLI inspection command and tests for batch parsing, profiles and broker fallback behavior.
- Added `HIGH_SWAP_DRAG` warning for USOUSD overnight holding beyond one bar.
- Wired broker-aware spread, slippage, swap, margin and cost fields into paper fills and closed trades.
- Added cost sensitivity analysis and `cost-analysis` CLI command.

## V2 Gold Session Volatility Filters
- Added UTC session labels, liquid-session flag, EMA slope features and rolling ATR median.
- Added GoldV2 session, ATR volatility and EMA slope gates with explicit reason codes.
- Added asset-specific session filter settings and parameter anchor library.
- Added tests for session filtering, ATR gates, EMA slope gates and anchors.

## V2 Net Metrics Quality Gates
- Added net-PnL Sharpe, Sortino, Calmar, recovery factor and consecutive streak metrics.
- Reworked GO/NO-GO into eight named criteria with per-criterion failure reasons.
- Added deterministic pivot triggers for plateau, overfitting proxy, cost defeat and tail risk.
- Added walk-forward stable parameter ranges and optimiser anchor/range source tracking.
- Added data quality scoring with low-quality warning and block thresholds.

## V2 Position Sizing Loss Guards
- Added fixed-lot, fixed-risk, ATR-based and half-Kelly paper position sizing.
- Added broker leverage safety cap and asset-class exposure guard for sizing.
- Added consecutive, daily and weekly loss guard checks with human-reset status.
- Added equity curve JSON export with cumulative PnL and cumulative cost fields.
- Wired ATR-based sizing into paper forward tests.

## V2 Next Layer
- Added result cache, walk-forward validation, Monte Carlo robustness and parameter sensitivity.
- Added strategy ranking, review log, Obsidian export, controlled discovery and dashboard modules.
- Added CLI commands for validation, ranking, Obsidian, discovery and dashboard workflows.
- Added cron-compatible local scripts and short skills guidance files.
- Added tests for the new lean research layer.

## V2 Final Lean Safety Layer
- Expanded manual environment risk from `configs/events.yaml`.
- Added future-date event checks, environment reports, forward-test gate and MT5 export protection.
- Added promotion gate, report generation, security checks and dashboard polish.
- Added daily forward-test script and safety tests.

## V2 Risk Strategy Optimiser
- Added optimisation package with GO/NO-GO gate, regime heatmap and improvement planner.
- Added optimiser review-log and Obsidian note outputs.
- Added CLI commands for optimiser, GO/NO-GO and regime heatmap.
- Updated dashboard and reports with optimiser summaries.
- Added optimiser skill note and tests.

## V2 Optimiser Audit Fixes
- Made dashboard optimiser view read-only.
- Added local validation artifact loading for GO/NO-GO checks.
- Updated regime heatmap CLI to read saved regime-trade artifacts.

## V2 Dashboard Control Layer
- Added modular Streamlit dashboard pages and shared components.
- Added runtime status files and safe start/stop controls for paper workflows.
- Backtest loop now checks dashboard stop requests between bars.
- Added dashboard control layer tests.
- Tightened dashboard typography, wrapping and spacing so status cards, metrics, buttons and terminal output stay readable in half-screen layouts.

## V2 Local Data Import Reference
- Inspected older TAR folders for reusable gold/forex data only.
- Added MT5 tick TSV resampling to the V2 CSV importer.
- Imported and feature-built XAUUSD M15 data through the V2 pipeline.

## V2 Dashboard Visual Polish
- Added a small Streamlit design layer with themed cards, metric rows and status pills.
- Updated core dashboard pages with cleaner layouts and filters.
- Made direct Streamlit execution resolve the local `src` package path.

## V2 Pipeline Automation
- Added dedicated MT5 tick detection and OHLCV conversion with `_clean.csv` sidecar output.
- Wired `import-csv` to auto-detect tick versus OHLCV data without overwriting original raw files.
- Added `convert-ticks` and `run-full-pipeline` CLI commands with safe audit logging.
- Added a dashboard full-pipeline control and tests for conversion, pipeline outputs and safe failure.

## V2 Pipeline Resume Safety
- Added local pipeline checkpoints in `runtime/pipeline_status.json`.
- Inserted the forward-test gate before scoring and memory writes.
- Added partial backtest protection so stopped runs are not scored into memory.
- Capped full-pipeline walk-forward splits for large local datasets.
- Added `--resume` and `--max-walk-forward-splits` to `run-full-pipeline`.

## V2 Upgrade A Assets Brokers Resolver
- Added asset profiles and registry for crypto, metals, commodities and forex symbols.
- Added paper-only broker profile dataclasses and loader for `current_broker_demo`.
- Added asset-aware strategy variant resolution for `strategy + symbol + timeframe`.
- Added broker-aware paper margin, cost and liquidation-warning estimates.
- Added `resolve-strategy` CLI command and tests for profiles, resolver and margin safety.

## V2 Upgrade B Optimise Compare Memory
- Expanded DuckDB strategy memory with asset, broker, variant, validation and promotion fields.
- Added one-parameter-at-a-time optimisation space and `optimise-asset` command.
- Added asset comparison engine and `compare-assets` command.
- Added bounded optimiser row windows for local performance on large M5 datasets.
- Added tests for optimiser mutations, asset comparison and expanded memory writes.

## V2 Upgrade C Forward Agents Dashboard
- Added incremental paper-only forward-test engine with new-bar state tracking.
- Added lightweight local agent wrappers and oversight paper-mode checks.
- Wired `forward-test` CLI to the real paper loop with broker-aware resolver support.
- Updated dashboard run controls with broker selector, forward-test execution, comparison, audit and memory views.
- Added tests for forward-test state, agent imports and CLI broker support.

## V2 RSI Reversion Regime Layer
- Added Bollinger Band feature columns and price-in-band location.
- Added `rsi_reversion_v1` mean-reversion strategy with ranging-regime and session filters.
- Added regime-aware strategy selector for paper forward tests.
- Added RSI reversion anchors and asset-aware variant parameters.
- Added variant comparison report and `compare-variants` CLI command.
- Added `scripts/run_all_backtests.sh` for overnight paper-only combination runs.
- Added tests for Bollinger features, RSI reversion signals, regime selector, variant reports and batch script helpers.

## V2 Dashboard Promotion Layer
- Added EA promotion Kanban board with MT5 review green-light, retest and kill actions.
- Added manual MT5 promotion log at `runtime/mt5_promotion_log.json`.
- Added daily summary dashboard page for audit, events, schedules and comparison snapshots.
- Added forensic GO/NO-GO criteria section to strategy detail.
- Added margin utilisation warning states to overview.
- Added scheduled job viewer controls and run-all-backtests launcher to run control.
- Added tests for promotion gates, daily summary, forensic criteria and margin warning thresholds.

## V2 Local Research Controller
- Added paper-only controller modules for raw-data watching, JSONL job queue and rule-based recommendations.
- Added bull/bear debate checks with cost-sensitive override to REVIEW.
- Added CLI commands `queue-job`, `show-queue` and `run-controller`.
- Updated scheduled worker and dashboard run control with research queue visibility.
- Added tests for data watcher, queue updates, controller safety states, debate recommendations and MT5 non-promotion guard.

## V2 Scale Foundation
- Upgraded the research queue to DuckDB with status, target and hash indexes while keeping a JSONL mirror.
- Added artifact cache table for compute-once result lookup and metadata.
- Added `run-worker` CLI for background queued-job processing.
- Added `load-test` CLI for synthetic queue/cache scale checks.
- Added dashboard queue stats and tests for indexed queue, artifact cache, worker and load-test behavior.

## V2 Positioning Context Layer
- Added local COT CSV importer and manual positioning note importer for Codex, ChatGPT, Claude or human summaries.
- Added DuckDB positioning store and blended `positioning-score` context.
- Added positioning context to reports, optimiser output, GO/NO-GO context and dashboard.
- Added CLI commands `import-cot`, `import-positioning-note` and `positioning-score`.
- Added tests for COT import, manual note import, scoring, CLI wiring and report context.

## V2 Research Loop Controller
- Added V2-native paper-only research loop that scans local raw CSV data, queues only missing strategy/data-hash tests and writes daily summaries.
- Tightened data watcher duplicate logic to skip per strategy/date hash instead of skipping an entire data file too early.
- Added active-job duplicate protection to the DuckDB queue.
- Added CLI commands `run-research-loop` and `research-summary`.
- Added dashboard next-action visibility for the research queue.
- Added tests for per-strategy duplicate guards, loop summaries and next-action recommendations.

## V2 Queue Safety Audit Fixes
- Added atomic DuckDB job claiming so concurrent workers cannot take the same queued job.
- Changed active-job dedupe to prefer strategy/symbol/timeframe/type/data-hash over exact file paths.
- Cached active queue keys during raw-data scans to avoid repeated full queue reads.
- Filtered research-loop best-candidate recommendations to KEEP or strong REVIEW results only.
- Added tests for atomic claim, hash-based dedupe and weak-candidate filtering.

## V2 Staged Research Runs
- Added queued job metadata for research stage, backtest date windows, forward-test date, walk-forward skip and split caps.
- Updated the research loop to queue smoke-stage jobs on recent data before full-history jobs.
- Gave smoke jobs higher queue priority so small tests run before large full-history tests.
- Wired staged queue metadata through the controller into `run-full-pipeline`, including smoke-stage forward-test skipping.
- Added tests for smoke-window queueing and staged controller pipeline arguments.

## V2 Legacy Risk Preset Layer
- Added research-only `kama_kt_pullback_fx_risk` YAML preset with risk, spread, stop, cooldown, breakeven, time-stop and margin controls only.
- Added legacy preset loader with safety validation and no new YAML dependency.
- Added legacy risk adapter that exposes TAR risk-input limits and reason-code context without importing legacy entries or execution triggers.
- Added tests for preset loading, research-only enforcement and adapted risk limits.

## V2 Dashboard Operator Controls
- Added global dashboard run state with run id, task identity, heartbeat, progress, live metrics, terminal lines and run history.
- Rebuilt Run Control as an operator panel with status card, grouped state-aware buttons, run lock, checklist, dataset summary and strategy summary.
- Added date presets with dataset-constrained calendar selectors and paper-only backtest subprocess logging.
- Added live activity feed, terminal/code output panel, previous runs table and explicit audit events for dashboard button actions.
- Added dashboard runtime tests for run lock, stop/reset flow and activity feed events.
- Added local auto-refresh while dashboard tasks are RUNNING or STOPPING so status and terminal output update without manual refresh.
- Moved primary operator actions into a top action bar so Start, Stop, Reset, checks, feature builds, exports and reports are accessible without scrolling.
- Persisted the selected dashboard section in Streamlit session state so Reset Run clears status without taking the operator off the current page.
- Fixed stale dashboard completion detection so a finished pipeline log immediately moves the run state to COMPLETED and disables Stop.
- Fixed environment checks for timezone-aware dashboard timestamps and refreshed Reset Run immediately in place.
- Replaced deprecated Streamlit dashboard width arguments with `width="stretch"` for buttons and tables.
- Added Run All Tests batch controls that queue every recognised raw CSV/strategy combination for the background paper worker using the selected A-B date range.
- Added optional daily Run All Tests scheduling with a time picker and recurring scheduled batch queue jobs.
- Added stable Streamlit session keys so dashboard selections, filters, date presets and batch preferences persist when switching pages.
- Added a stable key for Promotion Board manual checklist confirmations and removed Streamlit widget default/session-state warnings in Run Control.
