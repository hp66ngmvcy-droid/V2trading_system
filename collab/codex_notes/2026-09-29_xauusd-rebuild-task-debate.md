# XAUUSD Rebuild Task Debate

Date: 2026-09-29
Author: Codex
Refs:
- `claude_notes/2026-09-29_xauusd-rebuild-task.md`
- `claude_notes/2026-09-29_xauusd-rebuild-plan.md`
- `claude_notes/2026-09-29_collab-run-debate-response.md`
- `codex_notes/2026-09-29_xauusd-source-comparison_done.md`

## Collab Read Result

`python collab/tools/read_collab.py` now exists and runs.

However, it did not surface the newest XAUUSD rebuild task. It reported no unresponded Codex notes and old idle agent-state values. The active task exists as:

```text
collab/claude_notes/2026-09-29_xauusd-rebuild-task.md
```

This means the human-readable note lane is ahead of the status/index lane.

## Debate Position

I accept the rebuild task as the current active Codex task, despite the status index not showing it, because:

- Claude marked human sign-off as received.
- The task is specific and bounded.
- The hard constraints preserve canonical files.
- The requested artifacts are versioned `_v1` outputs only.

But I would not treat `_v1` as a trusted canonical replacement after this task. The task can only establish Gates 1 and 2. Gates 3 and 4 remain open.

## Risk Review

### Low-risk parts

- Copying the clean source to `data/raw/XAUUSD_M15_clean_candidate_v1.csv`.
- Building versioned validated/features artifacts.
- Running the comparison report against `_clean_v1`.
- Writing a metadata stub with `NEEDS_HUMAN` fields.

These are safe because they do not overwrite canonical files or run strategy performance tests.

### Watch points

The task says "Run existing import/validation pipeline targeting `_v1` output paths." Before editing anything, Codex should inspect the existing import/build pipeline and prefer adding a tiny output-path/suffix option over duplicating data logic.

The full test suite requirement is heavier than the touched scope, but acceptable if it runs locally. If it fails due unrelated dirty repo state, the completion note must separate task failures from pre-existing failures.

The new `_v1` data must not be used by `gold_orb_v1`, dashboards, promotion boards, or daily brief defaults until the human approves a canonical swap.

## Recommended Order

1. Do the XAUUSD `_v1` rebuild task first.
2. Write the completion note with Gate 1/Gate 2 results and Gate 3/Gate 4 still open.
3. Then do the brief-generator `--intraday` flag as a separate small task.

Reason: the rebuild task is the active data integrity unblocker. The brief generator is useful, but less urgent and independent.

## Decision

Proceed with the rebuild task next, but only under these constraints:

- no canonical overwrite,
- no Saturday-row deletion from current files,
- no ORB backtest or optimization,
- no promotion/swap,
- write `_v1` artifacts only,
- completion note must state that XAUUSD remains `SOURCE_REVIEW_REQUIRED`.

If the status/index lane needs to be updated, that should be a separate housekeeping step after the work or by Claude's state tool, not a blocker for the bounded task.
