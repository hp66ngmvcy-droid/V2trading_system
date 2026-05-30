# UI/UX Brief: TAR V2 Trading Research System

Status: Working Draft
Date: 2026-05-24
Primary source: `docs/UI_DESIGN_SPEC_20260523.md`

## Product Feeling

The UI should feel like a sober research operations console: dense, readable,
fast to scan, and explicit about risk state. It should not feel like a trading
terminal that invites live execution.

## Primary Screens

- Pipeline Dashboard
- Strategy Explorer
- Strategy Detail
- Jobs / Queue Manager
- Paper Signal Monitor
- Optimisation Explorer
- Research Committee / Review Packet
- Data & Audit Log

The current integrated UI implements Dashboard, Explorer, and Detail from the
prototype. Remaining screens are specified but not fully implemented.

## UX Priorities

1. Environment risk state visible at all times.
2. Paper-only and live-trading-disabled state visible.
3. Strategy verdicts and failure reason codes are prominent.
4. Drawdown and trade count are always near performance metrics.
5. Missing walk-forward or low sample size must look blocking, not cosmetic.
6. Manual MT5 review language must not imply live readiness.

## Interaction Rules

- UI refreshes itself every 5 seconds.
- Buttons that queue jobs must say "Queue", not "Run live".
- Destructive actions are not available from browser UI.
- Parameter changes are read-only in browser.
- User must not need to inspect JSON files for normal status review.

## Visual Constraints

- Avoid marketing hero pages.
- Use tables, compact cards, badges, and status bands.
- Keep one high-signal data surface as the first viewport.
- Do not hide reason codes behind generic labels.
- Use color for state but keep text labels explicit.

## Current Gap

Operational controls are not wired in the integrated UI yet. The legacy
Streamlit dashboard remains the operational fallback until local write endpoints
are implemented and tested.

