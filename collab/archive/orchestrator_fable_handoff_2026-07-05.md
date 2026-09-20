# Orchestrator / Fable Handoff - V2 Trading

Created: 2026-07-05
Mode: paper-only research

## Purpose

Give the orchestrator and Fable a clean task packet for the V2 trading review queue without reopening old completed notes or promoting anything prematurely.

## Current Live Index

Use:

- `collab/STATUS.md`

Do not reopen completed reviewed notes unless a new update needs appending.

## Active Task

Start with:

- PER-48 - ARSB walk-forward and robustness review

Source files:

- `collab/linear_ticket_plan_2026-07-05.md`
- `collab/claude_notes/2026-07-05_arsb-v1-bug-fixed.md`
- `collab/codex_notes/2026-07-05_ordered-work-queue_done.md`

## Fable Role

Fable should be used as a reviewer/planner, not as an executor that bypasses local gates.

Fable should:

- Review fresh metrics after Codex runs the local commands.
- Challenge false positives and one-sample optimism.
- Decide whether the smallest next action is REVIEW, RETEST, HOLD, or KILL.
- Keep all output paper-only.

Fable should not:

- Create live-trading instructions.
- Suggest MT5 deployment.
- Rewrite strategy code without a separate implementation ticket.
- Treat in-sample score alone as enough for promotion.

## Suggested Fable Command

```bash
claude --fable -p "Use V2 TAR paper-only rules. Review the latest arsb_v1 XAUUSD M15 walk-forward and score evidence. Do not edit files. Decide whether it remains REVIEW, should be KILL, or deserves one narrow retest. Consider OOS Sharpe, parameter stability, bootstrap CI, trade count, profit factor, drawdown, and robustness. Return only verdict, blockers, and next action."
```

Alternative:

```bash
ANTHROPIC_MODEL=claude-fable-5 claude -p "Use V2 TAR paper-only rules. Review the latest arsb_v1 XAUUSD M15 walk-forward and score evidence. Do not edit files. Decide whether it remains REVIEW, should be KILL, or deserves one narrow retest. Consider OOS Sharpe, parameter stability, bootstrap CI, trade count, profit factor, drawdown, and robustness. Return only verdict, blockers, and next action."
```

## Codex Lead Task

Codex should run PER-48 locally:

```bash
PYTHONPATH=src venv/bin/python -m tar_system.cli run-walk-forward --strategy arsb_v1 --symbol XAUUSD --timeframe M15
PYTHONPATH=src venv/bin/python -m tar_system.cli score-strategy --strategy arsb_v1 --symbol XAUUSD --timeframe M15
```

Then write a completion note under:

- `collab/codex_notes/`

And update:

- `collab/STATUS.md`

## Linear Import Notes

Linear MCP is not available in the current Codex session. Until PER-54 is done, use `collab/linear_ticket_plan_2026-07-05.md` as the source for manual ticket creation or later automated import.

## Queue Order

1. PER-48 - Codex runs ARSB walk-forward and score.
2. PER-49 - Fable reviews ARSB blockers from fresh evidence.
3. PER-50 - Decide whether RSI deserves a narrow second pass.
4. PER-51 - Decide whether gold_v2 overlap deserves walk-forward follow-up.
5. PER-52 - Triage failed/stale queue entries.
6. PER-53 - Refresh Phase 2 optimiser plan.
7. PER-54 - Human/agent setup for Linear MCP sync.

## Hard Stop Conditions

Stop and ask the user before:

- Any MT5 compile, copy, export, or deployment.
- Any live trading or order submission.
- Any queue deletion or destructive cleanup.
- Any broad parameter sweep beyond a ticket's acceptance criteria.
- Any dependency install or external integration.
