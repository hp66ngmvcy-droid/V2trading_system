"""Manual EA promotion board for MT5 review decisions."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tar_system.audit.writer import append_audit_event
from tar_system.dashboard.components.layout import page_header, status_pill
from tar_system.dashboard.runtime_control import append_mt5_promotion_log
from tar_system.memory.strategy_memory import latest_memory_record, update_latest_verdict
from tar_system.optimisation.go_no_go_gate import evaluate_go_no_go
from tar_system.scoring.scorer import score_strategy
from tar_system.strategies.asset_variants import default_variant


BOARD_COLUMNS = ["TESTING", "REVIEW", "READY FOR MT5", "PROMOTED", "KILLED"]


@dataclass(frozen=True)
class PromotionCard:
    strategy: str
    symbol: str
    timeframe: str
    score: float
    verdict: str
    last_tested_date: str
    walk_forward_pass: bool
    monte_carlo_pass: bool
    parameter_stability: str
    cost_sensitive: bool
    swap_drag: float
    realistic_score: float
    gross_score: float
    session_filter: bool
    go_no_go: dict[str, Any]
    column: str


def load_promotion_cards() -> list[PromotionCard]:
    cards: list[PromotionCard] = []
    for path in sorted(Path("data/results").glob("*_*_*_metrics.json")):
        parsed = parse_metrics_filename(path)
        if parsed is None:
            continue
        strategy, symbol, timeframe = parsed
        metrics = _load_json(path)
        score = score_strategy(metrics)
        memory = latest_memory_record(strategy, symbol, timeframe) or {}
        verdict = str(memory.get("verdict") or score.verdict)
        if verdict == "KILLED":
            verdict = "KILL"
        wf = _load_json(Path("data/results") / f"{strategy}_{symbol}_{timeframe}_walk_forward.json")
        mc = _load_json(Path("data/results") / f"{strategy}_{symbol}_{timeframe}_monte_carlo.json")
        ps = _load_json(Path("data/results") / f"{strategy}_{symbol}_{timeframe}_parameter_sensitivity.json")
        cost = _load_json(Path("data/results") / f"{strategy}_{symbol}_{timeframe}_cost_analysis.json")
        variant = default_variant(strategy, symbol, timeframe)
        go_no_go = evaluate_go_no_go(
            verdict,
            metrics,
            bool(wf),
            mc or None,
            ps or None,
            "SAFE_TO_TEST",
            realistic_score=float(cost.get("realistic_score", 1.0)) if cost else 1.0,
            cost_sensitive=bool(cost.get("cost_sensitive", False)),
        )
        walk_forward_pass = bool(wf) and bool(wf.get("parameter_stability_score", 0) >= 60)
        monte_carlo_pass = bool(mc) and float(mc.get("robustness_score", 0.0)) >= 60.0
        cost_sensitive = bool(cost.get("cost_sensitive", False))
        cards.append(
            PromotionCard(
                strategy=strategy,
                symbol=symbol,
                timeframe=timeframe,
                score=score.score,
                verdict=verdict,
                last_tested_date=_mtime(path),
                walk_forward_pass=walk_forward_pass,
                monte_carlo_pass=monte_carlo_pass,
                parameter_stability=str(ps.get("stability_score", wf.get("parameter_stability_score", "missing"))),
                cost_sensitive=cost_sensitive,
                swap_drag=float(cost.get("swap_drag", 0.0)),
                realistic_score=float(cost.get("realistic_score", 0.0)),
                gross_score=float(cost.get("gross_score", 0.0)),
                session_filter=bool(variant.parameters.get("session_filter", True)),
                go_no_go={"status": go_no_go.status, "passed": go_no_go.passed, "criteria": [criterion.__dict__ for criterion in go_no_go.criteria]},
                column=_column_for(verdict, go_no_go.passed, walk_forward_pass, monte_carlo_pass, cost_sensitive),
            )
        )
    return cards


def green_light_ready_for_mt5(card: PromotionCard, checklist_confirmed: bool = False) -> Path:
    if not checklist_confirmed:
        raise ValueError("Manual checklist must be confirmed before MT5 review green-light")
    if not is_green_light_enabled(card):
        raise ValueError("Strategy does not meet MT5 review green-light criteria")
    path = append_mt5_promotion_log(card.__dict__ | {"action": "READY_FOR_MT5_REVIEW"})
    append_audit_event("promotion_board", card.strategy, card.symbol, card.timeframe, "READY_FOR_MT5_REVIEW", "MANUAL_REVIEW_ONLY", card.__dict__)
    return path


def is_green_light_enabled(card: PromotionCard) -> bool:
    return (
        card.verdict == "KEEP"
        and card.walk_forward_pass
        and card.monte_carlo_pass
        and not card.cost_sensitive
        and bool(card.go_no_go.get("passed"))
    )


def kill_strategy(card: PromotionCard) -> bool:
    updated = update_latest_verdict(card.strategy, card.symbol, card.timeframe, "KILLED", "Killed from dashboard promotion board")
    append_audit_event("promotion_board", card.strategy, card.symbol, card.timeframe, "KILLED", "KILL_STRATEGY", card.__dict__)
    return updated


def send_to_retest(card: PromotionCard) -> Path:
    path = append_mt5_promotion_log(card.__dict__ | {"action": "RETEST", "status": "REVIEW_ONLY"})
    append_audit_event("promotion_board", card.strategy, card.symbol, card.timeframe, "RETEST", "REVIEW_ONLY", card.__dict__)
    return path


def render(st: object) -> None:
    page_header(st, "EA Promotion Board", "Manual paper-only promotion decisions before MT5 review.")
    cards = load_promotion_cards()
    columns = st.columns(len(BOARD_COLUMNS))
    for column, name in zip(columns, BOARD_COLUMNS):
        with column:
            st.subheader(name)
            for card in [item for item in cards if item.column == name]:
                _render_card(st, card)


def _render_card(st: object, card: PromotionCard) -> None:
    st.markdown(f"**{card.strategy}**  \n{card.symbol} {card.timeframe}")
    status_pill(st, "Verdict", card.verdict)
    st.write(
        {
            "score": card.score,
            "last_tested": card.last_tested_date,
            "walk_forward": "PASS" if card.walk_forward_pass else "FAIL",
            "monte_carlo": "PASS" if card.monte_carlo_pass else "FAIL",
            "parameter_stability": card.parameter_stability,
            "cost_sensitive": card.cost_sensitive,
            "swap_drag_pct": card.swap_drag,
            "realistic_vs_gross": f"{card.realistic_score}/{card.gross_score}",
            "session_filter": "on" if card.session_filter else "off",
            "go_no_go": card.go_no_go.get("status"),
        }
    )
    if card.cost_sensitive:
        st.warning("AMBER: cost sensitive")
    if not card.session_filter and card.symbol.upper() not in {"BTCUSD", "ETHUSD", "XRPUSD"}:
        st.warning("AMBER: session filter off on non-crypto asset")
    checklist = st.checkbox(
        f"Manual checklist confirmed: {card.strategy} {card.symbol} {card.timeframe}",
        key=f"tar_promotion_checklist_{card.strategy}_{card.symbol}_{card.timeframe}",
    )
    if st.button(f"Green Light: Ready for MT5 Review {card.strategy} {card.symbol}", disabled=not is_green_light_enabled(card)):
        green_light_ready_for_mt5(card, checklist)
        st.success("Green-light logged for manual MT5 review. No files exported and no trades placed.")
    if st.button(f"Send to Retest {card.strategy} {card.symbol}"):
        send_to_retest(card)
        st.warning("Sent to retest.")
    if st.button(f"Kill Strategy {card.strategy} {card.symbol}"):
        kill_strategy(card)
        st.error("Strategy marked killed.")
    st.divider()


def _column_for(verdict: str, go_passed: bool, walk_forward_pass: bool, monte_carlo_pass: bool, cost_sensitive: bool) -> str:
    if verdict == "KILL":
        return "KILLED"
    if verdict == "KEEP" and go_passed and walk_forward_pass and monte_carlo_pass and not cost_sensitive:
        return "READY FOR MT5"
    if verdict == "REVIEW":
        return "REVIEW"
    return "TESTING"


def parse_metrics_filename(path: Path) -> tuple[str, str, str] | None:
    stem = path.stem
    suffix = "_metrics"
    if not stem.endswith(suffix):
        return None
    core = stem[: -len(suffix)]
    parts = core.split("_")
    if len(parts) < 3:
        return None
    strategy = "_".join(parts[:-2])
    symbol = parts[-2]
    timeframe = parts[-1]
    if not strategy or not symbol or not timeframe:
        return None
    return strategy, symbol, timeframe


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _mtime(path: Path) -> str:
    from datetime import datetime

    return datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds")
