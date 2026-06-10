# Second Brain

This folder is the local-first second-brain scaffold for V2trading_system.

It is intentionally separate from trading execution code. Use it for markdown vault content, knowledge hubs, review outputs, SOPs, decisions, meeting notes, metadata, and future retrieval indexes.

## Structure

```text
second_brain/
|- vault/
|  |- 00_inbox/
|  |- 01_hubs/
|  |- 02_reviews/
|  |- 03_sops/
|  |- 04_decisions/
|  |- 05_meetings/
|  |- 06_research/
|  `- 07_archive/
|- indexes/
|- metadata/
`- scripts/
```

## Rules

- Markdown first.
- YAML frontmatter when notes need structured metadata.
- JSON or DuckDB for indexes.
- No automatic deletion.
- Keep this layer modular and readable by humans and AI agents.

## Commands

Initialize folders:

```bash
python3 second_brain/scripts/brain.py init
```

Build the local index:

```bash
python3 second_brain/scripts/brain.py index
```

Search notes:

```bash
python3 second_brain/scripts/brain.py search "strategy memory"
```

Generate today's daily review:

```bash
python3 second_brain/scripts/brain.py daily-review
```

Check vault tidy issues without changing files:

```bash
python3 second_brain/scripts/brain.py tidy-report
```
