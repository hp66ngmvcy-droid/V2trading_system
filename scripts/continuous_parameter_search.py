#!/usr/bin/env python3
"""Continuous local parameter search for paper strategies.

The normal research queue is good for strategy/symbol/timeframe jobs, but it
does not carry a full parameter set per candidate. This runner keeps a local
candidate queue with explicit parameters, tests each candidate, scores it, and
mutates the best survivors into the next round.

Everything is local and paper-only: feature parquet files, backtest engine,
JSONL candidate queue, and JSON reports.
"""

from __future__ import annotations

import argparse
import hashlib
import inspect
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tar_system.backtest.engine import run_backtest
from tar_system.data.store import load_feature_data
from tar_system.scoring.failure_logger import log_failure
from tar_system.scoring.gates import run_gates
from tar_system.scoring.scorer import score_strategy
from tar_system.strategies.asset_variants import asset_seed_overrides
from tar_system.strategies.registry import get_strategy
from tar_system.validation.walk_forward import run_walk_forward

QUEUE_PATH = Path("runtime") / "optimizer_candidate_queue.jsonl"
TESTED_DATA_REGISTRY_PATH = Path("runtime") / "tested_data_registry.json"
RESULTS_DIR = Path("data/results/parameter_search")

DEFAULT_STRATEGIES = [
    "gold_v2",
    "rsi_reversion_v1",
    "rsi_only_v3",
    "ema_volume_v3",
    "atr_breakout_v3",
    "momentum_crossover_v3",
    "multi_timeframe_v3",
    "liquidity_sweep_v1",
]


@dataclass(frozen=True)
class Candidate:
    candidate_id: str
    parent_id: str | None
    generation: int
    strategy: str
    symbol: str
    timeframe: str
    parameters: dict[str, Any]
    status: str = "QUEUED"
    score: float | None = None
    verdict: str | None = None
    metrics: dict[str, float] | None = None
    reason_codes: list[str] | None = None
    created_at: str = ""
    tested_at: str | None = None


def main() -> int:
    parser = argparse.ArgumentParser(description="Keep testing parameter ideas until KEEP candidates are found.")
    parser.add_argument("--symbols", default="XAUUSD,EURUSD,GBPUSD,AUDUSD,USDCAD,USDJPY,USOUSD,BTCUSD")
    parser.add_argument("--timeframes", default="M15")
    parser.add_argument("--strategies", default=",".join(DEFAULT_STRATEGIES))
    parser.add_argument("--max-generations", type=int, default=4)
    parser.add_argument("--max-candidates", type=int, default=300)
    parser.add_argument("--max-rows", type=int, default=20000)
    parser.add_argument("--survivors", type=int, default=5)
    parser.add_argument("--target-keeps", type=int, default=3)
    parser.add_argument("--min-score-to-mutate", type=float, default=35.0)
    parser.add_argument("--min-trades-for-keep", type=int, default=30)
    parser.add_argument("--min-profit-factor-for-keep", type=float, default=1.4)
    parser.add_argument("--max-drawdown-for-keep", type=float, default=0.2)
    parser.add_argument("--wf-train-months", type=int, default=12)
    parser.add_argument("--wf-test-months", type=int, default=3)
    parser.add_argument("--max-walk-forward-splits", type=int, default=12)
    parser.add_argument("--reset", action="store_true", help="Start a fresh optimiser candidate queue.")
    parser.add_argument("--fresh", action="store_true", help="Clear optimiser queue and tested-data registry before seeding.")
    parser.add_argument("--preflight-rows", type=int, default=500, help="Rows to sample before running a full candidate test.")
    args = parser.parse_args()

    if args.reset or args.fresh:
        reset_runtime_state(clear_tested_registry=args.fresh)

    candidates = load_candidates()
    if not candidates:
        candidates = seed_candidates(_split(args.strategies), _split(args.symbols), _split(args.timeframes))
        save_candidates(candidates)

    tested = 0
    for generation in range(args.max_generations + 1):
        queued = [candidate for candidate in candidates if candidate.status == "QUEUED" and candidate.generation == generation]
        for candidate in queued:
            if tested >= args.max_candidates:
                break
            candidate = test_candidate(
                candidate,
                args.max_rows,
                min_trades_for_keep=args.min_trades_for_keep,
                min_profit_factor_for_keep=args.min_profit_factor_for_keep,
                max_drawdown_for_keep=args.max_drawdown_for_keep,
                wf_train_months=args.wf_train_months,
                wf_test_months=args.wf_test_months,
                max_walk_forward_splits=args.max_walk_forward_splits,
                preflight_rows=args.preflight_rows,
            )
            candidates = replace_candidate(candidates, candidate)
            tested += 1
            save_candidates(candidates)
            keeps = [item for item in candidates if item.verdict == "KEEP"]
            if len(keeps) >= args.target_keeps:
                write_summary(candidates, stopped_reason="target_keeps_reached")
                print_summary(candidates, tested, "target_keeps_reached")
                return 0
        if tested >= args.max_candidates:
            break
        if generation < args.max_generations:
            new_candidates = next_generation(candidates, generation, args.survivors, args.min_score_to_mutate)
            if not new_candidates:
                break
            existing_ids = {candidate.candidate_id for candidate in candidates}
            candidates.extend([candidate for candidate in new_candidates if candidate.candidate_id not in existing_ids])
            save_candidates(candidates)

    write_summary(candidates, stopped_reason="search_exhausted_or_limited")
    print_summary(candidates, tested, "search_exhausted_or_limited")
    return 0


