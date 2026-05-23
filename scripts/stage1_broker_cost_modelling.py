"""Stage 1: Broker Cost Modelling — XAUUSD M15 baseline vs realistic costs."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tar_system.assets.profiles import ASSET_PROFILES
from tar_system.backtest.engine import run_backtest
from tar_system.brokers.registry import load_broker_profile
from tar_system.data.store import load_feature_data
from tar_system.strategies.rsi_trend_v4 import RSITrendV4

SYMBOL = "XAUUSD"
TIMEFRAME = "M15"

# Locked baseline parameters (XAUUSD_M15_20260415)
STRATEGY = RSITrendV4(
    rsi_period=20,
    rsi_buy_level=40.0,
    rsi_sell_level=60.0,
    atr_multiplier=2.0,
    reward_risk=3.0,
    liquid_sessions_only=True,
    ema_cross_gate=True,
)


def _fmt(metrics: dict, label: str) -> dict:
    return {
        "label": label,
        "total_trades": int(metrics.get("total_trades", 0)),
        "win_rate": round(float(metrics.get("win_rate", 0)) * 100, 2),
        "profit_factor": round(float(metrics.get("profit_factor", 0)), 4),
        "net_profit": round(float(metrics.get("net_profit", 0)), 4),
        "max_drawdown_pct": round(float(metrics.get("max_drawdown", 0)) * 100, 2),
        "sharpe_ratio": round(float(metrics.get("sharpe_ratio", 0)), 4),
        "total_cost": round(float(metrics.get("total_cost", 0)), 4),
        "swap_cost": round(float(metrics.get("swap_cost", 0)), 4),
        "expectancy": round(float(metrics.get("expectancy", 0)), 4),
    }


def main() -> None:
    print(f"Stage 1: Broker Cost Modelling — {SYMBOL} {TIMEFRAME}")
    print("=" * 60)

    features = load_feature_data(SYMBOL, TIMEFRAME)
    print(f"Data rows: {len(features):,}")

    asset_profile = ASSET_PROFILES.get(SYMBOL)
    broker_profile = load_broker_profile("current_broker_demo")

    # Run 1: no broker costs (raw signal quality)
    print("\n[1/2] Running WITHOUT broker costs...")
    result_raw = run_backtest(features, STRATEGY, audit_decisions=False)
    raw = _fmt(result_raw.metrics, "No broker costs (signal quality only)")

    # Run 2: with full broker costs (spread + slippage + swap)
    print("[2/2] Running WITH broker costs (spread + slippage + swap)...")
    result_costed = run_backtest(
        features,
        STRATEGY,
        audit_decisions=False,
        broker_profile=broker_profile,
        asset_profile=asset_profile,
        cost_multiplier=1.0,
    )
    costed = _fmt(result_costed.metrics, "With broker costs (spread + slippage + swap)")

    # Delta
    pf_delta = costed["profit_factor"] - raw["profit_factor"]
    pnl_delta = costed["net_profit"] - raw["net_profit"]
    cost_drag = costed["total_cost"]

    print("\n" + "=" * 60)
    print("STAGE 1 RESULTS")
    print("=" * 60)

    for r in (raw, costed):
        print(f"\n  {r['label']}")
        print(f"    Trades:        {r['total_trades']}")
        print(f"    Win rate:      {r['win_rate']}%")
        print(f"    Profit factor: {r['profit_factor']}")
        print(f"    Net profit:    {r['net_profit']:.4f}")
        print(f"    Max drawdown:  {r['max_drawdown_pct']}%")
        print(f"    Sharpe:        {r['sharpe_ratio']}")
        print(f"    Total cost:    {r['total_cost']:.4f}")
        print(f"    Swap cost:     {r['swap_cost']:.4f}")

    print(f"\n  PF delta:        {pf_delta:+.4f}")
    print(f"  Net PnL delta:   {pnl_delta:+.4f}")
    print(f"  Total cost drag: {cost_drag:.4f}")

    if costed["profit_factor"] > 1.0:
        verdict = "EDGE SURVIVES COSTS — proceed to Stage 2 (volatility gates)"
    elif costed["profit_factor"] > 0.95:
        verdict = "EDGE MARGINAL — cost reduce needed before Stage 2"
    else:
        verdict = "EDGE DESTROYED BY COSTS — revisit strategy before Stage 2"

    print(f"\n  VERDICT: {verdict}")
    print("=" * 60)

    out = Path("reports/stage1_broker_cost_modelling.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"raw": raw, "costed": costed,
                               "pf_delta": round(pf_delta, 4),
                               "pnl_delta": round(pnl_delta, 4),
                               "cost_drag": round(cost_drag, 4),
                               "verdict": verdict}, indent=2))
    print(f"\nResults saved: {out}")


if __name__ == "__main__":
    main()
