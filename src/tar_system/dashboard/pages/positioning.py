"""Positioning context dashboard page."""

from __future__ import annotations

from pathlib import Path

from tar_system.dashboard.components.layout import metric_row, page_header
from tar_system.positioning.store import latest_positioning_score, load_positioning_records


def render(st: object) -> None:
    page_header(st, "Positioning Context", "COT and manual prime-broker-style notes. Context only, never an automatic trade trigger.")
    symbol = st.selectbox("Symbol", ["XAUUSD", "BTCUSD", "ETHUSD", "EURUSD", "GBPUSD", "USDJPY", "USDCAD", "AUDUSD", "USOUSD"], key="tar_positioning_symbol")
    context = latest_positioning_score(symbol)
    metric_row(
        st,
        [
            ("Score", context.get("positioning_score", 0.0), None),
            ("Bias", context.get("bias", "NEUTRAL"), None),
            ("Confidence", context.get("confidence", 0.0), None),
            ("Mode", "Context only", None),
        ],
    )
    st.caption("Save notes from Codex, ChatGPT, Claude or manual research as markdown/text, then import them with the CLI.")
    st.code(
        f"python -m tar_system.cli import-positioning-note --file research/positioning/{symbol}_note.md --symbol {symbol} --source claude",
        language="bash",
    )
    st.code(
        f"python -m tar_system.cli import-cot --file data/raw/cot_{symbol}.csv --symbol {symbol}",
        language="bash",
    )
    rows = load_positioning_records(symbol, limit=50)
    if rows:
        st.dataframe(rows, width="stretch")
    else:
        st.info("No positioning records imported yet.")
    folder = Path("research/positioning")
    st.write({"suggested_note_folder": str(folder), "dashboard_places_no_trades": True})


if __name__ == "__main__":
    import streamlit as st

    from tar_system.dashboard.components.layout import apply_theme

    st.set_page_config(page_title="TAR V2 Positioning", layout="wide")
    apply_theme(st)
    render(st)
