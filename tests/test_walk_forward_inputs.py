"""Regression tests for walk-forward execution inputs."""

from __future__ import annotations

from types import SimpleNamespace

import pandas as pd


def test_walk_forward_passes_broker_and_asset_profiles(monkeypatch) -> None:
    from tar_system.backtest.engine import BacktestResult
    from tar_system.validation.walk_forward import run_walk_forward

    features = pd.DataFrame(
        {
            "timestamp": pd.date_range("2026-01-01", periods=6, freq="15min"),
            "symbol": ["XAUUSD"] * 6,
            "timeframe": ["M15"] * 6,
        }
    )
    strategy = SimpleNamespace(reward_risk=2.0)
    broker_profile = object()
    asset_profile = object()
    calls: list[dict[str, object]] = []

    def fake_run_backtest(_features, _strategy, **kwargs):
        calls.append(kwargs)
        return BacktestResult(metrics={"total_trades": 0.0, "trade_returns": [], "trade_pnls": []}, trades=0, final_equity=10_000.0)

    monkeypatch.setattr("tar_system.backtest.engine.run_backtest", fake_run_backtest)

    run_walk_forward(
        features,
        strategy,
        train_window=2,
        test_window=2,
        broker_profile=broker_profile,
        asset_profile=asset_profile,
        cost_multiplier=1.5,
    )

    assert calls
    assert all(call["broker_profile"] is broker_profile for call in calls)
    assert all(call["asset_profile"] is asset_profile for call in calls)
    assert all(call["cost_multiplier"] == 1.5 for call in calls)