def seed_candidates(strategies: list[str], symbols: list[str], timeframes: list[str]) -> list[Candidate]:
    now = _now()
    candidates: list[Candidate] = []
    for strategy in strategies:
        base = default_parameters(strategy)
        for symbol in symbols:
            for timeframe in timeframes:
                overrides = asset_seed_overrides(strategy, symbol, timeframe)
                dropped = [k for k in overrides if k not in base]
                if dropped:
                    print(f"[WARN] seed_candidates: {strategy}/{symbol} override keys not in defaults (ignored): {dropped}")
                parameters = {**base, **{k: v for k, v in overrides.items() if k in base}}
                candidates.append(make_candidate(strategy, symbol, timeframe, parameters, generation=0, parent_id=None, created_at=now))
    return candidates


def test_candidate(
    candidate: Candidate,
    max_rows: int,
    min_trades_for_keep: int,
    min_profit_factor_for_keep: float,
    max_drawdown_for_keep: float,
    wf_train_months: int,
    wf_test_months: int,
    max_walk_forward_splits: int,
    preflight_rows: int,
) -> Candidate:
    try:
        features = load_feature_data(candidate.symbol, candidate.timeframe).sort_values("timestamp")
        if max_rows > 0 and len(features) > max_rows:
            features = features.tail(max_rows).copy()
        strategy = get_strategy(candidate.strategy, **candidate.parameters)
        preflight = preflight_candidate(candidate, features, strategy, preflight_rows)
        if preflight["skip"]:
            print(f"SKIPPED: {candidate.strategy} {candidate.symbol} {candidate.timeframe} — {preflight['reason']}")
            return Candidate(
                **{
                    **asdict(candidate),
                    "status": "SKIPPED",
                    "score": 0.0,
                    "verdict": "REVIEW",
                    "metrics": {
                        "total_trades": float(preflight["trades"]),
                        "preflight_rows": float(preflight["rows"]),
                        "preflight_full_rows": float(preflight["full_rows"]),
                    },
                    "reason_codes": ["PREFLIGHT_NO_TRADES"],
                    "tested_at": _now(),
                }
            )
        result = run_backtest(features, strategy, audit_decisions=False)
        score = score_strategy(result.metrics)
        early_gate = run_gates(
            result.metrics,
            candidate.timeframe,
            min_trades=min_trades_for_keep,
            min_profit_factor=min_profit_factor_for_keep,
            max_drawdown=max_drawdown_for_keep,
            require_oos=False,
        )
        if early_gate.verdict == "KILL":
            gate = early_gate
            walk_forward_payload: dict[str, Any] = {"status": "SKIPPED", "reason": "EARLY_HARD_GATE_FAILED"}
            combined_metrics = dict(result.metrics)
        else:
            walk_forward_payload = _run_candidate_walk_forward(
                features,
                candidate,
                wf_train_months=wf_train_months,
                wf_test_months=wf_test_months,
                max_splits=max_walk_forward_splits,
            )
            combined_metrics = _merge_walk_forward_metrics(result.metrics, walk_forward_payload)
            gate = run_gates(
                combined_metrics,
                candidate.timeframe,
                min_trades=min_trades_for_keep,
                min_profit_factor=min_profit_factor_for_keep,
                max_drawdown=max_drawdown_for_keep,
                require_oos=True,
            )
        reasons = _merge_reason_codes(score.reason_codes, gate.reason_codes)
        metrics = {
            **combined_metrics,
            "gate_failed": gate.failed_gate or "",
            "gate_reason": gate.reason,
            "walk_forward_status": str(walk_forward_payload.get("status", "UNKNOWN")),
            "walk_forward_splits": float(walk_forward_payload.get("split_count", 0) or 0),
        }
        status = "COMPLETED"
        evaluated = Candidate(
            **{
                **asdict(candidate),
                "status": status,
                "score": score.score,
                "verdict": gate.verdict,
                "metrics": metrics,
                "reason_codes": reasons,
                "tested_at": _now(),
            }
        )
        log_failure(evaluated, gate)
        return evaluated
    except Exception as exc:
        return Candidate(
            **{
                **asdict(candidate),
                "status": "FAILED",
                "score": 0.0,
                "verdict": "KILL",
                "metrics": {"error": str(exc)},
                "reason_codes": ["TEST_FAILED"],
                "tested_at": _now(),
            }
        )


