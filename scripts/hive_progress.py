#!/usr/bin/env python3
"""
hive-progress.py — Roadmap/Plan progress calculator + CLI.

Reads ROADMAP.md (phases + milestone meta) and PLAN.md (waves) from cwd
and computes overall + per-phase progress.

CLI:
    python3 scripts/hive_progress.py            # full dashboard
    python3 scripts/hive_progress.py --short    # one-liner for status bar
    python3 scripts/hive_progress.py --json     # machine-readable
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import List, Optional, Tuple


PHASE_HEADER_RE = re.compile(
    r"^##\s+Phase\s+(\d+):\s+(.+?)\s+\(Wave\s+(\d+)-(\d+)\)\s+(✅|🟡|⬜)\s+(complete|in_progress|pending)",
    re.MULTILINE,
)
MILESTONE_RE = re.compile(r"^>\s*\*\*마일스톤:\*\*\s+(\S+)", re.MULTILINE)
START_DATE_RE = re.compile(r"^>\s*\*\*시작일:\*\*\s+(\S+)", re.MULTILINE)
STATUS_RE = re.compile(r"^>\s*\*\*상태:\*\*\s+(\S+)", re.MULTILINE)
WAVE_HEADER_RE = re.compile(r"^##\s+Wave\s+(\d+)", re.MULTILINE)


@dataclass
class Phase:
    number: int
    name: str
    wave_range: Tuple[int, int]
    status: str  # complete | in_progress | pending


@dataclass
class Roadmap:
    milestone: Optional[str]
    start_date: Optional[str]
    status: Optional[str]
    phases: List[Phase] = field(default_factory=list)


@dataclass
class Plan:
    completed_waves: List[int]
    total_waves: int


@dataclass
class FeatureList:
    """feature-list.json content (Wave 4)."""

    passing: int
    total: int
    milestone: Optional[str]


@dataclass
class Progress:
    completed_waves: int
    total_waves: int
    overall_pct: int
    current_phase: Optional[Phase]
    days_elapsed: int
    features: Optional[FeatureList] = None


def parse_roadmap(text: str) -> Roadmap:
    milestone_m = MILESTONE_RE.search(text)
    start_m = START_DATE_RE.search(text)
    status_m = STATUS_RE.search(text)
    phases = []
    for m in PHASE_HEADER_RE.finditer(text):
        phases.append(
            Phase(
                number=int(m.group(1)),
                name=m.group(2).strip(),
                wave_range=(int(m.group(3)), int(m.group(4))),
                status=m.group(6),
            )
        )
    return Roadmap(
        milestone=milestone_m.group(1) if milestone_m else None,
        start_date=start_m.group(1) if start_m else None,
        status=status_m.group(1) if status_m else None,
        phases=phases,
    )


def parse_feature_list(text: str) -> Optional[FeatureList]:
    """Parse feature-list.json text. Returns None on any error (graceful)."""
    try:
        data = json.loads(text)
    except (ValueError, json.JSONDecodeError):
        print("[hive-progress] feature-list.json: JSON 파싱 실패, skip", file=sys.stderr)
        return None
    if not isinstance(data, dict):
        return None
    features = data.get("features")
    if not isinstance(features, list):
        print("[hive-progress] feature-list.json: 'features' 키 누락 또는 비-array, skip", file=sys.stderr)
        return None
    total = 0
    passing = 0
    valid_statuses = {"pending", "passing", "failing", "partial"}
    for entry in features:
        if not isinstance(entry, dict):
            continue
        # Required field check (id, title, wave, pass_criteria, status)
        if not all(k in entry for k in ("id", "title", "wave", "pass_criteria", "status")):
            print(f"[hive-progress] feature entry 필수 필드 누락 (id={entry.get('id', '?')}), skip", file=sys.stderr)
            continue
        status = entry.get("status")
        if status not in valid_statuses:
            # Entry counted in total but not in passing
            total += 1
            continue
        total += 1
        if status == "passing":
            passing += 1
    milestone = data.get("milestone") if isinstance(data.get("milestone"), str) else None
    return FeatureList(passing=passing, total=total, milestone=milestone)


def parse_plan(text: str) -> Plan:
    completed = []
    total = 0
    current_wave = None
    for line in text.splitlines():
        wm = WAVE_HEADER_RE.match(line)
        if wm:
            current_wave = int(wm.group(1))
            total += 1
        elif current_wave is not None and "[x]" in line.lower():
            if current_wave not in completed:
                completed.append(current_wave)
    return Plan(completed_waves=sorted(completed), total_waves=total)


def compute_progress(roadmap: Roadmap, plan: Plan) -> Progress:
    pct = (
        int(round(len(plan.completed_waves) * 100 / plan.total_waves))
        if plan.total_waves > 0
        else 0
    )
    current = next(
        (p for p in roadmap.phases if p.status == "in_progress"),
        next((p for p in roadmap.phases if p.status == "pending"), None),
    )
    days_elapsed = 0
    if roadmap.start_date:
        try:
            start = date.fromisoformat(roadmap.start_date)
            days_elapsed = (date.today() - start).days
        except ValueError:
            pass
    return Progress(
        completed_waves=len(plan.completed_waves),
        total_waves=plan.total_waves,
        overall_pct=pct,
        current_phase=current,
        days_elapsed=days_elapsed,
    )


def format_short(roadmap: Roadmap, plan: Plan, progress: Progress) -> str:
    """One-line representation for status bar: 'P2/3 W7/12 (58%) F12/24'"""
    total_phases = len(roadmap.phases)
    current_n = progress.current_phase.number if progress.current_phase else 0
    base = f"P{current_n}/{total_phases} W{progress.completed_waves}/{progress.total_waves} ({progress.overall_pct}%)"
    if progress.features is not None:
        base += f" F{progress.features.passing}/{progress.features.total}"
    return base


def format_dashboard(roadmap: Roadmap, plan: Plan, progress: Progress) -> str:
    """Multi-line human-readable dashboard."""
    lines = []
    lines.append("━" * 41)
    if roadmap.milestone:
        days = f"{progress.days_elapsed}일 경과" if progress.days_elapsed else "오늘 시작"
        lines.append(f"🏷  마일스톤: {roadmap.milestone}  (시작 {roadmap.start_date}, {days})")
    lines.append("")
    lines.append(f"📊 전체 진척: {progress.completed_waves}/{progress.total_waves} Wave ({progress.overall_pct}%)")
    if progress.features is not None:
        feat = progress.features
        feat_pct = int(round(feat.passing * 100 / feat.total)) if feat.total > 0 else 0
        lines.append(f"🎯 기능 검증: {feat.passing}/{feat.total} passing ({feat_pct}%)")
    lines.append("")
    for p in roadmap.phases:
        wave_count = p.wave_range[1] - p.wave_range[0] + 1
        done_in_phase = sum(
            1 for w in plan.completed_waves if p.wave_range[0] <= w <= p.wave_range[1]
        )
        bar_w = 12
        filled = int(bar_w * done_in_phase / wave_count) if wave_count else 0
        bar = "█" * filled + "░" * (bar_w - filled)
        emoji = {"complete": "✅", "in_progress": "🟡", "pending": "⬜"}[p.status]
        cursor = " ← 현재" if p.status == "in_progress" else ""
        lines.append(f"Phase {p.number}: {p.name:<16}  {bar}  {done_in_phase}/{wave_count}   {emoji}{cursor}")
    lines.append("")
    if progress.current_phase:
        lines.append(f"📍 현재 위치: Phase {progress.current_phase.number} ({progress.current_phase.name})")
    lines.append("━" * 41)
    return "\n".join(lines)


def _load_files() -> Tuple[Optional[Roadmap], Optional[Plan], Optional[FeatureList]]:
    roadmap_path = Path("ROADMAP.md")
    plan_path = Path("PLAN.md")
    feature_path = Path("feature-list.json")
    rm = parse_roadmap(roadmap_path.read_text(encoding="utf-8")) if roadmap_path.exists() else None
    plan = parse_plan(plan_path.read_text(encoding="utf-8")) if plan_path.exists() else None
    features = parse_feature_list(feature_path.read_text(encoding="utf-8")) if feature_path.exists() else None
    return rm, plan, features


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--short", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    rm, plan, features = _load_files()
    if rm is None or plan is None:
        print("ROADMAP.md 또는 PLAN.md 없음. /hive:roadmap init 먼저 실행하세요.", file=sys.stderr)
        sys.exit(2)

    prog = compute_progress(rm, plan)
    prog.features = features

    if args.short:
        print(format_short(rm, plan, prog))
    elif args.json:
        payload = {
            "milestone": rm.milestone,
            "completed_waves": prog.completed_waves,
            "total_waves": prog.total_waves,
            "overall_pct": prog.overall_pct,
            "current_phase": prog.current_phase.number if prog.current_phase else None,
            "total_phases": len(rm.phases),
        }
        if features is not None:
            payload["features_passing"] = features.passing
            payload["features_total"] = features.total
        print(json.dumps(payload))
    else:
        print(format_dashboard(rm, plan, prog))


if __name__ == "__main__":
    main()
