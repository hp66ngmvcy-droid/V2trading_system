from __future__ import annotations

from pathlib import Path

import pandas as pd

from tar_system.research.bounded_trend_proxy import run_bounded_trend_proxy


def test_bounded_trend_proxy_runs_grid(tmp_path: Path) -> None:
    raw = tmp_path / "data" / "raw"
    raw.mkdir(parents=True)
    timestamps = pd.date_range("2024-01-01", periods=400, freq="1h", tz="UTC")
    for symbol, drift in [("GBPUSD", 0.0001), ("EURUSD", -0.00005)]:
        prices = [1.0 + index * drift for index in range(len(timestamps))]
        pd.DataFrame({"timestamp": timestamps, "close": prices}).to_csv(raw / f"{symbol}_H1.csv", index=False)

    result = run_bounded_trend_proxy(
        ["GBPUSD", "EURUSD"],
        raw_dir=raw,
        output_dir=tmp_path / "reports",
        fast_values=[10, 20],
        slow_values=[50],
        cost_bps=0.0,
    )

    assert result.rows
    assert result.best_symbol in {"GBPUSD", "EURUSD"}
    assert Path(result.report_path).exists()


def test_bounded_trend_proxy_rejects_missing_raw_data(tmp_path: Path) -> None:
    try:
        run_bounded_trend_proxy(["GBPUSD"], raw_dir=tmp_path / "missing", output_dir=tmp_path / "reports")
    except ValueError as exc:
        assert "Missing raw data" in str(exc)
    else:
        raise AssertionError("missing raw data should fail")
