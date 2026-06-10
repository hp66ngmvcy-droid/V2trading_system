"""Paper signal dashboard page."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from tar_system.dashboard.components.layout import metric_row, page_header, status_pill

LATEST_SIGNAL_PATH = Path("runtime") / "latest_paper_signal.json"
SIGNAL_LOG_PATH = Path("runtime") / "paper_signal_alerts.jsonl"
HEALTH_PATH = Path("runtime") / "strategy_health_status.json"


def render(st: object) -> None:
    page_header(st, "Paper Signals", "Latest paper-only signal, risk decision, strategy health and quant report controls.")
    strategy = st.selectbox("Strategy", ["liquidity_sweep_v1", "gold_v2", "rsi_reversion_v1", "atr_breakout_v3", "momentum_crossover_v3"], index=0)
    cols = st.columns(4)
    symbol = cols[0].selectbox("Symbol", ["XAUUSD", "EURUSD", "BTCUSD", "GBPUSD", "AUDUSD"], index=0)
    timeframe = cols[1].selectbox("Timeframe", ["M5", "M15", "M30", "H1"], index=1)
    broker = cols[2].selectbox("Broker", ["current_broker_demo"], index=0)
    sizing_model = cols[3].selectbox("Sizing", ["ATR_BASED", "FIXED_RISK_PCT", "FIXED_LOT", "HALF_KELLY"], index=0)

    action_cols = st.columns(3)
    if action_cols[0].button("Queue Paper Signal", type="primary"):
        from tar_system.controller.job_queue import add_job

        job = add_job(
            strategy,
            symbol,
            timeframe,
            f"data/raw/{symbol}_{timeframe}.csv",
            broker,
            job_type="paper_signal",
            priority=5,
            research_stage="paper_signal",
            skip_walk_forward=True,
            skip_forward_test=True,
            require_walk_forward=False,
            require_min_trades=False,
            no_live=True,
            no_mt5_promotion=True,
        )
        st.success(f"Queued paper signal job {job['job_id']}.")
    if action_cols[1].button("Refresh Health"):
        from tar_system.controller.strategy_health_monitor import evaluate_strategy_health

        result = evaluate_strategy_health(strategy, symbol, timeframe)
        st.info(f"Health: {result.status}")
    if action_cols[2].button("Generate Quant Report"):
        from tar_system.controller.strategy_health_monitor import read_strategy_health
        from tar_system.reporting.reporter import generate_quant_report

        signal = _read_json(LATEST_SIGNAL_PATH)
        health = read_strategy_health(strategy, symbol, timeframe)
        metrics = _read_json(Path("data/results") / f"{strategy}_{symbol}_{timeframe}_metrics.json")
        path = generate_quant_report(strategy, symbol, timeframe, metrics, signal=signal, health=asdict(health) if health else {})
        st.success(f"Report generated: {path}")

    signal = _read_json(LATEST_SIGNAL_PATH)
    health = _read_health(strategy, symbol, timeframe)
    _render_signal_summary(st, signal, health)
    st.subheader("Latest Paper Signal")
    st.json(signal if signal else {"status": "No signal generated yet"})
    st.subheader("Recent Signal Log")
    recent = _read_recent_signal_rows(strategy, symbol, timeframe, 20)
    if recent:
        st.dataframe(recent, use_container_width=True)
    else:
        st.write("No recent paper signal rows for this selection.")


def _render_signal_summary(st: object, signal: dict[str, Any], health: dict[str, Any]) -> None:
    status_pill(st, "Health", str(health.get("status", "UNKNOWN")))
    status_pill(st, "Risk", str(signal.get("risk_reason", "UNKNOWN")))
    metric_row(
        st,
        [
            ("Side", signal.get("side", "N/A"), None),
            ("Confidence", signal.get("confidence", "N/A"), None),
            ("Entry", signal.get("entry", "N/A"), None),
            ("Alert Ready", signal.get("alert_ready", False), None),
        ],
    )
    metric_row(
        st,
        [
            ("Stop Loss", signal.get("stop_loss", "N/A"), None),
            ("Take Profit", signal.get("take_profit", "N/A"), None),
            ("Regime", signal.get("regime", "N/A"), None),
            ("Environment", signal.get("environment_state", "N/A"), None),
        ],
    )


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _read_health(strategy: str, symbol: str, timeframe: str) -> dict[str, Any]:
    payload = _read_json(HEALTH_PATH)
    return dict(payload.get(f"{strategy}:{symbol.upper()}:{timeframe.upper()}", {}))


def _read_recent_signal_rows(strategy: str, symbol: str, timeframe: str, limit: int) -> list[dict[str, Any]]:
    if not SIGNAL_LOG_PATH.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in SIGNAL_LOG_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if row.get("strategy") == strategy and row.get("symbol") == symbol and row.get("timeframe") == timeframe:
            rows.append(row)
    return rows[-limit:]
