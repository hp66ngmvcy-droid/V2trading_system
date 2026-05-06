"""Security dashboard page."""

from __future__ import annotations

from tar_system.security.checks import run_security_checks
from tar_system.settings import LIVE_TRADING_ALLOWED, PAPER_MODE
from tar_system.dashboard.components.layout import metric_row, page_header, status_pill


def render(st: object) -> None:
    result = run_security_checks()
    page_header(st, "Security", "Paper-only guarantees and local safety checks.")
    metric_row(st, [("PAPER_MODE", PAPER_MODE, None), ("LIVE_TRADING_ALLOWED", LIVE_TRADING_ALLOWED, None), ("Security", "PASSED" if result.passed else "FAILED", None)])
    status_pill(st, "Security check", "PASSED" if result.passed else "FAILED")
    st.write(
        {
            "PAPER_MODE": PAPER_MODE,
            "LIVE_TRADING_ALLOWED": LIVE_TRADING_ALLOWED,
            ".env ignored check": "ENV_NOT_IGNORED" not in result.findings,
            "no broker keys detected": not any(finding.startswith("CONFIG_SECRET_NAME") for finding in result.findings),
            "MT5 export manual review only": "MT5_EXPORTER_ORDER_FUNCTION" not in result.findings,
            "dashboard cannot place trades": "DASHBOARD_TRADING_FUNCTION" not in result.findings,
            "findings": result.findings,
        }
    )


if __name__ == "__main__":
    import streamlit as st

    from tar_system.dashboard.components.layout import apply_theme

    st.set_page_config(page_title="TAR V2 Security", layout="wide")
    apply_theme(st)
    render(st)
