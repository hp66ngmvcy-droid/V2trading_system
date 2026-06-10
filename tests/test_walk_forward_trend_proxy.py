from __future__ import annotations

from pathlib import Path

import pandas as pd

from tar_system.research.walk_forward_trend_proxy import run_walk_forward_trend_proxy


def test_walk_forward_trend_proxy_runs_windows(tmp_path: Path) -> None:
    raw = tmp_path / "data" / "raw"
    raw.mkdir(parents=True)
    timestamps = pd.date_range("2020-01-01", periods=24 * 365 * 3, freq="1h", tz="UTC")
    prices = [1.0 + index * 0.00001 for index in range(len(timestamps))]
    pd.DataFrame({"timestamp": timestamps, "close": prices}).to_csv(raw / "GBPUSD_H1.csv", index=False)

    result = run_walk_forward_trend_proxy(
        ["GBPUSD"],
        raw_dir=raw,
        output_dir=tmp_path / "reports",
        ema_values=[10, 20, 50],
        train_months=6,
        validation_months=3,
        test_months=3,
        step_months=3,
        cost_bps=0.0,
    )

    assert result.rows
    assert result.rows[0].windows >= 4
    assert result.rows[0].selected_pairs
    assert Path(result.report_path).exists()


def test_walk_forward_trend_proxy_rejects_short_data(tmp_path: Path) -> None:
    raw = tmp_path / "data" / "raw"
    raw.mkdir(parents=True)
    timestamps = pd.date_range("2024-01-01", periods=100, freq="1h", tz="UTC")
    prices = [1.0 + index * 0.0001 for index in range(len(timestamps))]
    pd.DataFrame({"timestamp": timestamps, "close": prices}).to_csv(raw / "GBPUSD_H1.csv", index=False)

    try:
        run_walk_forward_trend_proxy(["GBPUSD"], raw_dir=raw, output_dir=tmp_path / "reports")
    except ValueError as exc:
        assert "Not enough walk-forward windows" in str(exc)
    else:
        raise AssertionError("short data should fail")
