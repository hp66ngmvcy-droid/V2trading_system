from __future__ import annotations

import argparse
import json
from pathlib import Path

from tar_system.cli import build_parser, run_research_committee_cmd
from tar_system.research.committee import run_research_committee


def test_research_committee_writes_paper_only_packet(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    Path("data/results").mkdir(parents=True)
    Path("data/results/gold_v2_XAUUSD_M15_metrics.json").write_text(
        json.dumps(
            {
                "total_trades": 55,
                "win_rate": 0.56,
                "profit_factor": 1.65,
                "max_drawdown": 0.08,
                "expectancy": 12.0,
                "net_profit": 800.0,
                "total_cost": 110.0,
                "sharpe_ratio": 1.25,
                "max_consecutive_losses": 3,
            }
        ),
        encoding="utf-8",
    )
    Path("data/results/gold_v2_XAUUSD_M15_walk_forward.json").write_text(
        json.dumps(
            {
                "split_count": 5,
                "ran": True,
                "stitched_metrics": {"total_trades": 30, "profit_factor": 1.35, "max_drawdown": 0.10, "sharpe_ratio": 1.1},
                "parameter_stability_score": 0.8,
                "bootstrap_ci": {"ci_lower": 0.2, "ci_upper": 1.2, "spans_zero": False},
            }
        ),
        encoding="utf-8",
    )

    result = run_research_committee("gold_v2", "XAUUSD", "M15", manual_notes="No major event risk in supplied notes.")

    assert result.paper_only is True
    assert result.recommendation in {"KEEP", "REVIEW", "KILL"}
    assert {agent.role for agent in result.agents} == {
        "Fundamental Analyst",
        "Sentiment Analyst",
        "News Analyst",
        "Technical Analyst",
    }
    assert {agent.role for agent in result.debate} == {"Bull Researcher", "Bear Researcher"}
    text = Path(result.output_markdown).read_text(encoding="utf-8")
    payload = json.loads(Path(result.output_json).read_text(encoding="utf-8"))
    assert "Mode: paper-only research" in text
    assert "Do not place trades" in text
    assert payload["paper_only"] is True
    assert Path("logs/audit/audit.jsonl").exists()


def test_research_committee_kills_directional_failure(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    result = run_research_committee(
        "gold_v2",
        "GBPUSD",
        "M5",
        metrics={
            "total_trades": 87,
            "win_rate": 0.0,
            "profit_factor": 0.0,
            "max_drawdown": 0.157,
            "expectancy": -18.0,
            "net_profit": -1578.0,
            "total_cost": 1052.0,
            "sharpe_ratio": -71.0,
            "max_consecutive_losses": 87,
        },
    )

    assert result.recommendation == "KILL"
    assert result.risk_review.stance == "KILL"
    assert any("Archive or redesign" in action for action in result.required_next_actions)


def test_cli_accepts_research_committee_command() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "run-research-committee",
            "--strategy",
            "gold_v2",
            "--symbol",
            "XAUUSD",
            "--timeframe",
            "M15",
            "--notes-file",
            "notes.md",
        ]
    )
    assert args.func is run_research_committee_cmd
    assert args.notes_file == "notes.md"


def test_research_committee_cmd_prints_paths(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    Path("notes.md").write_text("Manual note: quiet market.", encoding="utf-8")

    run_research_committee_cmd(
        argparse.Namespace(
            strategy="gold_v2",
            symbol="XAUUSD",
            timeframe="M15",
            notes_file="notes.md",
            output_dir="runtime",
        )
    )

    output = json.loads(capsys.readouterr().out)
    assert output["paper_only"] is True
    assert output["markdown"] == "runtime/research_committee_XAUUSD_M15_gold_v2.md"
    assert output["json"] == "runtime/research_committee_XAUUSD_M15_gold_v2.json"
