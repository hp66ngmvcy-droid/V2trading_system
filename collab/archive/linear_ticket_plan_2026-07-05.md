# Linear Ticket Plan - V2 Trading System

Created: 2026-07-05
Scope: V2 TAR trading system, paper-only research queue.

## Rules For All Tickets

- Paper mode only.
- No live trading, no MT5 deployment, no order submission.
- Do not overwrite raw data.
- Do not promote a strategy unless tests, walk-forward evidence, review, and manual approval gates pass.
- Do not interrupt running jobs.
- Use `collab/STATUS.md` as the live task index.
- Use Fable/Sonnet/Claude as review and planning agents only unless an explicit implementation task is assigned.

## Ticket Sequence

### PER-48 - ARSB walk-forward and robustness review

Status: Ready
Owner: Codex
Priority: P1
Project: V2 Trading
Labels: `trading`, `paper-only`, `strategy-review`, `arsb-v1`

Description:

Run the next review pass for `arsb_v1` on `XAUUSD M15`. The in-sample focused tuning improved the result to 41 trades, PF 2.10, Sharpe 5.09, score 82.45, but the strategy remains blocked by robustness gates: OOS Sharpe, parameter stability, and bootstrap CI.

Acceptance criteria:

- Run walk-forward for `arsb_v1 XAUUSD M15`.
- Re-score the strategy after walk-forward.
- Record metrics and verdict in a new Codex note under `collab/codex_notes/`.
- Update `collab/STATUS.md`.
- Do not promote beyond REVIEW unless robustness gates pass and user approval is explicit.

Verification commands:

```bash
PYTHONPATH=src venv/bin/python -m tar_system.cli run-walk-forward --strategy arsb_v1 --symbol XAUUSD --timeframe M15
PYTHONPATH=src venv/bin/python -m tar_system.cli score-strategy --strategy arsb_v1 --symbol XAUUSD --timeframe M15
```

References:

- `collab/STATUS.md`
- `collab/claude_notes/2026-07-05_arsb-v1-bug-fixed.md`
- `collab/codex_notes/2026-07-05_ordered-work-queue_done.md`

### PER-49 - Fable review of ARSB promotion blockers

Status: Blocked on PER-48
Owner: Fable/Claude review
Priority: P1
Project: V2 Trading
Labels: `trading`, `review`, `fable`, `risk`

Description:

Use Fable as a strategy-review agent after PER-48 produces fresh walk-forward and scoring evidence. The review should decide whether `arsb_v1` should remain REVIEW, be killed, or be queued for a very narrow next experiment.

Acceptance criteria:

- Review only the latest ARSB metrics, walk-forward output, bootstrap CI, parameter stability, and `collab/STATUS.md`.
- Return a concise verdict: KEEP-CANDIDATE, REVIEW, KILL, or RETEST.
- Include explicit blockers and the smallest next test if RETEST.
- No code edits.
- No live trading language.

Suggested Fable prompt:

```text
Use V2 TAR paper-only rules. Review arsb_v1 XAUUSD M15 after the latest walk-forward and score run. Do not edit files. Decide whether the strategy remains REVIEW, should be KILL, or deserves one narrow retest. Consider OOS Sharpe, parameter stability, bootstrap CI, trade count, profit factor, and drawdown. Return only actionable findings, verdict, and next step.
```

References:

- `collab/codex_notes/<PER-48 output note>`
- `reports/review_summary.md`
- `runtime/ai_review_packet.md` if refreshed

### PER-50 - RSI reversion second-pass decision

Status: Ready after PER-48/49
Owner: Codex or Fable planner
Priority: P2
Project: V2 Trading
Labels: `trading`, `strategy-review`, `rsi-reversion`

Description:

Decide whether `rsi_reversion_v1 XAUUSD M15` deserves another narrow experiment. The 25/75 and NEW_YORK pass produced 548 trades but weak PF/Sharpe, so further work must be justified before spending more cycles.

Acceptance criteria:

- Review current RSI result: 548 trades, PF 1.06, Sharpe 0.41, score 76.88.
- Decide KILL, HOLD, or one narrow retest.
- If retesting, define exactly one hypothesis and its verification command.
- Do not run a broad parameter sweep without explicit approval.

References:

- `collab/codex_notes/2026-07-05_ordered-work-queue_done.md`
- `reports/review_summary.md`
- `runtime/strategy_filter_plan.md`

### PER-51 - Gold v2 overlap result review

Status: Ready after PER-48/49
Owner: Codex or Fable planner
Priority: P2
Project: V2 Trading
Labels: `trading`, `strategy-review`, `gold-v2`

Description:

Review whether `gold_v2 XAUUSD M15` with the OVERLAP session gate deserves walk-forward follow-up or should remain parked. Current result: 52 trades, PF 1.49, Sharpe 2.74, score 79.09, verdict REVIEW.

Acceptance criteria:

- Confirm whether walk-forward/OOS evidence exists and is current.
- If not current, plan the smallest walk-forward check.
- Decide HOLD, REVIEW, KILL, or RETEST.
- Record decision in `collab/STATUS.md` only if it becomes active work.

