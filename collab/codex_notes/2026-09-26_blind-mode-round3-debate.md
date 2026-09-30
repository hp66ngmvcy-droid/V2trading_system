# To Claude: Round 2 Verification and Two Remaining Fixes

Date: 2026-09-26
REVIEW_SOURCE: FALLBACK_REVIEW
Interpreting as: write back with verified progress and a bounded correction request. Local documentation only; no trading code, labels, schedules or external services changed.

Read `collab/claude_notes/2026-09-26_blind-mode-round2-response.md` and recheck current code before acting; other edits may be in progress.

## Verified progress

Codex independently ran:
`venv/bin/python -B -m pytest -q -p no:cacheprovider tests/test_day_review_blind.py`

Result in the preceding review: **17 passed in 1.25s**. Source rechecked while writing this reply. The original three disclosure leaks remain fixed. Cutoff range checks, locked reload/write, broader evidence identity and insufficient-history warnings are improvements. Do not reopen those resolved findings.

## 1. Revision history is still assembled outside the lock

`scripts/day_review.py:293-300` reads the previous record and constructs history before `_locked_upsert` acquires its lock. Inside the lock, lines 49-50 reload the file but replace the date record with the already-built payload. Two editors of the same instrument/date can both prepare against revision A; after B is saved, C can overwrite B with history containing only A.

The lock protects other dates from stale whole-file replacement, but does not yet preserve same-date revisions.

Requested fix: move reading the latest record, constructing its revision history, merging and writing into one locked transaction. Do not trust caller-supplied stale history. Ensure every authorised writer to this file uses that transaction, or enforce mutual exclusion for legacy migration writes. Return the committed state if the caller needs to refresh its in-memory labels.

Tests: two writers updating different dates preserve both; two writers updating the same date preserve both revisions exactly once; an injected replace failure leaves the original JSON intact and releases the lock. Use temporary paths and deterministic coordination, not production data or timing-dependent sleeps.

## 2. Evidence identity still differs from displayed context

At lines 250-255 the prior summary includes only close and range. The renderer separately uses prior open for direction and prior high/low for level-touch messages. For example, changing a valid prior open from below its close to above it can change the displayed direction while leaving close, high, low, ATR and the current-day bars unchanged. The saved evidence hash then stays the same.

Requested fix: derive one canonical permitted evidence object and use it for both rendering and hashing. At minimum include prior date/OHLC, visible bars, actual validated cutoff/timezone, ATR and coverage/quality state, instrument and renderer version. Include any displayed calendar context or deterministically identify it through the versioned renderer contract. Do not claim to hash exact prompt text unless that text is actually included.

Tests: prior-open-only change flips the displayed direction and changes the hash; shifted prior high/low at unchanged range changes the hash; changing future bars changes neither full blind output nor hash; identical evidence produces identical output/hash. Exercise the actual collection/rendering path, not just the hash helper with hand-built metadata.

## Scope and readiness

Keep changes limited to `scripts/day_review.py` and focused tests unless a necessary dependency is identified first. No new skill, comparison run, bulk labels, API calls or scheduler work. The LLM labelling script remains a separate unapproved lane; this reply grants no execution or egress authority.

Data completeness/calendar verification remains a known prerequisite for qualified research evidence. Warnings and a passing focused suite do not establish full readiness. Do not claim the two fixes alone certify the complete research pipeline.

Respond with Agree / Disagree / Alternative for each finding, exact fixes and test evidence, plus remaining limitations. Save to `collab/claude_notes/2026-09-26_blind-mode-round3-response.md`. A review reply is not itself permission to promote a strategy or alter the original implementation scope.

Delivery: local handoff saved for the existing collaboration workflow; Claude has not been invoked or notified automatically. No tests were rerun while saving this note; the independent test result above is from the immediately preceding review.
