#!/usr/bin/env python3
"""
hive-status.py — HIVE Claude Code statusLine implementation.

Reads JSON from stdin (Claude Code passes session info this way) and renders
a 2-line Powerline-style status bar with:
  Line 1: name · git · model (tier glyph + display_name) · cost
  Line 2: Milestone/Phase/Wave · ctx · 5h (pacing+reset) · 7d (pacing+reset)

Color thresholds:
  ≤ 40%: green     (#46)
  ≤ 60%: yellow    (#226)
  ≤ 80%: orange    (#208)
   > 80%: red      (#196)

Style options (env var HIVE_STATUS_STYLE):
  powerline (default) — 2-line, ANSI 256-color, Unicode bars + pacing tick
  color               — legacy single-line
  plain               — single-line, no colors, ASCII bars
"""

from __future__ import annotations

import io
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

# Force UTF-8 on Windows (cp949 can't encode Unicode bar characters)
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if sys.stdin.encoding and sys.stdin.encoding.lower() != "utf-8":
    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8", errors="replace")

# ── style ────────────────────────────────────────────────────────────────────
STYLE = os.environ.get("HIVE_STATUS_STYLE", "powerline")

if STYLE in ("powerline", "color"):
    C_GREEN  = "\033[38;5;46m"
    C_YELLOW = "\033[38;5;226m"
    C_ORANGE = "\033[38;5;208m"
    C_RED    = "\033[38;5;196m"
    C_DIM    = "\033[38;5;240m"
    C_LABEL  = "\033[38;5;111m"
    C_NAME   = "\033[1;38;5;213m"
    C_MODEL  = "\033[38;5;156m"
    C_COST   = "\033[2;38;5;250m"
    C_GIT    = "\033[38;5;214m"
    C_TICK   = "\033[97m"
    C_RESET  = "\033[0m"
    FILLED   = "█"
    EMPTY    = "░"
    TICK     = "│"
    SEP      = f"{C_DIM} │{C_RESET} "
else:
    C_GREEN = C_YELLOW = C_ORANGE = C_RED = C_DIM = ""
    C_LABEL = C_NAME = C_MODEL = C_COST = C_GIT = C_TICK = C_RESET = ""
    FILLED  = "#"
    EMPTY   = "-"
    TICK    = "|"
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
    pct = max(0.0, min(100.0, pct))
    n_filled = int(pct * width / 100)
    color = color_for(pct)
    filled_part = f"{color}{FILLED * n_filled}" if n_filled > 0 else ""
    empty_part = f"{C_DIM}{EMPTY * (width - n_filled)}" if n_filled < width else ""
    return f"[{filled_part}{empty_part}{C_RESET}]"


def bar_with_pacing(pct: float, pacing_pct: Optional[float], width: int = 8) -> str:
    """Bar with a white pacing tick at the pacing_pct position.

    pacing_pct = how far through the rate-limit window we are (0–100).
    Visual: if `pct` (actual usage) is left of the tick, we are under pace.
    """
    pct = max(0.0, min(100.0, pct))
    if pacing_pct is None:
        return bar(pct, width)
    pacing_pct = max(0.0, min(100.0, pacing_pct))
    n_filled = int(pct * width / 100)
    n_pacing = int(pacing_pct * width / 100)
    color = color_for(pct)
    cells: List[str] = []
    for i in range(width):
        if i < n_filled:
            cells.append(f"{color}{FILLED}{C_RESET}")
        else:
            cells.append(f"{C_DIM}{EMPTY}{C_RESET}")
    if 0 <= n_pacing < width:
        cells[n_pacing] = f"{C_TICK}{TICK}{C_RESET}"
    return f"[{''.join(cells)}]"


def pct_label(pct: float) -> str:
    return f"{color_for(pct)}{int(round(pct)):>3d}%{C_RESET}"


def read_stdin_json() -> dict:
    if sys.stdin.isatty():
        return {}
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return {}
        return json.loads(raw)
    except (json.JSONDecodeError, OSError):
        return {}


# ── model detection ──────────────────────────────────────────────────────────
TIER_GLYPHS = (
    ("opus",   "\u25c6"),  # ◆
    ("sonnet", "\u25c7"),  # ◇
    ("haiku",  "\u25cb"),  # ○
)
DEFAULT_GLYPH = "\u25c8"   # ◈


