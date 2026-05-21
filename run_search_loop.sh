#!/bin/bash
# Runs continuous parameter search in a loop until Tuesday 2026-05-19 23:59.
# Results appended to logs/search_loop.log

set -e
cd "$(dirname "$0")"
source venv/bin/activate

LOGFILE="logs/search_loop.log"
DEADLINE=$(date -j -f "%Y-%m-%d" "2026-05-20" "+%s")
mkdir -p logs

echo "=== Search loop started at $(date) ===" | tee -a "$LOGFILE"

RUN=1
while [ "$(date +%s)" -lt "$DEADLINE" ]; do
    echo "" | tee -a "$LOGFILE"
    echo "--- Run #$RUN started at $(date) ---" | tee -a "$LOGFILE"

    python scripts/continuous_parameter_search.py \
        --fresh \
        --max-generations 4 \
        --max-candidates 300 \
        --survivors 5 \
        --target-keeps 3 \
        2>&1 | tee -a "$LOGFILE"

    echo "--- Run #$RUN finished at $(date) ---" | tee -a "$LOGFILE"

    # Report summary
    python - <<'EOF' 2>/dev/null | tee -a "$LOGFILE"
import json, pathlib
p = pathlib.Path("data/results/parameter_search/continuous_parameter_search_summary.json")
if p.exists():
    d = json.loads(p.read_text())
    print(f"  verdicts: {d.get('verdict_counts')}")
    keeps = [c for c in d.get('top_candidates', []) if c.get('verdict') == 'KEEP']
    if keeps:
        print(f"  KEEP candidates: {len(keeps)}")
        for k in keeps:
            print(f"    {k['strategy']} {k['symbol']} score={k['score']}")
EOF

    RUN=$((RUN + 1))

    if [ "$(date +%s)" -ge "$DEADLINE" ]; then
        break
    fi

    echo "  Sleeping 10 min before next run..." | tee -a "$LOGFILE"
    sleep 600
done

echo "" | tee -a "$LOGFILE"
echo "=== Search loop finished at $(date) (deadline reached) ===" | tee -a "$LOGFILE"
