from __future__ import annotations

import json
from pathlib import Path

from tar_system.research.hypothesis_review import review_hypotheses


def test_review_hypotheses_marks_extracted_notes_as_needing_rules(tmp_path: Path) -> None:
    inbox = tmp_path / "ideas" / "research_queue"
    inbox.mkdir(parents=True)
    (inbox / "idea.md").write_text(
        """---
idea_id: idea-1
title: Test Source
status: hypothesis_extracted
source_url: https://arxiv.org/abs/test
source_quality_score: 95
source_quality_label: high
---

# Test Source

Entry: To be defined from source after human review
Exit: To be defined from source after human review

- [ ] Rules are specific enough to implement.
""",
        encoding="utf-8",
    )

    result = review_hypotheses(inbox, tmp_path / "idea_reviews")

    assert result.reviewed_count == 1
    assert result.needs_rules_count == 1
    assert result.items[0].recommendation == "NEEDS_RULE_TRANSLATION"
    assert "strategy_rules_not_defined" in result.items[0].blockers
    assert Path(result.output_path).exists()
    assert json.loads(Path(result.output_json_path).read_text(encoding="utf-8"))["reviewed_count"] == 1


def test_review_hypotheses_rejects_low_quality_notes(tmp_path: Path) -> None:
    inbox = tmp_path / "ideas" / "research_queue"
    inbox.mkdir(parents=True)
    (inbox / "low.md").write_text(
        """---
idea_id: idea-low
title: Weak Source
status: hypothesis_extracted
source_url: http://example.com/tips
source_quality_score: 35
source_quality_label: low
---

# Weak Source
""",
        encoding="utf-8",
    )

    result = review_hypotheses(inbox, tmp_path / "idea_reviews")

    assert result.rejected_count == 1
    assert result.items[0].recommendation == "REJECT_OR_ARCHIVE"
