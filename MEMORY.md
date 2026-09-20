# V2 TAR Trading System Memory

Purpose: lightweight memory hook for agents working in this project.

## Current State

- Status: ACTIVE.
- Mode: paper-only trading research and validation.
- Updated: 2026-09-20
- Current focus: key_level_sweep_v1 hardening + paper collection.
- Data: XAUUSD M15 and BTCUSD M15 extended to 2026-09-20.
- key_level_sweep_v1: built, look-ahead fixed, 2 remaining HIGH blockers (conflicting
  filters, BTC schema gap). 10 briefs collected — regime/opening_type still null.
- rsi_trend_v4: OOS PF=1.44, 67 trades — needs ~150 trades to clear bootstrap CI.
- Next human action: populate `regime` + `opening_type` in 10 existing `_levels.json`
  files and add `issued_at` to all future briefs.

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
- 2026-08-23: The reusable BTCUSD/XAUUSD phone chart-review method lives at
  `docs/prompts/V2_PHONE_MULTI_TIMEFRAME_MARKET_REVIEW_PROMPT.md`; current
  market research must be refreshed for each run. Telegram remains disabled
  unless separately reviewed and approved.
- 2026-07-19: Fable seed fallback guidance is available for review routing:
  `/Users/whs1/Dev/collab/continuous-loop/LOCAL_FABLE_SEED_IDEA_2026-07-16.md`,
  `/Users/whs1/Dev/collab/continuous-loop/FABLE_AGENTIC_LOOP_WRAPPER_PROMPT_LIST_2026-07-15.md`,
  and `/Users/whs1/Dev/shared/policies/FABLE_REASONING_MODEL.md`.
  Non-Fable outputs must use `REVIEW_SOURCE: FALLBACK_REVIEW`; they cannot
  claim `FABLE_APPROVED`, close or sign off tickets, promote strategies,
  compile/copy/deploy MT5 files, enable live trading, or bypass human/security
  gates.

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
