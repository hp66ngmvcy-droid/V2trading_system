"""Strategy leaderboard dashboard page."""

from __future__ import annotations

from typing import Any

from tar_system.dashboard.components.tables import leaderboard_frame
from tar_system.dashboard.components.layout import metric_row, page_header
from tar_system.reporting.review_log import load_review_results


def load_leaderboard_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in load_review_results():
        metrics = item.get("metrics", {}) or {}
        rows.append(
            {
                "strategy": item.get("strategy", ""),
                "asset": item.get("symbol", ""),
                "symbol": item.get("symbol", ""),
                "timeframe": item.get("timeframe", ""),
                "win_rate": metrics.get("win_rate", 0),
                "profit_factor": metrics.get("profit_factor", 0),
                "max_drawdown": metrics.get("max_drawdown", 0),
                "trade_count": metrics.get("total_trades", 0),
                "expectancy": metrics.get("expectancy", 0),
                "score": item.get("score", item.get("optimiser_score", 0)),
                "verdict": item.get("verdict", item.get("optimiser_decision", "")),
                "environment_state": item.get("environment_state", "REVIEW_ONLY"),
                "last_tested_date": item.get("timestamp", ""),
            }
        )
    return rows


def render(st: object) -> None:
    rows = load_leaderboard_rows()
    page_header(st, "Strategy Leaderboard", "Compare paper-only research results without ranking by win rate alone.")
    metric_row(st, [("Rows", len(rows), None), ("Tracked symbols", len({row["symbol"] for row in rows}), None), ("Verdicts", len({row["verdict"] for row in rows}), None)])
    with st.expander("Filters", expanded=True):
        col1, col2, col3 = st.columns(3)
        asset_class = col1.selectbox("Asset class", ["All", "Gold / Metals", "Crypto", "Forex", "Commodities", "Indices"], key="tar_leaderboard_asset_class")
        symbol = col2.selectbox("Symbol", ["All", "XAUUSD", "XAGUSD", "BTCUSD", "ETHUSD", "EURUSD", "GBPUSD", "USDJPY", "USOIL"], key="tar_leaderboard_symbol")
        timeframe = col3.selectbox("Timeframe", ["All", "M1", "M5", "M15", "M30", "H1", "H4", "D1"], key="tar_leaderboard_timeframe")
        col4, col5, col6 = st.columns(3)
        verdict = col4.selectbox("Verdict", ["All", "KEEP", "REVIEW", "KILL", "RETEST", "REDUCE_RISK", "PAUSE", "PROMOTE_CANDIDATE"], key="tar_leaderboard_verdict")
        col5.selectbox("Regime", ["All", "TRENDING", "RANGING", "VOLATILE", "UNKNOWN"], key="tar_leaderboard_regime")
        score_range = col6.slider("Score range", 0, 100, (0, 100), key="tar_leaderboard_score_range")
    filtered = [
        row
        for row in rows
        if (symbol == "All" or row["symbol"] == symbol)
        and (timeframe == "All" or row["timeframe"] == timeframe)
        and (verdict == "All" or row["verdict"] == verdict)
        and score_range[0] <= float(row.get("score", 0) or 0) <= score_range[1]
    ]
    st.dataframe(leaderboard_frame(filtered), width="stretch")
    st.caption(f"Asset class filter selected: {asset_class}")


if __name__ == "__main__":
    import streamlit as st

    from tar_system.dashboard.components.layout import apply_theme

    st.set_page_config(page_title="TAR V2 Leaderboard", layout="wide")
    apply_theme(st)
    render(st)
