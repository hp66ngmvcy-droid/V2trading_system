"""Blind OOS Tester: Tests strategy on unseen data with fixed parameters"""
import pandas as pd
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class BlindOOSTester:
    def __init__(self, strategy_class, backtest_engine):
        self.strategy_class = strategy_class
        self.backtest_engine = backtest_engine
        self.logger = logger
    
    def test(self, test_data: pd.DataFrame, optimal_params: Dict[str, Any], window_num: int = 0) -> Dict[str, Any]:
        if not optimal_params:
            raise ValueError("optimal_params cannot be empty")
        self.logger.info(f"Window {window_num}: Testing BLIND ({len(test_data)} bars)")
        strategy = self.strategy_class(name=f"{self.strategy_class.__name__}_w{window_num}")
        result = self.backtest_engine.run(data=test_data, strategy=strategy, parameters=optimal_params, optimize=False)
        result['window'] = window_num
        result['is_blind'] = True
        result['parameters'] = optimal_params
        return result
    
    def test_batch(self, windows: list, optimal_params_per_window: Dict[int, Dict]) -> list:
        results = []
        for window_num, test_data in windows:
            optimal_params = optimal_params_per_window.get(window_num)
            if optimal_params is None:
                continue
            result = self.test(test_data, optimal_params, window_num)
            results.append(result)
        return results
