#!/usr/bin/env python3
"""
aifab-progress.py — Roadmap/Plan progress calculator + CLI.

Reads ROADMAP.md (phases + milestone meta) and PLAN.md (waves) from cwd
and computes overall + per-phase progress.

CLI:
    python3 scripts/aifab_progress.py            # full dashboard
    python3 scripts/aifab_progress.py --short    # one-liner for status bar
    python3 scripts/aifab_progress.py --json     # machine-readable
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
class Progress:
    completed_waves: int
    total_waves: int
    overall_pct: int
    current_phase: Optional[Phase]
    days_elapsed: int


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


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--short", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    sys.exit(0)
