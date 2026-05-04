#!/usr/bin/env bash
# aifab-status.sh — AI-Fab statusCommand for Claude Code
#
# Design:
#   1. Single line, compact, color-coded progress bars
#   2. 4-tier traffic light: 0-40% green, 40-60% yellow, 60-80% orange, 80%+ red
#   3. Pure ANSI escapes (works in any modern terminal)
#   4. UTF-8 locale forced + sanitization
#
# Style options (env var AIFAB_STATUS_STYLE):
#   color   — default, ANSI 256-color + unicode bars
#   plain   — no colors, ASCII bars (for log capture / unsupported terminals)

# ── locale guard ─────────────────────────────────────────────────────────────
if locale -a 2>/dev/null | grep -qi 'en_US\.utf-?8'; then
  export LC_ALL='en_US.UTF-8' LANG='en_US.UTF-8'
elif locale -a 2>/dev/null | grep -qi 'C\.utf-?8'; then
  export LC_ALL='C.UTF-8' LANG='C.UTF-8'
fi

set -u

STYLE="${AIFAB_STATUS_STYLE:-color}"

# ── ANSI color codes ─────────────────────────────────────────────────────────
if [[ "$STYLE" == "color" ]]; then
  C_GREEN=$'\033[38;5;46m'      # bright green (≤40%)
  C_YELLOW=$'\033[38;5;226m'    # yellow (40-60%)
  C_ORANGE=$'\033[38;5;208m'    # orange (60-80%)
  C_RED=$'\033[38;5;196m'       # bright red (>80%)
  C_DIM=$'\033[38;5;240m'       # dark grey for empty bar
  C_LABEL=$'\033[38;5;111m'     # light blue for labels
  C_NAME=$'\033[1;38;5;213m'    # bold pink for name
  C_MODEL=$'\033[38;5;156m'     # light green for model
  C_RESET=$'\033[0m'
  C_BOLD=$'\033[1m'
  FILLED='█'
  EMPTY='░'
  SEP=$'\033[38;5;240m │\033[0m'
else
  C_GREEN='' C_YELLOW='' C_ORANGE='' C_RED='' C_DIM=''
  C_LABEL='' C_NAME='' C_MODEL='' C_RESET='' C_BOLD=''
  FILLED='#'
  EMPTY='-'
  SEP=' | '
fi

# ── color picker by percentage ───────────────────────────────────────────────
color_for_pct() {
  local pct=$1
  if (( pct > 80 )); then
    printf '%s' "$C_RED"
  elif (( pct > 60 )); then
    printf '%s' "$C_ORANGE"
  elif (( pct > 40 )); then
    printf '%s' "$C_YELLOW"
  else
    printf '%s' "$C_GREEN"
  fi
}

# ── colored bar generator ────────────────────────────────────────────────────
# Args: pct width
# Output: [<filled-color>███<dim>░░░<reset>]
make_cbar() {
  local pct=$1 width=$2
  (( pct < 0 )) && pct=0
  (( pct > 100 )) && pct=100
  local n_filled=$(( pct * width / 100 ))
  local color=$(color_for_pct "$pct")
  local i bar=""

  # filled portion
  if (( n_filled > 0 )); then
    bar+="$color"
    for (( i=0; i<n_filled; i++ )); do bar+="$FILLED"; done
  fi
  # empty portion
  if (( n_filled < width )); then
    bar+="$C_DIM"
    for (( i=n_filled; i<width; i++ )); do bar+="$EMPTY"; done
  fi
  bar+="$C_RESET"
  printf '[%s]' "$bar"
}

# ── colored percent label ────────────────────────────────────────────────────
make_pct_label() {
  local pct=$1
  local color=$(color_for_pct "$pct")
  printf '%s%3d%%%s' "$color" "$pct" "$C_RESET"
}

# ── name + model ─────────────────────────────────────────────────────────────
model_raw="${AIFAB_ADVISOR_MODEL:-opus-4-7}"
model="${model_raw#claude-}"
# sanitize: strip control chars
model=$(printf '%s' "$model" | tr -d '\000-\037\177' | head -c 20)

name_part="${C_NAME}AI-Fab${C_RESET}"
model_part="${C_MODEL}${model}${C_RESET}"

