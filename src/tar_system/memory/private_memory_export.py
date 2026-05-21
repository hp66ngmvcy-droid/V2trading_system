"""Private local memory exports for strategy research.

Writes committee and fitter outputs into local-only Obsidian and second-brain
folders. These exports are intended for private use and must not be pushed to
GitHub.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tar_system.audit.writer import append_audit_event


DEFAULT_OBSIDIAN_PRIVATE_ROOT = Path("obsidian/private_trading_memory")
DEFAULT_SECOND_BRAIN_PRIVATE_ROOT = Path("second_brain/vault/01_hubs/private_trading_memory")


@dataclass(frozen=True)
class PrivateMemoryExport:
    generated_at: str
    paper_only: bool
    committee_notes: list[str] = field(default_factory=list)
    filter_plan_notes: list[str] = field(default_factory=list)
    index_notes: list[str] = field(default_factory=list)


def export_private_strategy_memory(
    *,
    runtime_dir: str | Path = "runtime",
    obsidian_root: str | Path = DEFAULT_OBSIDIAN_PRIVATE_ROOT,
    second_brain_root: str | Path = DEFAULT_SECOND_BRAIN_PRIVATE_ROOT,
    strategy: str | None = None,
    symbol: str | None = None,
    timeframe: str | None = None,
) -> PrivateMemoryExport:
    """Export private research notes from local runtime JSON artifacts."""

    runtime = Path(runtime_dir)
    obsidian = Path(obsidian_root)
    second_brain = Path(second_brain_root)
    for root in (obsidian, second_brain):
        (root / "strategy_reviews").mkdir(parents=True, exist_ok=True)
        (root / "filter_plans").mkdir(parents=True, exist_ok=True)
        (root / "indexes").mkdir(parents=True, exist_ok=True)

    committee_payloads = _load_committee_payloads(runtime, strategy, symbol, timeframe)
    committee_notes: list[str] = []
    for payload in committee_payloads:
        committee_notes.extend(
            [
                str(_write_committee_note(payload, obsidian / "strategy_reviews")),
                str(_write_committee_note(payload, second_brain / "strategy_reviews")),
            ]
        )

    filter_plan_notes: list[str] = []
    filter_payload = _load_json(runtime / "strategy_filter_plan.json")
    if filter_payload:
        filter_plan_notes.extend(
            [
                str(_write_filter_plan_note(filter_payload, obsidian / "filter_plans")),
                str(_write_filter_plan_note(filter_payload, second_brain / "filter_plans")),
            ]
        )

    index_notes = [
        str(_write_index(obsidian, committee_notes, filter_plan_notes)),
        str(_write_index(second_brain, committee_notes, filter_plan_notes)),
    ]
    export = PrivateMemoryExport(
        generated_at=datetime.now(timezone.utc).isoformat(),
        paper_only=True,
        committee_notes=committee_notes,
        filter_plan_notes=filter_plan_notes,
        index_notes=index_notes,
    )
    append_audit_event(
        "private_memory_export",
        strategy or "all",
        symbol or "",
        timeframe or "",
        "COMPLETED",
        "PRIVATE_LOCAL_MEMORY_EXPORTED",
        {
            "committee_notes": committee_notes,
            "filter_plan_notes": filter_plan_notes,
            "index_notes": index_notes,
            "paper_only": True,
        },
    )
    return export


def _load_committee_payloads(runtime: Path, strategy: str | None, symbol: str | None, timeframe: str | None) -> list[dict[str, Any]]:
    payloads: list[dict[str, Any]] = []
    for path in sorted(runtime.glob("research_committee_*.json")):
        payload = _load_json(path)
        if not payload:
            continue
        if strategy and payload.get("strategy") != strategy:
            continue
        if symbol and payload.get("symbol") != symbol:
            continue
        if timeframe and payload.get("timeframe") != timeframe:
            continue
        payloads.append(payload)
    return payloads


def _write_committee_note(payload: dict[str, Any], directory: Path) -> Path:
    strategy = str(payload.get("strategy", "unknown"))
    symbol = str(payload.get("symbol", "UNKNOWN"))
    timeframe = str(payload.get("timeframe", "NA"))
    note_id = _safe_name(f"{strategy}_{symbol}_{timeframe}_committee")
    path = directory / f"{note_id}.md"
    lines = [
        "---",
        f"title: Private Committee {strategy} {symbol} {timeframe}",
        "type: private-strategy-committee",
        "privacy: local-only",
        "paper_only: true",
        f"strategy: {strategy}",
        f"symbol: {symbol}",
        f"timeframe: {timeframe}",
        f"recommendation: {payload.get('recommendation', 'REVIEW')}",
        f"generated_at: {payload.get('generated_at', '')}",
        "tags: [private, trading, strategy-research, committee]",
        "---",
        "",
        f"# Private Committee - {strategy} {symbol} {timeframe}",
        "",
        "> Local-only memory. Do not push to GitHub.",
        "",
        "## Decision",
        "",
        f"- Recommendation: {payload.get('recommendation', 'REVIEW')}",
        f"- Confidence: {payload.get('confidence', 0.0)}",
        "- Mode: paper-only research",
        "",
        "## Guardrails",
    ]
    lines.extend(f"- {item}" for item in payload.get("guardrails", []) or ["Human review required."])
    lines.extend(["", "## Analyst Summary"])
    for section in ("agents", "debate"):
        for agent in payload.get(section, []) or []:
            lines.extend(_agent_lines(agent))
    if payload.get("synthesis"):
        lines.extend(["", "## Trader Synthesis", *_agent_lines(payload["synthesis"])])
    if payload.get("risk_review"):
        lines.extend(["", "## Risk Review", *_agent_lines(payload["risk_review"])])
    lines.extend(["", "## Next Actions"])
    lines.extend(f"- {item}" for item in payload.get("required_next_actions", []) or ["Review manually."])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _write_filter_plan_note(payload: dict[str, Any], directory: Path) -> Path:
    path = directory / "strategy_filter_plan.md"
    lines = [
        "---",
        "title: Private Strategy Filter Plan",
        "type: private-strategy-filter-plan",
        "privacy: local-only",
        "paper_only: true",
        f"generated_at: {payload.get('generated_at', '')}",
        "tags: [private, trading, strategy-research, filters]",
        "---",
        "",
        "# Private Strategy Filter Plan",
        "",
        "> Local-only memory. Do not push to GitHub.",
        "",
        "## Blocker Counts",
    ]
    blocker_counts = payload.get("blocker_counts", {}) or {}
    if blocker_counts:
        for blocker, count in sorted(blocker_counts.items(), key=lambda item: (-int(item[1]), item[0])):
            lines.append(f"- {blocker}: {count}")
    else:
        lines.append("- None")
    lines.extend(["", "## Recommendations"])
    for rec in payload.get("recommendations", []) or []:
        lines.extend(
            [
                "",
                f"### {rec.get('strategy')} {rec.get('symbol')} {rec.get('timeframe')}",
                f"- Committee: {rec.get('committee_recommendation')}",
                f"- Blockers: {', '.join(rec.get('blockers', []) or []) or 'None'}",
                "- Filters:",
            ]
        )
        lines.extend(f"  - {item}" for item in rec.get("filters", []) or [])
        tests = rec.get("parameter_tests", {}) or {}
        if tests:
            lines.append("- Paper retest parameters:")
            for key, value in tests.items():
                lines.append(f"  - {key}: {value}")
        if rec.get("retest_command"):
            lines.extend(["- Retest command:", f"  `{rec['retest_command']}`"])
    lines.extend(["", "## Next Actions"])
    lines.extend(f"- {item}" for item in payload.get("next_actions", []) or ["Review manually."])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _write_index(root: Path, committee_notes: list[str], filter_plan_notes: list[str]) -> Path:
    path = root / "indexes" / "Private Trading Memory.md"
    root_path = root.resolve()
    all_notes = [Path(item) for item in committee_notes + filter_plan_notes if _inside(Path(item), root_path)]
    lines = [
        "# Private Trading Memory",
        "",
        "Local-only index for paper strategy research. Do not push to GitHub.",
        "",
        "## Notes",
    ]
    if not all_notes:
        lines.append("- No private notes exported yet.")
    for note in sorted(all_notes):
        lines.append(f"- [[{note.stem}]]")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _agent_lines(agent: dict[str, Any]) -> list[str]:
    lines = [
        "",
        f"### {agent.get('role', 'Agent')}",
        f"- Stance: {agent.get('stance', 'REVIEW')}",
        f"- Score: {agent.get('score', 0)}",
        f"- Summary: {agent.get('summary', '')}",
    ]
    evidence = agent.get("evidence", []) or []
    concerns = agent.get("concerns", []) or []
    if evidence:
        lines.append("- Evidence:")
        lines.extend(f"  - {item}" for item in evidence)
    if concerns:
        lines.append("- Concerns:")
        lines.extend(f"  - {item}" for item in concerns)
    return lines


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _safe_name(value: str) -> str:
    return "".join(char if char.isalnum() or char in "-_" else "_" for char in value)


def _inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root)
        return True
    except ValueError:
        return False
