#!/usr/bin/env bash
# hive-status.sh — HIVE statusCommand for Claude Code
# Wrapper that pipes stdin JSON to the python implementation.
exec /usr/bin/env python3 "$(dirname "$0")/hive-status.py" "$@"
