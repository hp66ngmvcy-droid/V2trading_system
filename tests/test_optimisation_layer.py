from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

from tar_system.cli import build_parser, go_no_go_cmd, regime_heatmap_cmd
from tar_system.optimisation.go_no_go_gate import evaluate_go_no_go
from tar_system.optimisation.regime_heatmap import build_regime_heatmap
from tar_system.optimisation.risk_strategy_optimiser import RiskStrategyOptimiser
from tar_system.optimisation.strategy_improvement_planner import build_improvement_plan, detect_pivot_triggers
from tar_system.validation.walk_forward import derive_stable_parameter_ranges


def good_metrics() -> dict[str, float]:
    return {"total_trades": 45, "win_rate": 0.55, "profit_factor": 1.7, "max_drawdown": 0.08, "expectancy": 2.0}


def test_go_when_all_conditions_pass() -> None:
    result = evaluate_go_no_go(
        "KEEP",
        good_metrics(),
        walk_forward_exists=True,
        monte_carlo={"robustness_score": 75},
        parameter_sensitivity={"fragile": False, "stability_score": 80},
        environment_state="SAFE_TO_TEST",
        beats_baseline_after_costs=True,
        regime_count=2,
        audit_trail_exists=True,
    )
    assert result.passed
    assert result.status == "GO"
    assert len([criterion for criterion in result.criteria if criterion.name.startswith("C")]) == 8


def test_all_eight_go_no_go_criteria_individually() -> None:
    base = {**good_metrics(), "average_win": 2.0, "average_loss": -1.0}
    cases = [
        ("C1_edge_plausibility", {**base, "profit_factor": 1.0}, {"C1_EDGE_PLAUSIBILITY_FAIL"}),
        ("C2_overfitting_risk", base, {"C2_OVERFITTING_RISK_FAIL"}, {"walk_forward_oos_is_ratio": 0.4}),
        ("C3_sample_adequacy", {**base, "total_trades": 20}, {"C3_SAMPLE_ADEQUACY_FAIL"}),
        ("C4_regime_dependency", base, {"C4_REGIME_DEPENDENCY_FAIL"}, {"regime_count": 1}),
        ("C5_exit_calibration", {**base, "average_win": 0.5, "average_loss": -1.0}, {"C5_EXIT_CALIBRATION_FAIL"}),
        ("C6_risk_concentration", {**base, "max_drawdown": 0.25}, {"C6_RISK_CONCENTRATION_FAIL", "HIGH_DRAWDOWN"}),
        ("C7_execution_realism", base, {"C7_EXECUTION_REALISM_FAIL"}, {"realistic_score": 0}),
        ("C8_cost_sensitivity", base, {"C8_COST_SENSITIVITY_FAIL"}, {"cost_sensitive": True}),
    ]
    for _, metrics, expected, *extra in cases:
        kwargs = extra[0] if extra else {}
        result = evaluate_go_no_go("KEEP", metrics, True, {"robustness_score": 75}, {"fragile": False}, "SAFE_TO_TEST", **kwargs)
        assert expected.intersection(set(result.reason_codes))


def test_no_go_on_high_drawdown() -> None:
    metrics = good_metrics()
    metrics["max_drawdown"] = 0.35
    result = evaluate_go_no_go("KEEP", metrics, True, {"robustness_score": 75}, {"fragile": False}, "SAFE_TO_TEST")
    assert not result.passed
    assert "HIGH_DRAWDOWN" in result.reason_codes


def test_no_go_on_fragile_parameters() -> None:
    result = evaluate_go_no_go("KEEP", good_metrics(), True, {"robustness_score": 75}, {"fragile": True}, "SAFE_TO_TEST")
    assert not result.passed
    assert "FRAGILE_PARAMETERS" in result.reason_codes


def test_no_go_on_block_trading_environment() -> None:
    result = evaluate_go_no_go("KEEP", good_metrics(), True, {"robustness_score": 75}, {"fragile": False}, "BLOCK_TRADING")
    assert not result.passed
    assert "ENVIRONMENT_BLOCK_TRADING" in result.reason_codes


def test_regime_heatmap_output() -> None:
    heatmap = build_regime_heatmap(
        [
            {"regime": "TRENDING", "return": 0.02},
            {"regime": "TRENDING", "return": 0.01},
            {"regime": "VOLATILE", "return": -0.03},
        ],
        min_trades=1,
    )
    assert "TRENDING" in heatmap.regimes
    assert heatmap.regimes["TRENDING"].trade_count == 2


def test_improvement_planner_recommendations() -> None:
    plan = build_improvement_plan({"max_drawdown": 0.25, "total_trades": 5}, ["HIGH_DRAWDOWN", "LOW_TRADE_COUNT"])
    assert any("Reduce position size" in item for item in plan)
    assert any("timeframe" in item for item in plan)


