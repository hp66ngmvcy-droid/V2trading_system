from __future__ import annotations

import json
from pathlib import Path

from tar_system.research.proxy_decisions import draft_proxy_decisions


def test_draft_proxy_decisions_creates_guarded_note_for_blocked_source(tmp_path: Path) -> None:
    requirements = tmp_path / "ideas" / "data_requirements"
    raw = tmp_path / "data" / "raw"
    proxy = tmp_path / "ideas" / "proxy_decisions"
    requirements.mkdir(parents=True)
    raw.mkdir(parents=True)
    (raw / "EURUSD_H1.csv").write_text("timestamp\n2020-01-01\n", encoding="utf-8")
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
- Cost model for futures, or a documented spot-FX approximation.
""",
        encoding="utf-8",
    )

    result = draft_proxy_decisions(requirements, raw, proxy, tmp_path / "idea_reviews")

    assert result.drafted_count == 1
    assert result.items[0].decision == "DO_NOT_CONVERT_FULL_SOURCE"
    assert result.items[0].proxy_scope == "incomplete_local_spot_price_proxy_only"
    note = Path(result.items[0].note_path)
    assert note.exists()
    text = note.read_text(encoding="utf-8")
    assert "status: proxy_decision_required" in text
    assert "Candidate conversion: blocked" in text
    assert "Operator approval is required" in Path(result.output_path).read_text(encoding="utf-8")
    assert json.loads(Path(result.output_json_path).read_text(encoding="utf-8"))["drafted_count"] == 1


def test_draft_proxy_decisions_skips_fully_available_source(tmp_path: Path) -> None:
    requirements = tmp_path / "ideas" / "data_requirements"
    raw = tmp_path / "data" / "raw"
    requirements.mkdir(parents=True)
    raw.mkdir(parents=True)
    (requirements / "source.md").write_text(
        """---
idea_id: source-2
title: Source Data Requirements
status: data_required
---

# Data Requirements

## Required Data

- No special external data.
""",
        encoding="utf-8",
    )

    result = draft_proxy_decisions(requirements, raw, tmp_path / "proxy", tmp_path / "idea_reviews")

    assert result.drafted_count == 0
    assert result.items == []