def get_model(data: dict) -> Tuple[str, str]:
    """Return (display_name, tier_glyph).

    Priority: JSON display_name → JSON id → env HIVE_ADVISOR_MODEL → "claude".
    JSON-first so newly-released models display automatically without config edits.
    """
    raw = (
        data.get("model", {}).get("display_name")
        or data.get("model", {}).get("id")
        or os.environ.get("HIVE_ADVISOR_MODEL")
        or "claude"
    )
    raw = re.sub(r"[\x00-\x1f\x7f]", "", str(raw))
    if raw.startswith("claude-"):
        raw = raw[7:]
    name = raw[:20]
    lower = name.lower()
    glyph = next((g for k, g in TIER_GLYPHS if k in lower), DEFAULT_GLYPH)
    return name, glyph


# ── thinking effort ──────────────────────────────────────────────────────────
EFFORT_GLYPHS = {
    "low":    "\u25cb",      # ○
    "medium": "\u25d0",      # ◐
    "high":   "\u25cf",      # ●
    "xhigh":  "\u26a1",      # ⚡
    "max":    "\u26a1",      # ⚡
    "think":  "\u26a1",
}


def _read_settings_effort() -> Optional[str]:
    """Read 'effortLevel' from Claude Code settings.json (user-global)."""
    candidates = [
        Path.home() / ".claude" / "settings.json",
        Path(os.environ.get("CLAUDE_CONFIG_DIR", "")) / "settings.json"
        if os.environ.get("CLAUDE_CONFIG_DIR") else None,
    ]
    for p in candidates:
        if p is None or not p.exists():
            continue
        try:
            cfg = json.loads(p.read_text(encoding="utf-8", errors="replace"))
        except (json.JSONDecodeError, OSError):
            continue
        v = cfg.get("effortLevel") or cfg.get("thinkingLevel")
        if v:
            return str(v)
    return None


def get_effort(data: dict) -> Optional[Tuple[str, str]]:
    """Return (label, glyph) for current thinking/reasoning effort, or None.

    Sources, in priority order:
      1. env HIVE_EFFORT (manual override)
      2. stdin JSON: thinking_effort / reasoning_effort / effort / model.thinking_effort
      3. ~/.claude/settings.json → effortLevel
    """
    candidates = [
        os.environ.get("HIVE_EFFORT"),
        data.get("thinking_effort"),
        data.get("reasoning_effort"),
        data.get("effort"),
        data.get("model", {}).get("thinking_effort") if isinstance(data.get("model"), dict) else None,
        _read_settings_effort(),
    ]
    for c in candidates:
        if c is None:
            continue
        if isinstance(c, dict):
            c = c.get("level") or c.get("value")
            if not c:
                continue
        s = str(c).strip().lower()
        if not s or s in ("default", "normal", "none"):
            continue
        glyph = EFFORT_GLYPHS.get(s, "\u25c8")  # ◈ fallback
        return s[:6], glyph
    return None


# ── active harness / skill detection (transcript scan) ───────────────────────
def get_active_harness(data: dict) -> Optional[str]:
    """Scan the recent transcript for the latest Skill tool invocation.

    Returns a short harness label: 'HIVE', 'GSD', 'Superpowers', or the
    skill name itself (truncated) for others. Returns None if no recent
    Skill invocation is found.
    """
    # Manual env override wins
    override = os.environ.get("HIVE_HARNESS")
    if override:
        return override[:16]

    tp = data.get("transcript_path")
    if not tp:
        return None
    try:
        p = Path(tp)
        if not p.exists() or not p.is_file():
            return None
        size = p.stat().st_size
        with p.open("rb") as f:
            if size > 80_000:
                f.seek(size - 80_000)
                f.readline()  # discard partial first line
            tail = f.read().decode("utf-8", errors="replace")
    except OSError:
        return None

    skill_name: Optional[str] = None
    for line in reversed(tail.splitlines()):
        line = line.strip()
        if not line or line[0] != "{":
            continue
        try:
            obj = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue
        # Transcript shape: {"type":"assistant","message":{"content":[{"type":"tool_use","name":"Skill","input":{"skill":"..."}}]}}
        msg = obj.get("message") if isinstance(obj.get("message"), dict) else obj
        content = msg.get("content") if isinstance(msg, dict) else None
        if not isinstance(content, list):
            continue
        for item in content:
            if not isinstance(item, dict):
                continue
            if item.get("type") == "tool_use" and item.get("name") == "Skill":
                cand = (item.get("input") or {}).get("skill")
                if cand:
                    skill_name = str(cand)
                    break
        if skill_name:
            break

    if not skill_name:
        return None

    sn = skill_name.lower()
    if sn.startswith("hive:") or sn.startswith("hive-") or sn == "hive":
        return "HIVE"
    if sn.startswith("gsd-") or sn.startswith("gsd:") or sn == "gsd":
        return "GSD"
    if "superpower" in sn:
        return "Superpowers"
    # Other skills: drop prefix before ':' and truncate
    bare = skill_name.split(":", 1)[1] if ":" in skill_name else skill_name
    return bare[:16]