def next_generation(candidates: list[Candidate], generation: int, survivors: int, min_score: float) -> list[Candidate]:
    by_id = {candidate.candidate_id: candidate for candidate in candidates}
    completed = [
        candidate
        for candidate in candidates
        if candidate.generation == generation and candidate.status == "COMPLETED"
    ]
    tested = [c for c in completed if float(c.score or 0.0) >= min_score]
    if not tested:
        # No candidates met the threshold — fall back to best available non-KILL
        # candidates so mutations still happen rather than terminating early.
        tested = [c for c in completed if c.verdict != "KILL"] or completed
    tested.sort(key=lambda item: float(item.score or 0.0), reverse=True)
    children: list[Candidate] = []
    for parent in tested[:survivors]:
        hints = _compute_direction_hints(parent, by_id)
        for parameters in mutate_parameters(parent.parameters, hints):
            children.append(
                make_candidate(
                    parent.strategy,
                    parent.symbol,
                    parent.timeframe,
                    parameters,
                    generation=parent.generation + 1,
                    parent_id=parent.candidate_id,
                    created_at=_now(),
                )
            )
    return children


def _compute_direction_hints(candidate: Candidate, by_id: dict[str, Candidate]) -> dict[str, float]:
    """Return per-parameter direction (+1 keep going, -1 reverse) by comparing score to parent."""
    if not candidate.parent_id:
        return {}
    parent = by_id.get(candidate.parent_id)
    if parent is None:
        return {}
    score_delta = float(candidate.score or 0.0) - float(parent.score or 0.0)
    if score_delta == 0:
        return {}  # no signal — don't add momentum in either direction
    hints: dict[str, float] = {}
    for key in candidate.parameters:
        if key not in parent.parameters:
            continue
        try:
            delta = float(candidate.parameters[key]) - float(parent.parameters[key])
        except (TypeError, ValueError):
            continue
        if delta == 0:
            continue
        hints[key] = 1.0 if score_delta > 0 else -1.0
    return hints


def robust_verdict(
    verdict: str,
    reason_codes: list[str],
    metrics: dict[str, float],
    min_trades: int,
    min_profit_factor: float,
    max_drawdown: float,
) -> tuple[str, list[str]]:
    reasons = list(reason_codes)
    trades = float(metrics.get("total_trades", 0.0) or 0.0)
    profit_factor = float(metrics.get("profit_factor", 0.0) or 0.0)
    drawdown = float(metrics.get("max_drawdown", 1.0) or 1.0)
    if trades < min_trades:
        if "SEARCH_MIN_TRADES_NOT_MET" not in reasons:
            reasons.append("SEARCH_MIN_TRADES_NOT_MET")
        return ("REVIEW" if verdict == "KEEP" else verdict, reasons)
    if profit_factor < min_profit_factor:
        if "SEARCH_PROFIT_FACTOR_NOT_MET" not in reasons:
            reasons.append("SEARCH_PROFIT_FACTOR_NOT_MET")
        return ("REVIEW" if verdict == "KEEP" else verdict, reasons)
    if drawdown > max_drawdown:
        if "SEARCH_DRAWDOWN_TOO_HIGH" not in reasons:
            reasons.append("SEARCH_DRAWDOWN_TOO_HIGH")
        return ("REVIEW" if verdict == "KEEP" else verdict, reasons)
    return verdict, reasons


def _merge_reason_codes(*groups: list[str]) -> list[str]:
    merged: list[str] = []
    for group in groups:
        for code in group:
            if code not in merged:
                merged.append(code)
    return merged


