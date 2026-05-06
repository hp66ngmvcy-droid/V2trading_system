from __future__ import annotations

from pathlib import Path

import pandas as pd

from tar_system.agents.audit_agent import AuditAgent
from tar_system.agents.backtest_agent import BacktestAgent
from tar_system.agents.dashboard_agent import DashboardAgent
from tar_system.agents.data_validation_agent import DataValidationAgent
from tar_system.agents.feature_agent import FeatureAgent
from tar_system.agents.memory_agent import MemoryAgent
from tar_system.agents.optimisation_agent import OptimisationAgent
from tar_system.agents.oversight_agent import OversightAgent
from tar_system.agents.reporting_agent import ReportingAgent
from tar_system.agents.risk_agent import RiskAgent
from tar_system.agents.scoring_agent import ScoringAgent
from tar_system.agents.strategy_agent import StrategyAgent
from tar_system.agents.walk_forward_agent import WalkForwardAgent
from tar_system.cli import build_parser
from tar_system.data.store import save_feature_data
from tar_system.features.engineering import build_features
from tar_system.dashboard.runtime_control import request_start_forward_test, request_stop_forward_test
from tar_system.forward_test.engine import run_forward_test


def _features(symbol: str = "XAUUSD", timeframe: str = "M15", rows: int = 80) -> pd.DataFrame:
    timestamps = pd.date_range("2026-04-22", periods=rows, freq="15min")
    close = pd.Series(range(100, 100 + rows), dtype=float)
    raw = pd.DataFrame(
        {
            "timestamp": timestamps,
            "open": close - 0.1,
            "high": close + 0.3,
            "low": close - 0.3,
            "close": close,
            "volume": 100,
            "symbol": symbol,
            "timeframe": timeframe,
            "data_hash": "test-hash",
        }
    )
    return build_features(raw, symbol, timeframe)


def _copy_broker_config() -> None:
    Path("configs/brokers").mkdir(parents=True)
    source = Path("/Users/whs1/Dev/V2trading_system/configs/brokers/current_broker_demo.yaml")
    Path("configs/brokers/current_broker_demo.yaml").write_text(source.read_text(encoding="utf-8"), encoding="utf-8")


def test_forward_test_processes_new_bars_paper_only(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _copy_broker_config()
    save_feature_data(_features(), "XAUUSD", "M15")

    first = run_forward_test("gold_v2", "XAUUSD", "M15", "current_broker_demo")
    second = run_forward_test("gold_v2", "XAUUSD", "M15", "current_broker_demo")

    assert first.paper_only is True
    assert first.processed_bars == 80
    assert first.review_status == "TESTED"
    assert second.processed_bars == 0
    assert second.review_status == "REVIEW_ONLY"
    assert Path("data/results/gold_v2_XAUUSD_M15_forward_test.json").exists()
    assert Path("runtime/forward_test_gold_v2_XAUUSD_M15.json").exists()
    assert "FORWARD_TEST_COMPLETED" in Path("logs/audit/audit.jsonl").read_text(encoding="utf-8")


def test_stopped_forward_test_is_review_only_and_skips_memory(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _copy_broker_config()
    save_feature_data(_features(), "XAUUSD", "M15")
    request_start_forward_test({"strategy": "gold_v2", "symbol": "XAUUSD", "timeframe": "M15"})
    request_stop_forward_test()

    result = run_forward_test("gold_v2", "XAUUSD", "M15", "current_broker_demo")

    assert result.stopped is True
    assert result.review_status == "REVIEW_ONLY"
    assert not Path("data/tar_system.duckdb").exists()
    assert "forward_test_memory" in Path("logs/audit/audit.jsonl").read_text(encoding="utf-8")


def test_blocked_forward_test_is_review_only(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _copy_broker_config()
    save_feature_data(_features(), "XAUUSD", "M15")

    class Decision:
        state = "BLOCK_TRADING"
        reason_codes = ["TEST_BLOCK"]

    monkeypatch.setattr("tar_system.forward_test.engine.evaluate_environment", lambda *args, **kwargs: Decision())
    result = run_forward_test("gold_v2", "XAUUSD", "M15", "current_broker_demo")

    assert result.environment_state == "BLOCK_TRADING"
    assert result.review_status == "REVIEW_ONLY"
    assert not Path("data/tar_system.duckdb").exists()


def test_agents_import_and_oversight_blocks_no_live_trading(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    assert OversightAgent().decide_next_step("run-backtest").approved is True
    assert DashboardAgent().run()["backtest"]
    assert DataValidationAgent
    assert FeatureAgent
    assert StrategyAgent
    assert RiskAgent
    assert BacktestAgent
    assert WalkForwardAgent
    assert ScoringAgent
    assert MemoryAgent
    assert AuditAgent
    assert ReportingAgent
    assert OptimisationAgent


def test_forward_test_cli_command_has_broker() -> None:
    command = build_parser()._subparsers._group_actions[0].choices["forward-test"]  # type: ignore[attr-defined]
    option_dests = {action.dest for action in command._actions}
    assert "broker" in option_dests
