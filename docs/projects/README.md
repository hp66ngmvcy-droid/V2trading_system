# Project Workspace System

Use this folder for every new project, feature package, UI experiment, strategy
module, integration, or research build that needs its own organized working
area. This is also the home for non-trading systems such as business tools,
HR/legal helpers, graphics helpers, artwork designers, and other separate
ideas.

## Rule

Every new project gets one subfolder copied from `_template/`.

```bash
bash scripts/create_project_workspace.sh my-new-project
```

The generated folder keeps requirements, design, engineering, delivery,
decisions, research, screenshots, and assets separated so work stays fast to
scan and easy to reuse.

## Current Project Workspaces

- `workspace-librarian-system/` - librarian, second-brain, indexing, cleanup,
  and agent navigation system.
- `idea-orchestrator-system/` - idea intake, staging, review, and promotion
  workflow.
- `business-ops-system/` - placeholder for non-trading business operations
  systems.
- `hr-law-advice-helper/` - placeholder for HR/legal helper ideas.
- `graphics-helper/` - placeholder for graphics helper workflows.
- `artwork-designer/` - placeholder for artwork and creative design systems.

## Existing Setup Folders

- `.specify/` - Spec Kit workflow, templates, scripts, and project constitution.
- `.specify/templates/` - repo-installed Spec Kit templates.
- `docs/templates/source/` - downloaded/star-rated template sources.
- `docs/project/` - current V2 trading system PRD, TRD, app flow, UI brief,
  backend schema, and implementation plan.
- `docs/ui-for-trading/project/` - imported UI prototype bundle and screenshots.
- `ideas/` - idea intake and staging folders.
- `research/external_repos/` - external research repositories.
- `collab/` - multi-agent notes, memory, and shared working files.

## Folder Naming

Use lowercase slugs with hyphens:

- `v2-research-ui`
- `broker-data-import`
- `strategy-health-dashboard`

Avoid spaces in new project folder names. Keep human-readable titles inside the
project `README.md`.
