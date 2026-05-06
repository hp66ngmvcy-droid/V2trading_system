from __future__ import annotations

import json
from datetime import timezone
from pathlib import Path

import pandas as pd

from tar_system.cli import build_parser
from tar_system.discovery.promotion_gate import evaluate_promotion
from tar_system.environment.event_calendar import Event, load_events
from tar_system.environment.risk_state import check_environment_risk
from tar_system.exports.mt5_exporter import export_latest_signal
from tar_system.reporting.reporter import generate_report
from tar_system.security.checks import run_security_checks
from tar_system.strategies.base import Signal


def test_configs_events_yaml_loads() -> None:
    events = load_events("configs/events.yaml")
    assert events
    assert events[0].event_type == "CPI"
    assert "XAUUSD" in events[0].affected_assets


def test_high_impact_event_gives_hold_trading() -> None:
    events = load_events("configs/events.yaml")
    state = check_environment_risk("XAUUSD", pd.Timestamp("2026-06-12").to_pydatetime(), events)
    assert state == "HOLD_TRADING"


def test_environment_accepts_timezone_aware_target() -> None:
    events = load_events("configs/events.yaml")
    target = pd.Timestamp("2026-06-12 00:00", tz=timezone.utc).to_pydatetime()
    state = check_environment_risk("XAUUSD", target, events)
    assert state == "HOLD_TRADING"


def test_shock_gives_block_trading() -> None:
    event = Event("Bank failure", pd.Timestamp("2026-06-12 10:00").to_pydatetime(), "HIGH", True, "BANK_FAILURE", "US")
    state = check_environment_risk("XAUUSD", pd.Timestamp("2026-06-12 10:00").to_pydatetime(), [event])
    assert state == "BLOCK_TRADING"


def test_missing_event_data_gives_review_only() -> None:
    state = check_environment_risk("XAUUSD", pd.Timestamp("2026-06-12").to_pydatetime(), None)
    assert state == "REVIEW_ONLY"


def test_mt5_export_blocked_during_hold(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    signal = Signal(
        timestamp=pd.Timestamp("2026-06-12 13:30"),
        symbol="XAUUSD",
        timeframe="M15",
        strategy="gold_v2",
        version="0.1.0",
        side="BUY",
        confidence=0.8,
        entry=100.0,
        stop_loss=99.0,
        take_profit=102.0,
        reason_code="SIGNAL_BUY",
    )
    csv_path, json_path = export_latest_signal(signal, "HOLD_TRADING")
    assert csv_path == json_path
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["export_blocked"] is True
    assert not Path("exports/mt5/signal_latest.csv").exists()


def test_promotion_requires_human_approval() -> None:
    decision = evaluate_promotion("KEEP", True, True, True, "SAFE_TO_TEST", False)
    assert not decision.approved
    assert "MISSING_HUMAN_APPROVAL" in decision.reason_codes


def test_report_generation_creates_markdown_and_json(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    metrics = {"win_rate": 0.5}
    md = generate_report("gold_v2", "XAUUSD", "M15", metrics, 55, "REVIEW", "SAFE_TO_TEST", [], "REVIEW", "md")
    js = generate_report("gold_v2", "XAUUSD", "M15", metrics, 55, "REVIEW", "SAFE_TO_TEST", [], "REVIEW", "json")
    assert md.exists()
    assert js.exists()


def test_security_check_detects_paper_only_settings() -> None:
    result = run_security_checks()
    assert result.passed


def test_cli_imports_all_commands() -> None:
    parser = build_parser()
    commands = parser._subparsers._group_actions[0].choices.keys()  # type: ignore[attr-defined]
    expected = {
        "import-csv",
        "validate-data",
        "build-features",
        "run-backtest",
        "score-strategy",
        "rank-strategies",
        "run-walk-forward",
        "forward-test",
        "export-mt5",
        "export-obsidian",
        "check-environment",
        "check-events",
        "add-strategy-idea",
        "generate-candidates",
        "promote-candidate",
        "generate-report",
        "run-dashboard",
        "security-check",
    }
    assert expected.issubset(set(commands))
