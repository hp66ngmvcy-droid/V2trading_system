# Project Setup Contract

This file defines the minimum structure for a clean project workspace.

## Required Documents

- `00_requirements/PRD.md`
- `00_requirements/ACCEPTANCE_CRITERIA.md`
- `01_design/APP_FLOW.md`
- `01_design/UI_UX_BRIEF.md`
- `02_engineering/TRD.md`
- `02_engineering/BACKEND_SCHEMA.md`
- `03_delivery/IMPLEMENTATION_PLAN.md`
- `03_delivery/QA_CHECKLIST.md`
- `04_decisions/ADR-0001-initial-direction.md`
- `05_research/SOURCES.md`

## Quality Bar

- One folder per project.
- One document per purpose.
- Decisions go in ADRs, not hidden in chat notes.
- External sources go in `05_research/SOURCES.md`.
- Screenshots and generated assets stay out of requirements docs.
- Keep V2 trading safety constraints visible in the project `README.md`.

## Reuse

When a project graduates into production code, keep this folder as the audit and
planning trail. Link code paths from the implementation plan instead of moving
source files into docs.
