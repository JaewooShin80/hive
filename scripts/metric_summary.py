#!/usr/bin/env python3
"""
metric_summary.py — Read HIVE metrics JSONL and emit a summary.

CLI:
    python3 scripts/metric_summary.py [--file PATH] [--json]

Default file: .hive/metrics.jsonl (or HIVE_METRICS_FILE env var).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Optional

DEFAULT_PATH = Path(".hive") / "metrics.jsonl"


def _resolve_path(arg: Optional[str]) -> Path:
    if arg:
        return Path(arg)
    env = os.environ.get("HIVE_METRICS_FILE")
    if env:
        return Path(env)
    return DEFAULT_PATH


def summarize(path: Path) -> dict:
    if not path.exists():
        return {
            "file": str(path),
            "total_events": 0,
            "events_by_type": {},
            "events_by_skill": {},
            "malformed_lines": 0,
        }
    by_type: Counter = Counter()
    by_skill: Counter = Counter()
    malformed = 0
    total = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            malformed += 1
            continue
        total += 1
        if "event" in obj:
            by_type[obj["event"]] += 1
        if obj.get("skill"):
            by_skill[obj["skill"]] += 1
    return {
        "file": str(path),
        "total_events": total,
        "events_by_type": dict(by_type),
        "events_by_skill": dict(by_skill),
        "malformed_lines": malformed,
    }


def _format(summary: dict) -> str:
    lines = [
        f"HIVE metrics summary: {summary['file']}",
        f"  total events: {summary['total_events']}",
    ]
    if summary["malformed_lines"]:
        lines.append(f"  malformed lines: {summary['malformed_lines']}")
    if summary["events_by_type"]:
        lines.append("  events by type:")
        for k, v in sorted(summary["events_by_type"].items(), key=lambda x: -x[1]):
            lines.append(f"    {k:20s}  {v}")
    if summary["events_by_skill"]:
        lines.append("  events by skill:")
        for k, v in sorted(summary["events_by_skill"].items(), key=lambda x: -x[1]):
            lines.append(f"    {k:20s}  {v}")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--file", help="metrics file path (default: .hive/metrics.jsonl)")
    p.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = p.parse_args(argv[1:])
    summary = summarize(_resolve_path(args.file))
    if args.json:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        print(_format(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
