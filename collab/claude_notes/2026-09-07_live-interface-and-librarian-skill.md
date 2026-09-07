---
id: IDEA-LIVE-LIB-001
type: idea
status: LOGGED
priority: LOW
source: "Ideas to add/tar_missing_files_and_librarian_skill.md"
logged: 2026-09-07
---

# Live Interface Seal + Local Librarian Skill

Two-part proposal. Part A is a safety/completeness task; Part B is a new skill build.

## Part A — Sealed Live Interface Files

Missing files that should exist but be permanently disabled:

```
src/tar_system/live/
    __init__.py          # empty, marks package
    broker_adapter.py    # stub only — raises NotImplementedError always
    order_router.py      # stub only — raises NotImplementedError always
    live_runner.py       # stub only — raises NotImplementedError always
```

Purpose: makes the live/ package discoverable (for IDE, imports, docs) without enabling any execution path. Prevents accidental live trading from import drift.

Each stub must include: `raise NotImplementedError("Live trading disabled — paper-mode only.")`

Gate: unit tests must assert stubs raise on call. CI blocks if any live/ function returns without raising.

## Part B — Local Librarian Skill

Obsidian-integrated file indexer for the TAR project. Builds a queryable index of all markdown notes, claude_notes, codex_notes, strategies, and reports.

Key features:
- Walks `collab/` and `reports/` trees
- Extracts frontmatter (id, type, status, date)
- Writes to local DuckDB index table: `librarian_index`
- CLI: `python3 -m tar_system.librarian.cli search <query>`
- Obsidian plugin hook: exposes REST endpoint (localhost only) for Obsidian DataView queries

Schema sketch:
```sql
CREATE TABLE IF NOT EXISTS librarian_index (
    id TEXT PRIMARY KEY,
    file_path TEXT NOT NULL,
    doc_type TEXT,
    status TEXT,
    summary TEXT,
    indexed_at TEXT NOT NULL
);
```

Constraints:
- No external API calls — fully local
- Read-only index (never writes to source files)
- Obsidian endpoint: localhost:7771, no auth required (local machine only)

## Next Action

Part A: assign to Codex — small, bounded, safety improvement.
Part B: needs Greg sign-off on Obsidian endpoint approach before build.
