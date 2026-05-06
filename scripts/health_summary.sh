#!/bin/bash
cd /Users/whs1/Dev/V2trading_system
source venv/bin/activate

echo "=== TEST COUNT ==="
PYTHONPATH=src python -m pytest --collect-only -q 2>/dev/null | tail -3

echo "=== CLI COMMANDS ==="
PYTHONPATH=src python -m tar_system.cli --help 2>/dev/null

echo "=== DATA FILES ==="
echo "validated:"
ls data/validated/ 2>/dev/null
echo "features:"
ls data/features/ 2>/dev/null

echo "=== RECENT CHANGELOG ==="
tail -20 CHANGELOG.md

echo "=== MODULE COUNT ==="
find src -name "*.py" | wc -l

echo "=== LAST AUDIT EVENT ==="
tail -1 logs/audit/audit.jsonl 2>/dev/null
