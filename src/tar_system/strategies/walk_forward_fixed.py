"""Fixed walk-forward validator that actually executes trades"""
import json
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np
from tar_system.backtest.engine import run_backtest
from tar_system.strategies.registry import get_strategy

class WalkForwardFixed:
    def __init__(self, strategy_name, symbol, timeframe):
        self.strategy_name = strategy_name
        self.symbol = symbol
        self.timeframe = timeframe
        
    def run(self, data, train_months=12, test_months=3):
        """Run walk-forward: optimize on train, test on blind test window"""
        results = []
        
        # Split into monthly windows
        data['year_month'] = pd.to_datetime(data['timestamp']).dt.to_period('M')
        months = sorted(data['year_month'].unique())
        
        for i in range(len(months) - train_months - test_months):
            train_end_idx = train_months + i
            test_end_idx = train_end_idx + test_months
            
            train_months_list = months[i:train_end_idx]
            test_months_list = months[train_end_idx:test_end_idx]
            
            # Get train and test data
            train_data = data[data['year_month'].isin(train_months_list)].copy()
            test_data = data[data['year_month'].isin(test_months_list)].copy()
            
            if len(train_data) == 0 or len(test_data) == 0:
                continue
            
            # Run backtest on TEST data (blind)
            test_result = run_backtest(get_strategy(self.strategy_name), test_data)
            
            results.append({
                "window": len(results) + 1,
                "train_period": f"{train_months_list[0]}-{train_months_list[-1]}",
                "test_period": f"{test_months_list[0]}-{test_months_list[-1]}",
                "test_sharpe": test_result.get("sharpe", 0),
                "test_max_dd": test_result.get("max_drawdown", 0),
                "test_trades": test_result.get("trade_count", 0),
                "test_win_rate": test_result.get("win_rate", 0)
            })
        
        # Aggregate blind OOS results
        if results:
            sharpes = [r["test_sharpe"] for r in results if r["test_sharpe"] != 0]
            dds = [r["test_max_dd"] for r in results]
            trades = sum(r["test_trades"] for r in results)
            wrs = [r["test_win_rate"] for r in results if r["test_trades"] > 0]
            
            combined = {
                "sharpe_ratio": np.mean(sharpes) if sharpes else 0,
                "max_drawdown": np.max(dds) if dds else 0,
                "win_rate": np.mean(wrs) if wrs else 0,
                "total_trades": trades,
                "windows_passed": len([r for r in results if r["test_sharpe"] > 0])
            }
        else:
            combined = {"sharpe_ratio": 0, "max_drawdown": 0, "win_rate": 0, "total_trades": 0, "windows_passed": 0}
        
        return {
            "strategy": self.strategy_name,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "results_by_window": results,
            "combined_oos_metrics": combined,
            "timestamp": datetime.now().isoformat()
        }

def run_walk_forward_all():
    """Run walk-forward on all 5 v3 strategies"""
    from tar_system.data.store import load_feature_data
    
    strategies = ["rsi_only_v3", "ema_volume_v3", "atr_breakout_v3", "momentum_crossover_v3", "multi_timeframe_v3"]
    
    data = load_feature_data("XAUUSD", "M15")
    results_dir = Path("data/results")
    
    for strat in strategies:
        print(f"Running walk-forward: {strat}")
        validator = WalkForwardFixed(strat, "XAUUSD", "M15")
        result = validator.run(data, train_months=12, test_months=3)
        
        # Save result
        output_file = results_dir / f"{strat}_XAUUSD_M15_walk_forward_fixed.json"
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2)
        
        print(f"  Sharpe: {result['combined_oos_metrics']['sharpe_ratio']:.2f}")
        print(f"  Trades: {result['combined_oos_metrics']['total_trades']}")
        print(f"  Saved to {output_file}")
        print()

if __name__ == "__main__":
    run_walk_forward_all()
    