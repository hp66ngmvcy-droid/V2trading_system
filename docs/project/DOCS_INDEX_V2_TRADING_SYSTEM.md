# V2 Trading System Project Docs Index

Date: 2026-05-24

These docs turn the existing repo, UI spec, and installed/downloaded templates
into a practical documentation set for this project.

## Documents

| Need | V2 Document | Template/source basis |
|---|---|---|
| PRD - product requirements | `PRD_V2_TRADING_SYSTEM.md` | Opulo PRD template structure plus existing README/UI spec |
| TRD - technical requirements | `TRD_V2_TRADING_SYSTEM.md` | Spec Kit plan template plus repo code/docs |
| App flow | `APP_FLOW_V2_TRADING_SYSTEM.md` | UI spec navigation/pipeline sections |
| UI/UX design brief | `UI_UX_BRIEF_V2_TRADING_SYSTEM.md` | Existing `docs/UI_DESIGN_SPEC_20260523.md` and `ui/README.md` |
| Backend schema | `BACKEND_SCHEMA_V2_TRADING_SYSTEM.md` | Existing JSON schema section plus queue/runtime code |
| Implementation plan | `IMPLEMENTATION_PLAN_V2_TRADING_SYSTEM.md` | Spec Kit plan/tasks structure plus current V2 state |
| Scout / next stage | `SCOUT_V2_TRADING_SYSTEM_2026-05-24.md` | Repo/runtime scan plus next operating stages |
| Ops run | `OPS_RUN_2026-05-24.md` | Stage A ops checks and failed-job classification |

## Useful Existing Docs

- `docs/UI_DESIGN_SPEC_20260523.md` remains the detailed UI source of truth.
- `docs/PHASE2_OPTIMISER_IMPROVEMENT_PLAN.md` remains the optimiser-specific plan.
- `ui/README.md` remains the UI handoff/integration note.
- `README.md` remains the operator quickstart.

## Reuse For Future Ideas

For future project ideas, create a clean workspace from the project template:

```bash
bash scripts/create_project_workspace.sh my-new-project
```

This creates a subfolder under `docs/projects/` with requirements, design,
engineering, delivery, decisions, research, screenshots, and assets separated.
The smallest useful document set is PRD, TRD, App Flow, Backend Schema, and
Implementation Plan.
