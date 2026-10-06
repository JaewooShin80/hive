#!/usr/bin/env python3
"""Generate / update feature-list.json from PLAN.md success criteria.

Used by /hive:plan step 7-1. One feature per `- [ ]` / `- [x]` line inside a
Wave's "완료 기준 (Success Criteria)" block; ids are W{wave}-F{idx}.

Re-running (e.g. /hive:plan for the next Phase) only appends features whose id
is new — existing entries keep their status and any `verify` object.

Usage: python3 scripts/gen_feature_list.py [--milestone vX.Y.Z] [--plan PLAN.md] [--out feature-list.json]
"""

import argparse
import json
import re
import sys
from pathlib import Path

WAVE_RE = re.compile(r"^#{2,3}\s+Wave\s+(\d+)")
CRITERIA_RE = re.compile(r"^\*\*완료 기준")
BOX_RE = re.compile(r"^\s*- \[( |x|X)\]\s+(.+?)\s*$")
MILESTONE_RE = re.compile(r"^>\s*\*\*마일스톤:\*\*\s+(\S+)", re.MULTILINE)


def parse_criteria(plan_text):
    """Yield (wave, idx, title, checked) for each success-criteria checkbox."""
    wave = None
    in_criteria = False
    idx = 0
    for line in plan_text.splitlines():
        m = WAVE_RE.match(line)
        if m:
            wave, in_criteria, idx = int(m.group(1)), False, 0
            continue
        if wave is None:
            continue
        if CRITERIA_RE.match(line):
            in_criteria = True
            continue
        if in_criteria:
            b = BOX_RE.match(line)
            if b:
                idx += 1
                yield wave, idx, b.group(2), b.group(1).lower() == "x"
            elif line.strip():
                in_criteria = False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", default="PLAN.md")
    ap.add_argument("--out", default="feature-list.json")
    ap.add_argument("--milestone")
    args = ap.parse_args()

    plan_path, out_path = Path(args.plan), Path(args.out)
    if not plan_path.exists():
        print(f"{plan_path} 없음. /hive:plan 으로 PLAN.md 를 먼저 만드세요.", file=sys.stderr)
        sys.exit(2)

    existing = {}
    data = {"schema_version": "1.0", "milestone": None, "features": []}
    if out_path.exists():
        try:
            data = json.loads(out_path.read_text(encoding="utf-8"))
            existing = {f["id"]: f for f in data.get("features", [])}
        except (json.JSONDecodeError, KeyError, TypeError):
            print(f"{out_path} 파싱 실패 — 덮어쓰지 않고 중단합니다.", file=sys.stderr)
            sys.exit(2)

    milestone = args.milestone or data.get("milestone")
    roadmap = Path("ROADMAP.md")
    if not milestone and roadmap.exists():
        m = MILESTONE_RE.search(roadmap.read_text(encoding="utf-8"))
        milestone = m.group(1) if m else None

    features, added = [], 0
    for wave, idx, title, checked in parse_criteria(plan_path.read_text(encoding="utf-8")):
        fid = f"W{wave}-F{idx}"
        if fid in existing:
            features.append(existing.pop(fid))
            continue
        features.append({"id": fid, "title": title, "wave": wave, "pass_criteria": title,
                         "status": "passing" if checked else "pending"})
        added += 1
    features.extend(existing.values())  # ids no longer in PLAN are kept, never dropped silently

    out = {"schema_version": data.get("schema_version", "1.0"), "milestone": milestone or "unversioned",
           "features": features}
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"feature-list.json: {len(features)} features (added {added})")


if __name__ == "__main__":
    main()
