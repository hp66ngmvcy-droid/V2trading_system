# V2 TAR Trading System Memory

Purpose: lightweight memory hook for agents working in this project.

## Current State

- Status: ACTIVE.
- Mode: paper-only trading research and validation.
- Current focus: strategy research, queue repair, parameter sweeps, paper-test
  readiness, and safety-gated review.
- Control branch noted by user: `private/research-committee-fitter`.

## Read Next

1. `CLAUDE.md`
2. `PROJECT_ORCHESTRATOR.md`
3. `collab/STATUS.md`
4. Relevant project skill under `skills/`

Use `collab/STATUS.md` as the lightweight task index. Do not reopen completed
reviewed notes unless appending a new update.

## Durable Decisions

- Paper mode only.
- No live order submission.
- No MT5 compile, copy, promotion, or deployment without explicit human
  approval.
- Raw data must not be overwritten.
- Marketing, website, legal, or design-system files do not belong in this
  project.

## Active Next Actions

1. Follow the priority queue in `collab/STATUS.md`.
2. Keep strategy candidates blocked from promotion until tests, review, and
   approval gates are satisfied.
3. Record significant phase completions in the project notes.

## Approval Gates

- Live trading: blocked.
- MT5/EA compile, copy, promotion, or deployment: manual approval required.
- Strategy promotion: manual approval required after evidence review.

## Deeper Memory

- Agent memory: `collab/agent_memory/`
- Runtime status: `runtime/*_status.json`
- Obsidian/private export material: `obsidian/private_trading_memory/`

## Update Rules

- Update this file only when durable focus, gates, or active next actions
  change.
- Put task detail in `collab/STATUS.md`, `collab/claude_notes/`, or
  `collab/codex_notes/`.
- Do not store secrets, broker credentials, or private trading data here.
