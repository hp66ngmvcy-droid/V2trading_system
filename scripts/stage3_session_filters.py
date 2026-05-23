"""Stage 3: Session Filter Validation — test session windows with Stage 1+2 settings."""

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
ATR_CAP = 8.2761   # Stage 2 winner: p90

BASE_STRATEGY = RSITrendV4(
    rsi_period=20,
    rsi_buy_level=40.0,
    rsi_sell_level=60.0,
    atr_multiplier=2.0,
    reward_risk=3.0,
    liquid_sessions_only=False,  # session gating done externally per test
    ema_cross_gate=True,
)


class SessionATRGatedStrategy:
    """Blocks entry outside allowed hours and when ATR too high."""

    def __init__(self, inner: RSITrendV4, atr_cap: float,
                 start_utc: int, end_utc: int) -> None:
        self.inner = inner
        self.atr_cap = atr_cap
        self.start_utc = start_utc
        self.end_utc = end_utc
        self.name = inner.name
        self.version = inner.version

    def generate_signal(self, row: pd.Series, regime: str) -> Signal:
        base = dict(
            timestamp=pd.Timestamp(row["timestamp"]),
            symbol=str(row["symbol"]),
            timeframe=str(row["timeframe"]),
            strategy=self.inner.name,
            version=self.inner.version,
            entry=float(row["close"]),
            metadata={"regime": regime},
        )
        hour = int(row.get("hour_utc", -1))
        if not (self.start_utc <= hour < self.end_utc):
            return Signal(side="HOLD", confidence=0.0, stop_loss=None,
                          take_profit=None, reason_code="OUTSIDE_SESSION", **base)
        atr = float(row.get("atr", 0) or 0)
        if atr > self.atr_cap:
            return Signal(side="HOLD", confidence=0.0, stop_loss=None,
                          take_profit=None, reason_code="ATR_TOO_HIGH", **base)
        return self.inner.generate_signal(row, regime)


def _fmt(metrics: dict, label: str, hours: str) -> dict:
    return {
        "label": label,
        "hours": hours,
        "total_trades": int(metrics.get("total_trades", 0)),
        "win_rate": round(float(metrics.get("win_rate", 0)) * 100, 2),
        "profit_factor": round(float(metrics.get("profit_factor", 0)), 4),
        "net_profit": round(float(metrics.get("net_profit", 0)), 4),
        "max_drawdown_pct": round(float(metrics.get("max_drawdown", 0)) * 100, 2),
        "sharpe_ratio": round(float(metrics.get("sharpe_ratio", 0)), 4),
        "expectancy": round(float(metrics.get("expectancy", 0)), 4),
    }


SESSIONS = [
    ("Baseline 7-20 (13h)",   7, 20),
    ("London 7-12 (5h)",      7, 12),
    ("London+Overlap 7-16 (9h)", 7, 16),
    ("Overlap+NY 12-20 (8h)", 12, 20),
    ("London+NY 7-18 (11h)",  7, 18),
    ("Core 8-17 (9h)",        8, 17),   # the failed test window — now tested alone
    ("Extended 6-21 (15h)",   6, 21),
    ("All hours 0-24",        0, 24),
]


def main() -> None:
    print(f"Stage 3: Session Filters — {SYMBOL} {TIMEFRAME}  (ATR cap {ATR_CAP})")
    print("=" * 70)

    features = load_feature_data(SYMBOL, TIMEFRAME)
    asset_profile = ASSET_PROFILES.get(SYMBOL)
    broker_profile = load_broker_profile("current_broker_demo")

    results = []
    for label, start, end in SESSIONS:
        print(f"  Running: {label}...")
        strategy = SessionATRGatedStrategy(BASE_STRATEGY, ATR_CAP, start, end)
        result = run_backtest(
            features, strategy,
            audit_decisions=False,
            broker_profile=broker_profile,
            asset_profile=asset_profile,
        )
        results.append(_fmt(result.metrics, label, f"{start:02d}-{end:02d} UTC"))

    baseline = results[0]
    print("\n" + "=" * 70)
    print("STAGE 3 RESULTS")
    print("=" * 70)
    print(f"\n{'Label':<30} {'Hours':<12} {'Trades':>7} {'Win%':>6} {'PF':>7} {'DD%':>6} {'Sharpe':>7}")
    print("-" * 80)
    for r in results:
        marker = " ◄" if r["label"] == baseline["label"] else ""
        print(f"  {r['label']:<28} {r['hours']:<12} {r['total_trades']:>7} "
              f"{r['win_rate']:>5.1f}% {r['profit_factor']:>7.4f} "
              f"{r['max_drawdown_pct']:>5.2f}% {r['sharpe_ratio']:>7.4f}{marker}")

    # Best by Sharpe (risk-adjusted, includes PF and DD)
    best = max(results, key=lambda r: r["sharpe_ratio"])
    pf_delta = best["profit_factor"] - baseline["profit_factor"]
    dd_delta = best["max_drawdown_pct"] - baseline["max_drawdown_pct"]

    print(f"\n  Best session: {best['label']} ({best['hours']})")
    print(f"  PF delta vs baseline:  {pf_delta:+.4f}")
    print(f"  DD delta vs baseline:  {dd_delta:+.2f}%")
    print(f"  Sharpe vs baseline:    {best['sharpe_ratio'] - baseline['sharpe_ratio']:+.4f}")
    print(f"  Trades vs baseline:    {best['total_trades'] - baseline['total_trades']:+d}")

    if best["sharpe_ratio"] > baseline["sharpe_ratio"] * 1.05:
        verdict = f"SESSION FILTER IMPROVES RISK-ADJUSTED RETURN — use {best['hours']} in Stage 4"
    elif best["sharpe_ratio"] > baseline["sharpe_ratio"]:
        verdict = f"MARGINAL SESSION IMPROVEMENT — {best['hours']} worth using but small gain"
    else:
        verdict = "NO SESSION WINDOW BEATS BASELINE — keep 7-20 UTC for Stage 4"

    print(f"\n  VERDICT: {verdict}")
    print("=" * 70)

    out = Path("reports/stage3_session_filters.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"results": results, "best": best, "verdict": verdict}, indent=2))
    print(f"\nResults saved: {out}")


if __name__ == "__main__":
    main()
