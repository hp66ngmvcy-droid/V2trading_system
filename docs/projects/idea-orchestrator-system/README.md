# idea orchestrator system

Status: Draft
Owner: TBD
Created: 2026-05-24

## Purpose

Design and maintain the local idea intake workflow that captures ideas, stages
them for review, records approval/rejection, and promotes approved ideas into
the correct project workspace.

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

## Ported Local Sources

- `05_research/CONTINUAL_IDEA_ENGINE_NOTE_2026-05-24.md`
- `05_research/HYPOTHESIS_BACKTESTER_REPO_CHECK_2026-05-24.md`
- `05_research/RESEARCH_QUALITY_AND_FILTER_TUNING_UPGRADE_2026-05-24.md`
- `05_research/source-idea-orchestrator-guide.md`
- `05_research/source-idea-orchestrator-integration.md`
- `05_research/original-IDEA_ORCHESTRATOR_GUIDE.md`
- `05_research/original-IDEA_ORCHESTRATOR_INTEGRATION.md`
- `03_delivery/DAILY_IDEA_REVIEW_OPERATING_MODEL.md`
- `03_delivery/START_IDEA_ORCHESTRATOR.txt`
- `03_delivery/SESSION_MEMORY.md`
- `assets/IDEA_TEMPLATE.md`
