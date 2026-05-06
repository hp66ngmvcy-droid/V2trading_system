from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

from tar_system.cli import build_parser, import_positioning_note_cmd, positioning_score_cmd
from tar_system.optimisation.go_no_go_gate import evaluate_go_no_go
from tar_system.positioning.cot_importer import import_cot_csv
from tar_system.positioning.manual_note_importer import import_positioning_note
from tar_system.positioning.store import latest_positioning_score, load_positioning_records
from tar_system.reporting.reporter import generate_report


def _patch_db(monkeypatch, tmp_path: Path) -> None:
    import tar_system.positioning.store as store

    monkeypatch.setattr(store, "DB_PATH", tmp_path / "positioning.duckdb")


def test_cot_importer_scores_net_positioning(tmp_path, monkeypatch) -> None:
    _patch_db(monkeypatch, tmp_path)
    path = tmp_path / "cot.csv"
    path.write_text("date,noncommercial_long,noncommercial_short\n2026-05-01,150,50\n", encoding="utf-8")

    record = import_cot_csv(path, "XAUUSD")

    assert record.source == "COT"
    assert record.positioning_score == 50.0
    assert record.bias == "BULLISH"
    assert latest_positioning_score("XAUUSD")["bias"] == "BULLISH"


def test_cot_importer_rejects_multimarket_file_without_filter(tmp_path, monkeypatch) -> None:
    _patch_db(monkeypatch, tmp_path)
    path = tmp_path / "cot_multi.csv"
    path.write_text(
        "date,market,noncommercial_long,noncommercial_short\n"
        "2026-05-01,GOLD,150,50\n"
        "2026-05-01,CRUDE OIL,25,100\n",
        encoding="utf-8",
    )

    try:
        import_cot_csv(path, "XAUUSD")
    except ValueError as exc:
        assert "multiple markets" in str(exc)
    else:
        raise AssertionError("multi-market COT import should require a market filter")


def test_cot_importer_filters_requested_market(tmp_path, monkeypatch) -> None:
    _patch_db(monkeypatch, tmp_path)
    path = tmp_path / "cot_multi.csv"
    path.write_text(
        "date,market,noncommercial_long,noncommercial_short\n"
        "2026-05-01,GOLD,150,50\n"
        "2026-05-01,CRUDE OIL,25,100\n",
        encoding="utf-8",
    )

    record = import_cot_csv(path, "XAUUSD", market="GOLD")

    assert record.bias == "BULLISH"
    assert record.metrics["market"] == "GOLD"


def test_manual_note_importer_accepts_claude_or_chat_summary(tmp_path, monkeypatch) -> None:
    _patch_db(monkeypatch, tmp_path)
    path = tmp_path / "note.md"
    path.write_text("Prime brokerage note: hedge funds are net long but crowded long. positioning score: 42", encoding="utf-8")

    record = import_positioning_note(path, "BTCUSD", "claude", "2026-05-04")

    assert record.source == "NOTE_CLAUDE"
    assert record.positioning_score == 42
    assert record.metrics["manual_review_required"] is True


def test_manual_note_json_payload_can_set_score(tmp_path, monkeypatch) -> None:
    _patch_db(monkeypatch, tmp_path)
    path = tmp_path / "note.json"
    path.write_text(json.dumps({"date": "2026-05-04", "positioning_score": -35, "confidence": 0.7, "notes": "Dealer gamma short"}), encoding="utf-8")

    record = import_positioning_note(path, "EURUSD", "chatgpt")

    assert record.bias == "BEARISH"
    assert record.confidence == 0.7


def test_manual_note_json_without_score_uses_text_fields(tmp_path, monkeypatch) -> None:
    _patch_db(monkeypatch, tmp_path)
    path = tmp_path / "note.json"
    path.write_text(json.dumps({"date": "5/4/2026", "notes": "Prime brokerage summary is bearish and net short"}), encoding="utf-8")

    record = import_positioning_note(path, "EURUSD", "claude")

    assert record.bias == "BEARISH"
    assert record.date == "2026-05-04"


def test_latest_positioning_uses_normalised_dates(tmp_path, monkeypatch) -> None:
    _patch_db(monkeypatch, tmp_path)
    old_note = tmp_path / "old.md"
    new_note = tmp_path / "new.md"
    old_note.write_text("bullish positioning_score: 50", encoding="utf-8")
    new_note.write_text("bearish positioning_score: -50", encoding="utf-8")

    import_positioning_note(old_note, "GBPUSD", "manual", "12/31/2025")
    import_positioning_note(new_note, "GBPUSD", "manual", "2026-01-02")
    records = load_positioning_records("GBPUSD", 2)

    assert records[0]["date"] == "2026-01-02"
    assert records[0]["bias"] == "BEARISH"


def test_positioning_score_blends_latest_sources(tmp_path, monkeypatch) -> None:
    _patch_db(monkeypatch, tmp_path)
    cot = tmp_path / "cot.csv"
    note = tmp_path / "note.md"
    cot.write_text("date,long,short\n2026-05-01,200,100\n", encoding="utf-8")
    note.write_text("bearish positioning_score: -20", encoding="utf-8")

    import_cot_csv(cot, "XAUUSD")
    import_positioning_note(note, "XAUUSD", "codex")
    score = latest_positioning_score("XAUUSD")

    assert score["context_only"] is True
    assert len(score["sources"]) == 2


def test_positioning_go_no_go_is_context_not_blocker() -> None:
    metrics = {"profit_factor": 1.5, "total_trades": 40, "average_win": 2.0, "average_loss": -1.0, "max_drawdown": 0.1}
    result = evaluate_go_no_go(
        "KEEP",
        metrics,
        True,
        {"robustness_score": 75},
        {"fragile": False},
        "SAFE_TO_TEST",
        positioning_context={"positioning_score": 85},
    )

    assert "POSITIONING_CONTEXT_ONLY" not in result.reason_codes
    assert any(item.name == "positioning_context_extreme" for item in result.criteria)


def test_report_includes_positioning_context(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _patch_db(monkeypatch, tmp_path)
    note = tmp_path / "note.md"
    note.write_text("bullish positioning_score: 55", encoding="utf-8")
    import_positioning_note(note, "XAUUSD", "manual")

    path = generate_report("gold_v2", "XAUUSD", "M15", {}, 50, "REVIEW", "SAFE_TO_TEST", [], "REVIEW", "md")

    assert "Positioning Context" in path.read_text(encoding="utf-8")
    assert "Context only" in path.read_text(encoding="utf-8")


def test_positioning_cli_commands_exist() -> None:
    commands = build_parser()._subparsers._group_actions[0].choices

    assert "import-cot" in commands
    assert "import-positioning-note" in commands
    assert "positioning-score" in commands


def test_positioning_note_cli_writes_record(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    _patch_db(monkeypatch, tmp_path)
    path = tmp_path / "note.md"
    path.write_text("bullish positioning_score: 33", encoding="utf-8")

    import_positioning_note_cmd(Namespace(file=str(path), symbol="GBPUSD", source="codex", date=None))

    assert load_positioning_records("GBPUSD", 10)
    assert "NOTE_CODEX" in capsys.readouterr().out


def test_positioning_score_cli_outputs_context(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    _patch_db(monkeypatch, tmp_path)
    path = tmp_path / "note.md"
    path.write_text("bearish positioning_score: -44", encoding="utf-8")
    import_positioning_note(path, "USDCAD", "manual")

    positioning_score_cmd(Namespace(symbol="USDCAD", show_records=True, limit=5))

    payload = json.loads(capsys.readouterr().out)
    assert payload["bias"] == "BEARISH"
    assert payload["records"]
