#!/usr/bin/env bash
# aifab-status.sh — AI-Fab statusCommand for Claude Code
#
# Design principles:
#   1. Single line output (statusCommand expects 1 line; multi-line clobbers terminal)
#   2. Pure ASCII by default (Korean/CJK rendering safe across all terminals)
#   3. Fixed-ish width (avoids terminal re-layout when content changes)
#   4. UTF-8 locale forced (prevents byte-level mangling of any Korean output elsewhere)
#   5. Defensive: every variable sanitized; no control chars can leak through
#
# Style options (env var AIFAB_STATUS_STYLE):
#   ascii   — default, pure ASCII (safest)
#   unicode — box chars (█░) but no emoji (mid-safety)
#   emoji   — full emoji (requires modern terminal + font)

# ── locale guard ─────────────────────────────────────────────────────────────
# Force UTF-8 so any multi-byte chars in upstream/downstream output render correctly.
# Try en_US.UTF-8 first (macOS default), fall back to C.UTF-8 (Linux), then existing.
if locale -a 2>/dev/null | grep -qi 'en_US\.utf-?8'; then
  export LC_ALL='en_US.UTF-8' LANG='en_US.UTF-8'
elif locale -a 2>/dev/null | grep -qi 'C\.utf-?8'; then
  export LC_ALL='C.UTF-8' LANG='C.UTF-8'
fi

# ── strict mode ──────────────────────────────────────────────────────────────
set -u  # error on unset vars (safer)

STYLE="${AIFAB_STATUS_STYLE:-ascii}"

# ── sanitizer: strip any control chars, newlines, ANSI escapes from a string ─
# Returns max 40 chars to bound width.
sanitize() {
  local s="${1:-}"
  # Remove ANSI escapes, control chars (incl. \r \n \t), keep printable ASCII + UTF-8
  s=$(printf '%s' "$s" | tr -d '\000-\037\177' | tr -d '\033')
  # Cap length to prevent overflow
  printf '%.40s' "$s"
}

# ── style glyphs ─────────────────────────────────────────────────────────────
case "$STYLE" in
  emoji)
    G_NAME="AI-Fab"; G_ICON_NAME="🏭"; G_ICON_MODEL="🤖"; G_ICON_WAVE="📊"
    G_FILLED="█"; G_EMPTY="░"
    G_WARN="⚠"; G_DANGER="🔴"
    ;;
  unicode)
    G_NAME="AI-Fab"; G_ICON_NAME=""; G_ICON_MODEL=""; G_ICON_WAVE=""
    G_FILLED="█"; G_EMPTY="░"
    G_WARN="!"; G_DANGER="!!"
    ;;
  *)
    STYLE="ascii"
    G_NAME="AI-Fab"; G_ICON_NAME=""; G_ICON_MODEL=""; G_ICON_WAVE=""
    G_FILLED="#"; G_EMPTY="-"
    G_WARN="!"; G_DANGER="!!"
    ;;
esac

# ── helpers ──────────────────────────────────────────────────────────────────
make_bar() {
  local pct=$1 width=$2
  local n_filled=$(( pct * width / 100 ))
  (( n_filled < 0 )) && n_filled=0
  (( n_filled > width )) && n_filled=width
  local i bar=""
  for (( i=0; i<width; i++ )); do
    if (( i < n_filled )); then bar+="$G_FILLED"; else bar+="$G_EMPTY"; fi
  done
  printf '%s' "$bar"
}

# ── name + model ─────────────────────────────────────────────────────────────
model_raw="${AIFAB_ADVISOR_MODEL:-opus-4-7}"
model="${model_raw#claude-}"
model=$(sanitize "$model")

if [[ -n "$G_ICON_NAME" ]]; then
  name_part="${G_ICON_NAME} ${G_NAME}"
else
  name_part="[${G_NAME}]"
fi

if [[ -n "$G_ICON_MODEL" ]]; then
  model_part="${G_ICON_MODEL} ${model}"
else
  model_part="model:${model}"
fi

# ── wave progress ────────────────────────────────────────────────────────────
wave_done=0
wave_total=0
if [[ -f "WORKLOG.md" ]]; then
  wave_total=$(grep -c -i '^[ -]*\[.\] wave' WORKLOG.md 2>/dev/null || true)
  wave_done=$(grep -c -i '^[ -]*\[x\] wave' WORKLOG.md 2>/dev/null || true)
  # Sanitize: must be plain integer
  [[ "$wave_total" =~ ^[0-9]+$ ]] || wave_total=0
  [[ "$wave_done" =~ ^[0-9]+$ ]] || wave_done=0
fi

if (( wave_total > 0 )); then
  wave_pct=$(( wave_done * 100 / wave_total ))
  if [[ -n "$G_ICON_WAVE" ]]; then
    wave_part=$(printf '%s %d/%d (%d%%)' "$G_ICON_WAVE" "$wave_done" "$wave_total" "$wave_pct")
  else
    wave_part=$(printf 'wave:%d/%d(%d%%)' "$wave_done" "$wave_total" "$wave_pct")
  fi
else
  if [[ -n "$G_ICON_WAVE" ]]; then
    wave_part="${G_ICON_WAVE} -/-"
  else
    wave_part="wave:-/-"
  fi
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
  ctx_bar=$(make_bar "$ctx_pct" 8)
  if (( ctx_pct >= 50 )); then
    ctx_icon=" ${G_DANGER}"
  elif (( ctx_pct >= 35 )); then
    ctx_icon=" ${G_WARN}"
  else
    ctx_icon=""
  fi
  ctx_part=$(printf 'ctx %s %d%%%s' "$ctx_bar" "$ctx_pct" "$ctx_icon")
else
  ctx_part="ctx --"
fi

# ── usage stats (compact: just percent) ──────────────────────────────────────
STATS_FILE="$HOME/.claude/stats-cache.json"
fh_pct="--"
day7_pct="--"

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
  [[ "${_fh:-}" =~ ^[0-9]+$ ]] && fh_pct="$_fh"
  [[ "${_day7:-}" =~ ^[0-9]+$ ]] && day7_pct="$_day7"
fi

if [[ "$fh_pct" == "--" ]]; then
  usage_part="5h:--% 7d:--%"
else
  usage_part=$(printf '5h:%s%% 7d:%s%%' "$fh_pct" "$day7_pct")
fi

# ── final output (single line, sanitized, no trailing whitespace) ────────────
# Use printf with explicit format to prevent any variable injection.
output=$(printf '%s | %s | %s | %s | %s' \
  "$name_part" "$model_part" "$wave_part" "$ctx_part" "$usage_part")

# Strip any stray control chars one more time as final guard
output=$(printf '%s' "$output" | tr -d '\000-\037\177')

# Output with single trailing newline (no \r, no extra padding)
printf '%s\n' "$output"
