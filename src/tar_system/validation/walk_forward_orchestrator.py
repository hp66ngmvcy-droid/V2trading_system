"""Walk-Forward Orchestrator: Coordinates Phase 2 validation"""
import logging
import json
from typing import Dict, Any
from pathlib import Path
from datetime import datetime
import pandas as pd

logger = logging.getLogger(__name__)

class WalkForwardOrchestrator:
    def __init__(self, strategy_class, backtest_engine, window_splitter, blind_tester,
                 equity_stitcher, oos_metrics, failed_window_logger, initial_capital: float = 10000):
        self.strategy_class = strategy_class
        self.backtest_engine = backtest_engine
        self.window_splitter = window_splitter
        self.blind_tester = blind_tester
        self.equity_stitcher = equity_stitcher
        self.oos_metrics = oos_metrics
        self.failed_window_logger = failed_window_logger
        self.initial_capital = initial_capital
        self.window_results = []
        self.stitched_result = None
        self.aggregate_metrics = None
        self.final_verdict = None
        logger.info(f"WalkForwardOrchestrator initialized")
    
    def run(self, data: pd.DataFrame, param_ranges: Dict[str, Any] = None) -> Dict[str, Any]:
        logger.info(f"Starting walk-forward validation on {len(data)} bars")
        windows = list(self.window_splitter.generate_windows())
        if not windows:
            raise ValueError("No windows generated")
        
        for window_num, (train_data, test_data) in enumerate(windows, 1):
            logger.info(f"WINDOW {window_num}/{len(windows)}")
            result = self._process_window(window_num, train_data, test_data, param_ranges)
            self.window_results.append(result)
        
        self.stitched_result = self.equity_stitcher.stitch(self.window_results)
        self.aggregate_metrics = self.oos_metrics.aggregate(self.window_results)
        self.final_verdict = self._calculate_verdict()
        
        return {
            'strategy': self.strategy_class.__name__,
            'windows': len(self.window_results),
            'aggregate_metrics': self.aggregate_metrics,
            'final_verdict': self.final_verdict,
            'timestamp': datetime.now().isoformat(),
        }
    
    def _process_window(self, window_num, train_data, test_data, param_ranges):
        optimal_params = self.backtest_engine.optimize(train_data, self.strategy_class, param_ranges)
        train_result = self.backtest_engine.run(train_data, self.strategy_class(), optimal_params)
        test_result = self.blind_tester.test(test_data, optimal_params, window_num)
        
        degradation = (1 - test_result.get('sharpe_ratio', 0) / train_result.get('sharpe_ratio', 1)) * 100
        
        if not self._window_passed(test_result, degradation):
            self.failed_window_logger.log_failure(
                window_num, self.strategy_class.__name__, 'XAUUSD', 'M15',
                train_result, test_result, self._get_failure_reason(test_result, degradation)
            )
        
        return {
            'window': window_num,
            'train_result': train_result,
            'test_result': test_result,
            'degradation_pct': degradation,
        }
    
    def _window_passed(self, test_result, degradation):
        return (test_result.get('sharpe_ratio', 0) >= 1.0 and 
                test_result.get('max_drawdown', 0) <= 0.25 and degradation <= 15)
    
    def _get_failure_reason(self, test_result, degradation):
        sharpe = test_result.get('sharpe_ratio', 0)
        if sharpe < 1.0:
            return f"SHARPE_TOO_LOW"
        return "UNKNOWN_FAILURE"
    
    def _calculate_verdict(self):
        metrics = self.aggregate_metrics
        passed = sum(1 for w in self.window_results if self._window_passed(w['test_result'], w['degradation_pct']))
        pass_rate = passed / len(self.window_results)
        
        if metrics.get('sharpe_ratio', 0) >= 1.2 and pass_rate >= 0.75:
            verdict, confidence = "KEEP", 0.95
        elif metrics.get('sharpe_ratio', 0) >= 0.8:
            verdict, confidence = "REVISE", 0.70
        else:
            verdict, confidence = "KILL", 0.90
        
        return {'verdict': verdict, 'confidence': confidence, 'passed_windows': passed, 'total_windows': len(self.window_results)}
    
    def get_results_summary(self):
        if not self.final_verdict:
            return "Not yet run"
        v = self.final_verdict
        m = self.aggregate_metrics
        return f"VERDICT: {v['verdict']} | Sharpe: {m.get('sharpe_ratio', 0):.2f} | Windows: {v['passed_windows']}/{v['total_windows']}"
    
    def export_results(self, output_path: str = "reports/walk_forward_results.json"):
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump({'verdict': self.final_verdict}, f)
        return output_path
