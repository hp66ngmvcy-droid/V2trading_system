"""Review high-quality sources blocked by missing tradable rules."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from tar_system.research.candidate_selection import _frontmatter


@dataclass
class TranslationBlockedItem:
    path: str
    idea_id: str
    title: str
    status: str
    source_note: str
    source_url: str
    missing_rules: list[str] = field(default_factory=list)
    next_action: str = ""


@dataclass
class TranslationBlockedReview:
    generated_at: str
    input_dir: str
    output_path: str
    output_json_path: str
    blocked_count: int
    items: list[TranslationBlockedItem]


def review_translation_blockers(
    input_dir: str | Path = "ideas/translation_blocked",
    output_dir: str | Path = "idea_reviews",
) -> TranslationBlockedReview:
    source = Path(input_dir)
    items = [_review_one(path) for path in sorted(source.glob("*.md"))] if source.exists() else []
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    date_id = datetime.now(UTC).strftime("%Y-%m-%d")
    output_path = output / f"translation_blockers_{date_id}.md"
    output_json_path = output / f"translation_blockers_{date_id}.json"
    result = TranslationBlockedReview(
        generated_at=datetime.now(UTC).replace(microsecond=0).isoformat(),
        input_dir=str(source),
        output_path=str(output_path),
        output_json_path=str(output_json_path),
        blocked_count=len(items),
        items=items,
    )
    output_path.write_text(_markdown(result), encoding="utf-8")
    output_json_path.write_text(json.dumps(asdict(result), indent=2, default=str), encoding="utf-8")
    return result


def _review_one(path: Path) -> TranslationBlockedItem:
    text = path.read_text(encoding="utf-8")
    meta = _frontmatter(text)
    missing = _missing_rules(text)
    status = str(meta.get("status") or "unknown")
    next_action = _next_action(status, missing)
    return TranslationBlockedItem(
        path=str(path),
        idea_id=str(meta.get("idea_id") or path.stem),
        title=str(meta.get("title") or path.stem),
        status=status,
        source_note=str(meta.get("source_note") or ""),
        source_url=str(meta.get("source_url") or ""),
        missing_rules=missing,
        next_action=next_action,
    )


def _next_action(status: str, missing: list[str]) -> str:
    if not missing:
        return "Review note manually; no missing-rule checklist was found."
    if status == "formula_extracted_data_blocked":
        return "Resolve data coverage or document a reduced proxy before candidate conversion."
    return "Extract exact formulas from source or appendix before candidate conversion."


def _missing_rules(text: str) -> list[str]:
    lines = text.splitlines()
    capture = False
    missing: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## "):
            capture = stripped.lower() == "## required before candidate conversion"
            continue
        if capture and stripped.startswith("- "):
            missing.append(stripped.removeprefix("- ").rstrip("."))
    return missing


def _markdown(result: TranslationBlockedReview) -> str:
    lines = [
        "# Translation Blockers Review",
        "",
        f"- Generated: {result.generated_at}",
        f"- Input: `{result.input_dir}`",
        f"- Blocked sources: {result.blocked_count}",
        "",
        "## Items",
        "",
    ]
    if not result.items:
        lines.append("- No blocked translations found.")
    for item in result.items:
        lines.extend(
            [
                f"### {item.title}",
                "",
                f"- Path: `{item.path}`",
                f"- Status: {item.status}",
                f"- Source: {item.source_url}",
                f"- Next action: {item.next_action}",
                "",
                "Missing rules:",
                "",
            ]
        )
        if not item.missing_rules:
            lines.append("- none listed")
        for rule in item.missing_rules:
            lines.append(f"- {rule}")
        lines.append("")
    lines.extend(
        [
            "## Guardrails",
            "",
            "- This review does not create candidates.",
            "- Do not invent missing formulas.",
            "- Keep blocked sources out of proxy/backtest work until formulas and data are explicit.",
            "",
        ]
    )
    return "\n".join(lines)
