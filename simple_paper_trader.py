import json
from pathlib import Path
from datetime import datetime
import pandas as pd
from tar_system.data.store import load_feature_data
from tar_system.strategies.registry import get_strategy

for strategy_name in ["rsi_only_v3", "ema_volume_v3", "atr_breakout_v3", "momentum_crossover_v3", "multi_timeframe_v3"]:
    print(f"\nRunning: {strategy_name}")
    try:
        data = load_feature_data("XAUUSD", "M15")
        strategy = get_strategy(strategy_name)
        trades = 0
        for idx, row in data.iterrows():
            try:
                signal = strategy.generate_signal(row, regime="normal")
                if signal and signal.side != "HOLD":
                    trades += 1
            except:
                pass
        print(f"  Completed: {trades} signals generated")
    except Exception as e:
        print(f"  Error: {e}")

print("\nPaper trading run complete!")
