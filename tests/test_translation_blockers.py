from __future__ import annotations

import json
from pathlib import Path

from tar_system.research.translation_blockers import review_translation_blockers


def test_review_translation_blockers_extracts_missing_rules(tmp_path: Path) -> None:
    blocked = tmp_path / "ideas" / "translation_blocked"
    blocked.mkdir(parents=True)
    (blocked / "source.md").write_text(
        """---
idea_id: source-1
title: Blocked Source
status: needs_source_rules
source_url: https://example.com/paper
---

# Translation Blocked

## Required Before Candidate Conversion

- Exact momentum indicator formula.
- Portfolio weighting method.
- Cost model.
""",
        encoding="utf-8",
    )

    result = review_translation_blockers(blocked, tmp_path / "idea_reviews")

    assert result.blocked_count == 1
    assert result.items[0].missing_rules == [
        "Exact momentum indicator formula",
        "Portfolio weighting method",
        "Cost model",
    ]
    assert Path(result.output_path).exists()
    assert json.loads(Path(result.output_json_path).read_text(encoding="utf-8"))["blocked_count"] == 1


def test_review_translation_blockers_data_blocked_next_action(tmp_path: Path) -> None:
    blocked = tmp_path / "ideas" / "translation_blocked"
    blocked.mkdir(parents=True)
    (blocked / "source.md").write_text(
        """---
idea_id: source-2
title: Data Blocked Source
status: formula_extracted_data_blocked
---

# Formula Extracted, Data Blocked

## Required Before Candidate Conversion

- Daily rolled futures data.
- Yield data.
""",
        encoding="utf-8",
    )

    result = review_translation_blockers(blocked, tmp_path / "idea_reviews")

    assert result.items[0].next_action == (
        "Resolve data coverage or document a reduced proxy before candidate conversion."
    )


def test_review_translation_blockers_handles_empty_folder(tmp_path: Path) -> None:
    result = review_translation_blockers(tmp_path / "missing", tmp_path / "idea_reviews")

    assert result.blocked_count == 0
    assert result.items == []
