"""Convert online scout results into reviewable hypothesis notes."""

from __future__ import annotations

import datetime as dt
import hashlib
import re
from pathlib import Path
from typing import Any


def _slug(value: str, max_length: int = 64) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return (slug or "untitled")[:max_length].strip("-")


def _quality_score(row: dict[str, Any]) -> int:
    quality = row.get("source_quality")
    if isinstance(quality, dict):
        try:
            return int(quality.get("score", 0))
        except (TypeError, ValueError):
            return 0
    return 0


def _quality_label(row: dict[str, Any]) -> str:
    quality = row.get("source_quality")
    if isinstance(quality, dict):
        return str(quality.get("label", "unknown"))
    return "unknown"


def _iter_hits(scout_result: dict[str, Any]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    def add_rows(source_type: str, source_key: str, rows: Any) -> None:
        if not isinstance(rows, list):
            return
        for row in rows:
            if not isinstance(row, dict):
                continue
            url = str(row.get("url", "")).strip()
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            hits.append({"source_type": source_type, "source_key": source_key, **row})

    sweep = scout_result.get("exa_sweep")
    if isinstance(sweep, dict) and "error" not in sweep:
        for topic, rows in sweep.items():
            add_rows("topic", str(topic), rows)

    multi_agent = scout_result.get("exa_multi_agent_search")
    if isinstance(multi_agent, dict) and "error" not in multi_agent:
        for agent, rows in multi_agent.items():
            add_rows("multi_agent", str(agent), rows)

    return sorted(hits, key=_quality_score, reverse=True)


def _note_text(hit: dict[str, Any], idea_id: str) -> str:
    title = str(hit.get("title", "Untitled source")).strip() or "Untitled source"
    url = str(hit.get("url", "")).strip()
    source_type = str(hit.get("source_type", "unknown"))
    source_key = str(hit.get("source_key", "unknown"))
    score = _quality_score(hit)
    label = _quality_label(hit)
    highlights = [str(item).strip() for item in hit.get("highlights", []) if str(item).strip()]
    highlight_text = "\n".join(f"- {item}" for item in highlights[:5]) or "- No highlight text returned."

    return f"""---
idea_id: {idea_id}
title: {title}
status: hypothesis_extracted
source_url: {url}
source_quality_score: {score}
source_quality_label: {label}
source_context: {source_type}:{source_key}
created_from: online_scout
created_at: {dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat()}
---

# {title}

## Hypothesis
This source may support a testable trading hypothesis related to `{source_key}`. It should be translated into exact entry, exit, filter, and risk rules before any backtest is trusted.

## Source Evidence
- Source: {url}
- Quality: {label} ({score}/100)
- Context: {source_type}:{source_key}

## Highlights
{highlight_text}

## Strategy Translation
Entry: To be defined from source after human review
Exit: To be defined from source after human review
Filters: source_quality_{label}, context_{_slug(source_key)}, walk_forward_required
Risk: cost_sensitive, no_live_promotion, require_out_of_sample
Assumptions: source_requires_rule_translation, hypothesis_not_validated

- Candidate edge:
- Filter or tuning angle:
- Market regime where it may work:
- Market regime where it may fail:

## Backtest Plan
- Target instrument/timeframe:
- Baseline strategy to compare:
- Required filters:
- Walk-forward requirement:
- Kill condition:

## Review Gate
- [ ] Source is credible enough to keep.
- [ ] Rules are specific enough to implement.
- [ ] Cost, spread, and slippage sensitivity are considered.
- [ ] No promotion before out-of-sample and walk-forward review.
"""


def write_hypothesis_notes(
    scout_result: dict[str, Any],
    output_dir: str | Path = "ideas/research_queue",
    min_score: int = 70,
    limit: int = 10,
) -> list[dict[str, str]]:
    """Write high-quality scout hits as markdown hypothesis notes."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    written: list[dict[str, str]] = []

    for hit in _iter_hits(scout_result):
        if _quality_score(hit) < min_score:
            continue
        digest = hashlib.sha256(str(hit.get("url", "")).encode("utf-8")).hexdigest()[:10]
        idea_id = f"online-scout-{dt.date.today().strftime('%Y%m%d')}-{digest}"
        filename = f"{idea_id}-{_slug(str(hit.get('title', 'source')))}.md"
        path = output_path / filename
        path.write_text(_note_text(hit, idea_id), encoding="utf-8")
        written.append({"idea_id": idea_id, "path": str(path), "title": str(hit.get("title", ""))})
        if len(written) >= limit:
            break

    return written
