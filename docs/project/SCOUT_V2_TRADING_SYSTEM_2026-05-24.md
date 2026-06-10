# V2 Trading System Scout - 2026-05-24

## Scout Purpose

This is a `/scout` pass across the V2 trading system. It checks the major
areas, records what needs to be achieved, and sets the next operating stage.

Mode remains paper-only, local-first, and no live broker execution.

## Current System Map

| Area | Current State | Scout Read |
| --- | --- | --- |
| Project docs | PRD, TRD, app flow, UI brief, backend schema, implementation plan exist under `docs/project/` | Good baseline; next docs should track stages and decisions |
| Data pipeline | Raw, validated, and feature data exist for major symbols/timeframes | Usable for controlled backtest work |
| Backtester | Backtest engine, metrics, cost analysis, forward test, walk-forward, null model, bootstrap, parameter sensitivity exist | Strong enough to reject weak ideas |
| Scoring/gates | Structural gates, multi-agent scorer, failure logger, go/no-go gate exist | Good safety backbone; keep gating before promotion |
| Optimisation/tuning | Optimiser, parameter anchors/space, regime heatmap, improvement planner, Stage 1-3 tuner exist | Next work should focus on filter tuning and queue triage |
| Research committee | Committee reports and filter plan exist in runtime | Useful for KILL/REVIEW reasoning |
| UI | Integrated web UI has read-only snapshot bridge and self-refresh | Next missing piece is safe write endpoints |
| Idea orchestrator | Continual idea engine, hypothesis notes, research-quality scoring, daily review model documented | Needs implementation queues and scout command later |
| Librarian/workspace | Project folder system, manifest, librarian guide, archive cleanup exist | Good enough for organizing new work |
| Security | Local `security-check` passed with no findings | Keep no-live/no-broker guardrails |

## Runtime Scout Findings

Queue state:

```text
COMPLETED: 188
FAILED: 591
QUEUED: 0
RUNNING: 0
SKIPPED: 392
TOTAL: 1171
```

Research stages:

```text
continuous_all_strategies: 748
dashboard_batch: 268
smoke: 70
full: 69
paper_review: 8
dashboard: 1
none: 7
```

Current research summary says:

- Review 591 failed jobs before rerunning.
- Review best scored candidate: `gold_v2 XAUUSD M1 score=70.3`.
- Consider manual MT5 review gate for `gold_v2 BTCUSD H1`.

Strategy health currently shows WATCH states, not promotion states:

- `liquidity_sweep_v1:XAUUSD:M15`: WATCH, sample too small.
- `gold_v2:XAUUSD:M1`: WATCH, sample too small / one-trade style risk.

## Main Blockers

1. Queue quality
   - 591 failed jobs are too many to blindly rerun.
   - Need failure classification before new broad searches.

2. Drawdown and cost realism
   - Session memory says XAUUSD M15 has good signal quality but unacceptable
     drawdown.
   - Next practical stage is broker cost modelling and volatility/drawdown
     control, not more raw strategy ideas.

3. UI write path
   - New UI can read local runtime state.
   - Start/Stop/Run All still needs local-only, validated POST endpoints.

4. Idea-to-backtest bridge
   - The theory is now documented.
   - Actual folders/commands for `ideas/research_queue/` and
     `ideas/backtest_candidates/` still need implementation.

5. Candidate promotion clarity
   - Historical docs mention 30-trade gates, while manual MT5 review may need a
     higher threshold.
   - Need one explicit promotion ladder: WATCH -> REVIEW -> PAPER_FORWARD ->
     MANUAL_EXPORT_CANDIDATE.

## Stage Operating Plan

### Stage A - Stabilize Operations

Goal: make the current system easy to operate without creating more noise.

Actions:

- Classify failed queue jobs by failure reason.
- Mark stale/duplicate/obsolete failures as archived or skipped.
- Keep active queue at zero before new broad runs.
- Add a compact queue health report.

Exit criteria:

- Failed jobs grouped by cause.
- No blind rerun of all failed jobs.
- Daily scout report can show queue health in one screen.

### Stage B - Safe UI Control Layer

Goal: make the integrated web UI useful for normal operation.

Actions:

- Add local-only POST endpoints:
  - queue paper research job
  - queue paper signal job
  - run all tests batch
  - request stop active task
- Validate payloads against known symbols/timeframes/strategies/files.
- Append audit/activity records.
- Wire UI Start/Stop/Run All to these endpoints.

Exit criteria:

- UI can queue and stop paper-only tasks.
- Tests cover valid/invalid payloads.
- No shell endpoint, broker endpoint, or live-trading endpoint exists.

### Stage C - Filter And Drawdown Tuning

Goal: improve strategy quality by testing filters scientifically.

Actions:

- Start with confirmed XAUUSD M15 baseline.
- Test one filter family at a time:
  - broker costs/spread
  - ATR volatility cap
  - session filter
  - trend/range regime filter
  - position sizing / drawdown cap
- Record trade-count delta, PF delta, DD delta, OOS delta, and parameter
  stability delta.

Exit criteria:

- Drawdown reduction is proven without destroying trade count.
- Filter decision records exist.
- No multi-change parameter experiments without isolation.

### Stage D - Idea Orchestrator `/scout`

Goal: make continual idea generation useful, not noisy.

Actions:

- Add folders:
  - `ideas/research_queue/`
  - `ideas/backtest_candidates/`
  - `ideas/code_candidates/`
  - `ideas/security_review/`
- Add hypothesis schema and source-quality scoring.
- Add a daily scout output:
  - new sources
  - rejected junk
  - linked patterns
  - filter-tuning candidates
  - backtest candidates

Exit criteria:

- Online/user ideas become structured hypothesis notes.
- Only approved, safe, testable hypotheses reach the backtester.
- Pattern links connect MIT/AQR/research ideas to V2 filter families.

### Stage E - Candidate Promotion Ladder

Goal: make promotion impossible without evidence.

Actions:

- Define states:

```text
WATCH
  -> REVIEW
  -> PAPER_FORWARD
  -> MANUAL_EXPORT_CANDIDATE
  -> ARCHIVE/KILL
```

- Require minimum evidence for each state:
  - after-cost backtest
  - minimum trades
  - walk-forward evidence
  - parameter stability
  - bootstrap/null model check
  - drawdown cap
  - human review

Exit criteria:

- No strategy can be interpreted as live-ready.
- Manual export candidate is distinct from live trading.

## Next Best Stage

Start with **Stage A: Stabilize Operations**, then immediately follow with
**Stage B: Safe UI Control Layer**.

Reason:

- The queue has 591 failed jobs and no active jobs. This is the right moment to
  classify and clean the operating state.
- The UI read model is already working, but operator controls need safe write
  endpoints.
- Strategy research should pause broad reruns until failed jobs and filter
  stages are clean.

## Next Commands To Run Manually

Use these in order:

```bash
PYTHONPATH=src venv/bin/python -m tar_system.cli research-summary
PYTHONPATH=src venv/bin/python -m tar_system.cli security-check
PYTHONPATH=src venv/bin/python -m pytest tests/test_web_ui_integration.py
PYTHONPATH=src venv/bin/python -m pytest
```

Avoid broad queue reruns until failed jobs have been classified.

## Decision

The V2 project should operate next as a controlled research system, not a
bigger search loop. The immediate priority is queue cleanup, safe UI operations,
and one-filter-at-a-time drawdown reduction.
