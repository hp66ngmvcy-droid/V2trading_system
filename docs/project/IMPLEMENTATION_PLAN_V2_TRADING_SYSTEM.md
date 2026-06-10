# Implementation Plan: TAR V2 Trading System Docs And UI Integration

Status: Working Draft
Date: 2026-05-24
Template basis: `docs/templates/source/spec-kit-plan-template.md`

## Summary

Bring the V2 project docs and integrated web UI to a stable baseline: docs are
clear enough for future ideas, the UI self-refreshes from local runtime data,
and write actions are added only after safe queue endpoints exist.

## Phase 0 - Template And Doc Baseline

- Copy installed Spec Kit templates into `docs/templates/source/`.
- Download PRD source template and license into `docs/templates/source/`.
- Create V2-specific PRD, TRD, App Flow, UI/UX Brief, Backend Schema, and
  Implementation Plan under `docs/project/`.
- Add docs index for future project ideas.

Exit criteria:

- Docs exist and point to current source-of-truth files.
- No doc implies live trading or automated broker execution.

## Phase 1 - Integrated UI Read Model

Completed/current:

- Serve `ui/research-ui/index.html` on `127.0.0.1:8601`.
- Expose `GET /api/snapshot`.
- Expose `GET /runtime-data.js`.
- Feed strategies, jobs, forward tests, imported data, paper signal, static
  findings, and audit rows from local files.
- Poll snapshot every 5 seconds in the browser shell.

Exit criteria:

- `tests/test_web_ui_integration.py` passes.
- UI opens and self-updates without browser reload.
- Snapshot endpoint is bounded and quick.

## Phase 2 - Safe Write Endpoints

Add local-only POST endpoints:

- Queue paper research job.
- Queue paper signal job.
- Queue run-all-tests batch.
- Request stop active task.

Rules:

- No arbitrary shell endpoint.
- No broker/live endpoint.
- Each write appends activity/audit.
- Each write validates symbol/timeframe/strategy against allowlists or existing
  known files.
- Each write returns structured status for UI toast/state.

Tests:

- Endpoint tests for valid/invalid payloads.
- Queue dedupe tests.
- Stop request tests.
- No-live/no-MT5-promotion assertions.

## Phase 3 - New UI Operational Screens

Implement in integrated UI:

- Jobs screen.
- Paper signal monitor.
- Data and audit screen.
- Run controls using only safe endpoints.
- Error and success states for queued actions.

Exit criteria:

- Operator no longer needs Streamlit for common queue actions.
- Streamlit remains available as legacy fallback.

## Phase 4 - Frontend Hardening

- Replace CDN React/Babel/Chart.js with local bundled assets or a proper
  lightweight build.
- Remove browser Babel from production path.
- Add screenshot/browser smoke checks if browser automation is available.

Exit criteria:

- UI works without internet access.
- Static audit still passes.

## Phase 5 - Schema And Threshold Cleanup

- Reconcile 30-trade historical gate wording with 200-trade manual MT5 review
  promotion threshold.
- Add explicit schema tests for snapshot rows.
- Add docs checks for no live-trading language.

## Current Next Best Task

Implement Phase 2 safe write endpoints and wire UI buttons to queue-only
actions. This is the missing piece for Start/Stop/Run All from the new UI.

