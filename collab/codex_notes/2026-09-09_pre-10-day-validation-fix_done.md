# Pre-10-day validation repair

Interpreting as: have Claude review the completed prototype and the two
validation issues, then produce and apply a concrete repair decision before
the 10-day data collection continues.

Date: 2026-09-09
REVIEW_SOURCE: CLAUDE_REVIEW_AND_CODEX_ADJUDICATION
Status: DONE_AND_LOCALLY_TESTED
Approval ID: `user-request-20260909-v2-pre10-validation-fix`

## Decision

Claude returned `PATCH_NOW`. The response passed the local correspondence
guard with five required sections and three anchors; SHA-256:
`8d8d13c7737e9ac4c8660b2d22068764f94633fdfc2eb684db2a5f615dd52b4b`.
Only the manually abstracted `PUBLIC_TECHNICAL_ONLY` packet was sent.

Lead adjudication adopted the 20 stitched-OOS-trade minimum and fail-closed
handling of unmeasured sensitivity. It did not copy Claude's proposed `FAIL`
verdict because this project uses `KEEP/REVIEW`; insufficient evidence now
returns `REVIEW`. It also retained the existing bootstrap payload shape rather
than removing fields and creating a compatibility change.

## Changes

- Walk-forward requires at least 20 stitched out-of-sample trades for `KEEP`.
- Downstream scoring independently reports `WF_LOW_TRADE_COUNT` for 1–19 OOS
  trades, so a stale or forged `wf_verdict=KEEP` payload cannot bypass the
  sample gate.
- Identical parameter dictionaries across folds now score `0.0`, not `100.0`.
- Walk-forward results add `parameter_sensitivity_measured`; repeated fixed
  configurations are labelled `unmeasured`.
- CLI and optimiser result payloads carry the additive measured flag.
- Regression coverage includes five and 19 trades, the 20-trade boundary,
  identical parameters, varied stable parameters, and downstream bypass.

## Verification

Executed from the project root:

- `PYTHONPATH=src venv/bin/python -m pytest tests/test_optimisation_layer.py tests/test_core.py tests/test_pipeline_automation.py -q` — 64 passed.
- `PYTHONPATH=src venv/bin/python -m compileall -q src/tar_system/validation/walk_forward.py src/tar_system/scoring/scorer.py src/tar_system/optimisation/optimiser.py src/tar_system/cli.py` — exit 0.
- `PYTHONPATH=src venv/bin/python -m pytest -q` — 432 passed.
- Import-boundary search found no walk-forward, promotion, approval or readiness
  call in `post_import_review.py`; it explicitly labels synthetic observations
  as non-promotion evidence.

The working tree already contained unrelated user changes. They were preserved.

## Boundaries and residual limits

- This changes validation only. It does not start data input, a scheduler,
  feeds, promotion, MT5 work or live trading.
- The ten prospective daily observations remain learning/comparison evidence;
  they never count towards the 20 historical OOS trades.
- Aggregate OOS minimum is enforced; a per-fold trade minimum remains a later
  research decision.
- The numeric stability calculation still describes parameter-selection
  variation, not a complete performance-sensitivity surface. The new measured
  flag makes the untested case explicit; a future version may add a declared
  sensitivity method.
- The prospective prototype remains synthetic-only and independently reviewed
  status must not be confused with readiness for a real-data adapter or
  scheduler.

Claude response:
`collab/claude_notes/2026-09-09_pre-10-day-validation-fix-review.md`.

Collab follow-up for independent post-patch review:
`collab/CODEX_TO_CLAUDE_PRE10_VALIDATION_HANDOFF_2026-09-09.md`.