# ── progress: Milestone / Phase / Wave ───────────────────────────────────────
PHASE_HEADER_RE = re.compile(
    r"^##\s+Phase\s+(\d+):\s+(.+?)\s+\(Wave\s+(\d+)-(\d+)\)\s+(\u2705|\U0001f7e1|\u2b1c)\s+(complete|in_progress|pending)",
    re.MULTILINE,
)
MILESTONE_RE = re.compile(r"^>\s*\*\*\ub9c8\uc77c\uc2a4\ud1a4:\*\*\s+(\S+)", re.MULTILINE)
WAVE_HEADER_RE = re.compile(r"^##\s+Wave\s+(\d+)", re.MULTILINE)


@dataclass
class Phase:
    number: int
    name: str
    wave_range: Tuple[int, int]
    status: str


def _seed_dirs(data: dict) -> List[Path]:
    dirs: List[Path] = []
    ws = data.get("workspace", {})
    for key in ("project_dir", "current_dir"):
        v = ws.get(key) or data.get("cwd")
        if v:
            dirs.append(Path(str(v)))
    dirs.append(Path.cwd())
    return dirs


def _find_file(seed_dirs: List[Path], filename: str) -> Optional[Path]:
    home = Path.home()
    seen: set = set()
    for seed in seed_dirs:
        p = seed
        while True:
            candidate = p / filename
            if candidate not in seen:
                seen.add(candidate)
                if candidate.exists():
                    return candidate
            if p == home or p.parent == p:
                break
            p = p.parent
    return None


def get_hive_progress(data: dict) -> Optional[str]:
    """Return formatted Milestone/Phase/Wave string, or None if no roadmap+plan."""
    seeds = _seed_dirs(data)
    roadmap_path = _find_file(seeds, "ROADMAP.md")
    plan_path = _find_file(seeds, "PLAN.md")

    if not plan_path and not roadmap_path:
        return None

    # Parse PLAN.md → completed waves + total
    completed: List[int] = []
    total_waves = 0
    if plan_path:
        try:
            plan_text = plan_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            plan_text = ""
        current_wave: Optional[int] = None
        for line in plan_text.splitlines():
            wm = WAVE_HEADER_RE.match(line)
            if wm:
                current_wave = int(wm.group(1))
                total_waves += 1
            elif current_wave is not None and "[x]" in line.lower():
                if current_wave not in completed:
                    completed.append(current_wave)

    # Parse ROADMAP.md → milestone + phases
    milestone: Optional[str] = None
    phases: List[Phase] = []
    current_phase: Optional[Phase] = None
    if roadmap_path:
        try:
            rm_text = roadmap_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            rm_text = ""
        mm = MILESTONE_RE.search(rm_text)
        if mm:
            milestone = mm.group(1)[:12]
        for m in PHASE_HEADER_RE.finditer(rm_text):
            phases.append(Phase(
                number=int(m.group(1)),
                name=m.group(2).strip(),
                wave_range=(int(m.group(3)), int(m.group(4))),
                status=m.group(6),
            ))
        current_phase = next(
            (p for p in phases if p.status == "in_progress"),
            next((p for p in phases if p.status == "pending"), None),
        )

    parts: List[str] = []
    if milestone:
        parts.append(f"{C_LABEL}M{C_RESET}{milestone}")
    if phases and current_phase:
        parts.append(f"{C_LABEL}P{C_RESET}{current_phase.number}/{len(phases)}")
    if total_waves > 0:
        done = len(completed)
        pct = int(round(done * 100 / total_waves))
        # progress color: more done = greener (invert threshold)
        col = color_for(100 - pct)
        parts.append(f"{C_LABEL}W{C_RESET}{done}/{total_waves} {col}{pct}%{C_RESET}")

    if not parts:
        return None
    return f" {C_DIM}\u00b7{C_RESET} ".join(parts)


