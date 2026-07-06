#!/usr/bin/env bash
# nightly_strategy_review.sh
# Automated V2 strategy review: run walk-forward + DSR check, log results.
# Called by auto-builder or launchd on schedule.
#
# Usage: bash scripts/nightly_strategy_review.sh [--dry-run]
#
# Output: logs/nightly-review-YYYY-MM-DD.log

set -euo pipefail

DRY_RUN=false
for arg in "$@"; do [[ "$arg" == "--dry-run" ]] && DRY_RUN=true; done

LOG_DIR="$(dirname "$0")/../logs"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/nightly-review-$(date +%Y-%m-%d).log"
PYTHON="$(dirname "$0")/../venv/bin/python3.14"
[[ -x "$PYTHON" ]] || PYTHON="python3"

log() { echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOG"; }

log "=== V2 nightly strategy review start | dry=$DRY_RUN ==="

# 1. Health check — verify system is intact
if [[ -f "$(dirname "$0")/../src/tar_system/validation/bootstrap_ci.py" ]]; then
  log "bootstrap_ci.py present — DSR available"
else
  log "WARNING: bootstrap_ci.py missing"
fi

# 2. Compile check on core validation files
log "Compile check..."
if "$PYTHON" -m py_compile \
  "$(dirname "$0")/../src/tar_system/validation/bootstrap_ci.py" \
  "$(dirname "$0")/../src/tar_system/regime/detector.py" 2>>"$LOG"; then
  log "Compile: OK"
else
  log "ERROR: compile failed — see log"
  exit 1
fi

# 3. Run queue health check
CLI="$(dirname "$0")/../src/tar_system/cli.py"
if [[ -f "$CLI" ]]; then
  log "Checking queue health..."
  if [[ "$DRY_RUN" == false ]]; then
    PYTHONPATH="$(dirname "$0")/../src" "$PYTHON" -m tar_system.cli queue-health --limit 5 2>>"$LOG" | tee -a "$LOG" || log "queue-health returned non-zero (review log)"
  else
    log "[DRY RUN] Would run: python -m tar_system.cli queue-health --limit 5"
  fi
fi

# 4. DSR spot-check on any staged candidates
CANDIDATES_DIR="$(dirname "$0")/../data/candidates"
if [[ -d "$CANDIDATES_DIR" ]]; then
  count=$(ls "$CANDIDATES_DIR"/*.json 2>/dev/null | wc -l | tr -d ' ')
  log "Found $count candidate files in data/candidates/"
  if [[ "$DRY_RUN" == false && "$count" -gt 0 ]]; then
    "$PYTHON" - <<'PYEOF' 2>>"$LOG" | tee -a "$LOG"
import json, sys, glob
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from tar_system.validation.bootstrap_ci import deflated_sharpe_ratio

candidates_dir = Path(__file__).parent.parent / "data" / "candidates"
files = sorted(candidates_dir.glob("*.json"))
print(f"  DSR check on {len(files)} candidate(s):")
for f in files[:20]:  # cap at 20
    try:
        data = json.loads(f.read_text())
        returns = data.get("trade_returns", data.get("returns", []))
        n_trials = data.get("n_trials", 100)
        if returns:
            result = deflated_sharpe_ratio(returns, n_trials=n_trials)
            verdict = "PASS" if result["dsr_p_value"] < 0.05 else "REVIEW"
            print(f"  {f.stem}: SR={result['sr']} DSR_p={result['dsr_p_value']} → {verdict}")
    except Exception as e:
        print(f"  {f.stem}: error — {e}")
PYEOF
  fi
fi

log "=== V2 nightly review done ==="
