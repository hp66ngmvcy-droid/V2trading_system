"""Trading Dashboard: Shows LIVE TRADING: DISABLED"""
import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class TradingDashboard:
    def __init__(self, paper_broker, execution_interface):
        self.paper = paper_broker
        self.execution = execution_interface
    
    def get_status(self) -> Dict[str, Any]:
        return {
            'timestamp': datetime.now().isoformat(),
            'live_status': '🔴 DISABLED',
            'portfolio': self.paper.get_portfolio_value(),
        }
    
    def print_dashboard(self):
        print("\n" + "="*60)
        print("TAR TRADING DASHBOARD")
        print("="*60)
        print("🔴 LIVE TRADING: DISABLED")
        print("="*60 + "\n")
