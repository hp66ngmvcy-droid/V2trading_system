# Done: Fix Search Terminates After Generation 0
Date: 2026-05-20
Reviewed by: Claude
Task: ../claude_notes/2026-05-17_fix-search-terminates-early.md

## Verification
`scripts/continuous_parameter_search.py` contains fallback logic in `next_generation`: when no candidates meet min_score threshold, best non-KILL (REVIEW preferred) candidates are used instead. Normal path (above threshold) unchanged.

236 tests pass.

## Assessment
Bug was real and evidenced by the actual search summary (scores 5.1, 4.94, 1.43 — all below 35.0 threshold). Without this fix the directional mutation and per-asset seed improvements would have no effect since the search always stopped at gen 0. Fix is correct and minimal. No issues.
