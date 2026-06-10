# Project Porting Notes - 2026-05-24

## Rule Confirmed

New projects that are not directly part of the V2 trading runtime should live
under `docs/projects/<project-slug>/`.

The root folder remains for repo entry points, packaging, manifest files, and
shared commands. Runnable trading code remains in `src/tar_system/` unless a
future refactor explicitly updates imports, tests, scripts, and packaging.

## Ported Local Ideas

| New Project | Source Material Copied |
| --- | --- |
| `workspace-librarian-system/` | `Ideas to add/tar_missing_files_and_librarian_skill.md`, `Ideas to add/tar_markdown_pack/11_TAR_OBSIDIAN_AND_LIBRARIAN.md`, `SECOND_BRAIN_SYSTEM.md` |
| `idea-orchestrator-system/` | `IDEA_ORCHESTRATOR_GUIDE.md`, `IDEA_ORCHESTRATOR_INTEGRATION.md` |

## Placeholder Project Workspaces

These were created so future non-trading work has a clean destination:

- `business-ops-system/`
- `hr-law-advice-helper/`
- `graphics-helper/`
- `artwork-designer/`

## Root Cleanup Candidates

These root-level files now have clearer homes and were moved during the cleanup
pass:

- `IDEA_ORCHESTRATOR_GUIDE.md`
- `IDEA_ORCHESTRATOR_INTEGRATION.md`
- `IDEA_TEMPLATE.md`
- `SECOND_BRAIN_SYSTEM.md`
- `START_IDEA_ORCHESTRATOR.txt`
- `SESSION_MEMORY.md`
- one-off completion, validation, audit, report, log, and stray root files

## Cleanup Result

- Idea-orchestrator files moved to `docs/projects/idea-orchestrator-system/`.
- Second-brain/librarian root source moved to
  `docs/projects/workspace-librarian-system/05_research/`.
- One-off root reports moved to `docs/archive/root-cleanup-2026-05-24/`.
- The accidental SSH key pair was moved to
  `.local_private/root-key-cleanup-2026-05-24/` and `.local_private/` was added
  to `.gitignore`.
- Key cleanup details are recorded in
  `docs/archive/root-cleanup-2026-05-24/SSH_KEY_CLEANUP_NOTE.md`.

No source files were intentionally deleted during this port. If the SSH key
files were ever committed or pushed, rotate that key before sharing the repo.