References:

- `collab/claude_notes/2026-07-05_gold-v2-overlap-session-filter.md`
- `collab/codex_notes/2026-07-05_ordered-work-queue_done.md`

### PER-52 - Strategy candidate triage cleanup

Status: Backlog
Owner: Codex
Priority: P3
Project: V2 Trading
Labels: `trading`, `queue-health`, `paper-only`

Description:

Triage old queued/failed jobs without interrupting active jobs. The latest nightly review shows 1174 total jobs, 538 active jobs, and 19 failed jobs. The purpose is to identify stale or failed jobs for human review, not delete or mutate the queue.

Acceptance criteria:

- Read queue status and failed-job buckets.
- Produce a concise triage report with recommended archive/retry/no-action groups.
- Do not delete queue entries.
- Do not interrupt active jobs.

Suggested commands:

```bash
PYTHONPATH=src venv/bin/python -m tar_system.cli queue-health --limit 20
```

References:

- `logs/nightly-review-2026-07-05.log`
- `runtime/job_queue.jsonl`
- `runtime/ops_queue_health_latest.json`

### PER-53 - Phase 2 optimiser plan refresh

Status: Backlog
Owner: Fable planner then Codex
Priority: P3
Project: V2 Trading
Labels: `trading`, `optimiser`, `planning`

Description:

Refresh the older Phase 2 optimiser improvement plan against the current implementation. Several items appear partially implemented already: structural gates, mutation work, scoring gates, and reporting. The refresh should identify what remains true, what is done, and what should be retired.

Acceptance criteria:

- Compare `docs/PHASE2_OPTIMISER_IMPROVEMENT_PLAN.md` against current code and notes.
- Produce a small status table: Done, Still Needed, Retire, Needs Decision.
- Do not implement changes in the same pass.

References:

- `docs/PHASE2_OPTIMISER_IMPROVEMENT_PLAN.md`
- `src/tar_system/optimisation/mutate_loop.py`
- `src/tar_system/scoring/`
- `collab/codex_notes/2026-07-05_ordered-work-queue_done.md`

### PER-54 - Linear MCP setup and ticket sync

Status: Human blocked
Owner: Human then Codex
Priority: P2
Project: Ops
Labels: `linear`, `mcp`, `orchestration`

Description:

Enable agent ticket operations by installing/configuring Linear MCP in the native session. Until this is done, tickets remain Markdown drafts.

Acceptance criteria:

- Human confirms Linear MCP is installed and authenticated.
- Agent can read/create/update Linear tickets.
- Import PER-48 to PER-53 from this document into Linear.
- Close or update stale Linear items only after reading their current state.

References:

- `PLAN.md` PER-47 note.
- `collab/linear_ticket_plan_2026-07-05.md`

### PER-55 - Expose multi-agent verdicts in mutate-retest output

Status: Review ticket
Owner: Codex
Priority: P2
Project: V2 Trading
Labels: `trading`, `multi-agent`, `mutate-retest`, `review`

Description:

Correct the stale B2 ticket. The bounded mutate-retest loop already exists and calls `score_strategy(...)`; `score_strategy(...)` already wires `score_multi_agent(metrics)` indirectly. The remaining gap is visibility: `src/tar_system/optimisation/mutate_loop.py` stores `score`, `verdict`, and `reason_codes`, but does not expose the multi-agent verdict, confidence, dissent flag, or per-agent reasons in the mutate-retest result artifact.

Acceptance criteria:

- Confirm `score_strategy(...)` still attaches `ScoreResult.multi_agent`.
- Extend mutate-retest iteration output to include multi-agent verdict, confidence, dissent, and concise per-agent verdicts/reasons.
- Preserve the existing JSON result shape where possible; add fields rather than renaming existing fields.
- Add/update focused tests for the mutate-retest result structure.
- Run targeted tests only; do not run live trading or broad optimiser loops.

Suggested files:

- `src/tar_system/optimisation/mutate_loop.py`
- `src/tar_system/scoring/scorer.py`
- `src/tar_system/scoring/multi_agent_scorer.py`
- `tests/test_upgrade_b_optimise_compare.py`
- `tests/test_multi_agent_scorer.py`

Verification commands:

```bash
PYTHONPATH=src venv/bin/python -m pytest tests/test_upgrade_b_optimise_compare.py tests/test_multi_agent_scorer.py -q
```

References:

- `personal-organiser/LINEAR_TICKETS_PENDING.md` stale B2 ticket.
- `collab/codex_notes/2026-07-05_ordered-work-queue_done.md`
- `src/tar_system/optimisation/mutate_loop.py`
- `src/tar_system/scoring/scorer.py`

## Recommended First Move

Start with PER-48 only. PER-49 is the review gate after fresh evidence. PER-55 is a focused follow-up and should wait until ARSB is no longer consuming the lead review lane unless multi-agent output visibility becomes the immediate blocker.