def test_pivot_triggers_fire() -> None:
    plateau = detect_pivot_triggers(optimiser_scores=[70, 71, 70.5])
    cost = detect_pivot_triggers(cost_sensitive=True)
    assert plateau["pivot_required"] is True
    assert "IMPROVEMENT_PLATEAU" in plateau["triggers"]
    assert "COST_DEFEAT" in cost["triggers"]


def test_stable_parameter_ranges_detection() -> None:
    stable, stable_score = derive_stable_parameter_ranges([{"fast_ema": 12}, {"fast_ema": 13}, {"fast_ema": 12}])
    unstable, unstable_score = derive_stable_parameter_ranges([{"fast_ema": 8}, {"fast_ema": 50}])
    assert stable["fast_ema"] == (12.0, 13.0)
    assert stable_score == 100
    assert unstable["fast_ema"] == (8.0, 50.0)
    assert unstable_score == 0


def test_optimiser_review_log_append(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = RiskStrategyOptimiser().optimise(
        "gold_v2",
        "XAUUSD",
        "M15",
        good_metrics(),
        "KEEP",
        walk_forward_metrics={"total_trades": 20},
        monte_carlo={"robustness_score": 80},
        parameter_sensitivity={"fragile": False, "stability_score": 80},
        environment_state="SAFE_TO_TEST",
        regime_trades=[{"regime": "TRENDING", "return": 0.01} for _ in range(6)],
    )
    assert result.optimiser_decision in {"KEEP", "PROMOTE_CANDIDATE", "REVIEW", "RETEST", "REDUCE_RISK", "PAUSE", "KILL"}
    rows = [json.loads(line) for line in open("logs/review_log.jsonl", encoding="utf-8")]
    assert rows[-1]["optimiser_decision"] == result.optimiser_decision


def test_optimiser_read_only_mode_has_no_side_effects(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = RiskStrategyOptimiser().optimise(
        "gold_v2",
        "XAUUSD",
        "M15",
        good_metrics(),
        "KEEP",
        walk_forward_metrics={"total_trades": 20},
        monte_carlo={"robustness_score": 80},
        parameter_sensitivity={"fragile": False, "stability_score": 80},
        environment_state="SAFE_TO_TEST",
        write_outputs=False,
    )
    assert result.optimiser_score > 0
    assert not Path("logs/review_log.jsonl").exists()
    assert not Path("obsidian/60_Optimiser").exists()


def test_go_no_go_cli_uses_saved_validation_artifacts(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    Path("logs").mkdir()
    Path("data/results").mkdir(parents=True)
    Path("logs/review_log.jsonl").write_text(
        json.dumps({"strategy": "gold_v2", "symbol": "XAUUSD", "timeframe": "M15", "verdict": "KEEP", "metrics": good_metrics()}) + "\n",
        encoding="utf-8",
    )
    Path("data/results/gold_v2_XAUUSD_M15_walk_forward.json").write_text(json.dumps({"stitched_metrics": good_metrics()}), encoding="utf-8")
    Path("data/results/gold_v2_XAUUSD_M15_monte_carlo.json").write_text(json.dumps({"robustness_score": 80}), encoding="utf-8")
    Path("data/results/gold_v2_XAUUSD_M15_parameter_sensitivity.json").write_text(
        json.dumps({"fragile": False, "stability_score": 80}),
        encoding="utf-8",
    )
    Path("data/results/gold_v2_XAUUSD_M15_regime_trades.json").write_text(
        json.dumps([{"regime": "TRENDING", "return": 0.01}, {"regime": "RANGING", "return": 0.01}]),
        encoding="utf-8",
    )
    go_no_go_cmd(Namespace(strategy="gold_v2", symbol="XAUUSD", timeframe="M15"))
    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "GO"


def test_regime_heatmap_cli_uses_saved_regime_trades(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    Path("data/results").mkdir(parents=True)
    Path("data/results/gold_v2_XAUUSD_M15_regime_trades.json").write_text(
        json.dumps([{"regime": "TRENDING", "return": 0.02}, {"regime": "TRENDING", "return": 0.01}]),
        encoding="utf-8",
    )
    regime_heatmap_cmd(Namespace(strategy="gold_v2", symbol="XAUUSD", timeframe="M15"))
    output = json.loads(capsys.readouterr().out)
    assert output["regimes"]["TRENDING"]["trade_count"] == 2


def test_optimiser_cli_command_imports() -> None:
    parser = build_parser()
    commands = parser._subparsers._group_actions[0].choices.keys()  # type: ignore[attr-defined]
    assert {"optimise-strategy", "go-no-go", "regime-heatmap"}.issubset(set(commands))
