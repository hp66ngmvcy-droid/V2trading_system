# Product Requirements Document

## Problem

Ideas arrive from chat, local notes, project docs, and root-level markdown
files. Without a clean intake workflow, useful ideas can stay scattered or get
mixed into the wrong system.

## Goals

- Keep idea capture simple.
- Stage ideas for review before implementation.
- Promote approved ideas into the correct `docs/projects/<slug>/` folder.
- Preserve rejected and implemented idea history.
- Support continual idea intake from human notes, backtest failures, and
  approved online research sources.

## Non-Goals

- No automatic code changes from idea text.
- No live trading or broker action.
- No deletion of old idea notes without explicit cleanup approval.

## Users

- Primary user:
- Secondary user:

## Requirements

| ID | Requirement | Priority | Notes |
| --- | --- | --- | --- |
| PRD-001 | Keep inbox/staging/approved/rejected/implemented states | Must | Existing `ideas/` layout |
| PRD-002 | Generate or maintain review notes | Must | Existing `idea_reviews/` layout |
| PRD-003 | Promote non-trading ideas into `docs/projects/` | Must | New workspace structure |
| PRD-004 | Link original source files in project research notes | Should | Avoid losing context |
| PRD-005 | Collect online strategy hypotheses into a review queue | Should | No automatic implementation |
| PRD-006 | Promote only approved hypotheses into backtest candidates | Must | Human gate remains |

## Risks

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Idea goes to wrong project | Confusing docs | Use `PROJECT_INDEX.yaml` and source notes |
| Automation overreaches | User loses control | Human approval remains the gate |
| Trading and non-trading ideas mix | Navigation gets messy | Separate each system into `docs/projects/<slug>/` |

## Success Metrics

- Every approved non-trading idea has a project folder.
- Every migrated idea links back to its source note.
- Daily review notes remain easy to scan.
