"""Stage 4: Parameter Isolation — one-at-a-time sweeps with Stage 3 gates locked."""

import json
import sys
from dataclasses import replace
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

# Stage 3 locked gates
ATR_CAP = 8.2761
SESSION_START = 12
SESSION_END = 20

MIN_TRADES = 30


class GatedStrategy:
    """Wraps strategy with ATR cap + session hour gate."""

    def __init__(self, inner: RSITrendV4, atr_cap: float, start: int, end: int) -> None:
        self.inner = inner
        self.atr_cap = atr_cap
        self.start = start
        self.end = end
        self.name = inner.name
        self.version = inner.version

    def generate_signal(self, row: pd.Series, regime: str) -> Signal:
        hour = int(row.get("hour_utc", -1))
        if not (self.start <= hour < self.end):
            return Signal(
                side="HOLD", confidence=0.0, stop_loss=None, take_profit=None,
                reason_code="OUTSIDE_SESSION",
                timestamp=pd.Timestamp(row["timestamp"]), symbol=str(row["symbol"]),
                timeframe=str(row["timeframe"]), strategy=self.name, version=self.version,
                entry=float(row["close"]), metadata={"regime": regime},
            )
        atr = float(row.get("atr", 0) or 0)
        if 0 < self.atr_cap < atr:
            return Signal(
                side="HOLD", confidence=0.0, stop_loss=None, take_profit=None,
                reason_code="ATR_TOO_HIGH",
                timestamp=pd.Timestamp(row["timestamp"]), symbol=str(row["symbol"]),
                timeframe=str(row["timeframe"]), strategy=self.name, version=self.version,
                entry=float(row["close"]), metadata={"regime": regime},
            )
        return self.inner.generate_signal(row, regime)


def _run(features: pd.DataFrame, strategy: RSITrendV4, broker_profile, asset_profile) -> dict:
    gated = GatedStrategy(strategy, ATR_CAP, SESSION_START, SESSION_END)
    result = run_backtest(features, gated, audit_decisions=False,
                          broker_profile=broker_profile, asset_profile=asset_profile)
    m = result.metrics
    return {
        "total_trades": int(m.get("total_trades", 0)),
        "win_rate": round(float(m.get("win_rate", 0)) * 100, 2),
        "profit_factor": round(float(m.get("profit_factor", 0)), 4),
        "max_drawdown_pct": round(float(m.get("max_drawdown", 0)) * 100, 2),
        "sharpe_ratio": round(float(m.get("sharpe_ratio", 0)), 4),
        "net_profit": round(float(m.get("net_profit", 0)), 4),
    }


def _print_table(rows: list[dict], param_label: str, baseline_key: str) -> None:
    print(f"\n  {'Value':<20} {'Trades':>7} {'Win%':>7} {'PF':>7} {'DD%':>6} {'Sharpe':>8}")
    print("  " + "-" * 60)
    for r in rows:
        marker = " ◄ baseline" if str(r["value"]) == str(baseline_key) else ""
        print(f"  {str(r['value']):<20} {r['total_trades']:>7} {r['win_rate']:>6.1f}% "
              f"{r['profit_factor']:>7.4f} {r['max_drawdown_pct']:>5.2f}% "
              f"{r['sharpe_ratio']:>8.4f}{marker}")


def _best(rows: list[dict]) -> dict:
    eligible = [r for r in rows if r["total_trades"] >= MIN_TRADES]
    if not eligible:
        return rows[0]
    return max(eligible, key=lambda r: r["sharpe_ratio"])


