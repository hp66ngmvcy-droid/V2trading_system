#!/bin/bash

cd /Users/whs1/Dev/V2trading_system
source venv/bin/activate

echo "=========================================="
echo "RUNNING ALL BACKTESTS + WALK-FORWARD"
echo "Started: $(date)"
echo "=========================================="
echo ""

# Run all backtests
for strategy in goldv2_v2 rsi_only_v3 ema_volume_v3 atr_breakout_v3 momentum_crossover_v3 multi_timeframe_v3 ema_volume_fixed atr_breakout_fixed; do
    echo "[$strategy] Running backtest..."
    python -m tar_system.cli backtest --strategy $strategy --symbol XAUUSD --timeframe M15 2>&1 | tail -3
    echo ""
done

# Run all walk-forward tests
for strategy in rsi_only_v3 ema_volume_v3 atr_breakout_v3 momentum_crossover_v3 multi_timeframe_v3; do
    echo "[$strategy] Running walk-forward..."
    python -m tar_system.cli run-walk-forward --strategy $strategy --symbol XAUUSD --timeframe M15 --train-window 12 --test-window 3 2>&1 | tail -3
    echo ""
done

echo "=========================================="
echo "AUDIT RESULTS"
echo "=========================================="
python << 'PYEOF'
import json
from pathlib import Path

results_dir = Path("data/results")
strategies = ["rsi_only_v3", "ema_volume_v3", "atr_breakout_v3", "momentum_crossover_v3", "multi_timeframe_v3"]

print(f"{'Strategy':<28} | {'Sharpe':>7} | {'Max DD':>8} | {'Win Rate':>8} | {'Trades':>7} | Verdict")
print("-" * 110)

for strat in strategies:
    wf_file = results_dir / f"{strat}_XAUUSD_M15_walk_forward.json"
    if wf_file.exists():
        with open(wf_file) as f:
            data = json.load(f)
        metrics = data.get("stitched_metrics", {})
        sharpe = metrics.get("sharpe_ratio", 0)
        max_dd = metrics.get("max_drawdown", 0)
        win_rate = metrics.get("win_rate", 0)
        trades = metrics.get("total_trades", 0)
        
        verdict = "✅ PASS" if (sharpe >= 1.0 and max_dd <= 0.25) else "❌ FAIL"
        print(f"{strat:<28} | {sharpe:7.2f} | {max_dd*100:7.1f}% | {win_rate*100:7.1f}% | {trades:7.0f} | {verdict}")
PYEOF

echo ""
echo "=========================================="
echo "Completed: $(date)"
echo "Results saved to: data/results/"
echo "=========================================="
