"""Secondary Brain - Vault for learnings"""

import json
from pathlib import Path
from datetime import datetime


class SecondaryBrain:
    """Stores learnings from all systems"""
    
    def __init__(self, vault_path: str = "~/Dev/V2trading_system/src/master_system/vault"):
        self.vault_path = Path(vault_path).expanduser()
        self.vault_path.mkdir(parents=True, exist_ok=True)
    
    def record_learning(self, category: str, content: dict):
        """Record a learning"""
        log_file = self.vault_path / f"{category}_log.jsonl"
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "category": category,
            **content
        }
        
        with open(log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
    
    def record_decision(self, decision: str, context: str):
        """Record a strategic decision"""
        self.record_learning("decision", {
            "decision": decision,
            "context": context
        })
    
    def record_trade_outcome(self, strategy: str, symbol: str, result: dict):
        """Record trading outcome"""
        self.record_learning("trading", {
            "strategy": strategy,
            "symbol": symbol,
            "result": result
        })
    
    def get_learnings(self, category: str = None):
        """Retrieve learnings"""
        results = []
        
        if category:
            files = [self.vault_path / f"{category}_log.jsonl"]
        else:
            files = list(self.vault_path.glob("*_log.jsonl"))
        
        for file in files:
            if file.exists():
                with open(file) as f:
                    for line in f:
                        try:
                            results.append(json.loads(line))
                        except:
                            pass
        
        return results


if __name__ == "__main__":
    brain = SecondaryBrain()
    brain.record_decision("Start Master System", "All 3 skills ready")
    print("✅ Learning recorded")
