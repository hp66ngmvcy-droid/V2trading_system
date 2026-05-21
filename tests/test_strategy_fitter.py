from __future__ import annotations

import argparse
import json
from pathlib import Path

from tar_system.cli import build_parser, fit_strategy_filters_cmd
from tar_system.research.strategy_fitter import build_strategy_filter_plan, load_metric_candidates


def _write_metrics(path: Path, metrics: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(metrics), encoding="utf-8")


def test_strategy_fitter_detects_directional_failure(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _write_metrics(
        Path("data/results/gold_v2_GBPUSD_M5_metrics.json"),
        {
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

    rows = load_metric_candidates()

    assert rows[0].blockers == ["WEAK_PF", "LOW_WIN_RATE", "DIRECTIONAL_FAILURE"]
    assert rows[0].severity > 70


def test_strategy_fitter_writes_filter_plan_with_committee(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _write_metrics(
        Path("data/results/gold_v2_GBPUSD_M5_metrics.json"),
        {
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

    plan = build_strategy_filter_plan(limit=1)

    assert plan.paper_only is True
    assert plan.candidates_reviewed == 1
    rec = plan.recommendations[0]
    assert rec.committee_recommendation == "KILL"
    assert any("directional_sanity_gate" in item for item in rec.filters)
    assert any("do not auto-flip" in item for item in rec.filters)
    assert "rsi_buy_threshold" in rec.parameter_tests
    text = Path(plan.output_markdown).read_text(encoding="utf-8")
    payload = json.loads(Path(plan.output_json).read_text(encoding="utf-8"))
    assert "Strategy Filter Plan" in text
    assert payload["paper_only"] is True
    assert Path("logs/audit/audit.jsonl").exists()


def test_cli_accepts_fit_strategy_filters_command() -> None:
    parser = build_parser()
    args = parser.parse_args(["fit-strategy-filters", "--limit", "3", "--skip-committee"])
    assert args.func is fit_strategy_filters_cmd
    assert args.limit == 3
    assert args.skip_committee is True


def test_fit_strategy_filters_cmd_prints_paths(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)

    fit_strategy_filters_cmd(argparse.Namespace(limit=2, output_dir="runtime", skip_committee=True))

    output = json.loads(capsys.readouterr().out)
    assert output["paper_only"] is True
    assert output["markdown"] == "runtime/strategy_filter_plan.md"
    assert output["json"] == "runtime/strategy_filter_plan.json"
