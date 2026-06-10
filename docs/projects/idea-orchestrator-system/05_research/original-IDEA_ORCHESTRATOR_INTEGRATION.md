# Idea Orchestrator Integration

The orchestrator connects to the existing V2 trading system as a documentation and planning layer. It does not modify trading code, run backtests, or write strategy memory from partial runs.

## Integration Points

| Existing area | Connection |
|---|---|
| `CLAUDE.md` | Approved ideas are appended under approved enhancement notes. |
| `docs/projects/idea-orchestrator-system/03_delivery/SESSION_MEMORY.md` | Approved ideas are logged with score, component, and analysis. |
| Git | Approved idea updates can be auto-committed, but only orchestrator-managed paths are staged. |
| `ideas/` | Human approval gate: inbox, staging, approved, rejected, implemented. |
| `idea_reviews/` | Daily operator review files. |
| TAR policy | Paper-only and local-first rules are included in scoring and safety notes. |

## Workflow

```text
ideas/inbox/idea_*.md
  -> analyze
  -> ideas/staging/idea_*.md
  -> daily review
  -> human moves to approved or rejected
  -> approved ideas update CLAUDE.md and docs/projects/idea-orchestrator-system/03_delivery/SESSION_MEMORY.md
  -> ideas/implemented/idea_*.md
```

## Why It Helps

- Ideas are captured as files instead of chat fragments.
- Every idea has a stable audit trail.
- The morning review keeps planning lightweight.
- Approved ideas become visible in the normal project entry documents.
- Auto-commit is narrow and avoids committing unrelated runtime/data changes.

## Commands

Start continuous mode:

```bash
python3 idea_orchestrator.py
```

Run once without committing:

```bash
python3 idea_orchestrator.py --once --no-commit --force-review
```

Process approved ideas and allow a managed commit:

```bash
python3 idea_orchestrator.py --once
```

## Managed Commit Scope

The orchestrator stages only:

- `idea_orchestrator.py`
- `docs/projects/idea-orchestrator-system/assets/IDEA_TEMPLATE.md`
- `docs/projects/idea-orchestrator-system/05_research/original-IDEA_ORCHESTRATOR_GUIDE.md`
- `IDEA_ORCHESTRATOR_INTEGRATION.md`
- `docs/projects/idea-orchestrator-system/03_delivery/START_IDEA_ORCHESTRATOR.txt`
- `docs/projects/idea-orchestrator-system/03_delivery/SESSION_MEMORY.md`
- `CLAUDE.md`
- `ideas/**`
- `idea_reviews/**`

It does not stage `data/`, `runtime/`, source changes, or other unrelated dirty files.
