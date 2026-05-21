from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


MODULE_PATH = Path("/Users/whs1/Dev/V2trading_system/second_brain/scripts/brain.py")
SPEC = importlib.util.spec_from_file_location("second_brain_cli", MODULE_PATH)
brain = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = brain
SPEC.loader.exec_module(brain)


def test_frontmatter_parser() -> None:
    frontmatter, body = brain.parse_frontmatter("---\ntitle: Test Note\ntags: trading\n---\n# Body\n")
    assert frontmatter["title"] == "Test Note"
    assert body.startswith("# Body")


def test_note_record_extracts_metadata(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(brain, "ROOT", tmp_path)
    monkeypatch.setattr(brain, "SECOND_BRAIN", tmp_path / "second_brain")
    monkeypatch.setattr(brain, "VAULT", tmp_path / "second_brain" / "vault")
    note_dir = brain.VAULT / "01_hubs" / "trading"
    note_dir.mkdir(parents=True)
    path = note_dir / "gold_review.md"
    path.write_text("---\ntitle: Gold Review\n---\n# Gold Review\n\n#trading Link to [[Risk SOP]].\n", encoding="utf-8")

    record = brain.note_record(path)

    assert record.title == "Gold Review"
    assert record.hub == "trading"
    assert record.tags == ["trading"]
    assert record.links == ["Risk SOP"]


def test_index_search_and_tidy_report(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(brain, "ROOT", tmp_path)
    monkeypatch.setattr(brain, "SECOND_BRAIN", tmp_path / "second_brain")
    monkeypatch.setattr(brain, "VAULT", tmp_path / "second_brain" / "vault")
    monkeypatch.setattr(brain, "INDEXES", tmp_path / "second_brain" / "indexes")
    monkeypatch.setattr(brain, "METADATA", tmp_path / "second_brain" / "metadata")
    monkeypatch.setattr(
        brain,
        "NOTE_DIRS",
        [
            brain.VAULT / "00_inbox",
            brain.VAULT / "01_hubs" / "trading",
            brain.VAULT / "02_reviews" / "daily",
        ],
    )
    brain.ensure_structure()
    (brain.VAULT / "01_hubs" / "trading" / "strategy.md").write_text(
        "---\ntitle: Strategy Memory\n---\n# Strategy Memory\n\n#trading Strategy review with [[Missing Note]].\n",
        encoding="utf-8",
    )

    records = brain.build_index()
    results = brain.search("strategy trading")
    report = brain.tidy_report()

    assert len(records) == 1
    assert results[0]["title"] == "Strategy Memory"
    assert report["note_count"] == 1
    assert report["broken_links"][0]["link"] == "Missing Note"


def test_daily_review_writes_markdown(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(brain, "ROOT", tmp_path)
    monkeypatch.setattr(brain, "SECOND_BRAIN", tmp_path / "second_brain")
    monkeypatch.setattr(brain, "VAULT", tmp_path / "second_brain" / "vault")
    monkeypatch.setattr(brain, "INDEXES", tmp_path / "second_brain" / "indexes")
    monkeypatch.setattr(brain, "METADATA", tmp_path / "second_brain" / "metadata")
    monkeypatch.setattr(
        brain,
        "NOTE_DIRS",
        [
            brain.VAULT / "00_inbox",
            brain.VAULT / "01_hubs" / "operations",
            brain.VAULT / "02_reviews" / "daily",
        ],
    )
    brain.ensure_structure()
    (brain.VAULT / "01_hubs" / "operations" / "ops.md").write_text("# Ops Note\n\nProduction status note.\n", encoding="utf-8")

    output = brain.write_daily_review()

    assert output.exists()
    assert "Vault Health" in output.read_text(encoding="utf-8")
