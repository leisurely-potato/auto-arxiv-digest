#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ -f ".env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source ".env"
  set +a
fi

CONFIG_PATH="${AUTO_PAPER_CONFIG:-config.toml}"
LOG_PATH="${AUTO_PAPER_LOG:-logs/auto-paper.log}"

mkdir -p "$(dirname "$LOG_PATH")"

ARGS=(uv run auto-paper --config "$CONFIG_PATH" --log-path "$LOG_PATH" daily)
if [[ "${AUTO_PAPER_SYNC_ZOTERO:-0}" == "1" ]]; then
  ARGS+=(--sync-zotero)
fi

"${ARGS[@]}" >> "$LOG_PATH" 2>&1
