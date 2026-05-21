from __future__ import annotations

import json

import pandas as pd

from tar_system.controller.strategy_health_monitor import evaluate_strategy_health
from tar_system.features.engineering import build_features
from tar_system.reporting.reporter import generate_quant_report
from tar_system.strategies.liquidity_sweep_v1 import LiquiditySweepV1


def _row(**overrides: object) -> pd.Series:
    data = {
        "timestamp": pd.Timestamp("2026-01-01 08:00:00"),
        "symbol": "XAUUSD",
        "timeframe": "M15",
        "open": 100.0,
        "high": 100.5,
        "low": 98.8,
        "close": 99.8,
        "atr": 0.5,
        "prior_rolling_high": 101.0,
        "prior_rolling_low": 99.0,
    }
    data.update(overrides)
    return pd.Series(data)


def test_liquidity_sweep_buy_after_low_sweep() -> None:
    signal = LiquiditySweepV1().generate_signal(_row(), "ranging")

    assert signal.side == "BUY"
    assert signal.stop_loss is not None
    assert signal.take_profit is not None
    assert signal.confidence >= 0.6


def test_liquidity_sweep_sell_after_high_sweep() -> None:
    signal = LiquiditySweepV1().generate_signal(
        _row(open=100.0, high=101.4, low=99.7, close=100.2, prior_rolling_high=101.0, prior_rolling_low=99.0),
        "ranging",
    )

    assert signal.side == "SELL"
    assert signal.stop_loss is not None
    assert signal.take_profit is not None


def test_feature_engineering_adds_prior_liquidity_levels() -> None:
    close = pd.Series([100 + i * 0.1 for i in range(30)], dtype=float)
    df = pd.DataFrame(
        {
            "timestamp": pd.date_range("2026-01-01", periods=30, freq="15min"),
            "open": close,
            "high": close + 0.2,
            "low": close - 0.2,
            "close": close,
            "volume": 100,
            "symbol": "XAUUSD",
            "timeframe": "M15",
        }
    )

    features = build_features(df, "XAUUSD", "M15")

    assert "prior_rolling_high" in features
    assert "prior_rolling_low" in features


def test_strategy_health_monitor_writes_watch_status(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = evaluate_strategy_health(
        "liquidity_sweep_v1",
        "XAUUSD",
        "M15",
        metrics={"total_trades": 5, "max_drawdown": 0.01, "profit_factor": 1.2, "sharpe_ratio": 0.5},
    )

    assert result.status == "WATCH"
    payload = json.loads((tmp_path / "runtime" / "strategy_health_status.json").read_text(encoding="utf-8"))
    assert payload["liquidity_sweep_v1:XAUUSD:M15"]["status"] == "WATCH"


def test_strategy_health_reads_recent_signal_log(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    log = tmp_path / "runtime" / "paper_signal_alerts.jsonl"
    log.parent.mkdir(parents=True)
    for _ in range(3):
        log.write_text(
            "\n".join(
                json.dumps(
                    {
                        "strategy": "liquidity_sweep_v1",
                        "symbol": "XAUUSD",
                        "timeframe": "M15",
                        "side": "BUY",
                        "risk_approved": False,
                        "risk_reason": "DAILY_LOSS_LIMIT",
                        "alert_ready": False,
                    }
                )
                for _ in range(3)
            )
            + "\n",
            encoding="utf-8",
        )

    result = evaluate_strategy_health(
        "liquidity_sweep_v1",
        "XAUUSD",
        "M15",
        metrics={"total_trades": 40, "max_drawdown": 0.01, "profit_factor": 1.5, "sharpe_ratio": 1.0},
    )

    assert result.status == "PAUSED"
    assert "HEALTH_RECENT_HARD_BLOCKS" in result.reason_codes


def test_quant_report_writes_markdown_and_pdf(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    path = generate_quant_report(
        "liquidity_sweep_v1",
        "XAUUSD",
        "M15",
        {"total_trades": 22, "profit_factor": 1.37, "max_drawdown": 0.06},
        signal={"side": "BUY", "confidence": 0.7, "entry": 100.0, "stop_loss": 99.0, "take_profit": 102.0, "risk_approved": True, "risk_reason": "RISK_APPROVED"},
        health={"status": "WATCH", "recommendation": "Keep paper-only", "reason_codes": ["HEALTH_SAMPLE_TOO_SMALL"]},
    )

    assert path.exists()
    assert path.with_suffix(".pdf").exists()
    assert "Equity Summary" in path.read_text(encoding="utf-8")
