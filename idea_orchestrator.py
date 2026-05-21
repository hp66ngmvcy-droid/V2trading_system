#!/usr/bin/env python3
"""Local idea intake and review orchestrator for V2trading_system.

The orchestrator is intentionally local-only and dependency-free. It watches
markdown idea files, moves them through a human approval gate, updates project
memory/docs for approved ideas, and can commit only the files it manages.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, time as clock_time
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parent
IDEAS_DIR = ROOT / "ideas"
INBOX_DIR = IDEAS_DIR / "inbox"
STAGING_DIR = IDEAS_DIR / "staging"
APPROVED_DIR = IDEAS_DIR / "approved"
REJECTED_DIR = IDEAS_DIR / "rejected"
IMPLEMENTED_DIR = IDEAS_DIR / "implemented"
REVIEWS_DIR = ROOT / "idea_reviews"
CLAUDE_FILE = ROOT / "CLAUDE.md"
SESSION_MEMORY_FILE = ROOT / "SESSION_MEMORY.md"

MANAGED_DIRS = [
    INBOX_DIR,
    STAGING_DIR,
    APPROVED_DIR,
    REJECTED_DIR,
    IMPLEMENTED_DIR,
    REVIEWS_DIR,
]

MANAGED_FILES = [
    ROOT / "idea_orchestrator.py",
    ROOT / "IDEA_TEMPLATE.md",
    ROOT / "IDEA_ORCHESTRATOR_GUIDE.md",
    ROOT / "IDEA_ORCHESTRATOR_INTEGRATION.md",
    ROOT / "START_IDEA_ORCHESTRATOR.txt",
    SESSION_MEMORY_FILE,
]

FIELD_PATTERN = re.compile(r"^\s*([A-Za-z][A-Za-z0-9 _-]*):\s*(.*?)\s*$")


@dataclass
class Idea:
    path: Path
    title: str
    summary: str
    component: str
    priority: str
    status: str
    tags: str
    content: str
    score: int
    recommendation: str
    reasons: list[str]


def now_stamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def today_key() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def ensure_structure() -> None:
    for directory in MANAGED_DIRS:
        directory.mkdir(parents=True, exist_ok=True)
        keep = directory / ".gitkeep"
        if not keep.exists():
            keep.write_text("", encoding="utf-8")
    if not SESSION_MEMORY_FILE.exists():
        SESSION_MEMORY_FILE.write_text(
            "# Session Memory\n\n"
            "Local project memory for approved ideas, implementation progress, "
            "and operator notes.\n\n"
            "## Approved Idea Log\n\n",
            encoding="utf-8",
        )


def idea_files(directory: Path) -> list[Path]:
    if not directory.exists():
        return []
    return sorted(path for path in directory.glob("idea_*.md") if path.is_file())


def parse_fields(content: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in content.splitlines():
        match = FIELD_PATTERN.match(line)
        if match:
            key = match.group(1).strip().lower().replace(" ", "_")
            fields[key] = match.group(2).strip()
    return fields


def first_heading(content: str) -> str:
    for line in content.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return "Untitled idea"


def analyze_content(path: Path, content: str) -> Idea:
    fields = parse_fields(content)
    title = fields.get("title") or first_heading(content)
    summary = fields.get("summary", "")
    component = fields.get("component", "unspecified")
    priority = fields.get("priority", "medium").lower()
    status = fields.get("status", "inbox").lower()
    tags = fields.get("tags", "")

    score = 50
    reasons: list[str] = []
    lower = content.lower()

    if priority in {"critical", "high"}:
        score += 20
        reasons.append("High stated priority.")
    elif priority in {"low", "later"}:
        score -= 10
        reasons.append("Low stated priority.")

    if summary and len(summary) >= 30:
        score += 10
        reasons.append("Clear summary provided.")
    else:
        score -= 10
        reasons.append("Summary is short or missing.")

    if component != "unspecified":
        score += 10
        reasons.append(f"Target component: {component}.")
    else:
        reasons.append("No specific component supplied.")

    if any(term in lower for term in ["live trading", "real money", "broker api"]):
        score -= 40
        reasons.append("Potential conflict with paper-only project policy.")

    if any(term in lower for term in ["audit", "safe", "paper", "validation", "backtest"]):
        score += 10
        reasons.append("Aligns with local paper-safe research workflow.")

    if any(term in lower for term in ["docker", "ray", "polars", "cloud"]):
        score -= 15
        reasons.append("Mentions heavier dependency or infrastructure direction.")

    score = max(0, min(100, score))
    if score >= 75:
        recommendation = "APPROVE"
    elif score >= 45:
        recommendation = "REVIEW"
    else:
        recommendation = "REJECT"

    return Idea(
        path=path,
        title=title,
        summary=summary,
        component=component,
        priority=priority,
        status=status,
        tags=tags,
        content=content,
        score=score,
        recommendation=recommendation,
        reasons=reasons,
    )


def read_idea(path: Path) -> Idea:
    return analyze_content(path, path.read_text(encoding="utf-8"))


def with_analysis_block(idea: Idea, new_status: str) -> str:
    body = remove_analysis_block(idea.content)
    analysis = [
        "",
        "<!-- IDEA_ORCHESTRATOR_ANALYSIS_START -->",
        "## Orchestrator Analysis",
        "",
        f"- Status: {new_status}",
        f"- Reviewed at: {now_stamp()}",
        f"- Score: {idea.score}/100",
        f"- Recommendation: {idea.recommendation}",
        "- Reasons:",
    ]
    analysis.extend(f"  - {reason}" for reason in idea.reasons)
    analysis.append("<!-- IDEA_ORCHESTRATOR_ANALYSIS_END -->")
    analysis.append("")
    return body.rstrip() + "\n" + "\n".join(analysis)


def remove_analysis_block(content: str) -> str:
    pattern = re.compile(
        r"\n?<!-- IDEA_ORCHESTRATOR_ANALYSIS_START -->.*?"
        r"<!-- IDEA_ORCHESTRATOR_ANALYSIS_END -->\n?",
        re.DOTALL,
    )
    return pattern.sub("\n", content)


def unique_destination(directory: Path, source_name: str) -> Path:
    target = directory / source_name
    if not target.exists():
        return target
    stem = target.stem
    suffix = target.suffix
    index = 2
    while True:
        candidate = directory / f"{stem}_{index}{suffix}"
        if not candidate.exists():
            return candidate
        index += 1


def process_inbox() -> list[Path]:
    ensure_structure()
    moved: list[Path] = []
    for path in idea_files(INBOX_DIR):
        idea = read_idea(path)
        updated = with_analysis_block(idea, "staging")
        target = unique_destination(STAGING_DIR, path.name)
        path.write_text(updated, encoding="utf-8")
        shutil.move(str(path), str(target))
        moved.append(target)
    return moved


def staging_ideas() -> list[Idea]:
    return [read_idea(path) for path in idea_files(STAGING_DIR)]


def build_daily_review(ideas: Iterable[Idea]) -> str:
    items = list(ideas)
    lines = [
        f"# Idea Review - {today_key()}",
        "",
        f"Generated: {now_stamp()}",
        "",
        "## Summary",
        "",
        f"- Pending staging ideas: {len(items)}",
        f"- Approve candidates: {sum(1 for item in items if item.recommendation == 'APPROVE')}",
        f"- Review candidates: {sum(1 for item in items if item.recommendation == 'REVIEW')}",
        f"- Reject candidates: {sum(1 for item in items if item.recommendation == 'REJECT')}",
        "",
        "## Operator Actions",
        "",
        "Approve:",
        "",
        "```bash",
        "mv ideas/staging/idea_*.md ideas/approved/",
        "```",
        "",
        "Reject:",
        "",
        "```bash",
        "mv ideas/staging/idea_*.md ideas/rejected/",
        "```",
        "",
        "## Ideas",
        "",
    ]
    if not items:
        lines.append("No ideas are currently waiting in staging.")
        lines.append("")
        return "\n".join(lines)

    for idea in sorted(items, key=lambda item: item.score, reverse=True):
        lines.extend(
            [
                f"### {idea.title}",
                "",
                f"- File: `{idea.path.relative_to(ROOT)}`",
                f"- Component: {idea.component}",
                f"- Priority: {idea.priority}",
                f"- Score: {idea.score}/100",
                f"- Recommendation: {idea.recommendation}",
                f"- Summary: {idea.summary or 'No summary supplied.'}",
                "- Reasons:",
            ]
        )
        lines.extend(f"  - {reason}" for reason in idea.reasons)
        lines.append("")
    return "\n".join(lines)


def write_daily_review(force: bool = False) -> Path:
    ensure_structure()
    review_path = REVIEWS_DIR / f"review_{today_key()}.md"
    if review_path.exists() and not force:
        return review_path
    review_path.write_text(build_daily_review(staging_ideas()), encoding="utf-8")
    return review_path


def approved_ideas() -> list[Idea]:
    return [read_idea(path) for path in idea_files(APPROVED_DIR)]


def append_once(path: Path, marker: str, block: str) -> bool:
    content = path.read_text(encoding="utf-8") if path.exists() else ""
    if marker in content:
        return False
    if content and not content.endswith("\n"):
        content += "\n"
    path.write_text(content + block, encoding="utf-8")
    return True


def claude_block(idea: Idea) -> str:
    marker = f"<!-- idea:{idea.path.stem} -->"
    return (
        "\n"
        "## Approved Enhancement Ideas\n"
        f"{marker}\n"
        f"- [{now_stamp()}] {idea.title} ({idea.component}, {idea.priority})\n"
        f"  Recommendation: {idea.recommendation}; Score: {idea.score}/100.\n"
        f"  Summary: {idea.summary or 'No summary supplied.'}\n"
    )


def memory_block(idea: Idea) -> str:
    marker = f"<!-- idea-memory:{idea.path.stem} -->"
    reasons = "; ".join(idea.reasons)
    return (
        f"{marker}\n"
        f"### {now_stamp()} - Approved idea: {idea.title}\n\n"
        f"- Source: `{idea.path.relative_to(ROOT)}`\n"
        f"- Component: {idea.component}\n"
        f"- Priority: {idea.priority}\n"
        f"- Score: {idea.score}/100\n"
        f"- Summary: {idea.summary or 'No summary supplied.'}\n"
        f"- Analysis: {reasons}\n\n"
    )


def implement_approved(auto_commit: bool = True) -> list[Path]:
    ensure_structure()
    implemented: list[Path] = []
    for idea in approved_ideas():
        append_once(CLAUDE_FILE, f"<!-- idea:{idea.path.stem} -->", claude_block(idea))
        append_once(
            SESSION_MEMORY_FILE,
            f"<!-- idea-memory:{idea.path.stem} -->",
            memory_block(idea),
        )
        target = unique_destination(IMPLEMENTED_DIR, idea.path.name)
        shutil.move(str(idea.path), str(target))
        implemented.append(target)
    if implemented and auto_commit:
        commit_managed_files("Idea orchestrator updates")
    return implemented


def commit_managed_files(message: str) -> bool:
    paths: list[Path] = []
    paths.extend(path for path in MANAGED_FILES if path.exists())
    paths.extend(path for directory in MANAGED_DIRS for path in directory.glob("**/*") if path.is_file())
    paths.append(CLAUDE_FILE)

    relative_paths = [str(path.relative_to(ROOT)) for path in paths if path.exists()]
    if not relative_paths:
        return False

    subprocess.run(["git", "add", *relative_paths], cwd=ROOT, check=False)
    diff = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT, check=False)
    if diff.returncode == 0:
        return False
    result = subprocess.run(["git", "commit", "-m", message], cwd=ROOT, check=False)
    return result.returncode == 0


def seconds_until(target: clock_time) -> float:
    now = datetime.now()
    target_dt = now.replace(hour=target.hour, minute=target.minute, second=0, microsecond=0)
    if target_dt <= now:
        return 0
    return (target_dt - now).total_seconds()


def run_once(auto_commit: bool = True, force_review: bool = False) -> None:
    moved = process_inbox()
    review = write_daily_review(force=force_review)
    implemented = implement_approved(auto_commit=auto_commit)
    print(f"[{now_stamp()}] Inbox moved: {len(moved)}")
    print(f"[{now_stamp()}] Daily review: {review.relative_to(ROOT)}")
    print(f"[{now_stamp()}] Implemented approved ideas: {len(implemented)}")


def run_daemon(interval_minutes: int, auto_commit: bool) -> None:
    ensure_structure()
    print(f"[{now_stamp()}] Idea orchestrator started.")
    print(f"[{now_stamp()}] Watching {INBOX_DIR.relative_to(ROOT)} every {interval_minutes} minutes.")
    last_review_day = ""
    last_implementation_day = ""
    interval_seconds = max(1, interval_minutes) * 60
    while True:
        process_inbox()
        now = datetime.now()
        if now.hour == 4 and now.minute < max(interval_minutes, 1):
            if last_review_day != today_key():
                review = write_daily_review(force=True)
                print(f"[{now_stamp()}] Wrote daily review: {review.relative_to(ROOT)}")
                last_review_day = today_key()
        if now.hour == 4 and now.minute >= 15 and now.minute < 15 + max(interval_minutes, 1):
            if last_implementation_day != today_key():
                implemented = implement_approved(auto_commit=auto_commit)
                print(f"[{now_stamp()}] Implemented approved ideas: {len(implemented)}")
                last_implementation_day = today_key()
        time.sleep(interval_seconds)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local idea intake orchestrator")
    parser.add_argument("--once", action="store_true", help="Process inbox/review/approved ideas once and exit")
    parser.add_argument("--force-review", action="store_true", help="Rewrite today's review file")
    parser.add_argument("--interval-minutes", type=int, default=30, help="Inbox scan interval for daemon mode")
    parser.add_argument("--no-commit", action="store_true", help="Do not auto-commit approved idea updates")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    auto_commit = not args.no_commit
    if args.once:
        run_once(auto_commit=auto_commit, force_review=args.force_review)
    else:
        run_daemon(args.interval_minutes, auto_commit=auto_commit)


if __name__ == "__main__":
    main()
