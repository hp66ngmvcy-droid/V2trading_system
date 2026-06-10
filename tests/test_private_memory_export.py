from __future__ import annotations

import argparse
import json
from pathlib import Path

from tar_system.cli import build_parser, export_private_memory_cmd
from tar_system.memory.private_memory_export import export_private_strategy_memory


def test_private_memory_export_writes_obsidian_and_second_brain_notes(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    Path("runtime").mkdir()
    Path("runtime/research_committee_XAUUSD_M15_gold_v2.json").write_text(
        json.dumps(
            {
                "generated_at": "2026-05-21T00:00:00+00:00",
                "paper_only": True,
                "strategy": "gold_v2",
                "symbol": "XAUUSD",
                "timeframe": "M15",
                "recommendation": "REVIEW",
                "confidence": 0.65,
                "guardrails": ["Paper-only research. Do not place trades."],
                "agents": [{"role": "Fundamental Analyst", "stance": "REVIEW", "score": 50, "summary": "Check", "evidence": [], "concerns": []}],
                "debate": [],
                "synthesis": {"role": "Trader Synthesizer", "stance": "REVIEW", "score": 50, "summary": "Review", "evidence": [], "concerns": []},
                "risk_review": {"role": "Risk Reviewer", "stance": "REVIEW", "score": 55, "summary": "Guarded", "evidence": [], "concerns": []},
                "required_next_actions": ["Keep paper-only."],
            }
        ),
        encoding="utf-8",
    )
    Path("runtime/strategy_filter_plan.json").write_text(
        json.dumps(
            {
                "generated_at": "2026-05-21T00:00:00+00:00",
                "paper_only": True,
                "blocker_counts": {"WEAK_PF": 3},
                "recommendations": [
                    {
                        "strategy": "gold_v2",
                        "symbol": "XAUUSD",
                        "timeframe": "M15",
                        "committee_recommendation": "REVIEW",
                        "blockers": ["WEAK_PF"],
                        "filters": ["quality_gate"],
                        "parameter_tests": {"rsi_buy_threshold": [58]},
                        "retest_command": "paper retest",
                    }
                ],
                "next_actions": ["Retest one filter at a time."],
            }
        ),
        encoding="utf-8",
    )

    result = export_private_strategy_memory()

    assert result.paper_only is True
    assert len(result.committee_notes) == 2
    assert len(result.filter_plan_notes) == 2
    for note in result.committee_notes + result.filter_plan_notes + result.index_notes:
        text = Path(note).read_text(encoding="utf-8")
        assert "Local-only" in text or "Private Trading Memory" in text
    assert Path("logs/audit/audit.jsonl").exists()


def test_private_memory_export_filters_committee_notes(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    Path("runtime").mkdir()
    Path("runtime/research_committee_XAUUSD_M15_gold_v2.json").write_text(
        json.dumps({"strategy": "gold_v2", "symbol": "XAUUSD", "timeframe": "M15", "recommendation": "REVIEW"}),
        encoding="utf-8",
    )
    Path("runtime/research_committee_GBPUSD_M5_gold_v2.json").write_text(
        json.dumps({"strategy": "gold_v2", "symbol": "GBPUSD", "timeframe": "M5", "recommendation": "KILL"}),
        encoding="utf-8",
    )

    result = export_private_strategy_memory(symbol="GBPUSD")

    assert len(result.committee_notes) == 2
    assert all("GBPUSD" in Path(path).name for path in result.committee_notes)


def test_cli_accepts_export_private_memory_command() -> None:
    parser = build_parser()
    args = parser.parse_args(["export-private-memory", "--strategy", "gold_v2", "--symbol", "XAUUSD", "--timeframe", "M15"])
    assert args.func is export_private_memory_cmd
    assert args.strategy == "gold_v2"
    assert args.symbol == "XAUUSD"


def test_export_private_memory_cmd_prints_json(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)

    export_private_memory_cmd(
        argparse.Namespace(
            strategy=None,
            symbol=None,
            timeframe=None,
            obsidian_root="obsidian/private_trading_memory",
            second_brain_root="second_brain/vault/01_hubs/private_trading_memory",
        )
    )

    output = json.loads(capsys.readouterr().out)
    assert output["paper_only"] is True
    assert output["index_notes"]
