#!/usr/bin/env bash
# Installs a macOS launchd job to run nightly_research_scrape.py at 02:00 local time.
# Run once: bash scripts/setup_nightly_scrape.sh

set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
PLIST_LABEL="com.v2tar.nightly-research-scrape"
PLIST_PATH="$HOME/Library/LaunchAgents/${PLIST_LABEL}.plist"
PYTHON="${REPO}/venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
  PYTHON="$(which python3)"
fi
LOG_DIR="$REPO/logs"
mkdir -p "$LOG_DIR"

cat > "$PLIST_PATH" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>${PLIST_LABEL}</string>
  <key>ProgramArguments</key>
  <array>
    <string>${PYTHON}</string>
    <string>${REPO}/scripts/nightly_research_scrape.py</string>
  </array>
  <key>WorkingDirectory</key>
  <string>${REPO}</string>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Hour</key>
    <integer>2</integer>
    <key>Minute</key>
    <integer>0</integer>
  </dict>
  <key>StandardOutPath</key>
  <string>${LOG_DIR}/nightly_scrape.log</string>
  <key>StandardErrorPath</key>
  <string>${LOG_DIR}/nightly_scrape_err.log</string>
  <key>RunAtLoad</key>
  <false/>
</dict>
</plist>
EOF

launchctl unload "$PLIST_PATH" 2>/dev/null || true
launchctl load "$PLIST_PATH"
echo "Scheduled: nightly_research_scrape at 02:00 local time"
echo "Logs: $LOG_DIR/nightly_scrape.log"
echo "To remove: launchctl unload $PLIST_PATH && rm $PLIST_PATH"
