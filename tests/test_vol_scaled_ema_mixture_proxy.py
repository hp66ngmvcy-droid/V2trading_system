from __future__ import annotations

from pathlib import Path

import pandas as pd

from tar_system.research.vol_scaled_ema_mixture_proxy import run_vol_scaled_ema_mixture_proxy


def test_vol_scaled_ema_mixture_proxy_runs_basket(tmp_path: Path) -> None:
    raw = tmp_path / "data" / "raw"
    raw.mkdir(parents=True)
    timestamps = pd.date_range("2022-01-01", periods=24 * 260, freq="1h", tz="UTC")
    for symbol, drift in [("EURUSD", 0.00001), ("GBPUSD", 0.000008)]:
        prices = [1.0 + index * drift for index in range(len(timestamps))]
        pd.DataFrame({"timestamp": timestamps, "close": prices}).to_csv(raw / f"{symbol}_H1.csv", index=False)

    result = run_vol_scaled_ema_mixture_proxy(
        ["EURUSD", "GBPUSD"],
        raw_dir=raw,
        output_dir=tmp_path / "reports",
        ema_pairs=[(4, 12), (8, 24)],
        vol_window=48,
        threshold=0.01,
        cost_bps=0.0,
    )

    assert len(result.rows) == 2
    assert result.ema_pairs == ["4/12", "8/24"]
    assert Path(result.report_path).exists()
    assert result.basket_verdict in {"KEEP", "REVIEW", "KILL"}


def test_vol_scaled_ema_mixture_proxy_rejects_bad_pair(tmp_path: Path) -> None:
    raw = tmp_path / "data" / "raw"
    raw.mkdir(parents=True)
    timestamps = pd.date_range("2022-01-01", periods=500, freq="1h", tz="UTC")
    prices = [1.0 + index * 0.00001 for index in range(len(timestamps))]
    pd.DataFrame({"timestamp": timestamps, "close": prices}).to_csv(raw / "EURUSD_H1.csv", index=False)

    try:
        run_vol_scaled_ema_mixture_proxy(
            ["EURUSD"],
            raw_dir=raw,
            output_dir=tmp_path / "reports",
            ema_pairs=[(24, 8)],
        )
    except ValueError as exc:
        assert "fast must be less than slow" in str(exc)
    else:
        raise AssertionError("bad EMA pair should fail")
