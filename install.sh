#!/usr/bin/env bash
# install.sh — AI-Fab harness installer
#
# Installs the AI-Fab Claude Code harness into a target project directory.
# Idempotent: re-running is safe; existing CLAUDE.md / settings.json are preserved.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="$(pwd)"
DRY_RUN=0
GLOBAL=0
COPY=0

usage() {
  cat <<'EOF'
Usage: install.sh [OPTIONS]

Install AI-Fab harness into a target directory.

OPTIONS:
  --target DIR    Install into DIR (default: current directory)
  --global        Also link plugin under ~/.claude/plugins (all projects)
  --copy          Copy plugin instead of symlinking (default: symlink)
  --dry-run       Show what would be done without making changes
  -h, --help      Show this help

Behavior:
  - Symlinks (or copies) .claude/plugins/aifab into TARGET/.claude/plugins/aifab
  - Copies scripts/aifab-status.{sh,py} into TARGET/scripts/
  - Copies CLAUDE.md and settings.json only if absent (no overwrite)

Examples:
  ./install.sh                        # install into cwd
  ./install.sh --target /path/to/proj # install into specific dir
  ./install.sh --global               # also link to ~/.claude/plugins/aifab
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)  TARGET="$2"; shift 2 ;;
    --global)  GLOBAL=1; shift ;;
    --copy)    COPY=1; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "error: unknown flag: $1" >&2; usage >&2; exit 2 ;;
  esac
done

run() {
  if [[ $DRY_RUN -eq 1 ]]; then
    echo "[dry-run] $*"
  else
    "$@"
  fi
}

note() {
  if [[ $DRY_RUN -eq 1 ]]; then
    echo "[dry-run] $*"
  else
    echo "$*"
  fi
}

for dep in bash python3; do
  if ! command -v "$dep" >/dev/null 2>&1; then
    echo "error: missing dependency: $dep" >&2
    exit 3
  fi
done

mkdir -p "$TARGET"
TARGET="$(cd "$TARGET" && pwd)"

if [[ "$TARGET" == "$SCRIPT_DIR" ]]; then
  echo "error: target equals harness source ($TARGET); choose a different --target" >&2
  exit 4
fi

note "→ target: $TARGET"
note "→ source: $SCRIPT_DIR"

PLUGIN_SRC="$SCRIPT_DIR/.claude/plugins/aifab"
PLUGIN_DST="$TARGET/.claude/plugins/aifab"
run mkdir -p "$TARGET/.claude/plugins"
if [[ -e "$PLUGIN_DST" || -L "$PLUGIN_DST" ]]; then
  note "  plugin already present at $PLUGIN_DST (skip)"
else
  if [[ $COPY -eq 1 ]]; then
    run cp -R "$PLUGIN_SRC" "$PLUGIN_DST"
    note "  copied plugin → $PLUGIN_DST"
  else
    run ln -s "$PLUGIN_SRC" "$PLUGIN_DST"
    note "  linked plugin → $PLUGIN_DST"
  fi
fi

run mkdir -p "$TARGET/scripts"
for f in aifab-status.sh aifab-status.py; do
  src="$SCRIPT_DIR/scripts/$f"
  dst="$TARGET/scripts/$f"
  if [[ -e "$dst" ]]; then
    note "  scripts/$f already present (skip)"
  else
    run cp "$src" "$dst"
    run chmod +x "$dst"
    note "  installed scripts/$f"
  fi
done

if [[ -e "$TARGET/CLAUDE.md" ]]; then
  note "  CLAUDE.md already present — preserved (no overwrite)"
else
  run cp "$SCRIPT_DIR/CLAUDE.md" "$TARGET/CLAUDE.md"
  note "  installed CLAUDE.md"
fi

run mkdir -p "$TARGET/.claude"
if [[ -e "$TARGET/.claude/settings.json" ]]; then
  note "  .claude/settings.json already present — preserved (no overwrite)"
else
  run cp "$SCRIPT_DIR/.claude/settings.json" "$TARGET/.claude/settings.json"
  note "  installed .claude/settings.json"
fi

if [[ $GLOBAL -eq 1 ]]; then
  GLOBAL_DIR="$HOME/.claude/plugins/aifab"
  run mkdir -p "$HOME/.claude/plugins"
  if [[ -e "$GLOBAL_DIR" || -L "$GLOBAL_DIR" ]]; then
    note "  global plugin already present at $GLOBAL_DIR (skip)"
  else
    run ln -s "$PLUGIN_SRC" "$GLOBAL_DIR"
    note "  linked global plugin → $GLOBAL_DIR"
  fi
fi

note ""
note "✓ AI-Fab harness installed."
note "  Run 'claude' inside $TARGET, then try /aifab:discover"
