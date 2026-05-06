"""Strategy detail dashboard page."""

from __future__ import annotations

import json
from pathlib import Path

from tar_system.dashboard.components.charts import line_chart
from tar_system.dashboard.components.layout import page_header, status_pill
from tar_system.optimisation.go_no_go_gate import evaluate_go_no_go
from tar_system.strategies.asset_variants import default_variant


def render(st: object) -> None:
    page_header(st, "Strategy Detail", "Inspect metrics, validation artifacts, trades and export history.")
    from tar_system.strategies.registry import REGISTRY

    strategy = st.selectbox("Strategy", sorted(REGISTRY.keys()), key="tar_detail_strategy")
    symbol = st.selectbox("Symbol", ["XAUUSD", "XAGUSD", "BTCUSD", "ETHUSD", "EURUSD", "GBPUSD", "USDJPY", "USOUSD"], key="tar_detail_symbol")
    timeframe = st.selectbox("Timeframe", ["M1", "M5", "M15", "M30", "H1", "H4", "D1"], index=2, key="tar_detail_timeframe")
    metrics = _load_json(Path("data/results") / f"{strategy}_{symbol}_{timeframe}_metrics.json")
    equity = _load_json(Path("data/results") / f"{symbol}_{timeframe}_{strategy}_equity.json")
    st.write({"metrics": metrics, "score": metrics.get("score", 0), "verdict": metrics.get("verdict", "unknown")})
    line_chart(st, equity if isinstance(equity, list) else metrics.get("equity_curve", []), "Equity Curve")
    line_chart(st, metrics.get("drawdown_curve", []), "Drawdown")
    st.write({"trade_list": _load_json(Path("data/results") / f"{strategy}_{symbol}_{timeframe}_trades.json")})
    st.write({"equity_curve_export": equity})
    st.write({"regime_performance": _load_json(Path("data/results") / f"{strategy}_{symbol}_{timeframe}_regime_trades.json")})
    st.write({"walk_forward": _load_json(Path("data/results") / f"{strategy}_{symbol}_{timeframe}_walk_forward.json")})
    st.write({"monte_carlo": _load_json(Path("data/results") / f"{strategy}_{symbol}_{timeframe}_monte_carlo.json")})
    st.write({"parameter_sensitivity": _load_json(Path("data/results") / f"{strategy}_{symbol}_{timeframe}_parameter_sensitivity.json")})
    forensic = build_forensic_view(strategy, symbol, timeframe)
    st.subheader("Forensic GO / NO-GO")
    for criterion in forensic["criteria"]:
        state = "PASS" if criterion.get("passed") else "FAIL"
        if str(criterion.get("reason_code", "")).startswith("WAIVED"):
            state = "WAIVED"
        status_pill(st, str(criterion.get("name")), state)
        st.caption(str(criterion.get("message", "")))
    st.write(
        {
            "session_filter": forensic["session_filter"],
            "sessions_with_most_signals": forensic["sessions_with_most_signals"],
            "atr_gate_block_rate": forensic["atr_gate_block_rate"],
            "ema_slope_block_rate": forensic["ema_slope_block_rate"],
        }
    )
    st.write({"obsidian_note": str(Path("obsidian/10_Strategies"))})
    st.write({"mt5_export_history": [str(path) for path in Path("exports/mt5").glob("*")]})


def build_forensic_view(strategy: str, symbol: str, timeframe: str) -> dict[str, object]:
    metrics = _load_json(Path("data/results") / f"{strategy}_{symbol}_{timeframe}_metrics.json")
    wf = _load_json(Path("data/results") / f"{strategy}_{symbol}_{timeframe}_walk_forward.json")
    mc = _load_json(Path("data/results") / f"{strategy}_{symbol}_{timeframe}_monte_carlo.json")
    ps = _load_json(Path("data/results") / f"{strategy}_{symbol}_{timeframe}_parameter_sensitivity.json")
    cost = _load_json(Path("data/results") / f"{strategy}_{symbol}_{timeframe}_cost_analysis.json")
    verdict = str(metrics.get("verdict", "REVIEW"))
    if "verdict" not in metrics:
        from tar_system.scoring.scorer import score_strategy

        verdict = score_strategy(metrics).verdict
    gate = evaluate_go_no_go(
        verdict,
        metrics,
        bool(wf),
        mc or None,
        ps or None,
        "SAFE_TO_TEST",
        realistic_score=float(cost.get("realistic_score", 1.0)) if cost else 1.0,
        cost_sensitive=bool(cost.get("cost_sensitive", False)),
    )
    variant = default_variant(strategy, symbol, timeframe)
    audit_lines = _audit_lines(strategy, symbol, timeframe)
    signal_lines = [line for line in audit_lines if "SIGNAL_" in line or "signal" in line.lower()]
    return {
        "criteria": [criterion.__dict__ for criterion in gate.criteria if criterion.name.startswith("C")],
        "session_filter": bool(variant.parameters.get("session_filter", True)),
        "sessions_with_most_signals": _count_keywords(signal_lines, ["ASIAN", "LONDON", "OVERLAP", "NEW_YORK", "OFF"]),
        "atr_gate_block_rate": _block_rate(audit_lines, ["ATR_TOO_LOW_COMPRESSION", "ATR_TOO_HIGH_EXTREME_VOLATILITY"]),
        "ema_slope_block_rate": _block_rate(audit_lines, ["EMA_SLOPE_TOO_FLAT"]),
    }


def _load_json(path: Path) -> dict[str, object] | list[object]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _audit_lines(strategy: str, symbol: str, timeframe: str) -> list[str]:
    path = Path("logs/audit/audit.jsonl")
    if not path.exists():
        return []
    return [line for line in path.read_text(encoding="utf-8").splitlines() if strategy in line and symbol in line and timeframe in line]


def _count_keywords(lines: list[str], keywords: list[str]) -> dict[str, int]:
    return {keyword: sum(1 for line in lines if keyword in line) for keyword in keywords}


def _block_rate(lines: list[str], reason_codes: list[str]) -> float:
    if not lines:
        return 0.0
    blocked = sum(1 for line in lines if any(code in line for code in reason_codes))
    return round(blocked / len(lines), 4)


if __name__ == "__main__":
    import streamlit as st

    from tar_system.dashboard.components.layout import apply_theme

    st.set_page_config(page_title="TAR V2 Strategy Detail", layout="wide")
    apply_theme(st)
    render(st)
