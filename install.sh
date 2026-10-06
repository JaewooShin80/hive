#!/usr/bin/env bash
# install.sh — HIVE harness installer (macOS / Linux / Git Bash)
#
# Thin wrapper: all logic lives in scripts/hive-install.js (shared with install.ps1).
# Idempotent: re-running is safe; existing CLAUDE.md is preserved, settings.json is merged.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v node >/dev/null 2>&1; then
  echo "error: missing dependency: node (https://nodejs.org)" >&2
  exit 3
fi

exec node "$SCRIPT_DIR/scripts/hive-install.js" "$@"
