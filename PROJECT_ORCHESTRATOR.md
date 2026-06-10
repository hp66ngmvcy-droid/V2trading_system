# V2 TAR Trading System Orchestrator

Extends `CLAUDE.md`. Read `CLAUDE.md` first, then this file.

## Status

ACTIVE

## Start Here

1. Read `CLAUDE.md`.
2. Read this file.
3. Read `MEMORY.md`.
4. Read `collab/STATUS.md`.
5. Read the relevant project skill under `skills/`.

## Purpose

Local paper-only trading research, strategy testing, walk-forward validation,
agent review, UI inspection, and controlled export preparation.

## Hard Rules

- Paper mode only. Never add live order submission.
- No live trading, no auto-promotion, no MT5 deployment without human approval.
- Original raw data must never be overwritten.
- Every candidate must pass tests, review, and safety gates before promotion.
- Do not mix marketing, legal, website, or design-system files into this repo.

## Current Focus

- Strategy: `vol_filtered_momentum_v1`
- Market/timeframe: `XAUUSD M15`
- Current control branch noted by user: `private/research-committee-fitter`

## Pipeline

1. idea
2. tuner
3. walk-forward
4. code candidate
5. paper test
6. review
7. manual approval gate

## EA/MT5 Gate

- Source path: `ideas/code_candidates/`
- MT5/Wine path: manual only.
- MetaEditor compile: manual only.
- User approval required before any compile, copy, or promotion.

## Pending Tasks Noted By User

1. Manually compile `VolFilteredMomentumV1_XAUUSD_M15.mq5` in MetaEditor with
   F7.
2. Run tighter `rsi_reversion_v1` threshold sweep: RSI `25/75`, `22/78`,
   `20/80`.
3. Paper signal test for at least two weeks before any live consideration.
4. Research queue: possible `gpt-researcher` integration on a dev branch; not
   started.

## Standard Checks

- Focused pytest for changed modules.
- Full local pytest when touching shared CLI, dashboard, controller, strategy,
  safety, or research-selection paths.
- `security-check` for safety-sensitive changes.
- Local construction audit before considering a phase complete.

## Completion Rule

Record significant phases in the project notes and keep the queue state honest:
no candidate should be marked ready if data, formulas, proxy decisions, or
approval gates are unresolved.
