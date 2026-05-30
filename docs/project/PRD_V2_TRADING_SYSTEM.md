# PRD: TAR V2 Trading Research System

Status: Working Draft
Owner: WHS / local research operator
Date: 2026-05-24
Template basis: `docs/templates/source/opulo-prd-template.md`

## Overview

TAR V2 is a local-first, paper-only quantitative trading research system. It
imports market CSV data, validates and builds features, runs backtests and
walk-forward checks, scores strategies, queues paper research jobs, displays
results in a V2 web UI, and prepares manual MT5 review exports.

The system is a research and validation tool. It is not a live trading system.

## Goals

- Provide a repeatable local workflow for testing strategy ideas on imported
  OHLCV data.
- Keep all automated execution paper-only with `PAPER_MODE=True` and
  `LIVE_TRADING_ALLOWED=False`.
- Give the operator a clear dashboard for pipeline state, strategies, jobs,
  forward tests, audit log, and paper signal state.
- Preserve auditability through append-only JSONL logs and local artifacts.
- Make strategy promotion conservative: no live action, no MT5 review without
  explicit manual checklist and adequate evidence.
- Support future ideas by documenting product intent, technical requirements,
  app flow, backend schema, and implementation plan in repo-local Markdown.

## Non-Goals

- No live order placement.
- No broker login or broker API execution from the UI.
- No automated TradingView scraping or browser-session-dependent data feed.
- No cloud service dependency.
- No in-browser parameter editing for strategies.
- No raw data deletion/editing from the UI.
- No hidden or collapsed failure reason codes.

## Audience

Primary audience is a solo quant researcher/operator who wants fast local
iteration, clear evidence, and strong safety rails. The operator needs to see
what was tested, why it passed or failed, and what should happen next without
the UI implying live readiness.

Secondary audience is future coding agents working in this repo. They need
stable docs that explain what must not be changed accidentally.

## User Stories

### P1 - Review Pipeline Health

As the operator, I want to open the V2 web UI and see current jobs, recent
results, forward tests, and audit state so I can understand system health
without reading JSON files directly.

Acceptance:
- UI opens at `http://127.0.0.1:8601`.
- Snapshot refreshes every 5 seconds.
- Jobs and audit rows are sourced from local runtime files.

### P1 - Run Paper-Only Research Safely

As the operator, I want jobs to be queued through backend queue helpers so that
long-running tests do not execute directly in the browser.

Acceptance:
- UI actions queue paper jobs only.
- Duplicate active jobs are blocked by strategy/symbol/timeframe/type/data hash.
- Job history remains append-only from the UI.

### P1 - Prevent Live Trading Drift

As the operator, I want the UI and backend to make live trading impossible by
default so that research cannot accidentally become execution.

Acceptance:
- No "go live", "trade now", or "activate" action exists.
- MT5 wording says manual review.
- Broker API execution is not reachable from UI routes.

### P2 - Inspect Strategies

As the operator, I want strategy cards and detail pages to show scores, gates,
drawdown, trade counts, walk-forward evidence, and reason codes so I can decide
what to review or kill.

Acceptance:
- One-trade winners and low-sample results are not presented as viable.
- Drawdown and failure reason codes are visible.
- Missing walk-forward blocks KEEP-style promotion.

### P2 - Use Live Market Reference Links

As the operator, I want a TradingView reference link for the selected symbol and
timeframe so I can manually inspect or export market data.

Acceptance:
- Link is labelled as human reference/export only.
- Automated testing consumes only local imported files.

## Functional Requirements

- FR-001: System MUST remain local-first and paper-only.
- FR-002: System MUST import and validate CSV/tick exports into local data paths.
- FR-003: System MUST queue long-running research jobs through the queue layer.
- FR-004: System MUST expose a read-only V2 web UI snapshot endpoint.
- FR-005: UI MUST poll no faster than every 5 seconds by default.
- FR-006: UI MUST show environment/paper/live safety state.
- FR-007: UI MUST show full reason codes for failures.
- FR-008: UI MUST avoid destructive actions against raw data and JSONL audit logs.
- FR-009: Promotion board MUST require manual MT5 review language and adequate sample size.
- FR-010: Documentation MUST stay in repo-local Markdown.

## Success Metrics

- The integrated UI opens locally and refreshes without manual reload.
- Backtest, walk-forward, scoring, queue, dashboard, and web UI tests pass.
- Local construction audit reports zero findings.
- No UI route can place a trade or mutate raw data.
- New project ideas can start from the docs set without rediscovering V2 safety rules.

## Constraints

- Python backend, local files, DuckDB/JSONL mirror.
- Existing Streamlit dashboard remains legacy/operator fallback.
- Integrated web UI currently uses CDN React/Babel/Chart.js until asset bundling is hardened.
- No new heavy framework unless explicitly justified.

## Open Questions

- Should the new V2 web UI gain write endpoints for safe queue-only actions, or should operational controls stay in Streamlit until the UI is bundled locally?
- Should the minimum trade threshold be unified at 200 for all promotion gates, or remain stage-specific?
- Should generated docs be maintained manually or produced through Spec Kit feature folders?

