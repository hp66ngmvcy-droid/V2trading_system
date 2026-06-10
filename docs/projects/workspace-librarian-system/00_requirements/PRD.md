# Product Requirements Document

## Problem

The workspace contains trading docs, idea notes, reports, generated files,
second-brain notes, and agent memory spread across multiple folders. Humans and
agents need one safe system for discovering, classifying, indexing, and
reviewing files without losing track of source-of-truth documents.

## Goals

- Provide a local librarian workflow that scans and indexes project files.
- Keep project folders easy to understand from their README and index files.
- Support Obsidian/second-brain notes without mixing them into trading code.
- Detect duplicates and cleanup candidates without deleting files automatically.

## Non-Goals

- No automatic deletion.
- No automatic movement of files in v1.
- No scanning secrets, `.env` files, credentials, or broker login data.

## Users

- Primary user:
- Secondary user:

## Requirements

| ID | Requirement | Priority | Notes |
| --- | --- | --- | --- |
| PRD-001 | Scan selected folders and produce a reviewable index | Must | Local-only |
| PRD-002 | Classify files by project, domain, type, and cleanup status | Must | Human review before action |
| PRD-003 | Write source links into project `05_research/SOURCES.md` where useful | Should | Keeps projects clean |
| PRD-004 | Support Obsidian-compatible Markdown notes | Should | Use YAML frontmatter where useful |
| PRD-005 | Detect duplicate or stale files and queue them for review | Should | No automatic deletion |

## Risks

| Risk | Impact | Mitigation |
| --- | --- | --- |
| False cleanup recommendation | Important files could be moved later by mistake | Review queue only, no automatic move/delete |
| Secret leakage into indexes | Sensitive data exposure | Exclude secret patterns and credential paths |
| Too much automation | Workspace becomes harder to trust | Keep outputs human-readable |

## Success Metrics

- A new agent can identify the right project folder in under one minute.
- Every active project has README, `PROJECT_INDEX.yaml`, and source notes.
- Cleanup candidates are reviewable before any action.