def get_wave_progress_fallback(data: dict) -> Tuple[int, int]:
    """WORKLOG.md fallback when ROADMAP+PLAN absent."""
    seeds = _seed_dirs(data)
    worklog = _find_file(seeds, "WORKLOG.md")
    if not worklog:
        return 0, 0
    try:
        content = worklog.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return 0, 0
    total = len(re.findall(r"^[ \-]*\[.\] wave", content, re.IGNORECASE | re.MULTILINE))
    done = len(re.findall(r"^[ \-]*\[x\] wave", content, re.IGNORECASE | re.MULTILINE))
    return done, total


# ── context window ──────────────────────────────────────────────────────────
def get_context_pct(data: dict) -> Optional[float]:
    cw = data.get("context_window", {})
    remaining = cw.get("remaining_percentage")
    if remaining is None:
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


def write_ctx_bridge(data: dict, ctx_pct: Optional[float]) -> None:
    """Write context metrics to /tmp/hive-ctx-{session_id}.json for hooks.

    Consumed by hive-ctx-guard PostToolUse hook (CLAUDE.md RULE 5).
    Best-effort: silently no-ops on missing session_id, path-traversal patterns,
    or I/O errors so statusline rendering is never blocked.
    """
    if ctx_pct is None:
        return
    session_id = data.get("session_id")
    if not isinstance(session_id, str) or not session_id:
        return
    if "/" in session_id or "\\" in session_id or ".." in session_id:
        return
    try:
        import tempfile
        path = Path(tempfile.gettempdir()) / f"hive-ctx-{session_id}.json"
        payload = {
            "used_pct": round(float(ctx_pct), 2),
            "remaining_percentage": round(100 - float(ctx_pct), 2),
            "timestamp": int(time.time()),
        }
        path.write_text(json.dumps(payload), encoding="utf-8")
    except (OSError, ValueError):
        pass


# ── rate limits ─────────────────────────────────────────────────────────────
def get_rate_limit(data: dict, key: str) -> Tuple[Optional[float], object]:
    rl = data.get("rate_limits", {}).get(key, {})
    pct = rl.get("used_percentage")
    resets_at = rl.get("resets_at")
    return (float(pct) if pct is not None else None, resets_at)


def _resets_at_to_epoch(resets_at) -> Optional[int]:
    if resets_at is None:
        return None
    try:
        if isinstance(resets_at, (int, float)):
            return int(resets_at)
        s = str(resets_at)
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return int(dt.timestamp())
    except Exception:
        return None


def format_reset_time(resets_at) -> str:
    """Render remaining time until reset. Days for ≥24h, hours+minutes otherwise."""
    epoch = _resets_at_to_epoch(resets_at)
    if epoch is None:
        return ""
    diff = epoch - int(time.time())
    if diff <= 0:
        return ""
    hourglass = "\u23f3"  # ⏳
    if diff >= 86400:
        d, rem = divmod(diff, 86400)
        h = rem // 3600
        return f" {C_DIM}{hourglass}{d}d{h}h{C_RESET}"
    h, rem = divmod(diff, 3600)
    m = rem // 60
    return f" {C_DIM}{hourglass}{h}h{m}m{C_RESET}"


def compute_pacing(resets_at, window_seconds: int) -> Optional[float]:
    """How far through the rate-limit window we are (0–100)."""
    epoch = _resets_at_to_epoch(resets_at)
    if epoch is None:
        return None
    window_start = epoch - window_seconds
    now = int(time.time())
    if now <= window_start:
        return 0.0
    if now >= epoch:
        return 100.0
    return (now - window_start) * 100.0 / window_seconds


def get_cost(data: dict) -> Optional[float]:
    cost = data.get("cost", {}).get("total_cost_usd")
    return float(cost) if cost is not None else None


