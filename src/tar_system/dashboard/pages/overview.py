"""Overview dashboard page."""

from __future__ import annotations

import json
from pathlib import Path

from tar_system.dashboard.runtime_control import read_backtest_status, read_forward_status
from tar_system.dashboard.components.layout import card, metric_row, page_header, status_pill
from tar_system.environment.event_calendar import load_events
from tar_system.environment.risk_state import evaluate_environment
from tar_system.positioning.store import latest_positioning_score
from tar_system.settings import LIVE_TRADING_ALLOWED, PAPER_MODE


def render(st: object) -> None:
    events = load_events()
    env = evaluate_environment("XAUUSD", __import__("datetime").datetime.now(), events)
    backtest = read_backtest_status()
    forward = read_forward_status()
    page_header(st, "TAR V2 Research Console", "Local-first CSV research, paper backtests, safety gates and manual review exports.")
    metric_row(
        st,
        [
            ("System", "Online", None),
            ("Paper mode", str(PAPER_MODE), None),
            ("Live trading blocked", str(not LIVE_TRADING_ALLOWED), None),
            ("Environment", env.state, None),
        ],
    )
    left, right = st.columns(2)
    with left:
        card(st, "Latest Backtest", f"{backtest.get('strategy') or 'No strategy'} | {backtest.get('symbol') or 'No symbol'} | {backtest.get('latest_message')}")
    with right:
        card(st, "Latest Forward Test", f"{forward.get('strategy') or 'No strategy'} | {forward.get('symbol') or 'No symbol'} | {forward.get('latest_message')}")
    status_pill(st, "Environment", env.state)
    positioning = latest_positioning_score("XAUUSD")
    status_pill(st, "XAUUSD positioning", f"{positioning.get('bias')} {positioning.get('positioning_score')}")
    margin_state = margin_utilisation_warning(float(forward.get("margin_utilisation", 0.0) or backtest.get("margin_utilisation", 0.0) or 0.0))
    status_pill(st, "Margin utilisation", margin_state)
    st.subheader("Latest Audit Event")
    st.json(_latest_audit_event())


def margin_utilisation_warning(margin_utilisation: float) -> str:
    if margin_utilisation >= 0.9:
        return "BLOCK"
    if margin_utilisation >= 0.8:
        return "RED"
    if margin_utilisation >= 0.5:
        return "AMBER"
    return "OK"


def _latest_audit_event() -> dict[str, object] | str:
    path = Path("logs/audit/audit.jsonl")
    if not path.exists():
        return "No audit event yet"
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return json.loads(lines[-1]) if lines else "No audit event yet"


if __name__ == "__main__":
    import streamlit as st

    from tar_system.dashboard.components.layout import apply_theme

    st.set_page_config(page_title="TAR V2 Overview", layout="wide")
    apply_theme(st)
    render(st)
