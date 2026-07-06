---
name: task-management
description: Manage local orchestration tasks and messages safely. Use when creating, checking, reviewing, or explicitly closing work in the shared SQLite queue.
---

# Task Management

Use `/Users/whs1/Dev/shared/orchestration/database.py` with the target
project's `DB_PATH`.

## State Rules

- `pending`: waiting for review or work.
- `active`: a human or tool-capable agent is working on it.
- `review`: a text-only model produced a proposal; operator verification is
  still required.
- `done`: verified work exists and the operator or tool-capable lead confirmed
  completion.
- `failed`: attempted work failed and the reason is recorded.

Never mark a task `done` from a model response alone.

## Create Work

```python
from shared.orchestration.database import create_task

task_id = create_task(
    title="Review the scoped change",
    description="Return findings and verification requirements.",
    agent="review",
    priority=1,
    source="agent",
)
```

## Record A Proposal

```python
from shared.orchestration.database import mark_task

mark_task(task_id=42, status="review", result="Proposal awaiting verification.")
```

## Verify The Queue

```bash
DB_PATH=/absolute/project/orchestration/db.sqlite \
python3 /Users/whs1/Dev/shared/orchestration/database.py --tasks
```

Do not run migrations, delete records, reset active tasks, or start heartbeat
and Telegram services without explicit approval.
