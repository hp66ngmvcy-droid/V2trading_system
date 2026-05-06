from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from tar_system.analysis.strategy_ranker import balanced_score, rank_strategies
from tar_system.cache.result_cache import make_cache_key
from tar_system.discovery.mutation_engine import mutate_blueprint
from tar_system.discovery.strategy_blueprint import StrategyBlueprint
from tar_system.discovery.strategy_idea_parser import parse_strategy_idea
from tar_system.obsidian.exporter import export_result
from tar_system.reporting.review_log import append_review_result, load_review_results, write_review_summary
from tar_system.validation.monte_carlo import run_monte_carlo
from tar_system.validation.parameter_sensitivity import assess_parameter_sensitivity, neighbouring_parameters
from tar_system.validation.walk_forward import rolling_splits


def test_result_cache_hash_is_stable() -> None:
    first = make_cache_key("gold_v2", {"fast": 12}, "XAUUSD", "M15", "abc", ("a", "b"), "backtest")
    second = make_cache_key("gold_v2", {"fast": 12}, "XAUUSD", "M15", "abc", ("a", "b"), "backtest")
    assert first == second
    assert len(first) == 64


def test_walk_forward_split() -> None:
    splits = rolling_splits(row_count=100, train_window=30, test_window=10)
    assert len(splits) == 7
    assert splits[0].train_start == 0
    assert splits[0].test_start == 30


def test_monte_carlo_output_shape() -> None:
    result = run_monte_carlo([0.01, -0.005, 0.02, -0.01], iterations=20)
    assert 0 <= result.robustness_score <= 100
    assert result.worst_drawdown >= 0
    assert isinstance(result.warnings, list)


def test_parameter_sensitivity_output() -> None:
    variants = neighbouring_parameters({"fast": 12, "threshold": 55.0})
    result = assess_parameter_sensitivity(80, [75, 78, 60], ["fast", "threshold"])
    assert variants
    assert 0 <= result.stability_score <= 100
    assert isinstance(result.fragile, bool)


def test_balanced_ranker() -> None:
    rows = [
        {"strategy": "a", "symbol": "XAUUSD", "timeframe": "M15", "metrics": {"win_rate": 0.9, "profit_factor": 0.7, "max_drawdown": 0.3, "total_trades": 5}},
        {"strategy": "b", "symbol": "XAUUSD", "timeframe": "M15", "metrics": {"win_rate": 0.55, "profit_factor": 1.8, "max_drawdown": 0.05, "total_trades": 40, "expectancy": 2}},
    ]
    ranked = rank_strategies(rows)
    assert ranked[0].strategy == "b"
    assert balanced_score(rows[1]["metrics"]) > balanced_score(rows[0]["metrics"])


def test_review_log_append(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    append_review_result("gold_v2", "0.1.0", "XAUUSD", "M15", {"win_rate": 0.5}, 50, "REVIEW", "TEST", "EXPORT")
    rows = load_review_results("logs/review_log.jsonl")
    summary = write_review_summary(rows)
    assert rows[0]["strategy"] == "gold_v2"
    assert summary.exists()


def test_obsidian_note_generation(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    note = export_result(
        {
            "strategy": "gold_v2",
            "version": "0.1.0",
            "symbol": "XAUUSD",
            "timeframe": "M15",
            "metrics": {"win_rate": 0.6, "profit_factor": 1.6, "max_drawdown": 0.05, "total_trades": 30},
            "score": 75,
            "verdict": "KEEP",
            "reason_codes": ["LOW_DRAWDOWN"],
        }
    )
    text = note.read_text(encoding="utf-8")
    assert "tags:" in text
    assert "#asset/XAUUSD" in text


def test_strategy_blueprint_parser(tmp_path) -> None:
    idea = tmp_path / "new_idea.md"
    idea.write_text("# EMA Pullback\nEntry: EMA reclaim\nExit: ATR target\nFilters: trend, session\n", encoding="utf-8")
    blueprint = parse_strategy_idea(idea)
    assert blueprint.strategy_name == "ema_pullback"
    assert "trend" in blueprint.filters


def test_mutation_engine_controlled_mutation() -> None:
    blueprint = StrategyBlueprint(
        strategy_name="candidate",
        source="test",
        source_type="manual",
        asset_class="fx",
        timeframe="M15",
        entry_logic="entry",
        exit_logic="exit",
        filters=["trend"],
        parameters={"fast": 12},
    )
    mutations = mutate_blueprint(blueprint)
    assert mutations
    assert all(item.strategy_name != blueprint.strategy_name for item in mutations)


def test_dashboard_import() -> None:
    import tar_system.dashboard.app as app

    assert callable(app.main)


def test_skills_files_exist() -> None:
    expected = [
        "code_skill.md",
        "token_optimisation.md",
        "local_performance.md",
        "security_rules.md",
        "csv_data_rules.md",
        "backtest_rules.md",
        "obsidian_rules.md",
        "mt5_export_rules.md",
        "strategy_discovery_rules.md",
        "environment_risk_rules.md",
    ]
    for name in expected:
        assert Path("skills", name).exists()
