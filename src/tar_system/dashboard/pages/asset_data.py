"""Asset data dashboard page."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import quote

import pandas as pd

from tar_system.dashboard.components.controls import DATA_SOURCES, symbol_config
from tar_system.dashboard.components.layout import metric_row, page_header
from tar_system.data.validator import validate_ohlcv

TRADINGVIEW_SYMBOLS = {
    "XAUUSD": "OANDA:XAUUSD",
    "XAGUSD": "OANDA:XAGUSD",
    "BTCUSD": "BITSTAMP:BTCUSD",
    "ETHUSD": "BITSTAMP:ETHUSD",
    "EURUSD": "OANDA:EURUSD",
    "GBPUSD": "OANDA:GBPUSD",
    "USDJPY": "OANDA:USDJPY",
    "USOIL": "TVC:USOIL",
}

TRADINGVIEW_INTERVALS = {
    "M1": "1",
    "M5": "5",
    "M15": "15",
    "M30": "30",
    "H1": "60",
    "H4": "240",
    "D1": "D",
}


def render(st: object) -> None:
    page_header(st, "Asset Data", "Inspect local CSV, Parquet and feature-store readiness.")
    config = symbol_config(st)
    _render_live_reference(st, config["symbol"], config["timeframe"])
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


def _render_live_reference(st: object, symbol: str, timeframe: str) -> None:
    url = live_reference_url(symbol, timeframe)
    local_path = Path("data/raw") / f"{symbol}_{timeframe}.csv"
    st.subheader("Live Market Reference")
    st.write(
        {
            "source": "TradingView",
            "live_chart_url": url,
            "local_training_path": str(local_path),
            "ingestion_mode": "manual CSV import only",
        }
    )
    if hasattr(st, "link_button"):
        st.link_button("Open TradingView Chart", url)
    else:
        st.markdown(f"[Open TradingView Chart]({url})")
    st.caption("Use the live chart as a human reference/export source. Training and strategy tests only read local imported OHLCV files.")


def live_reference_url(symbol: str, timeframe: str, source: str = "TradingView") -> str:
    if source != "TradingView":
        raise ValueError(f"Unsupported live reference source: {source}")
    tv_symbol = TRADINGVIEW_SYMBOLS.get(symbol.upper(), f"OANDA:{symbol.upper()}")
    interval = TRADINGVIEW_INTERVALS.get(timeframe.upper(), "15")
    return f"https://www.tradingview.com/chart/?symbol={quote(tv_symbol, safe='')}&interval={quote(interval, safe='')}"


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