# ── wave progress ────────────────────────────────────────────────────────────
wave_done=0
wave_total=0
if [[ -f "WORKLOG.md" ]]; then
  wave_total=$(grep -c -i '^[ -]*\[.\] wave' WORKLOG.md 2>/dev/null || true)
  wave_done=$(grep -c -i '^[ -]*\[x\] wave' WORKLOG.md 2>/dev/null || true)
  [[ "$wave_total" =~ ^[0-9]+$ ]] || wave_total=0
  [[ "$wave_done" =~ ^[0-9]+$ ]] || wave_done=0
fi

if (( wave_total > 0 )); then
  wave_pct=$(( wave_done * 100 / wave_total ))
  wave_bar=$(make_cbar "$wave_pct" 8)
  wave_part="${C_LABEL}wave${C_RESET} ${wave_bar} ${wave_done}/${wave_total}"
else
  wave_bar=$(make_cbar 0 8)
  wave_part="${C_LABEL}wave${C_RESET} ${wave_bar} -/-"
fi

# ── context window ───────────────────────────────────────────────────────────
ctx_pct=""
for var in CLAUDE_CONTEXT_PERCENT CONTEXT_PERCENT CLAUDE_CTX_PERCENT; do
  val="${!var:-}"
  if [[ "$val" =~ ^[0-9]+$ ]] && (( val >= 0 && val <= 100 )); then
    ctx_pct="$val"
    break
  fi
done

if [[ -n "$ctx_pct" ]]; then
  ctx_bar=$(make_cbar "$ctx_pct" 8)
  ctx_pct_label=$(make_pct_label "$ctx_pct")
  ctx_part="${C_LABEL}ctx${C_RESET}  ${ctx_bar} ${ctx_pct_label}"
else
  ctx_bar="[${C_DIM}--------${C_RESET}]"
  ctx_part="${C_LABEL}ctx${C_RESET}  ${ctx_bar}  --"
fi

# ── usage stats ──────────────────────────────────────────────────────────────
STATS_FILE="$HOME/.claude/stats-cache.json"
fh_pct=0
day7_pct=0
fh_known=0
day7_known=0

if [[ -f "$STATS_FILE" ]] && command -v python3 &>/dev/null; then
  read -r _fh _day7 < <(python3 - "$STATS_FILE" 2>/dev/null <<'PYEOF'
import json, sys
from datetime import datetime, timedelta, timezone
try:
    with open(sys.argv[1]) as f:
        d = json.load(f)
    daily = d.get("dailyActivity", [])
    if not daily:
        print("- -"); sys.exit(0)
    now = datetime.now(timezone.utc)
    today = now.strftime("%Y-%m-%d")
    by_date = {e["date"]: e for e in daily}
    FH_LIMIT, DAY7_LIMIT = 500, 3500
    fh = min(int(by_date.get(today, {}).get("messageCount", 0) * 100 / FH_LIMIT), 100)
    cutoff = (now - timedelta(days=7)).strftime("%Y-%m-%d")
    d7 = sum(e.get("messageCount", 0) for e in daily if e["date"] >= cutoff)
    d7 = min(int(d7 * 100 / DAY7_LIMIT), 100)
    print(f"{fh} {d7}")
except Exception:
    print("- -")
PYEOF
)
  if [[ "${_fh:-}" =~ ^[0-9]+$ ]]; then fh_pct=$_fh; fh_known=1; fi
  if [[ "${_day7:-}" =~ ^[0-9]+$ ]]; then day7_pct=$_day7; day7_known=1; fi
fi

if (( fh_known )); then
  fh_bar=$(make_cbar "$fh_pct" 8)
  fh_label=$(make_pct_label "$fh_pct")
  fh_part="${C_LABEL}5h${C_RESET}   ${fh_bar} ${fh_label}"
else
  fh_bar="[${C_DIM}--------${C_RESET}]"
  fh_part="${C_LABEL}5h${C_RESET}   ${fh_bar}  --"
fi

if (( day7_known )); then
  day7_bar=$(make_cbar "$day7_pct" 8)
  day7_label=$(make_pct_label "$day7_pct")
  day7_part="${C_LABEL}7d${C_RESET}   ${day7_bar} ${day7_label}"
else
  day7_bar="[${C_DIM}--------${C_RESET}]"
  day7_part="${C_LABEL}7d${C_RESET}   ${day7_bar}  --"
fi

# ── final output (single line) ───────────────────────────────────────────────
printf '%s %s%s%s%s%s%s%s%s\n' \
  "$name_part" \
  "$model_part" \
  "$SEP" "$wave_part" \
  "$SEP" "$ctx_part" \
  "$SEP" "$fh_part" \
  "$SEP$day7_part"
