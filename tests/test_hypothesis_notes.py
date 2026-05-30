"""Tests for converting scout output into hypothesis notes."""

from __future__ import annotations

from pathlib import Path

from tar_system.research.hypothesis_notes import write_hypothesis_notes


def test_write_hypothesis_notes_keeps_high_quality_hits(tmp_path: Path):
    scout_result = {
        "exa_multi_agent_search": {
            "risk": [
                {
                    "title": "Walk forward volatility filter paper",
                    "url": "https://arxiv.org/abs/1234.5678",
                    "highlights": ["walk forward validation with volatility filter"],
                    "source_quality": {"score": 95, "label": "high", "reasons": ["trusted_or_research_host"]},
                }
            ],
            "performance": [
                {
                    "title": "Low signal blog post",
                    "url": "http://example.com/tips",
                    "highlights": ["opinion"],
                    "source_quality": {"score": 35, "label": "low", "reasons": []},
                }
            ],
        }
    }

    written = write_hypothesis_notes(scout_result, tmp_path, min_score=70)

    assert len(written) == 1
    note = Path(written[0]["path"])
    text = note.read_text(encoding="utf-8")
    assert "status: hypothesis_extracted" in text
    assert "source_quality_score: 95" in text
    assert "Walk forward volatility filter paper" in text
    assert "Entry: To be defined from source after human review" in text
    assert "Filters: source_quality_high, context_risk, walk_forward_required" in text
    assert "No promotion before out-of-sample" in text


def test_write_hypothesis_notes_deduplicates_urls(tmp_path: Path):
    source = {
        "title": "Shared source",
        "url": "https://github.com/example/strategy",
        "highlights": ["source code"],
        "source_quality": {"score": 90, "label": "high", "reasons": ["code_available"]},
    }
    scout_result = {
        "exa_sweep": {"momentum": [source]},
        "exa_multi_agent_search": {"performance": [source]},
    }

    written = write_hypothesis_notes(scout_result, tmp_path, min_score=70)

    assert len(written) == 1
