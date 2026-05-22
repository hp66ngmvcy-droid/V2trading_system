"""Equity Stitcher: Combines blind OOS equity curves from all windows"""
import numpy as np
from typing import List, Dict, Any

class EquityCurveStitcher:
    def __init__(self, initial_capital: float = 10000):
        self.initial_capital = initial_capital
    
    def stitch(self, window_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not window_results:
            raise ValueError("window_results cannot be empty")
        
        combined_equity = []
        combined_trades = []
        current_equity = self.initial_capital
        
        for window in window_results:
            equity_curve = window.get('equity_curve', [])
            trades = window.get('trades', [])
            
            if equity_curve:
                equity_arr = np.array(equity_curve, dtype=float)
                incremental = np.diff(equity_arr, prepend=equity_arr[0])
                window_start = equity_arr[0]
                for delta in incremental[1:]:
                    current_equity += delta / window_start * current_equity
                    combined_equity.append(current_equity)
                combined_trades.extend(trades)
        
        if not combined_equity:
            raise ValueError("No equity data to stitch")
        
        return {
            'combined_equity': combined_equity,
            'combined_trades': combined_trades,
            'total_length': len(combined_equity),
            'final_equity': combined_equity[-1],
            'windows_stitched': len(window_results)
        }
