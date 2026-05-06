"""Shared dashboard controls."""

from __future__ import annotations

ASSET_CLASSES = ["Gold / Metals", "Crypto", "Forex", "Commodities", "Indices"]
SYMBOLS = ["XAUUSD", "XAGUSD", "BTCUSD", "ETHUSD", "EURUSD", "GBPUSD", "USDJPY", "USOIL"]
TIMEFRAMES = ["M1", "M5", "M15", "M30", "H1", "H4", "D1"]
DATA_SOURCES = ["CSV", "Parquet", "Feature store"]


def symbol_config(st: object) -> dict[str, str]:
    return {
        "asset_class": st.selectbox("Asset class", ASSET_CLASSES, key="tar_asset_data_asset_class"),
        "symbol": st.selectbox("Symbol", SYMBOLS, key="tar_asset_data_symbol"),
        "timeframe": st.selectbox("Timeframe", TIMEFRAMES, index=2, key="tar_asset_data_timeframe"),
    }
