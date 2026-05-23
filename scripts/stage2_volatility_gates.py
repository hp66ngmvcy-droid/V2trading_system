"""Stage 2: Volatility Gates — test ATR thresholds to reduce drawdown."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd

from tar_system.assets.profiles import ASSET_PROFILES
from tar_system.backtest.engine import run_backtest
from tar_system.brokers.registry import load_broker_profile
from tar_system.data.store import load_feature_data
from tar_system.strategies.base import Signal
from tar_system.strategies.rsi_trend_v4 import RSITrendV4

SYMBOL = "XAUUSD"
TIMEFRAME = "M15"

# Baseline locked params
BASE_STRATEGY = RSITrendV4(
    rsi_buy_level=40.0,
    rsi_sell_level=60.0,
    atr_multiplier=2.0,
    reward_risk=3.0,
    liquid_sessions_only=True,
    ema_cross_gate=True,
)


class ATRGatedStrategy:
    """Wraps a strategy and returns HOLD when ATR exceeds threshold."""

    def __init__(self, inner: RSITrendV4, atr_cap: float) -> None:
        self.inner = inner
        self.atr_cap = atr_cap
        self.name = inner.name
        self.version = inner.version

    def generate_signal(self, row: pd.Series, regime: str) -> Signal:
        atr = float(row.get("atr", 0) or 0)
        if atr > self.atr_cap:
            # High volatility — hold; replicate HOLD structure from inner strategy
            return Signal(
                side="HOLD",
                confidence=0.0,
                stop_loss=None,
                take_profit=None,
                reason_code="ATR_TOO_HIGH",
                timestamp=pd.Timestamp(row["timestamp"]),
                symbol=str(row["symbol"]),
                timeframe=str(row["timeframe"]),
                strategy=self.inner.name,
                version=self.inner.version,
                entry=float(row["close"]),
                metadata={"regime": regime, "atr": atr, "atr_cap": self.atr_cap},
            )
        return self.inner.generate_signal(row, regime)


def _fmt(metrics: dict, label: str, atr_cap: float | None = None) -> dict:
    return {
        "label": label,
        "atr_cap": atr_cap,
        "total_trades": int(metrics.get("total_trades", 0)),
        "win_rate": round(float(metrics.get("win_rate", 0)) * 100, 2),
        "profit_factor": round(float(metrics.get("profit_factor", 0)), 4),
        "net_profit": round(float(metrics.get("net_profit", 0)), 4),
        "max_drawdown_pct": round(float(metrics.get("max_drawdown", 0)) * 100, 2),
        "sharpe_ratio": round(float(metrics.get("sharpe_ratio", 0)), 4),
        "total_cost": round(float(metrics.get("total_cost", 0)), 4),
        "expectancy": round(float(metrics.get("expectancy", 0)), 4),
    }


def main() -> None:
    print(f"Stage 2: Volatility Gates — {SYMBOL} {TIMEFRAME}")
    print("=" * 60)

    features = load_feature_data(SYMBOL, TIMEFRAME)
    asset_profile = ASSET_PROFILES.get(SYMBOL)
    broker_profile = load_broker_profile("current_broker_demo")

    atr = features["atr"].dropna()
    thresholds = {
        "No gate (baseline)": None,
        "ATR p95 cap": round(float(atr.quantile(0.95)), 4),
        "ATR p90 cap": round(float(atr.quantile(0.90)), 4),
        "ATR p85 cap": round(float(atr.quantile(0.85)), 4),
        "ATR p75 cap": round(float(atr.quantile(0.75)), 4),
    }

    print("\nATR distribution:")
    for label, cap in thresholds.items():
        pct_filtered = (atr > cap).sum() / len(atr) * 100 if cap else 0
        print(f"  {label}: cap={cap}  bars_filtered={pct_filtered:.1f}%")

    results = []
    for label, cap in thresholds.items():
        print(f"\nRunning: {label}...")
        strategy = ATRGatedStrategy(BASE_STRATEGY, cap) if cap else BASE_STRATEGY
        result = run_backtest(
            features,
            strategy,
            audit_decisions=False,
            broker_profile=broker_profile,
            asset_profile=asset_profile,
        )
        results.append(_fmt(result.metrics, label, cap))

    baseline = results[0]
    print("\n" + "=" * 60)
    print("STAGE 2 RESULTS")
    print("=" * 60)
    print(f"\n{'Label':<28} {'Trades':>7} {'Win%':>7} {'PF':>7} {'DD%':>7} {'Sharpe':>7} {'NetPnL':>10}")
    print("-" * 78)
    for r in results:
        marker = " ← BASELINE" if r["atr_cap"] is None else ""
        print(f"  {r['label']:<26} {r['total_trades']:>7} {r['win_rate']:>6.1f}% "
              f"{r['profit_factor']:>7.4f} {r['max_drawdown_pct']:>6.2f}% "
              f"{r['sharpe_ratio']:>7.4f} {r['net_profit']:>10.4f}{marker}")

    # Pick best: highest PF with drawdown improvement
    non_baseline = [r for r in results if r["atr_cap"] is not None]
    best = max(non_baseline, key=lambda r: r["profit_factor"])
    pf_delta = best["profit_factor"] - baseline["profit_factor"]
    dd_delta = best["max_drawdown_pct"] - baseline["max_drawdown_pct"]
    trade_delta = best["total_trades"] - baseline["total_trades"]

    print(f"\n  Best gate: {best['label']} (ATR cap {best['atr_cap']})")
    print(f"  PF delta:      {pf_delta:+.4f}")
    print(f"  DD delta:      {dd_delta:+.2f}%")
    print(f"  Trade delta:   {trade_delta:+d}")

    if best["profit_factor"] >= baseline["profit_factor"] and best["max_drawdown_pct"] < baseline["max_drawdown_pct"]:
        verdict = f"GATE IMPROVES BOTH PF AND DRAWDOWN — use ATR cap {best['atr_cap']} in Stage 3"
    elif best["profit_factor"] >= baseline["profit_factor"]:
        verdict = f"GATE IMPROVES PF, DRAWDOWN UNCHANGED — use ATR cap {best['atr_cap']}"
    elif best["max_drawdown_pct"] < baseline["max_drawdown_pct"]:
        verdict = f"GATE REDUCES DRAWDOWN AT PF COST — review trade-off before Stage 3"
    else:
        verdict = "NO GATE IMPROVES ON BASELINE — volatility filtering not beneficial here"

    print(f"\n  VERDICT: {verdict}")
    print("=" * 60)

    out = Path("reports/stage2_volatility_gates.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"results": results, "best": best,
                               "verdict": verdict}, indent=2))
    print(f"\nResults saved: {out}")


if __name__ == "__main__":
    main()
