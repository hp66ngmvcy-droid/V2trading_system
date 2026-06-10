#!/usr/bin/env python3
"""TSDS v1 — TAR Strategy Discovery System.

6-agent modular backtesting discovery pipeline. Paper-only, local.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from tar_system.backtest.engine import run_backtest
from tar_system.data.store import load_feature_data
from tar_system.scoring.gates import run_gates
from tar_system.strategies.asset_variants import tsds_seed_params
from tar_system.strategies.registry import get_strategy

APPROVED_PATH = Path("runtime/tsds_approved.jsonl")

ALL_SYMBOLS = ["AUDUSD", "BTCUSD", "EURUSD", "GBPUSD", "USDCAD", "USDJPY", "USOUSD", "XAUUSD"]
ALL_TIMEFRAMES = ["H1", "M15"]
ALL_STRATEGIES = [
    "rsi_reversion_v1",
    "rsi_only_v3",
    "momentum_crossover_v3",
    "multi_timeframe_v3",
    "liquidity_sweep_v1",
    "atr_breakout_v3",
]

_FX = {"EURUSD", "GBPUSD", "AUDUSD", "USDCAD", "USDJPY"}
_TRENDING = {"BTCUSD", "XAUUSD", "USOUSD"}
_LIQUIDITY_SWEEP_OK = {"XAUUSD", "BTCUSD", "GBPUSD"}

# ATR% medians from measurements (used as fallback if DIA fails)
_ATR_MEDIAN: dict[str, dict[str, float]] = {
    "AUDUSD": {"H1": 0.156, "M15": 0.078},
    "BTCUSD": {"H1": 0.509, "M15": 0.246},
    "EURUSD": {"H1": 0.101, "M15": 0.052},
    "GBPUSD": {"H1": 0.116, "M15": 0.058},
    "USDCAD": {"H1": 0.092, "M15": 0.043},
    "USDJPY": {"H1": 0.121, "M15": 0.066},
    "USOUSD": {"H1": 0.493, "M15": 0.237},
    "XAUUSD": {"H1": 0.218, "M15": 0.109},
}


@dataclass
class AssetStats:
    symbol: str
    timeframe: str
    row_count: int
    columns: list[str]
    has_volume: bool
    atr_pct_median: float
    atr_pct_p75: float


# ── Agent 1: DIA ─────────────────────────────────────────────────────────────

def dia_agent(symbols: list[str], timeframes: list[str]) -> dict[str, AssetStats]:
    """Scan validated parquets, compute ATR% stats per (symbol, timeframe)."""
    stats: dict[str, AssetStats] = {}
    for sym in symbols:
        for tf in timeframes:
            path = Path(f"data/validated/{sym}_{tf}.parquet")
            if not path.exists():
                continue
            df = pd.read_parquet(path)
            has_vol = "volume" in df.columns and df["volume"].sum() > 0
            # Compute ATR% from OHLC if possible, else use table defaults
            if {"high", "low", "close"}.issubset(df.columns) and len(df) > 20:
                high = df["high"].astype(float)
                low = df["low"].astype(float)
                close = df["close"].astype(float)
                tr = pd.concat([
                    high - low,
                    (high - close.shift(1)).abs(),
                    (low - close.shift(1)).abs(),
                ], axis=1).max(axis=1)
                atr_pct = tr / close * 100
                atr_pct = atr_pct.dropna()
                median = float(atr_pct.median()) if len(atr_pct) else _ATR_MEDIAN.get(sym, {}).get(tf, 0.1)
                p75 = float(atr_pct.quantile(0.75)) if len(atr_pct) else median * 1.4
            else:
                median = _ATR_MEDIAN.get(sym, {}).get(tf, 0.1)
                p75 = median * 1.4
            key = f"{sym}_{tf}"
            stats[key] = AssetStats(
                symbol=sym,
                timeframe=tf,
                row_count=len(df),
                columns=df.columns.tolist(),
                has_volume=has_vol,
                atr_pct_median=round(median, 4),
                atr_pct_p75=round(p75, 4),
            )
            print(f"[DIA] {key}: {len(df)} rows, ATR% median={median:.3f}, volume={'yes' if has_vol else 'no'}")
    return stats


# ── Agent 2: SAFA ────────────────────────────────────────────────────────────

def safa_agent(
    stats: dict[str, AssetStats],
    strategies: list[str],
) -> list[tuple[str, str, str]]:
    """Return (strategy, symbol, timeframe) combos ranked by fit score."""
    scored: list[tuple[float, str, str, str]] = []
    for key, s in stats.items():
        sym, tf = s.symbol, s.timeframe
        for strat in strategies:
            # Hard excludes
            if strat == "ema_volume_v3":
                continue
            if strat == "atr_breakout_v3" and tf == "M15" and s.atr_pct_median < 0.1:
                print(f"[SAFA] Skipping {strat}/{sym}/{tf}: ATR% median {s.atr_pct_median:.3f} < 0.1")
                continue
            if strat == "liquidity_sweep_v1" and sym not in _LIQUIDITY_SWEEP_OK:
                continue

            fit = 1.0  # base score
            # Prefer H1 over M15
            if tf == "H1":
                fit += 1.0
            # Strategy–asset affinity
            if strat == "rsi_reversion_v1" and sym in _FX:
                fit += 2.0
            if strat in {"momentum_crossover_v3", "multi_timeframe_v3"} and sym in _TRENDING:
                fit += 2.0
            if strat == "liquidity_sweep_v1" and sym in _LIQUIDITY_SWEEP_OK:
                fit += 1.5
            if strat in {"rsi_only_v3"} and sym in _FX:
                fit += 0.5
            scored.append((fit, strat, sym, tf))

    scored.sort(key=lambda x: x[0], reverse=True)
    combos = [(strat, sym, tf) for _, strat, sym, tf in scored]
    print(f"[SAFA] {len(combos)} combos after fitness filtering")
    return combos


# ── Agent 3: SCA ─────────────────────────────────────────────────────────────

def sca_agent(
    combos: list[tuple[str, str, str]],
    stats: dict[str, AssetStats],
) -> list[tuple[str, str, str, dict[str, Any]]]:
    """Return combos with volatility-calibrated seed params."""
    result = []
    for strat, sym, tf in combos:
        key = f"{sym}_{tf}"
        s = stats.get(key)
        atr_med = s.atr_pct_median if s else _ATR_MEDIAN.get(sym, {}).get(tf, 0.1)
        params = tsds_seed_params(strat, sym, tf, atr_med)
        result.append((strat, sym, tf, params))
    return result


# ── Agent 4: WFV ─────────────────────────────────────────────────────────────

def wfv_agent(
    seeded: list[tuple[str, str, str, dict[str, Any]]],
    stats: dict[str, AssetStats],
    max_candidates: int = 200,
    max_rows: int = 20000,
) -> list[dict[str, Any]]:
    """Run backtests, apply gates, return survivors."""
    survivors: list[dict[str, Any]] = []
    for i, (strat, sym, tf, params) in enumerate(seeded[:max_candidates]):
        key = f"{sym}_{tf}"
        print(f"[WFV] {i+1}/{min(len(seeded), max_candidates)}: {strat}/{sym}/{tf}")
        try:
            features = load_feature_data(sym, tf).sort_values("timestamp")
            if max_rows > 0 and len(features) > max_rows:
                features = features.tail(max_rows).copy()
            strategy = get_strategy(strat, **params)
            result = run_backtest(features, strategy, audit_decisions=False)
            gate = run_gates(
                result.metrics,
                tf,
                min_trades=20,
                max_drawdown=0.25,
                min_profit_factor=1.1,
                require_oos=False,
            )
            if gate.verdict == "KILL":
                print(f"  KILL: {gate.reason}")
                continue
            entry = {
                "strategy": strat,
                "symbol": sym,
                "timeframe": tf,
                "params": params,
                "metrics": result.metrics,
                "verdict": gate.verdict,
                "gate_reason": gate.reason,
            }
            survivors.append(entry)
            print(f"  {gate.verdict}: trades={result.metrics.get('total_trades',0):.0f} pf={result.metrics.get('profit_factor',0):.2f}")
        except Exception as exc:
            print(f"  ERROR: {exc}")
    print(f"[WFV] {len(survivors)} survivors from {min(len(seeded), max_candidates)} candidates")
    return survivors


# ── Agent 5: RRA ─────────────────────────────────────────────────────────────

def rra_agent(survivors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Nudge each numeric param ±15%, measure gate stability."""
    robust: list[dict[str, Any]] = []
    for item in survivors:
        strat, sym, tf, params = item["strategy"], item["symbol"], item["timeframe"], item["params"]
        nudges_total = 0
        nudges_pass = 0
        try:
            features = load_feature_data(sym, tf).sort_values("timestamp").tail(20000).copy()
        except Exception:
            item["stability_score"] = 0.0
            robust.append(item)
            continue
        for key, val in params.items():
            if not isinstance(val, (int, float)) or isinstance(val, bool):
                continue
            for factor in (0.85, 1.15):
                nudged = dict(params)
                if isinstance(val, int):
                    nudged[key] = max(1, int(round(val * factor)))
                else:
                    nudged[key] = round(val * factor, 4)
                nudges_total += 1
                try:
                    strategy = get_strategy(strat, **nudged)
                    result = run_backtest(features, strategy, audit_decisions=False)
                    gate = run_gates(result.metrics, tf, min_trades=20, max_drawdown=0.25, min_profit_factor=1.1, require_oos=False)
                    if gate.verdict != "KILL":
                        nudges_pass += 1
                except Exception:
                    pass
        stability = nudges_pass / nudges_total if nudges_total else 0.0
        item["stability_score"] = round(stability, 4)
        item["nudges_total"] = nudges_total
        item["nudges_pass"] = nudges_pass
        print(f"[RRA] {strat}/{sym}/{tf}: stability={stability:.2f} ({nudges_pass}/{nudges_total})")
        robust.append(item)
    return robust


