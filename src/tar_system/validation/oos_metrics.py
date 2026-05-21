"""OOS Metrics Aggregator: Calculates aggregate metrics from blind windows"""
import numpy as np
from typing import List, Dict, Any

class OOSMetricsAggregator:
    def __init__(self, risk_free_rate: float = 0.02):
        self.risk_free_rate = risk_free_rate
    
    def aggregate(self, window_results: List[Dict[str, Any]]) -> Dict[str, float]:
        if not window_results:
            raise ValueError("window_results cannot be empty")
        
        all_returns, all_trades = [], []
        
        for window in window_results:
            equity = window.get('equity_curve', [])
            if len(equity) > 1:
                equity_arr = np.array(equity)
                returns = np.diff(equity_arr) / equity_arr[:-1]
                all_returns.extend(returns)
            all_trades.extend(window.get('trades', []))
        
        if not all_returns:
            raise ValueError("No returns data found")
        
        returns_arr = np.array(all_returns)
        metrics = {
            'sharpe_ratio': self._calc_sharpe(returns_arr),
            'max_drawdown': self._calc_max_dd(returns_arr),
            'win_rate': self._calc_win_rate(all_trades),
            'total_trades': len(all_trades),
        }
        return metrics
    
    def _calc_sharpe(self, returns):
        excess = np.mean(returns) - (self.risk_free_rate / 252)
        vol = np.std(returns)
        return excess / vol * np.sqrt(252) if vol > 0 else 0
    
    def _calc_max_dd(self, returns):
        cumsum = (1 + returns).cumprod()
        running_max = np.maximum.accumulate(cumsum)
        dd = (cumsum - running_max) / running_max
        return np.min(dd)
    
    def _calc_win_rate(self, trades):
        if not trades: return 0
        wins = len([t for t in trades if t.get('pnl', 0) > 0])
        return wins / len(trades)
