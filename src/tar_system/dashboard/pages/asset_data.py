"""Asset data dashboard page."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from tar_system.dashboard.components.controls import DATA_SOURCES, symbol_config
from tar_system.dashboard.components.layout import metric_row, page_header
from tar_system.data.validator import validate_ohlcv


def render(st: object) -> None:
    page_header(st, "Asset Data", "Inspect local CSV, Parquet and feature-store readiness.")
    config = symbol_config(st)
    source = st.selectbox("Data source", DATA_SOURCES, key="tar_asset_data_source")
    path = _data_path(source, config["symbol"], config["timeframe"])
    st.write({"selected_source": source, "path": str(path)})
    if not path.exists():
        st.info("No local data found for this selection.")
        return
    df = pd.read_parquet(path) if path.suffix == ".parquet" else pd.read_csv(path)
    result = validate_ohlcv(df) if {"timestamp", "open", "high", "low", "close", "volume", "symbol", "timeframe"}.issubset(df.columns) else None
    metric_row(
        st,
        [
            ("Rows", len(df), None),
            ("Missing values", int(df.isna().sum().sum()), None),
            ("Duplicate timestamps", int(df["timestamp"].duplicated().sum()) if "timestamp" in df else "n/a", None),
            ("Validation", result.passed if result else "not validated", None),
            ("Quality", result.data_quality_score if result else "n/a", None),
        ],
    )
    st.write(
        {
            "start_date": str(pd.to_datetime(df["timestamp"]).min()) if "timestamp" in df else None,
            "end_date": str(pd.to_datetime(df["timestamp"]).max()) if "timestamp" in df else None,
            "feature_status": "available" if source == "Feature store" else "not selected",
            "data_hash": str(df["data_hash"].iloc[0]) if "data_hash" in df.columns and len(df) else None,
        }
    )


def _data_path(source: str, symbol: str, timeframe: str) -> Path:
    if source == "CSV":
        return Path("data/raw") / f"{symbol}_{timeframe}.csv"
    if source == "Feature store":
        return Path("data/features") / f"{symbol}_{timeframe}.parquet"
    return Path("data/validated") / f"{symbol}_{timeframe}.parquet"


if __name__ == "__main__":
    import streamlit as st

    from tar_system.dashboard.components.layout import apply_theme

    st.set_page_config(page_title="TAR V2 Asset Data", layout="wide")
    apply_theme(st)
    render(st)
