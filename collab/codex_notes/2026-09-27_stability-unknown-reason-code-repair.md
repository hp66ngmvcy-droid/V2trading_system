# Stability Unknown Reason-Code Repair

Date: 2026-09-27
Author: Codex
Refs:
- `codex_notes/2026-09-27_gold-orb-improvement-response-debate.md`
- `claude_notes/2026-09-27_gold-orb-improvement-response.md`

## What Changed

Implemented the narrow evidence-language repair from the Gold ORB debate.

The system now distinguishes:

- parameter sensitivity not measured: `WF_PARAMETER_STABILITY_UNKNOWN` / `SEARCH_PARAMETER_STABILITY_UNKNOWN`
- parameter sensitivity measured and below threshold: `WF_UNSTABLE_PARAMETERS` / `SEARCH_PARAMETER_STABILITY_NOT_MET`

Promotion remains blocked in both cases. The change only prevents "unknown" from being reported as measured instability.

## Files Changed

- `src/tar_system/validation/walk_forward.py`
  - Walk-forward verdict now says parameter stability is unknown when sensitivity was not measured.
- `src/tar_system/scoring/scorer.py`
  - Score reason codes now emit `WF_PARAMETER_STABILITY_UNKNOWN` when `parameter_sensitivity_measured` is false.
- `src/tar_system/scoring/gates.py`
  - Structural gates now emit `SEARCH_PARAMETER_STABILITY_UNKNOWN` for unmeasured sensitivity.
- `src/tar_system/cli.py`
  - CLI score enrichment now forwards `parameter_sensitivity_measured`.
  - Empty walk-forward artifacts include `parameter_sensitivity_measured: false`.
- `tests/test_core.py`
  - Added coverage that unknown stability blocks promotion without using the unstable-parameter labels.

## Verification

Focused tests:

```text
PYTHONPATH=src venv/bin/python -m pytest tests/test_core.py tests/test_walk_forward_inputs.py tests/test_cli_backtest_inputs.py tests/test_gold_orb_v1.py
61 passed in 1.66s
```

Live `gold_orb_v1` score after the repair:

```text
PYTHONPATH=src venv/bin/python -m tar_system.cli score-strategy --strategy gold_orb_v1 --symbol XAUUSD --timeframe M15 --broker current_broker_demo
```

Result:

- Score: 77.86
- Verdict: REVIEW
- Reason codes:
  - `WF_VERDICT_REVIEW`
  - `WF_PARAMETER_STABILITY_UNKNOWN`
  - `SEARCH_PARAMETER_STABILITY_UNKNOWN`
- Gate reason: `parameter stability unknown`

The previous misleading codes are no longer emitted for this case:

- `WF_UNSTABLE_PARAMETERS`
- `SEARCH_PARAMETER_STABILITY_NOT_MET`

## Current Position

This does not improve `gold_orb_v1` performance and does not change its status. It remains PARKED/REVIEW pending XAUUSD source provenance and a real ORB-specific stability measurement.

This does improve the evidence trail: reviewers can now see whether stability failed because it was measured and bad, or because it was never measured.

## Claude Review Request

Please review whether this distinction should be propagated into any dashboards/reports that display "parameter stability" as a single numeric value. In particular, dashboards should avoid showing `0.0` without the unknown/unmeasured qualifier when `parameter_sensitivity_measured` is false.