def reset_runtime_state(clear_tested_registry: bool = False) -> None:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    _backup_and_unlink(QUEUE_PATH, timestamp)
    if clear_tested_registry:
        _backup_and_unlink(TESTED_DATA_REGISTRY_PATH, timestamp)


def _backup_and_unlink(path: Path, timestamp: str) -> None:
    if not path.exists():
        return
    backup = path.with_suffix(f".{timestamp}.bak")
    backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    path.unlink()


def preflight_candidate(candidate: Candidate, features: Any, strategy: Any, rows: int = 500) -> dict[str, Any]:
    if rows <= 0:
        return {"skip": False, "trades": -1, "rows": 0, "full_rows": len(features), "reason": "disabled"}
    sample = features.head(min(rows, len(features))).copy()
    if sample.empty:
        return {"skip": True, "trades": 0, "rows": 0, "full_rows": len(features), "reason": "empty feature sample"}
    result = run_backtest(sample, strategy, audit_decisions=False)
    if result.trades == 0:
        return {
            "skip": True,
            "trades": 0,
            "rows": len(sample),
            "full_rows": len(features),
            "reason": f"0 trades in {len(sample)} row sample, likely filter issue",
        }
    return {"skip": False, "trades": result.trades, "rows": len(sample), "full_rows": len(features), "reason": ""}


def _run_candidate_walk_forward(
    features: Any,
    candidate: Candidate,
    wf_train_months: int,
    wf_test_months: int,
    max_splits: int,
) -> dict[str, Any]:
    train_window = _months_to_bars(candidate.timeframe, wf_train_months)
    test_window = _months_to_bars(candidate.timeframe, wf_test_months)
    if len(features) < train_window + test_window:
        return {
            "status": "INSUFFICIENT_DATA",
            "reason": f"Need {train_window + test_window} rows, found {len(features)}",
            "split_count": 0,
        }
    strategy = get_strategy(candidate.strategy, **candidate.parameters)
    result = run_walk_forward(
        features,
        strategy,
        train_window=train_window,
        test_window=test_window,
        audit_decisions=False,
        max_splits=max_splits,
    )
    return {
        "status": "COMPLETED" if not result.stopped else "STOPPED",
        "split_count": len(result.splits),
        "stitched_metrics": result.stitched_metrics,
        "parameter_stability_score": result.parameter_stability_score,
        "parameter_stability": result.parameter_stability,
        "reason": result.reason_code or "",
    }


def _merge_walk_forward_metrics(metrics: dict[str, float], walk_forward: dict[str, Any]) -> dict[str, float]:
    combined = dict(metrics)
    stitched = walk_forward.get("stitched_metrics") or {}
    combined["sharpe_oos"] = float(stitched.get("sharpe_ratio", 0.0) or 0.0)
    combined["param_stability"] = float(walk_forward.get("parameter_stability_score", 0.0) or 0.0) / 100.0
    combined["walk_forward_oos_trades"] = float(stitched.get("total_trades", 0.0) or 0.0)
    return combined


def _months_to_bars(timeframe: str, months: int) -> int:
    bars_per_day = {
        "M1": 24 * 60,
        "M5": 24 * 12,
        "M15": 24 * 4,
        "M30": 24 * 2,
        "H1": 24,
        "H4": 6,
        "D1": 1,
    }.get(timeframe.upper(), 96)
    return max(1, months * 21 * bars_per_day)


def mutate_parameters(parameters: dict[str, Any], direction_hints: dict[str, float] | None = None) -> list[dict[str, Any]]:
    hints = direction_hints or {}
    variants: list[dict[str, Any]] = []
    for key, value in parameters.items():
        if isinstance(value, bool):
            mutated = dict(parameters)
            mutated[key] = not value
            variants.append(mutated)
            continue
        if not isinstance(value, (int, float)):
            continue
        steps = parameter_steps(key, value)
        direction = hints.get(key, 0.0)
        if direction != 0.0:
            # Add a momentum step (2x) in the winning direction alongside normal variants.
            step_size = steps[1] - value  # always positive
            raw_momentum = value + direction * step_size * 2
            if isinstance(value, int):
                momentum = max(1, int(round(raw_momentum)))
            elif "rsi" in key or key in {"oversold", "overbought", "rsi_buy", "rsi_sell", "rsi_buy_level", "rsi_sell_level"}:
                momentum = round(max(1.0, min(99.0, raw_momentum)), 4)
            elif "wick" in key or "confidence" in key:
                momentum = round(max(0.05, min(0.95, raw_momentum)), 4)
            else:
                momentum = round(max(0.05, raw_momentum), 4)
            for changed in [*steps, momentum]:
                mutated = dict(parameters)
                mutated[key] = changed
                variants.append(mutated)
        else:
            for changed in steps:
                mutated = dict(parameters)
                mutated[key] = changed
                variants.append(mutated)
    return variants


