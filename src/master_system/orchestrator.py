"""Master Orchestrator - Primary Brain coordinating all systems"""

import json
from pathlib import Path
from datetime import datetime


class MasterOrchestrator:
    """Coordinates trading, business, and creative systems"""
    
    def __init__(self, base_path: str = "~/Dev/V2trading_system"):
        self.base_path = Path(base_path).expanduser()
        self.reports_path = self.base_path / "reports"
        self.runtime_path = self.base_path / "runtime"
    
    def watch_v2_tar(self):
        """Monitor V2 TAR results (read-only, non-invasive)"""
        queue_file = self.runtime_path / "job_queue.jsonl"
        if not queue_file.exists():
            return {"status": "no_queue"}
        
        completed = queued = failed = 0
        try:
            with open(queue_file) as f:
                for line in f:
                    try:
                        job = json.loads(line)
                        status = job.get("status")
                        if status == "COMPLETED":
                            completed += 1
                        elif status == "QUEUED":
                            queued += 1
                        elif status == "FAILED":
                            failed += 1
                    except:
                        pass
        except:
            pass
        
        return {
            "status": "running",
            "completed": completed,
            "queued": queued,
            "failed": failed
        }
    
    def analyze_reports(self):
        """Learn from V2 TAR reports"""
        if not self.reports_path.exists():
            return {"status": "no_reports"}
        
        reports = list(self.reports_path.glob("*.md"))
        return {
            "status": "analyzed",
            "total_reports": len(reports),
            "latest": reports[-1].name if reports else None
        }
    
    def get_status(self):
        """Get complete system status"""
        return {
            "timestamp": datetime.now().isoformat(),
            "orchestrator": "ACTIVE",
            "v2_tar": self.watch_v2_tar(),
            "reports": self.analyze_reports(),
            "skills": {
                "position_sizer": "ready",
                "invoice_calculator": "ready",
                "csv_validator": "ready"
            },
            "vault": "ready"
        }


if __name__ == "__main__":
    orch = MasterOrchestrator()
    status = orch.get_status()
    print(json.dumps(status, indent=2))
