# Synthetic post-import review prototype

Interpreting as: build and test the first isolated local import-to-report prototype.

Date: 2026-09-08; completion reconciled 2026-09-09
REVIEW_SOURCE: FALLBACK_REVIEW
Status: DONE_AND_LOCALLY_TESTED — synthetic prototype, independent review pending.
Collab task: `V2-POST-IMPORT-PROTOTYPE-001` marked `DONE` in the state store.

Implemented a separate standard-library reporting module and command, JSON
fixture, focused tests and [runbook](../../docs/runbooks/POST_IMPORT_REVIEW_PROTOTYPE.md).
Reused existing report-directory conventions; did not write strategy review or
memory tables because synthetic observations are not strategy results.

Behaviour: manifest readiness, bar/feature hashes, lineage, forecast timing,
regular-bar coverage, upper/lower first-touch observation labels, same-bar
ambiguity, duplicate protection, report-pair publication and advisory locking.
Partial input saves a waiting report with no outcomes. Synthetic runs always
contribute zero eligible prospective days. No LLM, dependency, importer, main
CLI, scheduler, scoring gate or existing strategy was changed.

Verification:

- `PYTHONPATH=src venv/bin/python -m pytest tests/test_post_import_review.py tests/test_next_layer.py::test_review_log_append -q`: 25 passed, exit 0.
- `PYTHONPATH=src venv/bin/python -m compileall -q src/tar_system/reporting/post_import_review.py tests/test_post_import_review.py`: passed.
- Runbook CLI command: first `COMPLETE`, reused false; second `COMPLETE`, reused true. Saved JSON/Markdown inspected; one synthetic upper-first outcome.
- Workspace `git diff --check` flags a pre-existing trailing blank line in the unrelated strategy registry; left untouched. New-file whitespace checked separately.

Local adversarial pass tightened integrity checks to compare both JSON and
Markdown, then added interruption/concurrent-writer tests. Initial 18 tests
passed; final authoritative result is 25 including the reporting regression.
No external reviewer was invoked for this implementation.

Completion reconciliation, 2026-09-09: reran the focused suite with 25 passing
tests and reran compileall with exit 0. Registered and completed the task in
the shared state store, then regenerated `collab/STATUS.md`. The generated
review state is `DONE`, not `REVIEWED`; independent review remains the next
gate before a real-data adapter or scheduler activation.

Limits: fixture-only input, no real-data adapter, no named-session calendar,
no prospective forecast provenance proof, no strategy evaluation, and no
durable scheduler. Atomic rename handles normal process interruption but no
power-loss durability guarantee is made. Full packet identity includes import
time; production adapter deduplication remains a separate integration task.

Next: inspect the active import owner and design its committed-data manifest
adapter, with real evidence-class and session validation, before activation.
