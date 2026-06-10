# V2 Trading Workspace Manifest

Read this first when entering the workspace. It explains what each major folder
does and where new work should go.

## Primary System

| Area | Path | Purpose |
| --- | --- | --- |
| Trading system code | `src/tar_system/` | Main V2 trading research package: data validation, features, backtests, scoring, UI bridges, paper workflows, reports, and runtime control. |
| Legacy/transition code | `src/v2trading/` | Older V2 package fragments. Treat as legacy unless a task explicitly targets it. |
| Master/orchestration code | `src/master_system/` | Higher-level domain/orchestration experiments. Check purpose before extending. |
| Tests | `tests/` | Python tests for the trading system and dashboard/control layers. |
| Scripts | `scripts/` | Repo-level commands, audits, setup helpers, and local workflow scripts. |

## Data And Runtime

| Area | Path | Purpose |
| --- | --- | --- |
| Raw/validated/features/results | `data/` | Local trading data inputs and generated research outputs. |
| Runtime state | `runtime/` | Local dashboard, queue, status, static-analysis, and run state files. |
| Audit logs | `logs/audit/` | Append-only audit-style records. |
| Reports | `reports/` | Generated research and review reports. |
| Exports | `exports/` | Manual review/export outputs, including MT5 handoff files. |

## Planning And Project Work

| Area | Path | Purpose |
| --- | --- | --- |
| V2 project docs | `docs/project/` | Current PRD, TRD, app flow, UI brief, backend schema, and implementation plan for the V2 trading system. |
| New project workspaces | `docs/projects/` | One subfolder per new project/idea with requirements, design, engineering, delivery, decisions, and research. |
| Template sources | `docs/templates/source/` | Star-checked and repo-ready source templates used to build project docs. |
| UI prototype docs | `docs/ui-for-trading/` | Imported UI handoff, screenshots, and prototype files. |
| Ideas pipeline | `ideas/` | Inbox/staging/approved/implemented/rejected idea tracking. |

## Agent And Knowledge Support

| Area | Path | Purpose |
| --- | --- | --- |
| Librarian instructions | `LIBRARIAN.md` | How agents should keep this workspace clean and navigable. |
| Spec Kit | `.specify/` | Spec-driven development templates, scripts, and constitution. |
| Collaboration notes | `collab/` | Shared agent memory and working notes. |
| Second brain | `second_brain/` | Knowledge indexing and vault-related material. |
| Obsidian | `obsidian/` | Private/trading memory vault content. |
| Skills | `skills/` | Local skill and workflow support. |

## Future Domain Projects

Do not create new root folders for every idea. Use:

```bash
bash scripts/create_project_workspace.sh my-new-project
```

Examples:

- `docs/projects/business-ops-system/`
- `docs/projects/hr-law-advice-helper/`
- `docs/projects/graphics-helper/`
- `docs/projects/artwork-designer/`
- `docs/projects/workspace-librarian-system/`
- `docs/projects/idea-orchestrator-system/`

Keep code in the existing package layout until a project has enough substance
to justify a real package. Link code paths from the project docs.
