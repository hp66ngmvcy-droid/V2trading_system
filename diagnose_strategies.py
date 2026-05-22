import pandas as pd
from tar_system.data.store import load_feature_data
from tar_system.strategies.registry import get_strategy

data = load_feature_data("XAUUSD", "M15")

for strategy_name in ["ema_volume_v3", "atr_breakout_v3"]:
    print(f"\n{'='*60}")
    print(f"Diagnosing: {strategy_name}")
    print(f"{'='*60}")
    
    try:
        strategy = get_strategy(strategy_name)
        print(f"✓ Strategy loaded: {strategy}")
        print(f"✓ Strategy name: {strategy.name}")
        
        # Test first 10 rows
        signals = []
        errors = []
        for idx in range(min(10, len(data))):
            try:
                row = data.iloc[idx]
                signal = strategy.generate_signal(row, regime="normal")
                signals.append(signal)
                if signal:
                    print(f"  Row {idx}: {signal.side} @ confidence {signal.confidence}")
            except Exception as e:
                errors.append((idx, str(e)))

        if errors:
            print(f"\nFirst error:")
            print(f"  Row {errors[0][0]}: {errors[0][1]}")