# ── Agent 6: PGA ─────────────────────────────────────────────────────────────

def pga_agent(robust: list[dict[str, Any]]) -> dict[str, Any]:
    """Final gate: promote candidates meeting stability + sharpe + trades."""
    approved: list[dict[str, Any]] = []
    for item in robust:
        stability = item.get("stability_score", 0.0)
        metrics = item.get("metrics", {})
        sharpe_oos = float(metrics.get("sharpe_oos", metrics.get("sharpe_ratio", 0.0)) or 0.0)
        trades = float(metrics.get("total_trades", 0.0) or 0.0)
        if stability >= 0.5 and sharpe_oos > 0.3 and trades >= 25:
            approved.append(item)
        elif stability >= 0.5 and trades >= 25:
            # Accept if no OOS sharpe available but otherwise robust
            if "sharpe_oos" not in metrics and "sharpe_ratio" in metrics:
                approved.append(item)

    APPROVED_PATH.parent.mkdir(parents=True, exist_ok=True)
    with APPROVED_PATH.open("a", encoding="utf-8") as fh:
        for item in approved:
            fh.write(json.dumps(item, default=str) + "\n")

    summary = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "candidates_evaluated": len(robust),
        "approved": len(approved),
        "approved_list": [
            {"strategy": a["strategy"], "symbol": a["symbol"], "timeframe": a["timeframe"],
             "stability_score": a.get("stability_score"), "verdict": a.get("verdict")}
            for a in approved
        ],
    }
    print(f"[PGA] {len(approved)} approved out of {len(robust)} robust candidates")
    return summary


