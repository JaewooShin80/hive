#!/usr/bin/env python3
"""
aifab-status.py — AI-Fab Claude Code statusLine implementation.

Reads JSON from stdin (Claude Code passes session info this way) and renders
a single-line status bar with colored progress bars for:
  - wave progress (from WORKLOG.md in cwd)
  - context window usage (real-time from stdin)
  - 5-hour rate limit (real-time from stdin)
  - 7-day rate limit (real-time from stdin)

Color thresholds (per user request):
  ≤ 40%: green     (#46)
  ≤ 60%: yellow    (#226)
  ≤ 80%: orange    (#208)
   > 80%: red      (#196)

Style options (env var AIFAB_STATUS_STYLE):
  color (default) — ANSI 256-color + unicode bars
  plain           — no colors, ASCII bars
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Optional, Tuple

# ── style ────────────────────────────────────────────────────────────────────
STYLE = os.environ.get("AIFAB_STATUS_STYLE", "color")

if STYLE == "color":
    C_GREEN  = "\033[38;5;46m"
    C_YELLOW = "\033[38;5;226m"
    C_ORANGE = "\033[38;5;208m"
    C_RED    = "\033[38;5;196m"
    C_DIM    = "\033[38;5;240m"
    C_LABEL  = "\033[38;5;111m"
    C_NAME   = "\033[1;38;5;213m"
    C_MODEL  = "\033[38;5;156m"
    C_COST   = "\033[2;38;5;250m"
    C_RESET  = "\033[0m"
    FILLED   = "█"
    EMPTY    = "░"
    SEP      = f"\033[38;5;240m │\033[0m "
else:
    C_GREEN = C_YELLOW = C_ORANGE = C_RED = C_DIM = ""
    C_LABEL = C_NAME = C_MODEL = C_COST = C_RESET = ""
    FILLED  = "#"
    EMPTY   = "-"
    SEP     = " | "


def color_for(pct: float) -> str:
    if pct > 80:
        return C_RED
    if pct > 60:
        return C_ORANGE
    if pct > 40:
        return C_YELLOW
    return C_GREEN


def bar(pct: float, width: int = 8) -> str:
    """Colored progress bar of given width."""
    pct = max(0.0, min(100.0, pct))
    n_filled = int(pct * width / 100)
    color = color_for(pct)
    filled_part = f"{color}{FILLED * n_filled}" if n_filled > 0 else ""
    empty_part = f"{C_DIM}{EMPTY * (width - n_filled)}" if n_filled < width else ""
    return f"[{filled_part}{empty_part}{C_RESET}]"


def pct_label(pct: float) -> str:
    return f"{color_for(pct)}{int(round(pct)):>3d}%{C_RESET}"


def read_stdin_json() -> dict:
    """Read JSON from stdin (Claude Code passes session data this way).

    Returns empty dict if stdin is empty/invalid.
    """
    if sys.stdin.isatty():
        return {}
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return {}
        return json.loads(raw)
    except (json.JSONDecodeError, OSError):
        return {}


def get_model(data: dict) -> str:
    """Extract model short name."""
    raw = (
        data.get("model", {}).get("display_name")
        or data.get("model", {}).get("id")
        or os.environ.get("AIFAB_ADVISOR_MODEL", "opus-4-7")
    )
    # Strip "claude-" prefix and sanitize control chars
    raw = re.sub(r"[\x00-\x1f\x7f]", "", str(raw))
    if raw.startswith("claude-"):
        raw = raw[7:]
    return raw[:20]


def get_wave_progress() -> tuple[int, int]:
    """Parse WORKLOG.md in cwd for wave completion."""
    p = Path("WORKLOG.md")
    if not p.exists():
        return 0, 0
    try:
        content = p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return 0, 0
    total = len(re.findall(r"^[ \-]*\[.\] wave", content, re.IGNORECASE | re.MULTILINE))
    done = len(re.findall(r"^[ \-]*\[x\] wave", content, re.IGNORECASE | re.MULTILINE))
    return done, total


def get_context_pct(data: dict) -> float | None:
    """Real-time context window usage from stdin JSON.

    Claude Code reserves ~16.5% for auto-compact buffer; we normalize so 100%
    of usable context displays as 100%.
    """
    cw = data.get("context_window", {})
    remaining = cw.get("remaining_percentage")
    if remaining is None:
        # Fallback to env var (if set by some other mechanism)
        for v in ("CLAUDE_CONTEXT_PERCENT", "CONTEXT_PERCENT", "CLAUDE_CTX_PERCENT"):
            val = os.environ.get(v)
            if val and val.isdigit():
                return float(val)
        return None

    AUTO_COMPACT_BUFFER = 16.5
    used = 100 - float(remaining)
    usable_total = 100 - AUTO_COMPACT_BUFFER
    if usable_total <= 0:
        return used
    normalized = (used / usable_total) * 100
    return min(normalized, 100.0)


def get_rate_limit(data: dict, key: str) -> float | None:
    """Real-time rate limit usage."""
    rl = data.get("rate_limits", {}).get(key, {})
    pct = rl.get("used_percentage")
    return float(pct) if pct is not None else None


def get_cost(data: dict) -> float | None:
    cost = data.get("cost", {}).get("total_cost_usd")
    return float(cost) if cost is not None else None


# ── main ─────────────────────────────────────────────────────────────────────
def main() -> None:
    data = read_stdin_json()

    # name + model
    model = get_model(data)
    name_part = f"{C_NAME}AI-Fab{C_RESET}"
    model_part = f"{C_MODEL}{model}{C_RESET}"

    # wave progress
    wave_done, wave_total = get_wave_progress()
    if wave_total > 0:
        wave_pct = wave_done * 100 / wave_total
        wave_part = f"{C_LABEL}wave{C_RESET} {bar(wave_pct)} {wave_done}/{wave_total}"
    else:
        wave_part = f"{C_LABEL}wave{C_RESET} {bar(0)} -/-"

    # context window
    ctx_pct = get_context_pct(data)
    if ctx_pct is not None:
        ctx_part = f"{C_LABEL}ctx{C_RESET}  {bar(ctx_pct)} {pct_label(ctx_pct)}"
    else:
        ctx_part = f"{C_LABEL}ctx{C_RESET}  [{C_DIM}--------{C_RESET}]  --"

    # 5h rate limit
    fh_pct = get_rate_limit(data, "five_hour")
    if fh_pct is not None:
        fh_part = f"{C_LABEL}5h{C_RESET}   {bar(fh_pct)} {pct_label(fh_pct)}"
    else:
        fh_part = f"{C_LABEL}5h{C_RESET}   [{C_DIM}--------{C_RESET}]  --"

    # 7d rate limit
    d7_pct = get_rate_limit(data, "seven_day")
    if d7_pct is not None:
        d7_part = f"{C_LABEL}7d{C_RESET}   {bar(d7_pct)} {pct_label(d7_pct)}"
    else:
        d7_part = f"{C_LABEL}7d{C_RESET}   [{C_DIM}--------{C_RESET}]  --"

    # cost (bonus, if available)
    cost = get_cost(data)
    cost_part = f"{SEP}{C_COST}${cost:.3f}{C_RESET}" if cost is not None else ""

    # final assembly
    line = (
        f"{name_part} {model_part}"
        f"{SEP}{wave_part}"
        f"{SEP}{ctx_part}"
        f"{SEP}{fh_part}"
        f"{SEP}{d7_part}"
        f"{cost_part}"
    )

    # Final guard: strip any stray newlines/control chars from the output
    line = re.sub(r"[\r\n]", " ", line)
    print(line)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # Fail safe: print minimal status if anything goes wrong
        print(f"[AI-Fab] (status error: {e})")
