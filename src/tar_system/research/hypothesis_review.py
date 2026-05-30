"""Review extracted hypothesis notes before candidate promotion."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass
class HypothesisReviewItem:
    path: str
    idea_id: str
    title: str
    status: str
    source_url: str
    source_quality_score: int
    source_quality_label: str
    recommendation: str
    blockers: list[str] = field(default_factory=list)
    next_action: str = ""


@dataclass
class HypothesisReviewResult:
    generated_at: str
    input_dir: str
    output_path: str
    output_json_path: str
    reviewed_count: int
    ready_count: int
    needs_rules_count: int
    rejected_count: int
    items: list[HypothesisReviewItem]


def review_hypotheses(
    input_dir: str | Path = "ideas/research_queue",
    output_dir: str | Path = "idea_reviews",
    min_ready_score: int = 75,
) -> HypothesisReviewResult:
    source = Path(input_dir)
    items = [_review_note(path, min_ready_score=min_ready_score) for path in sorted(source.glob("*.md"))] if source.exists() else []
    ready_count = sum(1 for item in items if item.recommendation == "READY_FOR_RULE_TRANSLATION")
    needs_rules_count = sum(1 for item in items if item.recommendation == "NEEDS_RULE_TRANSLATION")
    rejected_count = sum(1 for item in items if item.recommendation == "REJECT_OR_ARCHIVE")
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    date_id = datetime.now(UTC).strftime("%Y-%m-%d")
    output_path = output / f"hypothesis_review_{date_id}.md"
    output_json_path = output / f"hypothesis_review_{date_id}.json"
    result = HypothesisReviewResult(
        generated_at=datetime.now(UTC).replace(microsecond=0).isoformat(),
        input_dir=str(source),
        output_path=str(output_path),
        output_json_path=str(output_json_path),
        reviewed_count=len(items),
        ready_count=ready_count,
        needs_rules_count=needs_rules_count,
        rejected_count=rejected_count,
        items=items,
    )
    output_path.write_text(_markdown(result), encoding="utf-8")
    output_json_path.write_text(json.dumps(asdict(result), indent=2, default=str), encoding="utf-8")
    return result


def _review_note(path: Path, min_ready_score: int) -> HypothesisReviewItem:
    text = path.read_text(encoding="utf-8")
    meta = _frontmatter(text)
    score = _int(meta.get("source_quality_score"), 0)
    blockers: list[str] = []
    if score < min_ready_score:
        blockers.append("source_quality_below_ready_threshold")
    if "To be defined from source after human review" in text:
        blockers.append("strategy_rules_not_defined")
    if "- [ ] Rules are specific enough to implement." in text:
        blockers.append("review_gate_unchecked")
    if not meta.get("source_url"):
        blockers.append("missing_source_url")

    if score < 55:
        recommendation = "REJECT_OR_ARCHIVE"
        next_action = "Archive unless operator sees a unique reason to keep it."
    elif blockers:
        recommendation = "NEEDS_RULE_TRANSLATION"
        next_action = "Open the source, define exact Entry/Exit/Filters/Risk, then rerun review."
    else:
        recommendation = "READY_FOR_RULE_TRANSLATION"
        next_action = "Convert with add-strategy-idea after operator approval."

    return HypothesisReviewItem(
        path=str(path),
        idea_id=str(meta.get("idea_id") or path.stem),
        title=str(meta.get("title") or _title(text) or path.stem),
        status=str(meta.get("status") or "unknown"),
        source_url=str(meta.get("source_url") or ""),
        source_quality_score=score,
        source_quality_label=str(meta.get("source_quality_label") or "unknown"),
        recommendation=recommendation,
        blockers=blockers,
        next_action=next_action,
    )


def _frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    meta: dict[str, str] = {}
    for line in parts[1].splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip()
    return meta


def _title(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line.lstrip("#").strip()
    return ""


def _int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _markdown(result: HypothesisReviewResult) -> str:
    lines = [
        "# Hypothesis Review",
        "",
        f"- Generated: {result.generated_at}",
        f"- Input: `{result.input_dir}`",
        f"- Reviewed: {result.reviewed_count}",
        f"- Ready: {result.ready_count}",
        f"- Needs rules: {result.needs_rules_count}",
        f"- Reject/archive: {result.rejected_count}",
        "",
        "## Items",
        "",
        "| Recommendation | Score | Title | Blockers | Path |",
        "| --- | ---: | --- | --- | --- |",
    ]
    for item in result.items:
        blockers = ", ".join(item.blockers) if item.blockers else "none"
        lines.append(
            f"| {item.recommendation} | {item.source_quality_score} | {item.title} | {blockers} | `{item.path}` |"
        )
    lines.extend(
        [
            "",
            "## Guardrails",
            "",
            "- This review does not move files.",
            "- This review does not create strategy code.",
            "- Operator approval is required before candidate conversion.",
            "",
        ]
    )
    return "\n".join(lines)