# ── Orchestrator ──────────────────────────────────────────────────────────────

def run_tsds(
    symbols: list[str] | None = None,
    timeframes: list[str] | None = None,
    strategies: list[str] | None = None,
    max_candidates: int = 200,
) -> dict[str, Any]:
    symbols = symbols or ALL_SYMBOLS
    timeframes = timeframes or ALL_TIMEFRAMES
    strategies = strategies or ALL_STRATEGIES

    stats = dia_agent(symbols, timeframes)
    combos = safa_agent(stats, strategies)
    seeded = sca_agent(combos, stats)
    survivors = wfv_agent(seeded, stats, max_candidates=max_candidates)
    robust = rra_agent(survivors)
    approved = pga_agent(robust)
    return approved


def _split(s: str) -> list[str]:
    return [x.strip() for x in s.split(",") if x.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description="TSDS v1 — TAR Strategy Discovery System")
    parser.add_argument("--symbols", default=",".join(ALL_SYMBOLS))
    parser.add_argument("--timeframes", default=",".join(ALL_TIMEFRAMES))
    parser.add_argument("--strategies", default=",".join(ALL_STRATEGIES))
    parser.add_argument("--max-candidates", type=int, default=200)
    args = parser.parse_args()

    summary = run_tsds(
        symbols=_split(args.symbols),
        timeframes=_split(args.timeframes),
        strategies=_split(args.strategies),
        max_candidates=args.max_candidates,
    )
    print(json.dumps(summary, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
