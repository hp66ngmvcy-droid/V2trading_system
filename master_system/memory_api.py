"""
TAR Master System Memory API
REST API for shared learning across independent subsystems
"""

from flask import Flask, request, jsonify
from datetime import datetime
import json
from pathlib import Path
import os

app = Flask(__name__)

# Memory directory
MEMORY_DIR = Path(__file__).parent / "memory"
MEMORY_DIR.mkdir(exist_ok=True)

LESSONS_FILE = MEMORY_DIR / "lessons_learned.jsonl"
PATTERNS_FILE = MEMORY_DIR / "cross_system_patterns.json"

# Ensure files exist
LESSONS_FILE.touch()
if not PATTERNS_FILE.exists():
    PATTERNS_FILE.write_text('{}')


@app.route("/api/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "alive",
        "timestamp": datetime.now().isoformat(),
        "memory_dir": str(MEMORY_DIR)
    }), 200


@app.route("/api/memory/lessons", methods=["POST"])
def receive_lesson():
    """Receive lesson from any subsystem"""
    try:
        lesson = request.json
        lesson["timestamp"] = datetime.now().isoformat()
        lesson["source"] = request.headers.get("X-System-ID", "unknown")
        
        # Append to lessons log
        with open(LESSONS_FILE, "a") as f:
            f.write(json.dumps(lesson) + "\n")
        
        return jsonify({
            "status": "received",
            "id": lesson["timestamp"],
            "source": lesson["source"]
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/memory/lessons", methods=["GET"])
def get_lessons():
    """Retrieve lessons (optionally filtered by system or category)"""
    try:
        system_filter = request.args.get("system", None)
        category_filter = request.args.get("category", None)
        
        lessons = []
        if LESSONS_FILE.exists():
            with open(LESSONS_FILE, "r") as f:
                for line in f:
                    if line.strip():
                        lesson = json.loads(line)
                        
                        if system_filter and lesson.get("source") != system_filter:
                            continue
                        if category_filter and lesson.get("category") != category_filter:
                            continue
                        
                        lessons.append(lesson)
        
        return jsonify({
            "total": len(lessons),
            "lessons": lessons
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/memory/patterns", methods=["GET"])
def get_patterns():
    """Retrieve discovered patterns"""
    try:
        patterns = {}
        if PATTERNS_FILE.exists():
            patterns = json.loads(PATTERNS_FILE.read_text())
        
        return jsonify(patterns), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/memory/discover", methods=["POST"])
def discover_patterns():
    """Analyze all lessons and discover patterns"""
    try:
        lessons = []
        if LESSONS_FILE.exists():
            with open(LESSONS_FILE, "r") as f:
                for line in f:
                    if line.strip():
                        lessons.append(json.loads(line))
        
        # Group by category
        patterns = {}
        for lesson in lessons:
            cat = lesson.get("category", "general")
            if cat not in patterns:
                patterns[cat] = []
            patterns[cat].append(lesson)
        
        # Analyze each category
        insights = {}
        for category, cat_lessons in patterns.items():
            high_confidence = [
                l for l in cat_lessons
                if l.get("confidence", 0) >= 0.7
            ]
            
            insights[category] = {
                "total_lessons": len(cat_lessons),
                "high_confidence_lessons": len(high_confidence),
                "avg_confidence": round(
                    sum(l.get("confidence", 0) for l in cat_lessons) / len(cat_lessons),
                    2
                ),
                "top_lessons": [l.get("lesson") or l.get("lesson_text", "") for l in high_confidence[:3]]
            }
        
        # Save patterns
        PATTERNS_FILE.write_text(json.dumps(insights, indent=2))
        
        return jsonify({
            "status": "patterns_discovered",
            "insights": insights
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/memory/status", methods=["GET"])
def memory_status():
    """Get memory system status"""
    try:
        lesson_count = 0
        if LESSONS_FILE.exists():
            with open(LESSONS_FILE, "r") as f:
                lesson_count = sum(1 for line in f if line.strip())
        
        patterns = {}
        if PATTERNS_FILE.exists():
            patterns = json.loads(PATTERNS_FILE.read_text())
        
        return jsonify({
            "status": "operational",
            "total_lessons": lesson_count,
            "total_patterns": len(patterns),
            "memory_file": str(LESSONS_FILE),
            "patterns_file": str(PATTERNS_FILE)
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


if __name__ == "__main__":
    print("=" * 60)
    print("TAR Master System Memory API")
    print("=" * 60)
    print(f"Memory directory: {MEMORY_DIR}")
    print(f"Lessons log: {LESSONS_FILE}")
    print(f"Patterns file: {PATTERNS_FILE}")
    print("=" * 60)
    print("Starting server on http://localhost:8000")
    print("Endpoints:")
    print("  POST /api/memory/lessons         - Submit lesson")
    print("  GET  /api/memory/lessons         - Retrieve lessons")
    print("  GET  /api/memory/patterns        - Get patterns")
    print("  POST /api/memory/discover        - Discover patterns")
    print("  GET  /api/memory/status          - System status")
    print("=" * 60)
    app.run(host="127.0.0.1", port=8000, debug=False)