def main() -> None:
    print(f"Stage 4: Parameter Isolation — {SYMBOL} {TIMEFRAME}")
    print(f"  Gates locked: ATR cap={ATR_CAP}, session={SESSION_START}-{SESSION_END} UTC")
    print("=" * 70)

    features = load_feature_data(SYMBOL, TIMEFRAME)
    asset_profile = ASSET_PROFILES.get(SYMBOL)
    broker_profile = load_broker_profile("current_broker_demo")

    # Rolling locked config — updates as each sweep finds a winner
    locked = dict(
        rsi_buy_level=40.0,
        rsi_sell_level=60.0,
        atr_multiplier=2.0,
        reward_risk=3.0,
    )
    winners = {}

    # ── Sweep 1: ATR Multiplier (SL distance) ────────────────────────────────
    print("\n[1/4] ATR Multiplier (SL) sweep  (all others frozen)")
    rows = []
    for v in [2.0, 2.2, 2.5, 3.0]:  # floor 2.0x ATR per SL rules
        s = RSITrendV4(**{**locked, "atr_multiplier": v})
        m = _run(features, s, broker_profile, asset_profile)
        rows.append({"value": v, **m})
        print(f"  atr_multiplier={v}: trades={m['total_trades']}, PF={m['profit_factor']}, Sharpe={m['sharpe_ratio']}")
    _print_table(rows, "atr_multiplier", locked["atr_multiplier"])
    best = _best(rows)
    locked["atr_multiplier"] = best["value"]
    winners["atr_multiplier"] = best
    print(f"  → Winner: atr_multiplier={best['value']} (Sharpe={best['sharpe_ratio']}, trades={best['total_trades']})")

    # ── Sweep 2: Reward/Risk ratio ────────────────────────────────────────────
    print("\n[2/4] Reward/Risk ratio sweep  (all others frozen)")
    rows = []
    for v in [2.0, 2.5, 3.0, 3.5, 4.0]:
        s = RSITrendV4(**{**locked, "reward_risk": v})
        m = _run(features, s, broker_profile, asset_profile)
        rows.append({"value": v, **m})
        print(f"  reward_risk={v}: trades={m['total_trades']}, PF={m['profit_factor']}, Sharpe={m['sharpe_ratio']}")
    _print_table(rows, "reward_risk", locked["reward_risk"])
    best = _best(rows)
    locked["reward_risk"] = best["value"]
    winners["reward_risk"] = best
    print(f"  → Winner: reward_risk={best['value']} (Sharpe={best['sharpe_ratio']}, trades={best['total_trades']})")

    # ── Sweep 3: RSI Buy/Sell Levels ─────────────────────────────────────────
    print("\n[3/4] RSI Buy/Sell Levels sweep  (all others frozen)")
    rows = []
    for buy, sell in [(38, 62), (40, 60), (42, 58), (35, 65), (45, 55)]:
        s = RSITrendV4(**{**locked, "rsi_buy_level": buy, "rsi_sell_level": sell})
        m = _run(features, s, broker_profile, asset_profile)
        rows.append({"value": f"{buy}/{sell}", **m})
        print(f"  rsi={buy}/{sell}: trades={m['total_trades']}, PF={m['profit_factor']}, Sharpe={m['sharpe_ratio']}")
    _print_table(rows, "rsi_levels", f"{locked['rsi_buy_level']:.0f}/{locked['rsi_sell_level']:.0f}")
    best = _best(rows)
    buy_str, sell_str = str(best["value"]).split("/")
    locked["rsi_buy_level"] = float(buy_str)
    locked["rsi_sell_level"] = float(sell_str)
    winners["rsi_levels"] = best
    print(f"  → Winner: rsi={best['value']} (Sharpe={best['sharpe_ratio']}, trades={best['total_trades']})")

    # ── Final validation ─────────────────────────────────────────────────────
    print("\n[4/4] Final validation — all locked params together")
    s = RSITrendV4(**locked)
    final = _run(features, s, broker_profile, asset_profile)
    print(f"  Locked config: {locked}")
    print(f"  trades={final['total_trades']}, win%={final['win_rate']}, "
          f"PF={final['profit_factor']}, DD={final['max_drawdown_pct']}%, "
          f"Sharpe={final['sharpe_ratio']}")

    # ── Summary ──────────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("STAGE 4 RESULT: OPTIMISED PARAMS (with Stage 3 gates)")
    print("=" * 70)
    for k, v in locked.items():
        print(f"  {k}: {v}")
    print(f"\n  Final metrics:")
    print(f"    profit_factor:    {final['profit_factor']}")
    print(f"    sharpe_ratio:     {final['sharpe_ratio']}")
    print(f"    max_drawdown_pct: {final['max_drawdown_pct']}%")
    print(f"    total_trades:     {final['total_trades']}")
    print(f"    win_rate:         {final['win_rate']}%")

    out = Path("reports/stage4_parameter_isolation.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "symbol": SYMBOL, "timeframe": TIMEFRAME,
        "gates": {"atr_cap": ATR_CAP, "session_start": SESSION_START, "session_end": SESSION_END},
        "locked_params": locked,
        "final_metrics": final,
        "sweep_winners": winners,
    }, indent=2))
    print(f"\nResults saved: {out}")
    print("=" * 70)


if __name__ == "__main__":
    main()
