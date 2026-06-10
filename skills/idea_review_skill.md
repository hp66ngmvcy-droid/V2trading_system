# Idea Review Skill

Use this skill when reviewing ideas in `ideas/inbox/` or when `/heal` is invoked.

## What this skill does

Reads every file in `ideas/inbox/`, reviews each idea against the system, then:
- Moves it to `ideas/approved/`, `ideas/staging/`, or `ideas/rejected/`
- Writes a review note inside the file before moving it
- If approved, creates a Claude task note in `collab/claude_notes/` for Codex

No code is written during this review. This is a triage and routing step only.

## Review criteria

### Hard reject (move to `ideas/rejected/`)
- Requires live trading, broker API, cloud dependency, or paid API
- Duplicates something already implemented (check `ideas/implemented/`)
- Breaks the no-Docker, no-Ray, no-OpenAI constraint
- Would require rewriting a stable, tested module from scratch

### Staging (move to `ideas/staging/`)
- Good idea but depends on a task not yet completed in `collab/_state.yaml`
- Good idea but needs more research before a task note can be written
- Good idea but scope is too large to implement in one Codex task

### Approved (move to `ideas/approved/` + create collab task note)
- Fits the system constraints in `collab/shared/system_constraints.md`
- Has a clear implementation path that Codex can follow
- Does not break existing tests
- Adds genuine value: new validation, new strategy signal, new gate, or new report

## How to write the review block

Append this block to the idea file before moving it:

```
---
## Claude Review
Date: YYYY-MM-DD
Verdict: APPROVED | STAGING | REJECTED
Reason: <one sentence>
Depends on: <task ID from _state.yaml, or "nothing">
Codex task created: YES | NO | N/A
---
```

## Collab task note rules

Only create a collab task note for APPROVED ideas.
Follow the standard format in `collab/PROTOCOL.md`.
Add the task to `collab/STATUS.md` and `collab/_state.yaml` under `pending_tasks`.
Set `priority` based on: HIGH if it fixes a current blocker, NORMAL if it adds a feature, LOW if it is cosmetic or docs.
