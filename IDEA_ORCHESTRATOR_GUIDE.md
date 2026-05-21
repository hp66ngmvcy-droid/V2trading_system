# Idea Orchestrator Guide

The idea orchestrator is a local markdown workflow for capturing ideas, reviewing them daily, and promoting approved ideas into project memory.

## Files

- `idea_orchestrator.py` - local automation engine.
- `IDEA_TEMPLATE.md` - copy this for each idea.
- `ideas/inbox/` - drop new ideas here.
- `ideas/staging/` - analyzed ideas waiting for your decision.
- `ideas/approved/` - ideas you approve.
- `ideas/rejected/` - ideas you reject.
- `ideas/implemented/` - approved ideas after the orchestrator updates docs.
- `idea_reviews/` - daily review markdown files.
- `SESSION_MEMORY.md` - approved idea progress log.
- `CLAUDE.md` - receives approved enhancement notes.

## Start

```bash
cd ~/Dev/V2trading_system
python3 idea_orchestrator.py
```

For a single dry workflow pass:

```bash
python3 idea_orchestrator.py --once --no-commit --force-review
```

## Submit an Idea

```bash
cp IDEA_TEMPLATE.md ideas/inbox/idea_2026-05-14_my-idea.md
```

Edit the copied file and save it. The orchestrator scans `ideas/inbox` every 30 minutes by default, analyzes the file, adds an analysis block, and moves it to `ideas/staging`.

## Daily Review

At about 4:00 AM, daemon mode writes:

```text
idea_reviews/review_YYYY-MM-DD.md
```

The review lists staging ideas, scores, recommendations, and reasons.

## Approve or Reject

Approve:

```bash
mv ideas/staging/idea_*.md ideas/approved/
```

Reject:

```bash
mv ideas/staging/idea_*.md ideas/rejected/
```

At about 4:15 AM, daemon mode processes approved ideas, updates `CLAUDE.md` and `SESSION_MEMORY.md`, moves approved ideas to `ideas/implemented`, and commits only orchestrator-managed files unless started with `--no-commit`.

## Scoring Rules

The analyzer is intentionally simple:

- Higher priority gets a higher score.
- Clear summaries get a higher score.
- Specific components get a higher score.
- Paper-safe, validation, audit, and backtest ideas get a higher score.
- Live trading, broker API, cloud, Docker, Ray, or Polars language lowers the score.

The score is not final authority. You are. Approved/rejected folders are the gate.

## Safety Policy

The orchestrator does not run strategies, alter raw data, call external APIs, or enable live trading. It only moves markdown files and updates local project docs.
