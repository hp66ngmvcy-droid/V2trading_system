"""Daily idea loop summary and optional scout intake.

This loop is deliberately paper-only. It can collect and summarize research,
but it does not promote candidates, edit strategy code, or trade.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from tar_system.audit.writer import append_audit_event
from tar_system.controller.job_queue import queue_health


@dataclass
class DailyIdeaLoopResult:
    generated_at: str
    review_path: str
    review_json_path: str
    paper_only: bool = True
    online_ready: bool = False
    online_scout_ran: bool = False
    online_scout_saved_to: str | None = None
    hypothesis_notes_written: int = 0
    research_queue_count: int = 0
    backtest_candidate_count: int = 0
    code_candidate_count: int = 0
    ui_candidate_count: int = 0
    security_review_count: int = 0
    next_actions: list[str] = field(default_factory=list)


def run_daily_idea_loop(
    online_query: str | None = None,
    run_online: bool = False,
    output_dir: str | Path = "idea_reviews",
    hypothesis_dir: str | Path = "ideas/research_queue",
    min_source_score: int = 70,
    hypothesis_limit: int = 10,
) -> DailyIdeaLoopResult:
    generated_at = datetime.now(UTC).replace(microsecond=0).isoformat()
    online_ready = _online_ready()
    scout_payload: dict[str, Any] | None = None
    scout_saved_to: str | None = None
    notes_written = 0

    if run_online and online_query and online_ready:
        from tar_system.research.exa_searcher import multi_agent_search
        from tar_system.research.hypothesis_notes import write_hypothesis_notes

        scout_payload = {
            "generated_at": generated_at,
            "query": online_query,
            "exa_multi_agent_search": multi_agent_search(
                online_query,
                num_results=5,
                max_workers=3,
                source_quality="strict",
            ),
        }
        scout_path = _scout_output_path(online_query)
        scout_path.write_text(json.dumps(scout_payload, indent=2, default=str), encoding="utf-8")
        scout_saved_to = str(scout_path)
        notes = write_hypothesis_notes(
            scout_payload,
            output_dir=hypothesis_dir,
            min_score=min_source_score,
            limit=hypothesis_limit,
        )
        notes_written = len(notes)

    counts = _idea_counts()
    actions = _next_actions(online_ready=online_ready, run_online=run_online, online_query=online_query, counts=counts)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    date_id = datetime.now(UTC).strftime("%Y-%m-%d")
    review_path = output_path / f"review_{date_id}.md"
    review_json_path = output_path / f"review_{date_id}.json"
    result = DailyIdeaLoopResult(
        generated_at=generated_at,
        review_path=str(review_path),
        review_json_path=str(review_json_path),
        online_ready=online_ready,
        online_scout_ran=scout_payload is not None,
        online_scout_saved_to=scout_saved_to,
        hypothesis_notes_written=notes_written,
        research_queue_count=counts["research_queue"],
        backtest_candidate_count=counts["backtest_candidates"],
        code_candidate_count=counts["code_candidates"],
        ui_candidate_count=counts["ui_candidates"],
        security_review_count=counts["security_review"],
        next_actions=actions,
    )
    review_path.write_text(_review_markdown(result), encoding="utf-8")
    review_json_path.write_text(json.dumps(asdict(result), indent=2, default=str), encoding="utf-8")
    append_audit_event(
        "daily_idea_loop",
        "idea_orchestrator",
        "",
        "",
        "COMPLETED",
        "DAILY_IDEA_LOOP_COMPLETED",
        asdict(result),
    )
    return result


def _online_ready() -> bool:
    if not os.environ.get("EXA_API_KEY"):
        return False
    try:
        import exa_py  # noqa: F401
    except ImportError:
        return False
    return True


def _idea_counts() -> dict[str, int]:
    return {
        "research_queue": _count_markdown("ideas/research_queue"),
        "backtest_candidates": _count_markdown("ideas/backtest_candidates"),
        "code_candidates": _count_markdown("ideas/code_candidates"),
        "ui_candidates": _count_markdown("ideas/ui_candidates"),
        "security_review": _count_markdown("ideas/security_review"),
    }


def _count_markdown(path: str | Path) -> int:
    folder = Path(path)
    if not folder.exists():
        return 0
    return len([item for item in folder.glob("*.md") if item.is_file()])


def _next_actions(
    online_ready: bool,
    run_online: bool,
    online_query: str | None,
    counts: dict[str, int],
) -> list[str]:
    actions: list[str] = []
    try:
        health = queue_health(limit=5)
    except Exception as exc:
        health = {"error": str(exc)}
        actions.append(f"Queue health unavailable: {exc}")
    if not online_ready:
        actions.append("Add EXA_API_KEY to enable live online scout intake")
    elif run_online and not online_query:
        actions.append("Provide --online-query to run a daily online scout")
    elif online_ready:
        actions.append("Run daily online scout with a focused query if new sources are needed")
    if counts["research_queue"]:
        actions.append(f"Review {counts['research_queue']} research queue notes and move approved items to backtest/code/UI candidate folders")
    else:
        actions.append("No research queue notes waiting; add user ideas or run scout when online is ready")
    if counts["backtest_candidates"]:
        actions.append(f"Prepare deterministic test packets for {counts['backtest_candidates']} backtest candidates")
    if counts["security_review"]:
        actions.append(f"Resolve {counts['security_review']} security review items before implementation")
    failed = int(health.get("failed_jobs", 0) or 0)
    if failed:
        actions.append(f"Review {failed} failed jobs before broad reruns")
    return actions[:8]


def _review_markdown(result: DailyIdeaLoopResult) -> str:
    return "\n".join(
        [
            "# Daily Idea Review",
            "",
            f"- Generated: {result.generated_at}",
            "- Mode: paper-only",
            f"- Online ready: {result.online_ready}",
            f"- Online scout ran: {result.online_scout_ran}",
            f"- Online scout saved to: {result.online_scout_saved_to or 'not run'}",
            f"- Hypothesis notes written: {result.hypothesis_notes_written}",
            "",
            "## Queues",
            f"- Research queue: {result.research_queue_count}",
            f"- Backtest candidates: {result.backtest_candidate_count}",
            f"- Code candidates: {result.code_candidate_count}",
            f"- UI candidates: {result.ui_candidate_count}",
            f"- Security review: {result.security_review_count}",
            "",
            "## Next Actions",
            *(f"- {action}" for action in result.next_actions),
            "",
            "## Guardrails",
            "- No live trading.",
            "- No automatic MT5 promotion.",
            "- No strategy code generation without review.",
            "- Online sources become hypotheses first, not production logic.",
            "",
        ]
    )


def _scout_output_path(query: str) -> Path:
    import re

    output = Path("data/research/online_scout")
    output.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", query.lower()).strip("-")[:48] or "daily-scout"
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return output / f"{stamp}_{slug}.json"
