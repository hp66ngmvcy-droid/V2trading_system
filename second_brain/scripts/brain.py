#!/usr/bin/env python3
"""Local second-brain utilities.

This module is deliberately dependency-light and safe by default:
- indexes Markdown into JSON and DuckDB
- searches the local index
- generates daily review Markdown
- reports vault-tidy issues without deleting or moving files
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SECOND_BRAIN = ROOT / "second_brain"
VAULT = SECOND_BRAIN / "vault"
INDEXES = SECOND_BRAIN / "indexes"
METADATA = SECOND_BRAIN / "metadata"

NOTE_DIRS = [
    VAULT / "00_inbox",
    VAULT / "01_hubs" / "trading",
    VAULT / "01_hubs" / "production",
    VAULT / "01_hubs" / "operations",
    VAULT / "01_hubs" / "ai_engineering",
    VAULT / "01_hubs" / "packaging_rd",
    VAULT / "01_hubs" / "finance",
    VAULT / "01_hubs" / "automation",
    VAULT / "01_hubs" / "marketing",
    VAULT / "01_hubs" / "supplier",
    VAULT / "01_hubs" / "strategy_research",
    VAULT / "02_reviews" / "daily",
    VAULT / "02_reviews" / "nightly",
    VAULT / "02_reviews" / "weekly",
    VAULT / "03_sops",
    VAULT / "04_decisions",
    VAULT / "05_meetings",
    VAULT / "06_research",
    VAULT / "07_archive",
]

WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9_-]{2,}")
WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)")
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
TAG_RE = re.compile(r"(?<!\w)#([A-Za-z][A-Za-z0-9_/-]*)")


@dataclass
class NoteRecord:
    path: str
    title: str
    hub: str
    tags: list[str]
    links: list[str]
    word_count: int
    modified_at: str
    sha256: str
    summary: str
    frontmatter: dict[str, str]


def ensure_structure() -> None:
    for directory in [SECOND_BRAIN, VAULT, INDEXES, METADATA, *NOTE_DIRS]:
        directory.mkdir(parents=True, exist_ok=True)
        keep = directory / ".gitkeep"
        if not keep.exists() and directory != SECOND_BRAIN:
            keep.write_text("", encoding="utf-8")


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end == -1:
        return {}, text
    raw = text[4:end].strip()
    body = text[end + 4 :].lstrip("\n")
    data: dict[str, str] = {}
    for line in raw.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"')
    return data, body


def markdown_files() -> list[Path]:
    ensure_structure()
    files = []
    for path in VAULT.rglob("*.md"):
        if path.is_file():
            files.append(path)
    return sorted(files)


def title_from(body: str, path: Path, frontmatter: dict[str, str]) -> str:
    if frontmatter.get("title"):
        return frontmatter["title"]
    for line in body.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem.replace("_", " ").replace("-", " ").title()


def hub_from(path: Path) -> str:
    try:
        relative = path.relative_to(VAULT)
    except ValueError:
        return "external"
    parts = relative.parts
    if len(parts) >= 3 and parts[0] == "01_hubs":
        return parts[1]
    if parts:
        return parts[0]
    return "vault"


def summarize(body: str, max_chars: int = 240) -> str:
    cleaned = " ".join(line.strip() for line in body.splitlines() if line.strip() and not line.startswith("#"))
    if len(cleaned) <= max_chars:
        return cleaned
    return cleaned[: max_chars - 3].rstrip() + "..."


def note_record(path: Path) -> NoteRecord:
    text = path.read_text(encoding="utf-8")
    frontmatter, body = parse_frontmatter(text)
    words = WORD_RE.findall(body)
    tags = sorted(set(TAG_RE.findall(text)))
    links = sorted(set(WIKILINK_RE.findall(text) + [link for link in MARKDOWN_LINK_RE.findall(text) if not link.startswith(("http://", "https://"))]))
    stat = path.stat()
    return NoteRecord(
        path=str(path.relative_to(ROOT)),
        title=title_from(body, path, frontmatter),
        hub=hub_from(path),
        tags=tags,
        links=links,
        word_count=len(words),
        modified_at=datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
        sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
        summary=summarize(body),
        frontmatter=frontmatter,
    )


def build_index() -> list[NoteRecord]:
    records = [note_record(path) for path in markdown_files()]
    INDEXES.mkdir(parents=True, exist_ok=True)
    payload = [asdict(record) for record in records]
    (INDEXES / "notes_index.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_duckdb_index(payload)
    return records


def write_duckdb_index(payload: list[dict[str, Any]]) -> None:
    try:
        import duckdb
    except Exception:
        return
    db_path = INDEXES / "second_brain.duckdb"
    with duckdb.connect(str(db_path)) as con:
        con.execute(
            """
            create table if not exists notes (
                path varchar primary key,
                title varchar,
                hub varchar,
                tags varchar,
                links varchar,
                word_count integer,
                modified_at varchar,
                sha256 varchar,
                summary varchar,
                frontmatter varchar
            )
            """
        )
        con.execute("delete from notes")
        for item in payload:
            con.execute(
                "insert into notes values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    item["path"],
                    item["title"],
                    item["hub"],
                    json.dumps(item["tags"]),
                    json.dumps(item["links"]),
                    item["word_count"],
                    item["modified_at"],
                    item["sha256"],
                    item["summary"],
                    json.dumps(item["frontmatter"]),
                ],
            )


def load_index() -> list[dict[str, Any]]:
    path = INDEXES / "notes_index.json"
    if not path.exists():
        return [asdict(record) for record in build_index()]
    return json.loads(path.read_text(encoding="utf-8"))


def search(query: str, limit: int = 10) -> list[dict[str, Any]]:
    terms = [term.lower() for term in WORD_RE.findall(query)]
    if not terms:
        return []
    results = []
    for item in load_index():
        haystack = " ".join(
            [
                item.get("title", ""),
                item.get("hub", ""),
                item.get("summary", ""),
                " ".join(item.get("tags", [])),
            ]
        ).lower()
        score = sum(haystack.count(term) for term in terms)
        if score:
            results.append({"score": score, **item})
    return sorted(results, key=lambda row: (-row["score"], row["path"]))[:limit]


def tidy_report() -> dict[str, Any]:
    records = load_index()
    paths = {record["path"] for record in records}
    titles = Counter(record["title"].lower() for record in records)
    broken_links: list[dict[str, str]] = []
    orphan_notes = []
    short_notes = []

    title_to_paths: dict[str, list[str]] = {}
    for record in records:
        title_to_paths.setdefault(record["title"].lower(), []).append(record["path"])

    linked_titles = {link.lower() for record in records for link in record.get("links", [])}
    for record in records:
        if record["title"].lower() not in linked_titles and record["hub"] != "07_archive":
            orphan_notes.append(record["path"])
        if record["word_count"] < 20:
            short_notes.append(record["path"])
        for link in record.get("links", []):
            link_path = (Path(record["path"]).parent / link).as_posix()
            title_match = link.lower() in title_to_paths
            path_match = link in paths or link_path in paths
            if not title_match and not path_match:
                broken_links.append({"source": record["path"], "link": link})

    duplicates = {title: linked for title, linked in title_to_paths.items() if titles[title] > 1}
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "note_count": len(records),
        "orphan_notes": sorted(orphan_notes),
        "short_notes": sorted(short_notes),
        "duplicate_titles": duplicates,
        "broken_links": broken_links,
        "safe_mode": "No files were modified, moved, archived, or deleted.",
    }


def write_daily_review() -> Path:
    records = build_index()
    report = tidy_report()
    today = datetime.now().strftime("%Y-%m-%d")
    output = VAULT / "02_reviews" / "daily" / f"{today}.md"
    hubs = Counter(record.hub for record in records)
    recent = sorted(records, key=lambda record: record.modified_at, reverse=True)[:10]
    lines = [
        "---",
        f"title: Daily Review {today}",
        "type: daily-review",
        f"generated_at: {datetime.now().isoformat(timespec='seconds')}",
        "---",
        "",
        f"# Daily Review - {today}",
        "",
        "## Vault Health",
        "",
        f"- Notes indexed: {len(records)}",
        f"- Hubs active: {len(hubs)}",
        f"- Orphan candidates: {len(report['orphan_notes'])}",
        f"- Broken link candidates: {len(report['broken_links'])}",
        f"- Duplicate title groups: {len(report['duplicate_titles'])}",
        "",
        "## Hub Counts",
        "",
    ]
    for hub, count in sorted(hubs.items()):
        lines.append(f"- {hub}: {count}")
    lines.extend(["", "## Recent Notes", ""])
    if recent:
        for record in recent:
            lines.append(f"- [[{record.title}]] - `{record.path}`")
    else:
        lines.append("- No notes indexed yet.")
    lines.extend(
        [
            "",
            "## Safe Tidy Suggestions",
            "",
            "No files were changed by this review.",
            "",
            f"- Review orphan candidates: {len(report['orphan_notes'])}",
            f"- Review short notes: {len(report['short_notes'])}",
            f"- Review broken links: {len(report['broken_links'])}",
            "",
        ]
    )
    output.write_text("\n".join(lines), encoding="utf-8")
    return output


def print_json(value: Any) -> None:
    print(json.dumps(value, indent=2, default=str))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local second-brain command utilities")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init", help="Create the second-brain folder structure")
    sub.add_parser("index", help="Build JSON and DuckDB note indexes")
    search_parser = sub.add_parser("search", help="Search the local note index")
    search_parser.add_argument("query")
    search_parser.add_argument("--limit", type=int, default=10)
    sub.add_parser("daily-review", help="Generate today's daily review")
    sub.add_parser("tidy-report", help="Report vault issues without modifying files")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "init":
        ensure_structure()
        print(f"Second-brain structure ready at {SECOND_BRAIN.relative_to(ROOT)}")
    elif args.command == "index":
        records = build_index()
        print_json({"notes_indexed": len(records), "index": str((INDEXES / "notes_index.json").relative_to(ROOT))})
    elif args.command == "search":
        print_json(search(args.query, args.limit))
    elif args.command == "daily-review":
        output = write_daily_review()
        print(f"Wrote {output.relative_to(ROOT)}")
    elif args.command == "tidy-report":
        print_json(tidy_report())


if __name__ == "__main__":
    main()
