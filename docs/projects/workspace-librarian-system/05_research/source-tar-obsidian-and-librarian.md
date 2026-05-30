# TAR Obsidian and Librarian Skill

## Objective

Create a Librarian Skill that organises TAR files, reports, repo reviews, prompts and local business knowledge.

---

## Recommended Librarian Folder

```text
src/tar_system/librarian/
├── __init__.py
├── scanner.py
├── classifier.py
├── metadata.py
├── obsidian_writer.py
├── index_builder.py
├── duplicate_checker.py
├── safety.py
└── librarian_agent.py
```

---

## What the Librarian Does

- scans local folders
- classifies files
- creates metadata
- writes JSONL and DuckDB indexes
- generates Obsidian Markdown notes
- creates index pages
- detects duplicate files
- creates review queues
- never deletes files automatically
- never moves files automatically in v1
- never scans secrets or `.env`

---

## Obsidian Vault Structure

```text
ObsidianVault/
├── 00_Inbox/
├── 01_TAR_System/
│   ├── Strategies/
│   ├── Backtests/
│   ├── Risk/
│   ├── GitHub_Reviews/
│   ├── Architecture/
│   └── Audit/
├── 02_Business_Automation/
├── 03_Print_Production/
├── 04_Research/
├── 90_Index/
└── 99_Archive/
```

---

## Note Template

```markdown
---
type: tar_report
source_path: /local/source/path
created: 2026-05-06
system: TAR
tags:
  - tar
  - review
status: review
---

# Title

## Summary

Summary here.

## Linked Files

- Source: `local path`

## Next Action

- Review
- Keep
- Revise
- Archive
```

---

## Commands

```bash
python -m tar_system.cli librarian-scan --path /Users/whs1/Dev/V2trading_system
python -m tar_system.cli librarian-index --vault /Users/whs1/Obsidian/TAR
python -m tar_system.cli librarian-duplicates --path /Users/whs1/Dev/V2trading_system
```
