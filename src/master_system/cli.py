"""Master System CLI commands"""

import json
import sys
from pathlib import Path
from src.master_system.orchestrator import MasterOrchestrator
from src.master_system.secondary_brain import SecondaryBrain


def show_status():
    """Show system status"""
    orch = MasterOrchestrator()
    status = orch.get_status()
    print(json.dumps(status, indent=2))


def show_v2_tar():
    """Show V2 TAR status"""
    orch = MasterOrchestrator()
    tar = orch.watch_v2_tar()
    print(json.dumps(tar, indent=2))


def show_learnings(category=None):
    """Show recorded learnings"""
    brain = SecondaryBrain()
    learnings = brain.get_learnings(category)
    print(f"Found {len(learnings)} learnings")
    for learning in learnings[-5:]:
        print(json.dumps(learning, indent=2))


def record_test():
    """Test recording a learning"""
    brain = SecondaryBrain()
    brain.record_decision("Test Decision", "Testing vault storage")
    print("✅ Test learning recorded")


def main():
    if len(sys.argv) < 2:
        print("Master System CLI")
        print("  status          - Show system status")
        print("  v2-tar          - Show V2 TAR status")
        print("  learnings       - Show recorded learnings")
        print("  record-test     - Test recording")
        return
    
    command = sys.argv[1]
    
    if command == "status":
        show_status()
    elif command == "v2-tar":
        show_v2_tar()
    elif command == "learnings":
        show_learnings()
    elif command == "record-test":
        record_test()
    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
