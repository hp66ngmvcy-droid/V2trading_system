"""Environment dashboard page."""

from __future__ import annotations

from pathlib import Path

from tar_system.environment.event_calendar import load_events
from tar_system.environment.risk_state import evaluate_environment, event_hold_window
from tar_system.dashboard.components.layout import page_header, status_pill


def render(st: object) -> None:
    page_header(st, "Environment Risk", "Manual macro and shock-event controls for paper-only research.")
    symbol = st.selectbox("Symbol", ["XAUUSD", "XAGUSD", "BTCUSD", "ETHUSD", "EURUSD", "GBPUSD", "USDJPY", "USOIL"], key="tar_environment_symbol")
    events = load_events() or []
    decision = evaluate_environment(symbol, __import__("datetime").datetime.now(), events)
    status_pill(st, "Environment", decision.state)
    st.write({"blocked_assets": [event.affected_assets for event in decision.matched_events]})
    for event in events:
        st.write(
            {
                "title": event.title,
                "event_type": event.event_type,
                "affected_assets": event.affected_assets,
                "hold_windows": event_hold_window(event),
            }
        )
    reports = sorted(Path("reports/environment").glob("*"))
    st.write({"latest_environment_report": str(reports[-1]) if reports else None})


if __name__ == "__main__":
    import streamlit as st

    from tar_system.dashboard.components.layout import apply_theme

    st.set_page_config(page_title="TAR V2 Environment", layout="wide")
    apply_theme(st)
    render(st)
