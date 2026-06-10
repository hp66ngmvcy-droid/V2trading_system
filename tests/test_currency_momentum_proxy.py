from __future__ import annotations

from pathlib import Path

import pandas as pd

from tar_system.research.currency_momentum_proxy import run_currency_momentum_proxy


def test_currency_momentum_proxy_runs_on_synthetic_basket(tmp_path: Path) -> None:
    raw = tmp_path / "data" / "raw"
    raw.mkdir(parents=True)
    months = pd.date_range("2020-01-31", periods=60, freq="ME", tz="UTC")
    symbols = ["EURUSD", "GBPUSD", "AUDUSD", "USDJPY"]
    for offset, symbol in enumerate(symbols):
        prices = [1.0 + offset * 0.1 + index * (0.01 + offset * 0.002) for index in range(len(months))]
        pd.DataFrame({"timestamp": months, "close": prices}).to_csv(raw / f"{symbol}_H1.csv", index=False)

    result = run_currency_momentum_proxy(symbols, raw_dir=raw, output_dir=tmp_path / "reports", cost_bps=0.0)

    assert result.months_tested > 36
    assert result.trades
    assert result.verdict in {"KEEP", "REVIEW", "KILL"}
    assert Path(result.report_path).exists()


def test_currency_momentum_proxy_rejects_missing_data(tmp_path: Path) -> None:
    try:
        run_currency_momentum_proxy(["EURUSD"], raw_dir=tmp_path / "missing", output_dir=tmp_path / "reports")
    except ValueError as exc:
        assert "No usable close data" in str(exc)
    else:
        raise AssertionError("missing data should fail")
