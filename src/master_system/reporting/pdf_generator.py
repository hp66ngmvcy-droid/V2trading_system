"""PDF Report Generator"""

from typing import Dict, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ReportMetrics:
    total_trades: float
    win_rate: float
    profit_factor: float
    max_drawdown: float
    sharpe_ratio: float
    net_profit: float


class PDFReportGenerator:
    """Generate reports from trading data"""
    
    def __init__(self):
        self.reports = []
    
    def create_report(self, strategy: str, symbol: str, metrics: Dict):
        """Create a report"""
        report = {
            "strategy": strategy,
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics
        }
        self.reports.append(report)
        return report
    
    def generate_text(self, report: Dict) -> str:
        """Generate text report"""
        m = report["metrics"]
        return f"""
═══════════════════════════════════════════════════════════════
                    TRADING STRATEGY REPORT
═══════════════════════════════════════════════════════════════

Strategy:              {report['strategy']}
Symbol:                {report['symbol']}
Generated:             {report['timestamp']}

Performance Metrics:
  Total Trades:        {m.get('total_trades', 0):.0f}
  Win Rate:            {m.get('win_rate', 0) * 100:.2f}%
  Profit Factor:       {m.get('profit_factor', 0):.2f}
  Max Drawdown:        {m.get('max_drawdown', 0) * 100:.2f}%
  Sharpe Ratio:        {m.get('sharpe_ratio', 0):.2f}
  Net Profit:          ${m.get('net_profit', 0):,.2f}

═══════════════════════════════════════════════════════════════
"""
    
    def save_text_report(self, report: Dict, filename: str):
        """Save text report"""
        content = self.generate_text(report)
        with open(filename, "w") as f:
            f.write(content)
        return filename


if __name__ == "__main__":
    gen = PDFReportGenerator()
    print("✅ PDF Generator ready")
