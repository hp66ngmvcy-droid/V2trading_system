"""Streamlit dashboard for local paper-only research."""

from __future__ import annotations

import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[2]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


def main() -> None:
    import streamlit as st

    from tar_system.dashboard.components.layout import apply_theme
    from tar_system.dashboard.pages import asset_data, daily_summary, environment, leaderboard, overview, paper_signals, positioning, promotion_board, run_control, security, strategy_detail

    st.set_page_config(page_title="TAR V2 Research", layout="wide")
    apply_theme(st)
    st.sidebar.markdown("### TAR V2")
    st.sidebar.caption("Local paper-only research")
    sections = [
        "Overview",
        "Daily Summary",
        "Import CSV",
        "Asset Data",
        "Run Backtest",
        "Forward Test",
        "Paper Signals",
        "Strategy Ranking",
        "Strategy Detail",
        "Positioning Context",
        "EA Promotion Board",
        "Review Log",
        "Obsidian Export",
        "Environment",
        "Strategy Discovery",
        "Risk + Strategy Optimiser",
        "MT5 Export",
        "Security",
    ]
    if st.session_state.get("tar_section") not in sections:
        st.session_state["tar_section"] = "Overview"
    section = st.sidebar.radio(
        "Section",
        sections,
        index=sections.index(st.session_state["tar_section"]),
        key="tar_section",
    )
    if section == "Overview":
        overview.render(st)
    elif section == "Daily Summary":
        daily_summary.render(st)
    elif section == "Strategy Ranking":
        leaderboard.render(st)
    elif section == "Run Backtest":
        run_control.render(st)
    elif section == "Forward Test":
        run_control.render(st)
    elif section == "Paper Signals":
        paper_signals.render(st)
    elif section == "Import CSV":
        asset_data.render(st)
    elif section == "Asset Data":
        asset_data.render(st)
    elif section == "Environment":
        environment.render(st)
    elif section == "Security":
        security.render(st)
    elif section == "Strategy Discovery":
        from tar_system.dashboard.components.layout import page_header

        page_header(st, "Strategy Discovery", "Candidate ideas are controlled blueprints, never live strategy code.")
        st.write("Candidate discovery is CLI-controlled and candidates remain paper-only.")
    elif section == "MT5 Export":
        from tar_system.dashboard.components.layout import page_header

        page_header(st, "MT5 Export", "Manual review files only. No login, no order placement.")
        st.write("Manual review exports only. No MT5 login and no live order placement.")
    elif section == "Review Log":
        from tar_system.dashboard.components.layout import page_header

        page_header(st, "Review Log", "Local JSONL decisions and paper-only audit history.")
        st.write("Review log records are stored in `logs/review_log.jsonl`.")
    elif section == "Obsidian Export":
        from tar_system.dashboard.components.layout import page_header

        page_header(st, "Obsidian Export", "Local research notes, winners, failures, patterns and optimiser decisions.")
        st.write("Obsidian notes are written locally under `obsidian/` when export commands are run.")
    elif section == "Strategy Detail":
        strategy_detail.render(st)
    elif section == "Positioning Context":
        positioning.render(st)
    elif section == "EA Promotion Board":
        promotion_board.render(st)
    elif section == "Risk + Strategy Optimiser":
        from tar_system.dashboard.components.layout import page_header, metric_row

        page_header(st, "Risk + Strategy Optimiser", "Robustness-first recommendations across backtests, validation and environment state.")
        st.write("Paper-only optimiser summary. It recommends actions but cannot place trades or promote without approval.")
        try:
            from tar_system.optimisation.risk_strategy_optimiser import RiskStrategyOptimiser

            result = RiskStrategyOptimiser().optimise_from_logs("gold_v2", "XAUUSD", "M15", write_outputs=False)
            metric_row(
                st,
                [
                    ("Optimiser score", result.optimiser_score, None),
                    ("Decision", result.optimiser_decision, None),
                    ("GO / NO-GO", result.go_no_go_status, None),
                    ("Risk", result.risk_adjustment, None),
                ],
            )
            st.write(
                {
                    "optimiser_score": result.optimiser_score,
                    "optimiser_decision": result.optimiser_decision,
                    "go_no_go_status": result.go_no_go_status,
                    "main_failure_reasons": result.reason_codes,
                    "improvement_plan": result.improvement_plan,
                    "best_regime": "See regime heatmap",
                    "avoid_regime": [key for key, value in result.regime_heatmap.items() if value.get("flag") == "avoid regime"],
                    "latest_environment_state": "REVIEW_ONLY",
                    "next_recommended_action": result.next_actions,
                }
            )
        except Exception as exc:  # pragma: no cover - dashboard resilience
            st.write(f"Optimiser unavailable: {exc}")
    else:
        st.write("Use the CLI commands for this workflow. Dashboard controls remain review-only.")


if __name__ == "__main__":
    main()