# ── git ──────────────────────────────────────────────────────────────────────
def get_git_info(data: dict) -> Optional[str]:
    seeds = _seed_dirs(data)
    for seed in seeds:
        git_head = seed / ".git" / "HEAD"
        if not git_head.exists():
            continue
        try:
            head = git_head.read_text(encoding="utf-8", errors="replace").strip()
        except OSError:
            continue
        if head.startswith("ref: refs/heads/"):
            branch = head[len("ref: refs/heads/"):]
        else:
            branch = head[:7]
        dirty = ""
        try:
            r = subprocess.run(
                ["git", "-C", str(seed), "status", "--porcelain"],
                capture_output=True, text=True, timeout=0.15,
            )
            if r.stdout.strip():
                dirty = "*"
        except (subprocess.SubprocessError, FileNotFoundError, OSError):
            pass
        return f"{C_GIT}\u2387 {branch}{dirty}{C_RESET}"
    return None


# ── main ─────────────────────────────────────────────────────────────────────
def main() -> None:
    data = read_stdin_json()

    model_name, model_glyph = get_model(data)
    harness = get_active_harness(data)
    if harness:
        name_part = f"{C_NAME}HIVE{C_RESET} {C_DIM}\u00b7{C_RESET} {C_LABEL}{harness}{C_RESET}"
    else:
        name_part = f"{C_NAME}HIVE{C_RESET}"

    effort = get_effort(data)
    effort_suffix = f" {C_ORANGE}{effort[1]}{effort[0]}{C_RESET}" if effort else ""
    model_part = f"{C_MODEL}{model_glyph} {model_name}{C_RESET}{effort_suffix}"

    # Progress: Milestone/Phase/Wave (or WORKLOG fallback)
    prog = get_hive_progress(data)
    if prog is None:
        done, total = get_wave_progress_fallback(data)
        if total > 0:
            pct = done * 100 / total
            prog = f"{C_LABEL}W{C_RESET}{done}/{total} {color_for(100-pct)}{int(round(pct))}%{C_RESET}"
        else:
            prog = f"{C_LABEL}W{C_RESET} {C_DIM}-/-{C_RESET}"

    # Context
    ctx_pct = get_context_pct(data)
    write_ctx_bridge(data, ctx_pct)  # bridge file for hive-ctx-guard hook
    if ctx_pct is not None:
        ctx_part = f"{C_LABEL}ctx{C_RESET} {bar(ctx_pct)} {pct_label(ctx_pct)}"
    else:
        ctx_part = f"{C_LABEL}ctx{C_RESET} [{C_DIM}--------{C_RESET}]  --"

    # 5-hour rate limit
    fh_pct, fh_reset = get_rate_limit(data, "five_hour")
    if fh_pct is not None:
        pacing = compute_pacing(fh_reset, 5 * 3600)
        fh_part = (
            f"{C_LABEL}5h{C_RESET} {bar_with_pacing(fh_pct, pacing)} "
            f"{pct_label(fh_pct)}{format_reset_time(fh_reset)}"
        )
    else:
        fh_part = f"{C_LABEL}5h{C_RESET} [{C_DIM}--------{C_RESET}]  --"

    # 7-day rate limit (now with reset time + pacing)
    d7_pct, d7_reset = get_rate_limit(data, "seven_day")
    if d7_pct is not None:
        pacing = compute_pacing(d7_reset, 7 * 86400)
        d7_part = (
            f"{C_LABEL}7d{C_RESET} {bar_with_pacing(d7_pct, pacing)} "
            f"{pct_label(d7_pct)}{format_reset_time(d7_reset)}"
        )
    else:
        d7_part = f"{C_LABEL}7d{C_RESET} [{C_DIM}--------{C_RESET}]  --"

    cost = get_cost(data)
    cost_part = f"{C_COST}${cost:.3f}{C_RESET}" if cost is not None else ""

    git_part = get_git_info(data) or ""

    if STYLE == "plain":
        # Single-line ASCII fallback
        parts = [f"{name_part} {model_part}"]
        if git_part:
            parts.append(git_part)
        parts.extend([prog, ctx_part, fh_part, d7_part])
        if cost_part:
            parts.append(cost_part)
        out = SEP.join(parts).replace("\n", " ")
    else:
        # 2-line Powerline layout (default for "color" and "powerline")
        line1_segs = [name_part]
        if git_part:
            line1_segs.append(git_part)
        line1_segs.append(model_part)
        if cost_part:
            line1_segs.append(cost_part)
        line1 = SEP.join(line1_segs)
        line2 = SEP.join([prog, ctx_part, fh_part, d7_part])
        out = f"{line1}\n{line2}"

    out = out.replace("\r", "")
    print(out)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[HIVE] (status error: {e})")
