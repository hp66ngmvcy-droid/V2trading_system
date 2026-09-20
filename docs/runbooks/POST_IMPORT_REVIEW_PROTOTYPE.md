# Post-import review prototype

Built: 2026-09-08. Stage: isolated synthetic import-to-report slice.

From the V2 project root:

```bash
PYTHONPATH=src venv/bin/python -m tar_system.reporting.post_import_review \
  --input tests/fixtures/post_import_review.json \
  --output-dir reports/post_import_review_synthetic_demo
```

The command writes `report.json` and `report.md` inside a content-addressed
directory. An identical repeat returns `reused: true`. The supplied fixture
produces one `UPPER_FIRST` observation. It is not a trade or a return.

Exit codes: 0 complete, 3 waiting for input, 2 invalid input/output or another
writer holding the lock. A corrected input, new evaluator version or changed
prompt version produces a distinct report. Prompt version is provenance only:
this prototype does not call an LLM or execute a prompt.

## Input contract

Use the JSON fixture as the complete schema example. The prototype accepts
`schema_version: 1` and `evidence_class: SYNTHETIC` only. Required dataset IDs
declare batch readiness. Dataset bars and feature payloads have canonical JSON
SHA-256 hashes; the feature source hash must match the bar hash. The public
`digest` helper computes these hashes using sorted compact JSON with finite
values. Hashes establish content consistency, not independent authenticity.

OHLC bars have explicit offset-aware open and close timestamps, a positive
integer minute cadence, finite prices and ordered non-overlapping intervals.
They must cover the entire forecast horizon without gaps. The first bar can
start at the horizon start; the last closes at its end. A forecast input's
availability precedes or equals its freeze time, which precedes evaluation.
Bar OHLC becomes available at close. Bars outside a completed forecast window
do not affect its observation label.

Frozen forecasts define lower/upper observation levels and an expected side.
The evaluator records which threshold is first reached. If both are touched
within the first triggering bar, ordering is ambiguous. No threshold reached
is unresolved. These are observational fixtures: no entry, stop-fill, slippage,
profit, win-rate or strategy-eligibility calculations occur.

One incomplete required dataset or forecast window holds the whole batch and
publishes operational findings without outcomes. Invalid chronology, malformed
bars or duplicate identifiers fail the command before publication. Existing
reports that differ from expected content are preserved and reported as errors.

## Storage and recovery

Uses the standard library only. A non-blocking advisory file lock serialises
cooperating local writers and is released by the OS when the process exits.
Reports are staged together and renamed into place. An interrupted process
before publication can be retried; a killed process might leave an unused
temporary directory, which is never counted as a completed run. This is process
crash recovery, not a guarantee against disk failure or power-loss durability.
Unix advisory locking targets the existing macOS environment.

Input identity includes the whole packet, so even an import timestamp change
creates a different revision. The real ingestion adapter must normalise stable
dataset identity and operational timestamps before claiming production-level
deduplication. No day counter accumulates from these synthetic runs.

## Verification

```bash
PYTHONPATH=src venv/bin/python -m pytest tests/test_post_import_review.py tests/test_next_layer.py::test_review_log_append -q
PYTHONPATH=src venv/bin/python -m compileall -q src/tar_system/reporting/post_import_review.py tests/test_post_import_review.py
```

Current result: 25 tests passed, including the existing reporting regression.
CLI smoke ran twice: first complete, second reused. Report inspected locally.

## Next integration slice

Identify the actual ingestion/scheduler owner. Map committed validated data and
feature versions to a stable manifest, then connect real frozen forecast records.
Add venue/research-session rules, calendar/DST fixtures and evidence-class
handling before accepting non-synthetic inputs. Preserve the original raw data.

The current prototype neither subscribes to imports nor activates a scheduler.
It does not resolve the separate sample-count/stability findings or approve
strategy eligibility. The design remains at
[post-import learning plan](../prompts/V2_POST_IMPORT_LEARNING_REVIEW_PLAN.md).
