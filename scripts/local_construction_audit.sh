#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHONPATH=src venv/bin/python -m tar_system.cli run-local-construction-audit \
  --tool opengrep \
  --target src \
  --scan-output runtime/static_analysis/opengrep.json \
  --packet-output runtime/ai_review_packet.md \
  --limit 10 \
  --fail-on-findings
