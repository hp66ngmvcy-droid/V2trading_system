from __future__ import annotations

import json
from pathlib import Path

from tar_system.dashboard.pages.daily_summary import build_daily_summary
from tar_system.dashboard.pages.overview import margin_utilisation_warning
from tar_system.dashboard.pages.promotion_board import PromotionCard, green_light_ready_for_mt5, is_green_light_enabled, kill_strategy, load_promotion_cards, parse_metrics_filename
from tar_system.dashboard.pages.strategy_detail import build_forensic_view
from tar_system.dashboard.pages import strategy_detail
from tar_system.memory.strategy_memory import record_strategy_memory


def _card(**updates: object) -> PromotionCard:
    payload = {
        "strategy": "gold_v2",
        "symbol": "XAUUSD",
        "timeframe": "M15",
        "score": 80.0,
        "verdict": "KEEP",
        "last_tested_date": "2026-05-04",
        "walk_forward_pass": True,
        "monte_carlo_pass": True,
        "parameter_stability": "80",
        "cost_sensitive": False,
        "swap_drag": 0.0,
        "realistic_score": 75.0,
        "gross_score": 80.0,
        "session_filter": True,
        "go_no_go": {"passed": True, "criteria": []},
        "column": "READY FOR MT5",
    }
    payload.update(updates)
    return PromotionCard(**payload)


def test_promotion_board_loads_safely_with_empty_memory(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    assert load_promotion_cards() == []


def test_promotion_board_parses_metric_filenames() -> None:
    assert parse_metrics_filename(Path("data/results/gold_v2_XAUUSD_M15_metrics.json")) == ("gold_v2", "XAUUSD", "M15")
    assert parse_metrics_filename(Path("data/results/rsi_reversion_v1_XAUUSD_M15_metrics.json")) == ("rsi_reversion_v1", "XAUUSD", "M15")


def test_green_light_writes_promotion_log(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    path = green_light_ready_for_mt5(_card(), checklist_confirmed=True)
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["entries"][0]["action"] == "READY_FOR_MT5_REVIEW"
    assert payload["entries"][0]["paper_only"] is True


def test_green_light_blocks_cost_sensitive_and_failed_gate() -> None:
    assert not is_green_light_enabled(_card(cost_sensitive=True))
    assert not is_green_light_enabled(_card(go_no_go={"passed": False, "criteria": []}))


def test_kill_button_updates_memory_verdict(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    record_strategy_memory(
        base_strategy="gold_v2",
        variant_name="gold_v2_xauusd_m15",
        version="0.1",
        symbol="XAUUSD",
        timeframe="M15",
        broker="current_broker_demo",
        asset_profile={},
        broker_profile={},
        parameters={},
        backtest_metrics={},
        walk_forward_metrics={},
        forward_test_metrics={},
        score=50,
        verdict="REVIEW",
        reason_codes=[],
    )
    assert kill_strategy(_card()) is True


def test_promotion_board_uses_killed_memory_verdict(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    Path("data/results").mkdir(parents=True)
    Path("data/results/gold_v2_XAUUSD_M15_metrics.json").write_text(
        json.dumps({"profit_factor": 3.0, "total_trades": 50, "average_win": 2, "average_loss": -1, "max_drawdown": 0.05, "win_rate": 0.7, "expectancy": 1}),
        encoding="utf-8",
    )
    record_strategy_memory(
        base_strategy="gold_v2",
        variant_name="gold_v2_xauusd_m15",
        version="0.1",
        symbol="XAUUSD",
        timeframe="M15",
        broker="current_broker_demo",
        asset_profile={},
        broker_profile={},
        parameters={},
        backtest_metrics={},
        walk_forward_metrics={},
        forward_test_metrics={},
        score=50,
        verdict="KILLED",
        reason_codes=[],
    )
    cards = load_promotion_cards()
    assert cards[0].strategy == "gold_v2"
    assert cards[0].symbol == "XAUUSD"
    assert cards[0].timeframe == "M15"
    assert cards[0].column == "KILLED"


def test_daily_summary_loads_without_data(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    summary = build_daily_summary()
    assert summary["strategies_tested_today"] == 0
    assert summary["pending_scheduled_jobs"] == []


def test_forensic_view_shows_all_eight_criteria(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    Path("data/results").mkdir(parents=True)
    Path("data/results/gold_v2_XAUUSD_M15_metrics.json").write_text(
        json.dumps({"profit_factor": 1.5, "total_trades": 40, "average_win": 2, "average_loss": -1, "max_drawdown": 0.1}),
        encoding="utf-8",
    )
    forensic = build_forensic_view("gold_v2", "XAUUSD", "M15")
    assert len(forensic["criteria"]) == 8


def test_strategy_detail_selectors_include_rsi_and_usousd() -> None:
    source = Path(strategy_detail.__file__).read_text(encoding="utf-8")
    assert "rsi_reversion_v1" not in source
    assert "REGISTRY.keys()" in source
    assert "USOUSD" in source
    assert "USOIL" not in source


def test_margin_warning_thresholds() -> None:
    assert margin_utilisation_warning(0.5) == "AMBER"
    assert margin_utilisation_warning(0.8) == "RED"
    assert margin_utilisation_warning(0.91) == "BLOCK"
