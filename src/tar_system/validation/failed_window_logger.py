"""Failed Window Logger: Logs failed walk-forward windows with reason codes"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

class FailedWindowLogger:
    def __init__(self, log_file: str = "logs/failed_windows.jsonl"):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def log_failure(self, window: int, strategy: str, asset: str, timeframe: str,
                   train_result: Dict, test_result: Dict, reason: str,
                   regime_notes: str = "", logic_to_keep: List = None,
                   logic_to_revise: List = None, logic_to_reject: List = None) -> bool:
        try:
            train_sharpe = train_result.get('sharpe_ratio', 0)
            test_sharpe = test_result.get('sharpe_ratio', 0)
            degradation = (1 - test_sharpe / train_sharpe) * 100 if train_sharpe > 0 else 0
            
            entry = {
                'timestamp': datetime.now().isoformat(),
                'window': window,
                'strategy': strategy,
                'asset': asset,
                'timeframe': timeframe,
                'reason': reason,
                'degradation_pct': round(degradation, 2),
            }
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(entry) + '\n')
            return True
        except Exception as e:
            return False
    
    def get_summary(self) -> Dict[str, Any]:
        if not self.log_file.exists(): 
            return {'total_failures': 0}
        return {'total_failures': 0}
