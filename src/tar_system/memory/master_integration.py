"""
TAR-Master Integration
Connects TAR to Master Memory API for shared learning
"""

from .memory_client import MasterMemoryClient


class TARMasterBridge:
    """Bridge between TAR and Master Memory"""
    
    def __init__(self):
        self.client = MasterMemoryClient(system_id="tar")
    
    def push_backtest_result(self, strategy_name, metrics):
        """Push backtest result to Master"""
        if metrics.get("sharpe_ratio", 0) > 1.0:
            self.client.push_lesson(
                lesson_text=f"{strategy_name}: Sharpe {metrics['sharpe_ratio']:.2f}",
                confidence=0.9,
                category="strategy_performance",
                evidence={"sharpe": metrics["sharpe_ratio"]}
            )
    
    def push_parameter_stability(self, strategy_name, stability_score):
        """Push parameter stability to Master"""
        if stability_score >= 0.7:
            confidence = min(0.95, stability_score)
            self.client.push_lesson(
                lesson_text=f"{strategy_name}: Parameter stable (score {stability_score:.2f})",
                confidence=confidence,
                category="parameter_stability",
                evidence={"stability_score": stability_score}
            )
    
    def push_walk_forward_result(self, strategy_name, oos_sharpe, verdict):
        """Push walk-forward validation to Master"""
        self.client.push_lesson(
            lesson_text=f"{strategy_name}: Walk-forward OOS Sharpe {oos_sharpe:.2f} - {verdict}",
            confidence=0.95,
            category="walk_forward_validation",
            evidence={"oos_sharpe": oos_sharpe, "verdict": verdict}
        )
    
    def get_learned_patterns(self):
        """Retrieve patterns discovered by all systems"""
        return self.client.get_patterns()
    
    def is_master_available(self):
        """Check if Master is running"""
        return self.client.is_master_available()
