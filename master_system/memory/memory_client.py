"""
Memory Client for TAR System
Connects to Master System API to share learning
"""

import requests
import json
import os
from datetime import datetime


class MasterMemoryClient:
    def __init__(self, master_api_url=None, system_id="tar"):
        self.master_api = master_api_url or os.getenv(
            "MASTER_MEMORY_API",
            "http://localhost:8000"
        )
        self.system_id = system_id
        self.timeout = 5
    
    def is_master_available(self):
        """Check if Master System is running"""
        try:
            response = requests.get(
                f"{self.master_api}/api/health",
                timeout=self.timeout
            )
            return response.status_code == 200
        except:
            return False
    
    def push_lesson(self, lesson_text, confidence=0.5, category=None, evidence=None):
        """Push a lesson to Master memory"""
        if not self.is_master_available():
            print(f"[WARNING] Master System unavailable at {self.master_api}")
            return False
        
        payload = {
            "lesson": lesson_text,
            "confidence": confidence,
            "category": category or "general",
            "evidence": evidence or {},
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            response = requests.post(
                f"{self.master_api}/api/memory/lessons",
                json=payload,
                headers={"X-System-ID": self.system_id},
                timeout=self.timeout
            )
            return response.status_code == 200
        except Exception as e:
            print(f"[ERROR] Failed to push lesson: {e}")
            return False
    
    def get_patterns(self, system=None):
        """Retrieve patterns from Master memory"""
        if not self.is_master_available():
            return {}
        
        try:
            params = {}
            if system:
                params["system"] = system
            
            response = requests.get(
                f"{self.master_api}/api/memory/patterns",
                params=params,
                timeout=self.timeout
            )
            return response.json()
        except Exception as e:
            print(f"[ERROR] Failed to get patterns: {e}")
            return {}
    
    def discover_patterns(self):
        """Trigger pattern discovery in Master"""
        if not self.is_master_available():
            return {}
        
        try:
            response = requests.post(
                f"{self.master_api}/api/memory/discover",
                timeout=self.timeout
            )
            return response.json()
        except Exception as e:
            print(f"[ERROR] Failed to discover patterns: {e}")
            return {}
    
    def get_status(self):
        """Get Master System status"""
        if not self.is_master_available():
            return {"status": "unavailable"}
        
        try:
            response = requests.get(
                f"{self.master_api}/api/memory/status",
                timeout=self.timeout
            )
            return response.json()
        except Exception as e:
            print(f"[ERROR] Failed to get status: {e}")
            return {}


# Example usage
if __name__ == "__main__":
    client = MasterMemoryClient()
    
    print("Testing Master Memory Client...")
    print(f"Master available: {client.is_master_available()}")
    
    if client.is_master_available():
        print(f"Status: {client.get_status()}")
        
        # Push a test lesson
        client.push_lesson(
            "EMA(12,26) strategy works well in trending markets",
            confidence=0.85,
            category="strategy_performance"
        )
        
        # Get patterns
        patterns = client.get_patterns()
        print(f"Patterns: {json.dumps(patterns, indent=2)}")
