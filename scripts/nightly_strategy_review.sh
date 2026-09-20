#!/usr/bin/env bash
# nightly_strategy_review.sh
# Walk-forward + DSR check on all COMPLETED candidates nightly.
# Wired into auto-builder loop via V2 collab/TASKS.md.
#
# Usage: bash scripts/nightly_strategy_review.sh [--dry-run]
# Output: logs/nightly-review-YYYY-MM-DD.log
#         reports/nightly-wf-YYYY-MM-DD.json

set -euo pipefail

DRY_RUN=false
for arg in "$@"; do [[ "$arg" == "--dry-run" ]] && DRY_RUN=true; done

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_DIR="$PROJECT_ROOT/logs"
mkdir -p "$LOG_DIR"

TODAY=$(date +%Y-%m-%d)
LOG="$LOG_DIR/nightly-review-$TODAY.log"

# Lock guard — prevent duplicate concurrent runs (e.g. two LaunchAgents)
LOCK="$LOG_DIR/nightly-review-$TODAY.lock"
if [[ -f "$LOCK" ]]; then
  echo "[$(date '+%H:%M:%S')] Already ran today ($LOCK exists). Exiting." | tee -a "$LOG"
  exit 0
fi
touch "$LOCK"
# Remove lock on abnormal exit so the next run can proceed
trap 'rm -f "$LOCK"' ERR

PYTHON="$PROJECT_ROOT/venv/bin/python3"
[[ -x "$PYTHON" ]] || PYTHON="python3"

log() { echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOG"; }

log "=== V2 nightly strategy review start | dry=$DRY_RUN | $TODAY ==="

# 1. Compile check
log "Compile check..."
if ! "$PYTHON" -m py_compile \
  "$PROJECT_ROOT/src/tar_system/validation/bootstrap_ci.py" \
  "$PROJECT_ROOT/src/tar_system/validation/walk_forward.py" \
  "$PROJECT_ROOT/src/tar_system/cli_walk_forward.py" \
  "$PROJECT_ROOT/scripts/run_nightly_wf.py" 2>>"$LOG"; then
  log "ERROR: compile failed — aborting"
  exit 1
fi
log "Compile: OK"

# 2. Queue health check
CLI="$PROJECT_ROOT/src/tar_system/cli.py"
if [[ -f "$CLI" ]]; then
  log "Queue health check..."
  PYTHONPATH="$PROJECT_ROOT/src" "$PYTHON" -m tar_system.cli queue-health --limit 5 2>>"$LOG" | tee -a "$LOG" || log "queue-health returned non-zero (check log)"
fi

# 3. Walk-forward + DSR on all COMPLETED candidates
log "Starting WF+DSR run..."
EXTRA_ARGS=""
[[ "$DRY_RUN" == true ]] && EXTRA_ARGS="--dry-run"

PYTHONPATH="$PROJECT_ROOT/src" "$PYTHON" \
  "$PROJECT_ROOT/scripts/run_nightly_wf.py" \
  $EXTRA_ARGS \
  2>>"$LOG" | tee -a "$LOG"

log "=== V2 nightly review done ==="
