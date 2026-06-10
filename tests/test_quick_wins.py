from __future__ import annotations

from pathlib import Path

import pandas as pd

from tar_system.research.multi_asset_backtester import MultiAssetBacktester
from tar_system.research.paper_backtester import PaperStrategyBacktester
from tar_system.research.strategy_enhancements import (
    AdaptiveParameters,
    MultiTimeframeFilter,
    RegimeDetection,
    VolumeConfirmation,
)


def _bars(rows: int = 80, volume: float = 100.0, symbol: str = "XAUUSD", timeframe: str = "M15") -> pd.DataFrame:
    close = pd.Series([100 + i * 0.15 for i in range(rows)], dtype=float)
    return pd.DataFrame(
        {
            "timestamp": pd.date_range("2026-01-01", periods=rows, freq="15min"),
            "open": close - 0.05,
            "high": close + 0.25,
            "low": close - 0.25,
            "close": close,
            "volume": volume,
            "symbol": symbol,
            "timeframe": timeframe,
        }
    )


def test_volume_confirmation_blocks_low_relative_volume() -> None:
    df = _bars(30, volume=100)
    df.loc[29, "volume"] = 110
    assert VolumeConfirmation(lookback_period=20, volume_multiplier=1.2).is_valid_volume(df, 29) is False

    df.loc[29, "volume"] = 130
    assert VolumeConfirmation(lookback_period=20, volume_multiplier=1.2).is_valid_volume(df, 29) is True


def test_multi_timeframe_filter_confirms_or_blocks_direction() -> None:
    higher = pd.DataFrame({"close": [100.0, 101.0, 102.0, 103.0, 104.0]})
    filt = MultiTimeframeFilter({"XAUUSD": {"H1": higher}})

    assert filt.get_higher_timeframe_signal("XAUUSD", "M15", 16) == 1
    assert filt.confirms_signal("XAUUSD", "M15", 16, 1) is True
    assert filt.confirms_signal("XAUUSD", "M15", 16, -1) is False
    assert filt.confirms_signal("XAUUSD", "M5", 16, -1) is True


def test_regime_detection_returns_known_regime() -> None:
    df = _bars(50)
    regime = RegimeDetection().detect_regime(df, 49)
    assert regime in {"TRENDING", "RANGING", "BREAKOUT", "NEUTRAL"}


def test_parameter_variants_and_regime_mapping() -> None:
    params = AdaptiveParameters()
    variants = params.get_all_variants()
    assert {"conservative", "moderate", "aggressive", "breakout"} <= set(variants)
    assert params.get_variant_for_regime("BREAKOUT") == variants["breakout"]
    assert params.get_variant_for_regime("RANGING") == variants["conservative"]


def test_paper_backtester_volume_confirmation_changes_results(tmp_path) -> None:
    data_dir = tmp_path / "data" / "validated"
    data_dir.mkdir(parents=True)
    df = _bars(80, volume=100)
    df.loc[25:, "volume"] = 80
    df.to_parquet(data_dir / "XAUUSD_M15.parquet", index=False)

    backtester = PaperStrategyBacktester(str(data_dir))
    without_filter = backtester.backtest_strategy(
        "momentum",
        symbol="XAUUSD",
        timeframe="M15",
        use_volume_confirmation=False,
        use_regime_detection=False,
        entry_threshold=0.001,
        take_profit_pct=0.001,
    )
    with_filter = backtester.backtest_strategy(
        "momentum",
        symbol="XAUUSD",
        timeframe="M15",
        use_volume_confirmation=True,
        use_regime_detection=False,
        entry_threshold=0.001,
        take_profit_pct=0.001,
    )

    assert without_filter["total_trades"] > with_filter["total_trades"]


def test_multi_asset_backtester_discovers_assets_and_runs_variant(tmp_path) -> None:
    data_dir = tmp_path / "data" / "validated"
    data_dir.mkdir(parents=True)
    _bars(symbol="XAUUSD", timeframe="M15").to_parquet(data_dir / "XAUUSD_M15.parquet", index=False)
    _bars(symbol="EURUSD", timeframe="M15").to_parquet(data_dir / "EURUSD_M15.parquet", index=False)

    backtester = MultiAssetBacktester(str(data_dir))
    assert backtester.get_available_assets() == ["EURUSD", "XAUUSD"]
    results = backtester.test_strategy_across_assets(
        "momentum",
        assets=["EURUSD", "XAUUSD"],
        timeframe="M15",
        param_variant="aggressive",
        max_rows=40,
    )
    assert set(results) == {"EURUSD", "XAUUSD"}
    assert all("total_trades" in result for result in results.values())


def test_multi_asset_backtester_accepts_strategy_and_asset_limits(tmp_path) -> None:
    data_dir = tmp_path / "data" / "validated"
    data_dir.mkdir(parents=True)
    _bars(symbol="XAUUSD", timeframe="M15").to_parquet(data_dir / "XAUUSD_M15.parquet", index=False)

    backtester = MultiAssetBacktester(str(data_dir))
    results = backtester.test_all_strategies_all_assets(
        timeframe="M15",
        param_variant="aggressive",
        strategies=["momentum"],
        assets=["XAUUSD"],
        max_rows=40,
    )

    assert list(results) == ["momentum"]
    assert list(results["momentum"]) == ["XAUUSD"]
