"""Draft guarded reduced-proxy decisions for data-blocked research sources."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from tar_system.research.data_requirements_review import DataRequirementItem, review_data_requirements


@dataclass
class ProxyDecisionItem:
    idea_id: str
    title: str
    source_url: str
    note_path: str
    decision: str
    proxy_scope: str
    blocked_components: list[str] = field(default_factory=list)


@dataclass
class ProxyDecisionDraftResult:
    generated_at: str
    requirements_dir: str
    raw_dir: str
    proxy_dir: str
    output_path: str
    output_json_path: str
    drafted_count: int
    items: list[ProxyDecisionItem]


def draft_proxy_decisions(
    requirements_dir: str | Path = "ideas/data_requirements",
    raw_dir: str | Path = "data/raw",
    proxy_dir: str | Path = "ideas/proxy_decisions",
    output_dir: str | Path = "idea_reviews",
) -> ProxyDecisionDraftResult:
    review = review_data_requirements(requirements_dir=requirements_dir, raw_dir=raw_dir, output_dir=output_dir)
    proxy_output = Path(proxy_dir)
    proxy_output.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%d")
    items: list[ProxyDecisionItem] = []
    for item in review.items:
        if all(row.status == "AVAILABLE" for row in item.rows):
            continue
        note_path = proxy_output / f"{_slug(item.idea_id)}-{stamp}.md"
        decision = _decision_item(item, note_path)
        note_path.write_text(_decision_markdown(decision, item), encoding="utf-8")
        items.append(decision)

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    date_id = datetime.now(UTC).strftime("%Y-%m-%d")
    output_path = output / f"proxy_decisions_{date_id}.md"
    output_json_path = output / f"proxy_decisions_{date_id}.json"
    result = ProxyDecisionDraftResult(
        generated_at=datetime.now(UTC).replace(microsecond=0).isoformat(),
        requirements_dir=str(Path(requirements_dir)),
        raw_dir=str(Path(raw_dir)),
        proxy_dir=str(proxy_output),
        output_path=str(output_path),
        output_json_path=str(output_json_path),
        drafted_count=len(items),
        items=items,
    )
    output_path.write_text(_summary_markdown(result), encoding="utf-8")
    output_json_path.write_text(json.dumps(asdict(result), indent=2, default=str), encoding="utf-8")
    return result


def _decision_item(item: DataRequirementItem, note_path: Path) -> ProxyDecisionItem:
    blocked = [f"{row.requirement}: {row.status}" for row in item.rows if row.status != "AVAILABLE"]
    return ProxyDecisionItem(
        idea_id=item.idea_id,
        title=item.title,
        source_url=item.source_url,
        note_path=str(note_path),
        decision="DO_NOT_CONVERT_FULL_SOURCE",
        proxy_scope="incomplete_local_spot_price_proxy_only",
        blocked_components=blocked,
    )


def _decision_markdown(decision: ProxyDecisionItem, item: DataRequirementItem) -> str:
    lines = [
        "---",
        f"idea_id: {decision.idea_id}",
        f"title: {decision.title} - Proxy Decision Required",
        "status: proxy_decision_required",
        f"source_url: {decision.source_url}",
        f"created_at: {datetime.now(UTC).date().isoformat()}",
        "paper_only: true",
        "---",
        "",
        "# Proxy Decision Required",
        "",
        "## Decision",
        "",
        f"- Current decision: {decision.decision}",
        f"- Allowed local proxy scope: {decision.proxy_scope}",
        "- Candidate conversion: blocked until an operator explicitly accepts the reduced scope.",
        "",
        "## Why This Is Blocked",
        "",
    ]
    for blocked in decision.blocked_components:
        lines.append(f"- {blocked}")
    lines.extend(
        [
            "",
            "## If A Reduced Proxy Is Approved",
            "",
            "- Label the candidate as incomplete and not representative of the full source.",
            "- Exclude missing components rather than inventing them.",
            "- Compare only against local price-action baselines.",
            "- Do not use the result to reject or promote the full paper.",
            "- Keep live, paper, and automation promotion disabled.",
            "",
            "## Data Review Snapshot",
            "",
            "| Requirement | Status | Local Evidence | Action |",
            "| --- | --- | --- | --- |",
        ]
    )
    for row in item.rows:
        lines.append(f"| {row.requirement} | {row.status} | {row.local_evidence} | {row.action} |")
    lines.append("")
    return "\n".join(lines)


def _summary_markdown(result: ProxyDecisionDraftResult) -> str:
    lines = [
        "# Proxy Decision Drafts",
        "",
        f"- Generated: {result.generated_at}",
        f"- Requirements dir: `{result.requirements_dir}`",
        f"- Raw dir: `{result.raw_dir}`",
        f"- Proxy dir: `{result.proxy_dir}`",
        f"- Drafted notes: {result.drafted_count}",
        "",
        "| Decision | Proxy Scope | Title | Note |",
        "| --- | --- | --- | --- |",
    ]
    for item in result.items:
        lines.append(f"| {item.decision} | {item.proxy_scope} | {item.title} | `{item.note_path}` |")
    lines.extend(
        [
            "",
            "## Guardrails",
            "",
            "- These drafts do not create candidates.",
            "- Reduced proxies are incomplete by default.",
            "- Operator approval is required before any reduced-proxy backtest.",
            "",
        ]
    )
    return "\n".join(lines)


def _slug(value: str) -> str:
    return "".join(char.lower() if char.isalnum() else "-" for char in value).strip("-")
