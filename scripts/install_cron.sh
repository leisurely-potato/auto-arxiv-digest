#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCHEDULE="${AUTO_PAPER_CRON:-0 8 * * *}"
COMMAND="$ROOT_DIR/scripts/run_daily.sh"
ENTRY="$SCHEDULE $COMMAND"

(crontab -l 2>/dev/null | grep -v "$COMMAND" || true; echo "$ENTRY") | crontab -
echo "Installed cron entry: $ENTRY"
