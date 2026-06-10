"""Rank research notes and flag duplicate or already-tested candidates."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass
class CandidateSelectionItem:
    path: str
    folder: str
    idea_id: str
    title: str
    status: str
    source_note: str
    source_url: str
    score: int
    recommendation: str
    reasons: list[str] = field(default_factory=list)
    next_action: str = ""


@dataclass
class CandidateSelectionResult:
    generated_at: str
    research_dir: str
    candidate_dir: str
    rejected_dir: str
    output_path: str
    output_json_path: str
    reviewed_count: int
    translate_count: int
    blocked_count: int
    items: list[CandidateSelectionItem]


def select_next_candidates(
    research_dir: str | Path = "ideas/research_queue",
    candidate_dir: str | Path = "ideas/backtest_candidates",
    rejected_dir: str | Path = "ideas/rejected",
    output_dir: str | Path = "idea_reviews",
    translation_blocked_dir: str | Path = "ideas/translation_blocked",
    proxy_decisions_dir: str | Path = "ideas/proxy_decisions",
    limit: int = 20,
) -> CandidateSelectionResult:
    research = Path(research_dir)
    candidates = Path(candidate_dir)
    rejected = Path(rejected_dir)
    translation_blocked = Path(translation_blocked_dir)
    proxy_decisions = Path(proxy_decisions_dir)
    rejected_refs = _reference_set(rejected)
    candidate_refs = _reference_set(candidates)
    blocked_refs = _blocked_reference_map(translation_blocked)
    proxy_refs = _blocked_reference_map(proxy_decisions)

    items: list[CandidateSelectionItem] = []
    for path in sorted(research.glob("*.md")) if research.exists() else []:
        items.append(_score_research_note(path, rejected_refs, candidate_refs, blocked_refs, proxy_refs))
    for path in sorted(candidates.glob("*.md")) if candidates.exists() else []:
        items.append(_score_candidate(path, rejected_refs))

    items.sort(key=lambda item: (item.recommendation == "TRANSLATE_NEXT", item.score), reverse=True)
    items = items[:limit]
    translate_count = sum(1 for item in items if item.recommendation == "TRANSLATE_NEXT")
    blocked_count = sum(1 for item in items if item.recommendation != "TRANSLATE_NEXT")

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    date_id = datetime.now(UTC).strftime("%Y-%m-%d")
    output_path = output / f"candidate_selection_{date_id}.md"
    output_json_path = output / f"candidate_selection_{date_id}.json"
    result = CandidateSelectionResult(
        generated_at=datetime.now(UTC).replace(microsecond=0).isoformat(),
        research_dir=str(research),
        candidate_dir=str(candidates),
        rejected_dir=str(rejected),
        output_path=str(output_path),
        output_json_path=str(output_json_path),
        reviewed_count=len(items),
        translate_count=translate_count,
        blocked_count=blocked_count,
        items=items,
    )
    output_path.write_text(_markdown(result), encoding="utf-8")
    output_json_path.write_text(json.dumps(asdict(result), indent=2, default=str), encoding="utf-8")
    return result


def _score_research_note(
    path: Path,
    rejected_refs: set[str],
    candidate_refs: set[str],
    blocked_refs: dict[str, str],
    proxy_refs: dict[str, str],
) -> CandidateSelectionItem:
    text = path.read_text(encoding="utf-8")
    meta = _frontmatter(text)
    refs = _refs(meta)
    score = _int(meta.get("source_quality_score"), 0)
    reasons = [f"source_quality_{score}"]

    if refs & rejected_refs:
        return _item(path, "research_queue", meta, 0, "ALREADY_TESTED_REJECTED", ["source_or_note_already_rejected"], "Keep for history; do not convert again.")
    if refs & candidate_refs:
        return _item(path, "research_queue", meta, 10, "ALREADY_HAS_CANDIDATE", ["matching_candidate_exists"], "Review existing candidate result before translating again.")
    blocked_statuses = {blocked_refs[ref] for ref in refs if ref in blocked_refs}
    proxy_statuses = {proxy_refs[ref] for ref in refs if ref in proxy_refs}
    if "formula_extracted_data_blocked" in blocked_statuses:
        if proxy_statuses:
            return _item(
                path,
                "research_queue",
                meta,
                score,
                "PROXY_DECISION_REQUIRED",
                reasons + ["formula_extracted_data_blocked", "proxy_decision_required"],
                "Add missing data or explicitly approve the incomplete proxy scope before candidate conversion.",
            )
        return _item(
            path,
            "research_queue",
            meta,
            score,
            "DATA_BLOCKED",
            reasons + ["formula_extracted_data_blocked"],
            "Resolve data coverage or document a reduced proxy before candidate conversion.",
        )
    if blocked_statuses:
        return _item(
            path,
            "research_queue",
            meta,
            score,
            "FORMULA_BLOCKED",
            reasons + ["translation_blocked"],
            "Extract exact tradable rules before creating any candidate.",
        )

    lower = text.lower()
    if "to be defined from source after human review" in lower:
        score -= 25
        reasons.append("rules_not_defined")
    if "walk-forward" in lower or "walk forward" in lower:
        score += 8
        reasons.append("walk_forward_relevant")
    if "transaction cost" in lower or "spread" in lower or "commission" in lower:
        score += 8
        reasons.append("cost_model_relevant")
    if "filter" in lower or "regime" in lower or "volatility" in lower:
        score += 6
        reasons.append("filter_or_regime_relevant")
    if "carry" in lower or "mean reversion" in lower or "multi-strategy" in lower or "combining" in lower:
        score += 10
        reasons.append("portfolio_or_signal_combination")
    if "ema crossover" in lower and "negative_after_costs" not in lower:
        score -= 12
        reasons.append("ema_family_already_failed_locally")

    if score >= 82 and "rules_not_defined" not in reasons:
        recommendation = "TRANSLATE_NEXT"
        next_action = "Convert into exact Entry/Exit/Filters/Risk packet."
    elif score >= 82:
        recommendation = "NEEDS_RULE_TRANSLATION"
        next_action = "Extract exact tradable rules before creating any candidate."
    else:
        recommendation = "HOLD"
        next_action = "Do not convert until stronger rules or a clearer V2 mapping exists."
    return _item(path, "research_queue", meta, max(score, 0), recommendation, reasons, next_action)


def _score_candidate(path: Path, rejected_refs: set[str]) -> CandidateSelectionItem:
    text = path.read_text(encoding="utf-8")
    meta = _frontmatter(text)
    refs = _refs(meta)
    status = str(meta.get("status") or "unknown")
    if status == "tested_rejected":
        return _item(path, "backtest_candidates", meta, 0, "CLOSED_REJECTED", ["candidate_already_tested_rejected"], "No further work unless source is reframed.")
    if refs & rejected_refs:
        return _item(path, "backtest_candidates", meta, 0, "CLOSE_DUPLICATE", ["source_or_note_already_rejected"], "Mark as tested_rejected or move to rejected notes.")
    return _item(path, "backtest_candidates", meta, 50, "OPEN_CANDIDATE", ["candidate_needs_result_or_review"], "Run or close the candidate before adding similar work.")


def _reference_set(folder: Path) -> set[str]:
    refs: set[str] = set()
    if not folder.exists():
        return refs
    for path in folder.glob("*.md"):
        meta = _frontmatter(path.read_text(encoding="utf-8"))
        refs.update(_refs(meta))
    return {ref for ref in refs if ref}


def _blocked_reference_map(folder: Path) -> dict[str, str]:
    refs: dict[str, str] = {}
    if not folder.exists():
        return refs
    for path in folder.glob("*.md"):
        meta = _frontmatter(path.read_text(encoding="utf-8"))
        status = str(meta.get("status") or "translation_blocked")
        for ref in _refs(meta):
            refs[ref] = status
    return refs


def _refs(meta: dict[str, str]) -> set[str]:
    return {
        str(meta.get("idea_id") or "").strip(),
        str(meta.get("source_note") or "").strip(),
        str(meta.get("source_url") or "").strip(),
    } - {""}


def _item(
    path: Path,
    folder: str,
    meta: dict[str, str],
    score: int,
    recommendation: str,
    reasons: list[str],
    next_action: str,
) -> CandidateSelectionItem:
    return CandidateSelectionItem(
        path=str(path),
        folder=folder,
        idea_id=str(meta.get("idea_id") or path.stem),
        title=str(meta.get("title") or path.stem),
        status=str(meta.get("status") or "unknown"),
        source_note=str(meta.get("source_note") or ""),
        source_url=str(meta.get("source_url") or ""),
        score=score,
        recommendation=recommendation,
        reasons=reasons,
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


def _int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _markdown(result: CandidateSelectionResult) -> str:
    lines = [
        "# Candidate Selection Review",
        "",
        f"- Generated: {result.generated_at}",
        f"- Research queue: `{result.research_dir}`",
        f"- Candidate dir: `{result.candidate_dir}`",
        f"- Rejected dir: `{result.rejected_dir}`",
        f"- Reviewed: {result.reviewed_count}",
        f"- Translate next: {result.translate_count}",
        f"- Blocked/hold: {result.blocked_count}",
        "",
        "## Items",
        "",
        "| Recommendation | Score | Folder | Title | Reasons | Next Action |",
        "| --- | ---: | --- | --- | --- | --- |",
    ]
    for item in result.items:
        lines.append(
            f"| {item.recommendation} | {item.score} | {item.folder} | {item.title} | {', '.join(item.reasons)} | {item.next_action} |"
        )
    lines.extend(
        [
            "",
            "## Guardrails",
            "",
            "- This review ranks and blocks only; it does not promote strategy code.",
            "- Already rejected sources should not be converted again without a new thesis.",
            "- Prefer filter, regime, cost, and portfolio-construction improvements over repeated plain EMA tests.",
            "",
        ]
    )
    return "\n".join(lines)
