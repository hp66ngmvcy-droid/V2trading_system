from __future__ import annotations

import json
from pathlib import Path

from tar_system.research.candidate_selection import select_next_candidates


def test_select_next_candidates_blocks_rejected_source(tmp_path: Path) -> None:
    research = tmp_path / "ideas" / "research_queue"
    rejected = tmp_path / "ideas" / "rejected"
    candidates = tmp_path / "ideas" / "backtest_candidates"
    research.mkdir(parents=True)
    rejected.mkdir(parents=True)
    candidates.mkdir(parents=True)
    (rejected / "old.md").write_text(
        """---
idea_id: rejected-1
source_note: source-1
source_url: https://example.com/source
status: rejected
---
""",
        encoding="utf-8",
    )
    (research / "note.md").write_text(
        """---
idea_id: note-1
title: Same Source
source_note: source-1
source_url: https://example.com/source
source_quality_score: 95
status: hypothesis_extracted
---

Entry: To be defined from source after human review
""",
        encoding="utf-8",
    )

    result = select_next_candidates(research, candidates, rejected, tmp_path / "idea_reviews")

    assert result.items[0].recommendation == "ALREADY_TESTED_REJECTED"
    assert result.translate_count == 0


def test_select_next_candidates_prioritizes_filter_or_portfolio_notes(tmp_path: Path) -> None:
    research = tmp_path / "ideas" / "research_queue"
    rejected = tmp_path / "ideas" / "rejected"
    candidates = tmp_path / "ideas" / "backtest_candidates"
    research.mkdir(parents=True)
    rejected.mkdir(parents=True)
    candidates.mkdir(parents=True)
    (research / "note.md").write_text(
        """---
idea_id: note-2
title: Multi Strategy Filters
source_url: https://example.com/new
source_quality_score: 92
status: hypothesis_extracted
---

Entry: rank normalized carry, momentum, and mean reversion indicators.
Exit: rebalance on the next test window.
Filters: volatility regime filter and transaction cost gate.
Risk: walk-forward validation required.
""",
        encoding="utf-8",
    )

    result = select_next_candidates(research, candidates, rejected, tmp_path / "idea_reviews")

    assert result.items[0].recommendation == "TRANSLATE_NEXT"
    assert result.items[0].score > 92
    assert Path(result.output_path).exists()
    assert json.loads(Path(result.output_json_path).read_text(encoding="utf-8"))["translate_count"] == 1


def test_select_next_candidates_marks_formula_extracted_source_data_blocked(tmp_path: Path) -> None:
    research = tmp_path / "ideas" / "research_queue"
    rejected = tmp_path / "ideas" / "rejected"
    candidates = tmp_path / "ideas" / "backtest_candidates"
    blocked = tmp_path / "ideas" / "translation_blocked"
    research.mkdir(parents=True)
    rejected.mkdir(parents=True)
    candidates.mkdir(parents=True)
    blocked.mkdir(parents=True)
    (blocked / "source.md").write_text(
        """---
idea_id: blocked-1
source_note: scout-1
source_url: https://example.com/source
status: formula_extracted_data_blocked
---
""",
        encoding="utf-8",
    )
    (research / "note.md").write_text(
        """---
idea_id: scout-1
title: Formula Ready Data Blocked
source_url: https://example.com/source
source_quality_score: 95
status: hypothesis_extracted
---

Entry: To be defined from source after human review
Filters: walk-forward and volatility.
""",
        encoding="utf-8",
    )

    result = select_next_candidates(
        research,
        candidates,
        rejected,
        tmp_path / "idea_reviews",
        translation_blocked_dir=blocked,
    )

    assert result.items[0].recommendation == "DATA_BLOCKED"
    assert result.items[0].next_action == (
        "Resolve data coverage or document a reduced proxy before candidate conversion."
    )
    assert result.translate_count == 0


def test_select_next_candidates_marks_proxy_decision_required(tmp_path: Path) -> None:
    research = tmp_path / "ideas" / "research_queue"
    rejected = tmp_path / "ideas" / "rejected"
    candidates = tmp_path / "ideas" / "backtest_candidates"
    blocked = tmp_path / "ideas" / "translation_blocked"
    proxy = tmp_path / "ideas" / "proxy_decisions"
    research.mkdir(parents=True)
    rejected.mkdir(parents=True)
    candidates.mkdir(parents=True)
    blocked.mkdir(parents=True)
    proxy.mkdir(parents=True)
    (blocked / "source.md").write_text(
        """---
idea_id: blocked-1
source_note: scout-1
source_url: https://example.com/source
status: formula_extracted_data_blocked
---
""",
        encoding="utf-8",
    )
    (proxy / "source.md").write_text(
        """---
idea_id: blocked-1
source_url: https://example.com/source
status: proxy_decision_required
---
""",
        encoding="utf-8",
    )
    (research / "note.md").write_text(
        """---
idea_id: scout-1
title: Formula Ready Proxy Decision Required
source_url: https://example.com/source
source_quality_score: 95
status: hypothesis_extracted
---

Entry: To be defined from source after human review
Filters: walk-forward and volatility.
""",
        encoding="utf-8",
    )

    result = select_next_candidates(
        research,
        candidates,
        rejected,
        tmp_path / "idea_reviews",
        translation_blocked_dir=blocked,
        proxy_decisions_dir=proxy,
    )

    assert result.items[0].recommendation == "PROXY_DECISION_REQUIRED"
    assert result.items[0].next_action == (
        "Add missing data or explicitly approve the incomplete proxy scope before candidate conversion."
    )
    assert result.translate_count == 0
