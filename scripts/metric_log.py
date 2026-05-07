#!/usr/bin/env python3
"""
metric_log.py — Opt-in event logger for AI-Fab harness usage.

Disabled by default. Enabled when env var AIFAB_METRICS is one of
{"1", "true", "yes", "on"} (case-insensitive). Output is line-delimited
JSON appended to AIFAB_METRICS_FILE (default: .aifab/metrics.jsonl).

CLI:
    python3 scripts/metric_log.py EVENT [--skill NAME] [--data K=V ...]

Schema per line:
    {"ts": "<ISO8601>", "event": "<name>", "skill": "<...>", "data": {...}}

Skills can shell out to this script at start/end without changing user
behavior — when the env var is unset the script exits silently.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

ENABLED_VALUES = {"1", "true", "yes", "on"}
DEFAULT_PATH = Path(".aifab") / "metrics.jsonl"


def is_enabled() -> bool:
    return os.environ.get("AIFAB_METRICS", "").strip().lower() in ENABLED_VALUES


def _resolve_path(path: Optional[Path]) -> Path:
    if path is not None:
        return path
    env_path = os.environ.get("AIFAB_METRICS_FILE")
    if env_path:
        return Path(env_path)
    return DEFAULT_PATH


def log_event(
    event: str,
    skill: Optional[str] = None,
    path: Optional[Path] = None,
    enabled: Optional[bool] = None,
    data: Optional[dict] = None,
) -> None:
    """Append one JSONL event. No-op when disabled."""
    if enabled is None:
        enabled = is_enabled()
    if not enabled:
        return
    target = _resolve_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "event": event,
        "skill": skill,
        "data": data or {},
    }
    with target.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def _parse_kv(items: list[str]) -> dict:
    out: dict = {}
    for kv in items:
        if "=" not in kv:
            continue
        k, v = kv.split("=", 1)
        # try int
        try:
            out[k] = int(v)
            continue
        except ValueError:
            pass
        # try float
        try:
            out[k] = float(v)
            continue
        except ValueError:
            pass
        out[k] = v
    return out


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: metric_log.py EVENT [--skill NAME] [--data K=V ...]", file=sys.stderr)
        return 2
    event = argv[1]
    skill: Optional[str] = None
    data_kv: list[str] = []
    i = 2
    while i < len(argv):
        a = argv[i]
        if a == "--skill" and i + 1 < len(argv):
            skill = argv[i + 1]
            i += 2
        elif a == "--data" and i + 1 < len(argv):
            data_kv.append(argv[i + 1])
            i += 2
        else:
            i += 1
    log_event(event, skill=skill, data=_parse_kv(data_kv) if data_kv else None)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
