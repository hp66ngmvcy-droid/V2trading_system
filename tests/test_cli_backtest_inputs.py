"""Regression tests for CLI backtest input wiring."""

from __future__ import annotations

import argparse
from types import SimpleNamespace

import pandas as pd


def test_run_backtest_cmd_passes_resolved_broker_and_asset_profiles(monkeypatch, tmp_path) -> None:
    from tar_system import cli
    from tar_system.backtest.engine import BacktestResult
    from tar_system.cache import result_cache
    from tar_system.data import store
    from tar_system.reporting import review_log
    from tar_system.strategies import resolver

    monkeypatch.chdir(tmp_path)

    features = pd.DataFrame(
        {
            "timestamp": [pd.Timestamp("2026-01-01 00:00:00")],
            "symbol": ["XAUUSD"],
            "timeframe": ["M15"],
            "data_hash": ["hash-1"],
        }
    )
    broker_profile = SimpleNamespace(
        broker_name="test_broker",
        to_dict=lambda: {"broker_name": "test_broker", "symbols": {"XAUUSD": {"spread_model": "medium"}}},
    )
    asset_profile = SimpleNamespace(
        symbol="XAUUSD",
        to_dict=lambda: {"symbol": "XAUUSD", "spread_assumption": 15.0},
    )
    strategy = SimpleNamespace(name="gold_orb_v1", version="0.1.0")
    resolved = SimpleNamespace(
        strategy=strategy,
        variant=SimpleNamespace(parameters={"one_trade_per_day": True}),
        broker_profile=broker_profile,
        asset_profile=asset_profile,
    )
    captured: dict[str, object] = {}

    def fake_make_cache_key(strategy_name, parameters, symbol, timeframe, data_hash, date_range, mode):
        captured["cache_parameters"] = parameters
        return "cache-key"

    def fake_run_backtest(_features, _strategy, **kwargs):
        captured["broker_profile"] = kwargs.get("broker_profile")
        captured["asset_profile"] = kwargs.get("asset_profile")
        return BacktestResult(metrics={"total_trades": 0.0}, trades=0, final_equity=10_000.0)

    monkeypatch.setattr(store, "load_feature_data", lambda *_args, **_kwargs: features)
    monkeypatch.setattr(store, "filter_by_date_range", lambda df, *_args, **_kwargs: df)
    monkeypatch.setattr(resolver, "resolve_strategy", lambda *_args, **_kwargs: resolved)
    monkeypatch.setattr(result_cache, "make_cache_key", fake_make_cache_key)
    monkeypatch.setattr(result_cache, "load_cached_result", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(result_cache, "save_cached_result", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(review_log, "append_review_result", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("tar_system.backtest.engine.run_backtest", fake_run_backtest)

    cli.run_backtest_cmd(
        argparse.Namespace(
            strategy="gold_orb_v1",
            symbol="XAUUSD",
            timeframe="M15",
            broker="test_broker",
            force=True,
            from_date=None,
            to_date=None,
        )
    )

    assert captured["broker_profile"] is broker_profile
    assert captured["asset_profile"] is asset_profile
    assert captured["cache_parameters"] == {
        "variant": {"one_trade_per_day": True},
        "broker_profile": {"broker_name": "test_broker", "symbols": {"XAUUSD": {"spread_model": "medium"}}},
        "asset_profile": {"symbol": "XAUUSD", "spread_assumption": 15.0},
        "cost_multiplier": 1.0,
    }