def parameter_steps(key: str, value: int | float) -> list[int | float]:
    if isinstance(value, int):
        step = max(1, int(round(abs(value) * 0.2)))
        return [max(1, value - step), value + step]
    if "rsi" in key or key in {"oversold", "overbought", "rsi_buy", "rsi_sell", "rsi_buy_level", "rsi_sell_level"}:
        return [round(max(1.0, value - 5.0), 4), round(min(99.0, value + 5.0), 4)]
    if "wick" in key or "confidence" in key:
        return [round(max(0.05, value - 0.05), 4), round(min(0.95, value + 0.05), 4)]
    step = max(abs(float(value)) * 0.2, 0.1)
    return [round(max(0.05, value - step), 4), round(value + step, 4)]


def default_parameters(strategy: str) -> dict[str, Any]:
    instance = get_strategy(strategy)
    signature = inspect.signature(instance.__class__)
    parameters: dict[str, Any] = {}
    for name, param in signature.parameters.items():
        if name in {"name", "version"} or param.default is inspect.Parameter.empty:
            continue
        if isinstance(param.default, (int, float, bool)) and not isinstance(param.default, str):
            parameters[name] = param.default
    return parameters


def make_candidate(
    strategy: str,
    symbol: str,
    timeframe: str,
    parameters: dict[str, Any],
    generation: int,
    parent_id: str | None,
    created_at: str,
) -> Candidate:
    payload = json.dumps(
        {
            "strategy": strategy,
            "symbol": symbol.upper(),
            "timeframe": timeframe.upper(),
            "parameters": parameters,
            "generation": generation,
            "parent_id": parent_id,
        },
        sort_keys=True,
        default=str,
    )
    candidate_id = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return Candidate(candidate_id, parent_id, generation, strategy, symbol.upper(), timeframe.upper(), parameters, created_at=created_at)


def load_candidates() -> list[Candidate]:
    if not QUEUE_PATH.exists():
        return []
    candidates: list[Candidate] = []
    for line in QUEUE_PATH.read_text(encoding="utf-8").splitlines():
        if line.strip():
            candidates.append(Candidate(**json.loads(line)))
    return candidates


def save_candidates(candidates: list[Candidate]) -> None:
    QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    QUEUE_PATH.write_text("\n".join(json.dumps(asdict(candidate), default=str) for candidate in candidates) + "\n", encoding="utf-8")


def replace_candidate(candidates: list[Candidate], replacement: Candidate) -> list[Candidate]:
    return [replacement if candidate.candidate_id == replacement.candidate_id else candidate for candidate in candidates]


def write_summary(candidates: list[Candidate], stopped_reason: str) -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    ranked = sorted(candidates, key=lambda item: float(item.score or -1.0), reverse=True)
    path = RESULTS_DIR / "continuous_parameter_search_summary.json"
    path.write_text(
        json.dumps(
            {
                "created_at": _now(),
                "stopped_reason": stopped_reason,
                "candidate_count": len(candidates),
                "status_counts": _counts(candidate.status for candidate in candidates),
                "verdict_counts": _counts(candidate.verdict or "UNTESTED" for candidate in candidates),
                "top_candidates": [asdict(candidate) for candidate in ranked[:25]],
            },
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )
    return path


def print_summary(candidates: list[Candidate], tested: int, stopped_reason: str) -> None:
    ranked = sorted(candidates, key=lambda item: float(item.score or -1.0), reverse=True)
    print(
        json.dumps(
            {
                "tested_this_run": tested,
                "stopped_reason": stopped_reason,
                "status_counts": _counts(candidate.status for candidate in candidates),
                "verdict_counts": _counts(candidate.verdict or "UNTESTED" for candidate in candidates),
                "summary_path": str(RESULTS_DIR / "continuous_parameter_search_summary.json"),
                "top_candidates": [asdict(candidate) for candidate in ranked[:10]],
            },
            indent=2,
            default=str,
        )
    )


def _counts(values: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        counts[str(value)] = counts.get(str(value), 0) + 1
    return counts


def _split(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
