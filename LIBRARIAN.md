# Librarian Guide

Use this guide to keep the workspace clean, searchable, and easy for humans and
agents to navigate.

## First Read Order

1. `MANIFEST.md`
2. `README.md`
3. Relevant project folder under `docs/projects/`
4. Relevant code paths under `src/`, `scripts/`, `tests/`, `data/`, or `runtime/`

## Organization Rules

- New project idea: create `docs/projects/<slug>/` with
  `bash scripts/create_project_workspace.sh <slug>`.
- New trading system code: keep it under `src/tar_system/` unless there is a
  clear package-level reason to create something else.
- New tests: keep them under `tests/` and name them after the behavior.
- New generated runtime outputs: keep them under `runtime/`, `data/`,
  `reports/`, `exports/`, or `logs/` based on purpose.
- New external research notes: use the project `05_research/SOURCES.md` or
  `research/external_repos/`.
- New screenshots: use the project `screenshots/` folder or the relevant UI
  docs folder.

## Do Not Do

- Do not create new top-level folders for every idea.
- Do not move `src/tar_system/`, `data/`, `configs/`, or `tests/` into a
  domain folder without updating imports, packaging, scripts, and docs.
- Do not mix business, HR/legal, graphics, artwork, and trading requirements in
  one document.
- Do not hide decisions in chat transcripts. Add an ADR under
  `04_decisions/`.
- Do not delete or overwrite data/results/logs unless the task explicitly asks
  for cleanup and the rollback risk is understood.

## Cleanup Checklist

- [ ] Is there a single obvious folder for the work?
- [ ] Does that folder have a README or project index?
- [ ] Are source files, docs, outputs, and screenshots separated?
- [ ] Are external links recorded in `05_research/SOURCES.md`?
- [ ] Are decisions recorded in `04_decisions/`?
- [ ] Are new root-level files truly necessary?
- [ ] Can an agent understand the project in under one minute from the folder
      README?

## Domain Project Pattern

Use `docs/projects/<slug>/` for separate systems such as:

- Business operations
- HR/legal advice helper
- Graphics helper
- Artwork designer
- Trading research UI
- Strategy testing module

If a project later needs runnable code, add a code path and link it from the
project `README.md` and `02_engineering/TRD.md`.
