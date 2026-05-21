---
id: task-20260516-archive-stale-repo
status: PENDING
assigned_to: codex
priority: low
depends_on: []
ready: true
created: 2026-05-16
---

# Task: Mark stale repo copy as archived so agents don't edit it
Date: 2026-05-16
Status: PENDING

## What to build

Add a clear `ARCHIVED.md` file at the root of the stale repo copy so any agent or human
opening it knows immediately not to edit it.

## Why
There are two copies of the trading system:
- `/Users/whs1/Dev/V2trading_system` — the live repo (edit here)
- `/Users/whs1/Documents/To DEl/V2trading_system` — old copy, marked for deletion

If an agent opens the wrong path and edits files there, changes are silently lost.
The folder name ("To DEl") is not a strong enough signal in context windows.

## What to do

1. Create `/Users/whs1/Documents/To DEl/V2trading_system/ARCHIVED.md` with content:

```
# ARCHIVED — DO NOT EDIT

This is a stale copy of the V2 trading system kept temporarily before deletion.

Active repo: /Users/whs1/Dev/V2trading_system

Do not make changes here. They will not be reflected in the live system.
```

2. No code changes needed. No tests needed.

## Constraints
- Do not delete anything — the user will delete the folder when ready
- Only add the ARCHIVED.md file

## Test
Confirm file exists:
```bash
ls "/Users/whs1/Documents/To DEl/V2trading_system/ARCHIVED.md"
```
