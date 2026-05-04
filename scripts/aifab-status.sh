#!/usr/bin/env bash
# aifab-status.sh — AI-Fab statusCommand for Claude Code
# Wrapper that pipes stdin JSON to the python implementation.
exec /usr/bin/env python3 "$(dirname "$0")/aifab-status.py" "$@"
