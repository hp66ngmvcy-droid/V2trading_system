# Project Title

Status: Draft
Owner: TBD
Created: YYYY-MM-DD

## Purpose

Describe the project in one short paragraph. Name the user problem, the system
area affected, and what success looks like.

## Folder Map

- `00_requirements/` - PRD, acceptance criteria, scope, and constraints.
- `01_design/` - app flow, UI/UX brief, wire notes, screenshots.
- `02_engineering/` - TRD, backend schema, APIs, data contracts.
- `03_delivery/` - implementation plan, task list, QA checklist, release notes.
- `04_decisions/` - ADRs and technical/product decisions.
- `05_research/` - references, audits, external repo notes, experiments.
- `assets/` - images, exports, fixture files, diagrams.
- `screenshots/` - UI verification images.

## Project Safety

For V2 trading work, default to research-only and paper-only behavior unless a
signed-off document explicitly expands scope.

- No live order placement.
- No broker credential storage.
- No destructive data edits without a rollback path.
- No hidden network dependency for local workflows.

## Source Templates

- Spec/workflow: `docs/templates/source/spec-kit-spec-template.md`
- Plan/tasks/checklists: `docs/templates/source/spec-kit-plan-template.md`
- Architecture: `docs/templates/source/arc42-template.adoc`
- Decisions: `docs/templates/source/madr-adr-template.md`
- Source audit: `docs/templates/source/STAR_RATED_SOURCE_CHECK_2026-05-24.md`
