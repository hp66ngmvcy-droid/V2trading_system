"""Runner regression: non-brief days must remain available for paper exits."""

import importlib.util
import json
from pathlib import Path

import pandas as pd
import pytest

from tar_system.backtest import engine
from tar_system.execution.paper_broker import PaperBroker
from tar_system.portfolio.tracker import PortfolioTracker
from tar_system.strategies.key_level_sweep_v1 import _brief_cache


@pytest.fixture
def runner():
    path = Path(__file__).resolve().parents[1] / "scripts/run_key_level_sweep_real_backtest.py"
    spec = importlib.util.spec_from_file_location("key_level_runner", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("symbol,scale", [("XAUUSD", 1), ("BTCUSD", 20)])
@pytest.mark.parametrize("bar_low,bar_high,expected_exit", [
    (4380, 4440, 4385), (4420, 4480, 4470),
])
def test_exit_on_day_without_brief(
    runner, tmp_path, monkeypatch, symbol, scale, bar_low, bar_high, expected_exit
):
    brief = {
        "issued_at": "2026-09-07T00:00:00Z",
        symbol: {
            "sell_confidence": 0.9, "buy_confidence": 0.0,
            "key_levels": {
                "sell_zone_low": 4435 * scale,
                "sell_zone_high": 4455 * scale,
                "bearish_invalidation": 4470 * scale,
            },
            "top_scenario_targets": [4385 * scale],
        },
    }
    briefs = tmp_path / "briefs"
    briefs.mkdir()
    (briefs / "2026-09-07_levels.json").write_text(json.dumps(brief))
    rows = []
    for date, open_, high, low, close in [
        ("2026-09-07", 4432, 4445, 4428, 4430),
        ("2026-09-08", 4430, bar_high, bar_low, 4430),
        ("2026-09-09", 4430, 4440, 4420, 4430),
    ]:
        rows.append({
            "timestamp": pd.Timestamp(f"{date}T09:00:00Z"),
            "symbol": symbol, "timeframe": "M15", "atr": 20 * scale,
            "open": open_ * scale, "high": high * scale,
            "low": low * scale, "close": close * scale,
        })
    features = pd.DataFrame(rows).iloc[::-1].reset_index(drop=True)
    original = features.copy(deep=True)
    trackers = []

    class RecordingTracker(PortfolioTracker):
        def __post_init__(self):
            super().__post_init__()
            trackers.append(self)

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(runner, "BRIEFS_DIR", briefs)
    monkeypatch.setattr(runner, "RESULTS_DIR", tmp_path / "results")
    monkeypatch.setattr(runner.pd, "read_parquet", lambda _: features)
    monkeypatch.setattr(runner, "load_broker_profile", lambda _: None)
    monkeypatch.setattr(engine, "PortfolioTracker", RecordingTracker)
    monkeypatch.setattr(engine, "PaperBroker", lambda: PaperBroker(slippage_bps=0.0))
    monkeypatch.setattr(engine, "read_backtest_status", lambda: {})
    monkeypatch.setattr("sys.argv", ["runner", "--symbol", symbol])
    _brief_cache.clear()
    try:
        assert runner.main() == 0
        assert len(trackers[0].closed_trades) == 1
        trade = trackers[0].closed_trades[0]
        assert trade.closed_at == pd.Timestamp("2026-09-08T09:00:00Z")
        assert trade.exit_price == pytest.approx(expected_exit * scale)
        report = json.loads(next((tmp_path / "results").glob("*_real.json")).read_text())
        assert report["bars_in_slice"] == 3
        assert report["brief_dates"] == ["2026-09-07"]
        pd.testing.assert_frame_equal(features, original)
    finally:
        _brief_cache.clear()


def test_empty_features_fail_without_running_backtest(runner, tmp_path, monkeypatch):
    (tmp_path / "2026-09-07_levels.json").write_text("{}")
    monkeypatch.setattr(runner, "BRIEFS_DIR", tmp_path)
    monkeypatch.setattr(runner, "load_daily_levels", lambda *args: {"key_levels": {}})
    monkeypatch.setattr(runner.pd, "read_parquet", lambda _: pd.DataFrame(columns=["timestamp"]))
    monkeypatch.setattr(runner, "run_backtest", lambda *a, **kw: pytest.fail("must not run"))
    monkeypatch.setattr("sys.argv", ["runner"])
    assert runner.main() == 1
