from __future__ import annotations

import json
from pathlib import Path

from tar_system.research.data_requirements_review import review_data_requirements


def test_review_data_requirements_marks_partial_and_missing_inputs(tmp_path: Path) -> None:
    requirements = tmp_path / "ideas" / "data_requirements"
    raw = tmp_path / "data" / "raw"
    requirements.mkdir(parents=True)
    raw.mkdir(parents=True)
    (raw / "EURUSD_H1.csv").write_text("timestamp\n2020-01-01\n", encoding="utf-8")
    (raw / "XAUUSD_H1.csv").write_text("timestamp\n2020-01-01\n", encoding="utf-8")
    (requirements / "source.md").write_text(
        """---
idea_id: source-1
title: Source Data Requirements
status: data_required
source_url: https://example.com/source
---

# Data Requirements

## Required Data

- Daily rolled FX futures series or a documented spot-FX proxy.
- 1-year and 10-year yields for each currency geography.
- Linked equity indices.
- Commodity indices/assets.
- Cost model for futures, or a documented spot-FX approximation.
""",
        encoding="utf-8",
    )

    result = review_data_requirements(requirements, raw, tmp_path / "idea_reviews")

    assert result.item_count == 1
    assert result.ready_count == 0
    assert result.blocked_count == 1
    statuses = {row.requirement: row.status for row in result.items[0].rows}
    assert statuses["FX futures or documented spot-FX proxy"] == "PARTIAL"
    assert statuses["1-year and 10-year yield history"] == "MISSING"
    assert statuses["Linked equity index history"] == "MISSING"
    assert statuses["Commodity index/assets history"] == "PARTIAL"
    assert statuses["Futures cost model or spot-FX approximation"] == "DECISION_REQUIRED"
    assert Path(result.output_path).exists()
    assert json.loads(Path(result.output_json_path).read_text(encoding="utf-8"))["blocked_count"] == 1


def test_review_data_requirements_handles_empty_folder(tmp_path: Path) -> None:
    result = review_data_requirements(tmp_path / "missing", tmp_path / "raw", tmp_path / "idea_reviews")

    assert result.item_count == 0
    assert result.items == []
