#!/usr/bin/env python3
"""Stub evaluate harness — Playwright MCP fallback for `/aifab:evaluate`.

Reads feature-list.json with optional `verify` fields, opens each `target`
relative to its directory (type=url, file:// only here), checks `assert`
substring against the file content, and updates `status` in-place.

This is the offline equivalent of the Playwright-driven flow described in
`.claude/plugins/aifab/skills/evaluate.md` — same input/output, no browser.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


def load_features(fl_path: Path) -> dict:
    with fl_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_features(fl_path: Path, data: dict) -> None:
    with fl_path.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def verify_url(target: str, assert_pattern: str, base_dir: Path) -> str:
    target_path = base_dir / target
    if not target_path.exists():
        return "failing"
    try:
        content = target_path.read_text(encoding="utf-8")
    except OSError:
        return "partial"
    return "passing" if re.search(assert_pattern, content) else "failing"


def verify_cmd(target: str, assert_pattern: str, base_dir: Path) -> str:
    try:
        result = subprocess.run(
            target,
            shell=True,
            cwd=str(base_dir),
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        return "partial"
    if result.returncode != 0:
        return "failing"
    return "passing" if re.search(assert_pattern, result.stdout) else "failing"


def run(fl_path: Path, wave: int | None = None, feature_id: str | None = None) -> dict:
    data = load_features(fl_path)
    base_dir = fl_path.parent
    summary = {"passing": 0, "failing": 0, "partial": 0, "skipped": 0, "diffs": []}

    for entry in data.get("features", []):
        if wave is not None and entry.get("wave") != wave:
            continue
        if feature_id is not None and entry.get("id") != feature_id:
            continue

        verify = entry.get("verify")
        if not verify:
            summary["skipped"] += 1
            continue

        vtype = verify.get("type")
        target = verify.get("target", "")
        assert_pat = verify.get("assert", "")

        if vtype == "url":
            new_status = verify_url(target, assert_pat, base_dir)
        elif vtype == "cmd":
            new_status = verify_cmd(target, assert_pat, base_dir)
        else:
            summary["skipped"] += 1
            continue

        old_status = entry.get("status", "pending")
        if old_status != new_status:
            summary["diffs"].append(f"{entry['id']} ({entry['title']}): {old_status} -> {new_status}")
        entry["status"] = new_status
        summary[new_status] = summary.get(new_status, 0) + 1

    save_features(fl_path, data)
    return summary


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("fl_path", type=Path, help="path to feature-list.json")
    ap.add_argument("--wave", type=int, default=None)
    ap.add_argument("--feature", type=str, default=None)
    args = ap.parse_args()

    if not args.fl_path.exists():
        print(f"ERROR: {args.fl_path} not found", file=sys.stderr)
        return 1

    summary = run(args.fl_path, wave=args.wave, feature_id=args.feature)
    for diff in summary["diffs"]:
        print(diff)
    total = summary["passing"] + summary["failing"] + summary["partial"]
    print(f"evaluate: {summary['passing']}/{total} passing, "
          f"{summary['failing']} failing, {summary['partial']} partial, "
          f"{summary['skipped']} skipped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
