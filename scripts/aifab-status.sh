#!/usr/bin/env bash
# aifab-status.sh — AI-Fab statusCommand for Claude Code
# Outputs 2-line status bar: model, wave progress, context, and usage.
#
# Encoding strategy:
#   - Default: ASCII-only (works on any terminal/font)
#   - Set AIFAB_STATUS_STYLE=emoji to enable emoji + box-drawing characters
#   - Set AIFAB_STATUS_STYLE=unicode for box chars only (no emoji)

# Force UTF-8 locale so multi-byte chars don't get mangled
export LC_ALL="${LC_ALL:-${LANG:-C.UTF-8}}"

STYLE="${AIFAB_STATUS_STYLE:-ascii}"

# ── style-dependent glyphs ──────────────────────────────────────────────────

case "$STYLE" in
  emoji)
    G_NAME="🏭 AI-Fab"
    G_MODEL_PREFIX="🤖"
    G_WAVE_PREFIX="📊"
    G_FILLED="█" G_EMPTY="░"
    G_WARN="⚠" G_DANGER="🔴"
    ;;
  unicode)
    G_NAME="[AI-Fab]"
    G_MODEL_PREFIX="model:"
    G_WAVE_PREFIX="wave:"
    G_FILLED="█" G_EMPTY="░"
    G_WARN="!" G_DANGER="!!"
    ;;
  *)  # ascii (default)
    G_NAME="[AI-Fab]"
    G_MODEL_PREFIX="model:"
    G_WAVE_PREFIX="wave:"
    G_FILLED="#" G_EMPTY="-"
    G_WARN="!" G_DANGER="!!"
    ;;
esac

# ── helpers ─────────────────────────────────────────────────────────────────

# Build a bar of given width using filled/empty chars
make_bar() {
  local pct=$1 width=$2
  local n_filled=$(( pct * width / 100 ))
  local bar=""
  for (( i=0; i<width; i++ )); do
    if (( i < n_filled )); then bar+="$G_FILLED"; else bar+="$G_EMPTY"; fi
  done
  printf '%s' "$bar"
}

make_bbar() {
  local pct=$1 width=$2
  printf '[%s]' "$(make_bar "$pct" "$width")"
}

# ── line 1: model ────────────────────────────────────────────────────────────

model_raw="${AIFAB_ADVISOR_MODEL:-opus-4-7}"
model="${model_raw#claude-}"   # strip "claude-" prefix

# ── line 1: wave progress ────────────────────────────────────────────────────

wave_str="${G_WAVE_PREFIX} -/-"
if [[ -f "WORKLOG.md" ]]; then
  total=$(grep -c -i '\- \[.\] wave' WORKLOG.md 2>/dev/null || echo 0)
  done=$(grep -c -i '\- \[x\] wave' WORKLOG.md 2>/dev/null || echo 0)
  if (( total > 0 )); then
    pct=$(( done * 100 / total ))
    wave_str="${G_WAVE_PREFIX} ${done}/${total} (${pct}%)"
  else
    wave_str="${G_WAVE_PREFIX} 0/0 (0%)"
  fi
fi

# ── line 1: context window ───────────────────────────────────────────────────

ctx_str="ctx --"
ctx_pct=""
for var in CLAUDE_CONTEXT_PERCENT CONTEXT_PERCENT CLAUDE_CTX_PERCENT; do
  val="${!var:-}"
  if [[ -n "$val" && "$val" =~ ^[0-9]+$ ]]; then
    ctx_pct="$val"
    break
  fi
done

if [[ -n "$ctx_pct" ]]; then
  bar=$(make_bar "$ctx_pct" 8)
  if (( ctx_pct >= 50 )); then
    icon=" $G_DANGER"
  elif (( ctx_pct >= 35 )); then
    icon=" $G_WARN"
  else
    icon=""
  fi
  ctx_str="ctx ${bar} ${ctx_pct}%${icon}"
fi

# ── line 2: usage stats (5h and 7day) ────────────────────────────────────────

STATS_FILE="$HOME/.claude/stats-cache.json"

fh_str="5h   [----------] --%"
day7_str="7day [----------] --%"

if [[ -f "$STATS_FILE" ]] && command -v python3 &>/dev/null; then
  read -r fh_pct day7_pct < <(python3 - "$STATS_FILE" <<'PYEOF'
import json, sys
from datetime import datetime, timedelta, timezone

try:
    with open(sys.argv[1]) as f:
        d = json.load(f)
except Exception:
    print("- -")
    sys.exit(0)

daily = d.get("dailyActivity", [])
if not daily:
    print("- -")
    sys.exit(0)

now = datetime.now(timezone.utc)
today_str = now.strftime("%Y-%m-%d")
by_date = {e["date"]: e for e in daily}

FH_LIMIT = 500
DAY7_LIMIT = 3500

today_entry = by_date.get(today_str, {})
fh_msgs = today_entry.get("messageCount", 0)
fh_pct = min(int(fh_msgs * 100 / FH_LIMIT), 100)

cutoff = (now - timedelta(days=7)).strftime("%Y-%m-%d")
day7_msgs = sum(
    e.get("messageCount", 0)
    for e in daily
    if e["date"] >= cutoff
)
day7_pct = min(int(day7_msgs * 100 / DAY7_LIMIT), 100)

print(f"{fh_pct} {day7_pct}")
PYEOF
  )

  if [[ "$fh_pct" =~ ^[0-9]+$ && "$day7_pct" =~ ^[0-9]+$ ]]; then
    fh_bar=$(make_bbar "$fh_pct" 10)
    day7_bar=$(make_bbar "$day7_pct" 10)
    fh_str="5h   ${fh_bar} ${fh_pct}%"
    day7_str="7day ${day7_bar} ${day7_pct}%"
  fi
fi

# ── output (single line — Claude Code statusCommand expects 1 line) ─────────

# Compact 5h/7day usage to inline form: "5h:78% 7d:41%"
fh_compact=$(echo "$fh_str" | grep -oE '[0-9]+%|--%' | head -1)
day7_compact=$(echo "$day7_str" | grep -oE '[0-9]+%|--%' | head -1)
[[ -z "$fh_compact" ]] && fh_compact="--%"
[[ -z "$day7_compact" ]] && day7_compact="--%"

printf '%s | %s %s | %s | %s | 5h:%s 7d:%s\n' \
  "$G_NAME" "$G_MODEL_PREFIX" "$model" "$wave_str" "$ctx_str" "$fh_compact" "$day7_compact"
