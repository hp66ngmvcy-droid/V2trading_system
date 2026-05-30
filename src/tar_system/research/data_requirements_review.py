"""Review data requirement notes against local raw market files."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from tar_system.research.candidate_selection import _frontmatter


@dataclass
class DataRequirementRow:
    requirement: str
    status: str
    local_evidence: str
    action: str


@dataclass
class DataRequirementItem:
    path: str
    idea_id: str
    title: str
    status: str
    source_url: str
    rows: list[DataRequirementRow] = field(default_factory=list)


@dataclass
class DataRequirementReview:
    generated_at: str
    requirements_dir: str
    raw_dir: str
    output_path: str
    output_json_path: str
    item_count: int
    ready_count: int
    blocked_count: int
    items: list[DataRequirementItem]


def review_data_requirements(
    requirements_dir: str | Path = "ideas/data_requirements",
    raw_dir: str | Path = "data/raw",
    output_dir: str | Path = "idea_reviews",
) -> DataRequirementReview:
    requirements = Path(requirements_dir)
    raw = Path(raw_dir)
    symbols = _available_symbols(raw)
    items = [_review_one(path, symbols) for path in sorted(requirements.glob("*.md"))] if requirements.exists() else []
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    date_id = datetime.now(UTC).strftime("%Y-%m-%d")
    output_path = output / f"data_requirements_{date_id}.md"
    output_json_path = output / f"data_requirements_{date_id}.json"
    result = DataRequirementReview(
        generated_at=datetime.now(UTC).replace(microsecond=0).isoformat(),
        requirements_dir=str(requirements),
        raw_dir=str(raw),
        output_path=str(output_path),
        output_json_path=str(output_json_path),
        item_count=len(items),
        ready_count=sum(1 for item in items if all(row.status == "AVAILABLE" for row in item.rows)),
        blocked_count=sum(1 for item in items if any(row.status != "AVAILABLE" for row in item.rows)),
        items=items,
    )
    output_path.write_text(_markdown(result), encoding="utf-8")
    output_json_path.write_text(json.dumps(asdict(result), indent=2, default=str), encoding="utf-8")
    return result


def _review_one(path: Path, symbols: set[str]) -> DataRequirementItem:
    text = path.read_text(encoding="utf-8")
    meta = _frontmatter(text)
    rows = _evaluate_requirements(text, symbols)
    return DataRequirementItem(
        path=str(path),
        idea_id=str(meta.get("idea_id") or path.stem),
        title=str(meta.get("title") or path.stem),
        status=str(meta.get("status") or "unknown"),
        source_url=str(meta.get("source_url") or ""),
        rows=rows,
    )


def _available_symbols(raw_dir: Path) -> set[str]:
    symbols: set[str] = set()
    if not raw_dir.exists():
        return symbols
    for path in raw_dir.glob("*.csv"):
        parts = path.stem.split("_")
        if len(parts) == 2:
            symbols.add(parts[0].upper())
    return symbols


def _evaluate_requirements(text: str, symbols: set[str]) -> list[DataRequirementRow]:
    lower = text.lower()
    rows: list[DataRequirementRow] = []
    if "fx futures" in lower or "spot-fx proxy" in lower:
        required = {"AUDUSD", "GBPUSD", "USDCAD", "EURUSD", "USDJPY"}
        available = sorted(required & symbols)
        missing = sorted(required - symbols)
        status = "PARTIAL" if available else "MISSING"
        action = "Document spot-FX proxy limits and missing MXN/NZD/CHF futures coverage."
        rows.append(
            DataRequirementRow(
                requirement="FX futures or documented spot-FX proxy",
                status=status,
                local_evidence=f"spot symbols present: {', '.join(available) or 'none'}; missing core spot symbols: {', '.join(missing) or 'none'}",
                action=action,
            )
        )
    if "yield" in lower:
        rows.append(
            DataRequirementRow(
                requirement="1-year and 10-year yield history",
                status="MISSING",
                local_evidence="no yield symbols found in data/raw",
                action="Add approved yield datasets or remove carry from any reduced proxy.",
            )
        )
    if "equity indices" in lower:
        rows.append(
            DataRequirementRow(
                requirement="Linked equity index history",
                status="MISSING",
                local_evidence="no linked equity index symbols found in data/raw",
                action="Add index datasets before testing equity-momentum components.",
            )
        )
    if "commodity" in lower:
        evidence = []
        if "XAUUSD" in symbols:
            evidence.append("XAUUSD can proxy gold")
        if "USOUSD" in symbols:
            evidence.append("USOUSD can proxy oil, not Brent")
        rows.append(
            DataRequirementRow(
                requirement="Commodity index/assets history",
                status="PARTIAL" if evidence else "MISSING",
                local_evidence="; ".join(evidence) if evidence else "no commodity proxies found in data/raw",
                action="Add GSCI, Brent, and agriculture data or explicitly omit commodity momentum.",
            )
        )
    if "cost model" in lower:
        rows.append(
            DataRequirementRow(
                requirement="Futures cost model or spot-FX approximation",
                status="DECISION_REQUIRED",
                local_evidence="strategy-specific cost model not documented for this source",
                action="Document futures costs or spot-FX approximation before candidate conversion.",
            )
        )
    return rows


def _markdown(result: DataRequirementReview) -> str:
    lines = [
        "# Data Requirements Review",
        "",
        f"- Generated: {result.generated_at}",
        f"- Requirements dir: `{result.requirements_dir}`",
        f"- Raw dir: `{result.raw_dir}`",
        f"- Items: {result.item_count}",
        f"- Fully ready: {result.ready_count}",
        f"- Blocked: {result.blocked_count}",
        "",
    ]
    if not result.items:
        lines.append("- No data requirement notes found.")
    for item in result.items:
        lines.extend(
            [
                f"## {item.title}",
                "",
                f"- Path: `{item.path}`",
                f"- Status: {item.status}",
                f"- Source: {item.source_url}",
                "",
                "| Requirement | Status | Local Evidence | Action |",
                "| --- | --- | --- | --- |",
            ]
        )
        for row in item.rows:
            lines.append(f"| {row.requirement} | {row.status} | {row.local_evidence} | {row.action} |")
        lines.append("")
    lines.extend(
        [
            "## Guardrails",
            "",
            "- Data requirement readiness is not a strategy result.",
            "- Partial local proxies must be labelled incomplete before backtesting.",
            "- Do not promote data-blocked sources to live or paper trading.",
            "",
        ]
    )
    return "\n".join(lines)
