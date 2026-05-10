# AIFAB Phase·로드맵·마일스톤·진척률 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** AIFAB 하네스에 Phase·ROADMAP·마일스톤·진척률 매니지먼트 레이어를 추가하여 Wave 실행 정체성을 유지하면서 GSD 스타일 프로젝트 추적 기능을 제공한다.

**Architecture:** 기존 PLAN.md/WORKLOG.md/ARCHITECTURE.md를 그대로 두고 ROADMAP.md(Phase 인덱스)를 추가한다. Python 헬퍼(`scripts/aifab-progress.py`)가 진척률을 계산하고, 새 스킬 3개(roadmap, progress, milestone)와 상태바·`/aifab:plan`이 이를 활용한다. ROADMAP.md 부재 시 기존 동작을 유지하여 역호환을 보장한다.

**Tech Stack:** Python 3 (stdlib only), Markdown, Bash, YAML frontmatter (AIFAB v2 표준), unittest

---

## File Structure

| 파일 | 책임 |
|------|------|
| `scripts/aifab-progress.py` | ROADMAP/PLAN 파싱 + 진척률 계산 라이브러리 + CLI |
| `scripts/tests/test_progress.py` | progress.py 단위 테스트 |
| `.claude/plugins/aifab/skills/roadmap.md` | `/aifab:roadmap` 스킬 (init/add-phase/update) |
| `.claude/plugins/aifab/skills/progress.py` 호출 | `/aifab:progress` 스킬 (대시보드) |
| `.claude/plugins/aifab/skills/milestone.md` | `/aifab:milestone` 스킬 (new/complete/audit) |
| `scripts/aifab-status.py` (수정) | ROADMAP 있을 때 `P*/* W*/*` 표시 |
| `.claude/plugins/aifab/skills/plan.md` (수정) | ROADMAP 참조 + Phase 메타 부착 |

---

### Task 1: `scripts/aifab-progress.py` — 데이터 모델 + 파서 (TDD)

**Files:**
- Create: `scripts/aifab-progress.py`
- Create: `scripts/tests/test_progress.py`

- [ ] **Step 1: 실패 테스트 작성 — Roadmap 파싱**

`scripts/tests/test_progress.py` 생성:

```python
"""Tests for aifab-progress.py."""
from __future__ import annotations
import sys
import unittest
from pathlib import Path
from textwrap import dedent

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from aifab_progress import parse_roadmap, parse_plan, compute_progress, Phase, Roadmap, Plan


class TestRoadmapParser(unittest.TestCase):
    def test_parses_milestone_metadata(self):
        text = dedent("""\
            # 프로젝트 로드맵

            > **마일스톤:** v1.0.0
            > **시작일:** 2026-05-08
            > **상태:** in_progress

            ## Phase 1: 인증 (Wave 1-3) ✅ complete
            - [x] Wave 1: User
            - [x] Wave 2: Login
            - [x] Wave 3: Session
        """)
        rm = parse_roadmap(text)
        self.assertEqual(rm.milestone, "v1.0.0")
        self.assertEqual(rm.start_date, "2026-05-08")
        self.assertEqual(rm.status, "in_progress")

    def test_parses_phases_with_status(self):
        text = dedent("""\
            ## Phase 1: 인증 (Wave 1-3) ✅ complete
            - [x] Wave 1: User
            - [x] Wave 2: Login
            - [x] Wave 3: Session

            ## Phase 2: 데이터 (Wave 4-7) 🟡 in_progress
            - [x] Wave 4: Schema
            - [ ] Wave 5: Migration
            - [ ] Wave 6: Seed
            - [ ] Wave 7: Index

            ## Phase 3: API (Wave 8-12) ⬜ pending
        """)
        rm = parse_roadmap(text)
        self.assertEqual(len(rm.phases), 3)
        self.assertEqual(rm.phases[0].number, 1)
        self.assertEqual(rm.phases[0].name, "인증")
        self.assertEqual(rm.phases[0].wave_range, (1, 3))
        self.assertEqual(rm.phases[0].status, "complete")
        self.assertEqual(rm.phases[1].status, "in_progress")
        self.assertEqual(rm.phases[2].status, "pending")


class TestPlanParser(unittest.TestCase):
    def test_counts_completed_and_total_waves(self):
        text = dedent("""\
            # 개발 플랜

            ## Wave 1
            - [x] task A
            ## Wave 2
            - [x] task B
            ## Wave 3
            - [ ] task C
        """)
        plan = parse_plan(text)
        self.assertEqual(plan.completed_waves, [1, 2])
        self.assertEqual(plan.total_waves, 3)


class TestComputeProgress(unittest.TestCase):
    def test_computes_phase_and_overall_percentages(self):
        roadmap_text = dedent("""\
            > **마일스톤:** v1.0.0
            > **시작일:** 2026-05-08

            ## Phase 1: A (Wave 1-2) ✅ complete
            - [x] Wave 1
            - [x] Wave 2

            ## Phase 2: B (Wave 3-4) 🟡 in_progress
            - [x] Wave 3
            - [ ] Wave 4
        """)
        plan_text = dedent("""\
            ## Wave 1
            - [x] done
            ## Wave 2
            - [x] done
            ## Wave 3
            - [x] done
            ## Wave 4
            - [ ] todo
        """)
        rm = parse_roadmap(roadmap_text)
        plan = parse_plan(plan_text)
        prog = compute_progress(rm, plan)
        self.assertEqual(prog.completed_waves, 3)
        self.assertEqual(prog.total_waves, 4)
        self.assertEqual(prog.overall_pct, 75)
        self.assertEqual(prog.current_phase.number, 2)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
cd /Users/jaybee/lab/AIFAB-harness && python3 -m unittest scripts.tests.test_progress 2>&1 | tail -3
```
Expected: `ModuleNotFoundError: No module named 'aifab_progress'` 또는 ImportError

- [ ] **Step 3: `scripts/aifab-progress.py` 최소 구현**

```python
#!/usr/bin/env python3
"""
aifab-progress.py — Roadmap/Plan progress calculator + CLI.

Reads ROADMAP.md (phases + milestone meta) and PLAN.md (waves) from cwd
and computes overall + per-phase progress.

CLI:
    python3 scripts/aifab-progress.py            # full dashboard
    python3 scripts/aifab-progress.py --short    # one-liner for status bar
    python3 scripts/aifab-progress.py --json     # machine-readable
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
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
cd /Users/jaybee/lab/AIFAB-harness && python3 -m unittest scripts.tests.test_progress -v 2>&1 | tail -15
```
Expected: `OK` with 4 tests passing

- [ ] **Step 5: 커밋**

```bash
git add scripts/aifab-progress.py scripts/tests/test_progress.py
git commit -m "feat(progress): add aifab-progress.py library with roadmap/plan parsers"
```

---

### Task 2: `aifab-progress.py` — CLI 출력 (대시보드 + short + json)

**Files:**
- Modify: `scripts/aifab-progress.py`
- Modify: `scripts/tests/test_progress.py`

- [ ] **Step 1: 실패 테스트 추가**

`scripts/tests/test_progress.py` 끝에 다음 클래스를 추가한다:

```python
class TestFormatters(unittest.TestCase):
    def _make_progress(self):
        rm = parse_roadmap(dedent("""\
            > **마일스톤:** v1.0.0
            > **시작일:** 2026-05-08

            ## Phase 1: A (Wave 1-2) ✅ complete
            - [x] Wave 1
            - [x] Wave 2

            ## Phase 2: B (Wave 3-4) 🟡 in_progress
            - [x] Wave 3
            - [ ] Wave 4
        """))
        plan = parse_plan(dedent("""\
            ## Wave 1
            - [x] done
            ## Wave 2
            - [x] done
            ## Wave 3
            - [x] done
            ## Wave 4
            - [ ] todo
        """))
        return rm, plan, compute_progress(rm, plan)

    def test_format_short_one_liner(self):
        from aifab_progress import format_short
        rm, plan, prog = self._make_progress()
        out = format_short(rm, plan, prog)
        self.assertIn("P2/2", out)
        self.assertIn("W3/4", out)
        self.assertIn("75%", out)

    def test_format_dashboard_contains_milestone_and_phases(self):
        from aifab_progress import format_dashboard
        rm, plan, prog = self._make_progress()
        out = format_dashboard(rm, plan, prog)
        self.assertIn("v1.0.0", out)
        self.assertIn("Phase 1: A", out)
        self.assertIn("Phase 2: B", out)
        self.assertIn("75%", out)
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
cd /Users/jaybee/lab/AIFAB-harness && python3 -m unittest scripts.tests.test_progress.TestFormatters 2>&1 | tail -3
```
Expected: `ImportError: cannot import name 'format_short'`

- [ ] **Step 3: `format_short`, `format_dashboard`, CLI main 구현**

`scripts/aifab-progress.py`의 `if __name__ == "__main__":` 블록을 다음으로 교체:

```python
def format_short(roadmap: Roadmap, plan: Plan, progress: Progress) -> str:
    """One-line representation for status bar: 'P2/3 W7/12 (58%)'"""
    total_phases = len(roadmap.phases)
    current_n = progress.current_phase.number if progress.current_phase else 0
    return f"P{current_n}/{total_phases} W{progress.completed_waves}/{progress.total_waves} ({progress.overall_pct}%)"


def format_dashboard(roadmap: Roadmap, plan: Plan, progress: Progress) -> str:
    """Multi-line human-readable dashboard."""
    lines = []
    lines.append("━" * 41)
    if roadmap.milestone:
        days = f"{progress.days_elapsed}일 경과" if progress.days_elapsed else "오늘 시작"
        lines.append(f"🏷  마일스톤: {roadmap.milestone}  (시작 {roadmap.start_date}, {days})")
    lines.append("")
    lines.append(f"📊 전체 진척: {progress.completed_waves}/{progress.total_waves} Wave ({progress.overall_pct}%)")
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


def _load_files() -> Tuple[Optional[Roadmap], Optional[Plan]]:
    roadmap_path = Path("ROADMAP.md")
    plan_path = Path("PLAN.md")
    rm = parse_roadmap(roadmap_path.read_text(encoding="utf-8")) if roadmap_path.exists() else None
    plan = parse_plan(plan_path.read_text(encoding="utf-8")) if plan_path.exists() else None
    return rm, plan


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--short", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    rm, plan = _load_files()
    if rm is None or plan is None:
        print("ROADMAP.md 또는 PLAN.md 없음. /aifab:roadmap init 먼저 실행하세요.", file=sys.stderr)
        sys.exit(2)

    prog = compute_progress(rm, plan)

    if args.short:
        print(format_short(rm, plan, prog))
    elif args.json:
        print(json.dumps({
            "milestone": rm.milestone,
            "completed_waves": prog.completed_waves,
            "total_waves": prog.total_waves,
            "overall_pct": prog.overall_pct,
            "current_phase": prog.current_phase.number if prog.current_phase else None,
            "total_phases": len(rm.phases),
        }))
    else:
        print(format_dashboard(rm, plan, prog))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
cd /Users/jaybee/lab/AIFAB-harness && python3 -m unittest scripts.tests.test_progress -v 2>&1 | tail -8
```
Expected: 6 tests passing, `OK`

- [ ] **Step 5: 전체 테스트 회귀 확인**

```bash
cd /Users/jaybee/lab/AIFAB-harness && python3 -m unittest discover -s scripts/tests 2>&1 | tail -3
```
Expected: 100+ tests, `OK`

- [ ] **Step 6: 커밋**

```bash
git add scripts/aifab-progress.py scripts/tests/test_progress.py
git commit -m "feat(progress): add format_short/format_dashboard formatters and CLI"
```

---

### Task 3: `/aifab:roadmap` 스킬 파일 생성

**Files:**
- Create: `.claude/plugins/aifab/skills/roadmap.md`

- [ ] **Step 1: 스킬 파일 생성**

```markdown
---
name: aifab:roadmap
description: Manage project roadmap (Phase-level grouping of Waves) and milestone metadata. Subcommands init/add-phase/update. Generates ROADMAP.md as the index above PLAN.md.
argument-hint: [init <semver> | add-phase <name> | update]
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
---

# `/aifab:roadmap` — Phase 인덱스 + 마일스톤 메타 관리

**담당 모델:** Advisor (claude-opus-4-7) — 도메인 분해 판단 필요

---

## 역할

ROADMAP.md를 생성·갱신하여 PLAN.md의 Wave를 Phase 단위로 그룹핑한다. 마일스톤(semver) 메타와 Phase별 진행 상태를 추적한다.

---

## 사용 방법

```
/aifab:roadmap                       # 현재 ROADMAP.md 표시 (없으면 안내)
/aifab:roadmap init <semver>         # ROADMAP.md 신규 생성 (예: init v1.0.0)
/aifab:roadmap add-phase <이름>      # Phase 추가
/aifab:roadmap update                # PLAN.md 읽어 Wave 상태 자동 동기화
```

---

## init 동작

1. `ROADMAP.md`가 이미 있으면 안내 후 중단:
   > "ROADMAP.md가 이미 존재합니다. 새 마일스톤은 `/aifab:milestone new` 사용하세요."

2. `ARCHITECTURE.md` 읽어 도메인 파악

3. 사용자 인터뷰로 Phase 분해 (3-5개 권장):
   - "이 마일스톤을 몇 개의 Phase로 나누시겠습니까?"
   - 각 Phase의 이름·목표·예상 Wave 범위 결정

4. ROADMAP.md 생성:

```markdown
# 프로젝트 로드맵

> **마일스톤:** <semver>
> **시작일:** <YYYY-MM-DD (오늘)>
> **상태:** in_progress

## Phase 1: <이름> (Wave 1-N) ⬜ pending

**목표:** <한 줄>

(Wave는 /aifab:plan으로 생성)

## Phase 2: ...
```

5. 다음 명령어 안내:
   > "ROADMAP.md 생성 완료. `/aifab:plan`으로 Phase 1의 Wave를 분해하세요."

---

## add-phase 동작

1. ROADMAP.md 부재 시 안내 후 중단
2. 마지막 Phase 다음에 새 Phase 섹션 추가
3. Wave 범위는 PLAN.md 기준으로 자동 산정 또는 사용자 입력

---

## update 동작

1. `PLAN.md` 읽어 각 Wave의 `[x]` / `[ ]` 상태 파싱
2. 각 Phase의 Wave 항목 체크박스 갱신
3. Phase 상태 자동 결정:
   - 모든 Wave `[x]` → `✅ complete`
   - 일부 `[x]` → `🟡 in_progress`
   - 모두 `[ ]` → `⬜ pending`
4. 갱신 결과 요약:
   > "Phase 1: complete, Phase 2: in_progress (2/4 Wave), Phase 3: pending"

---

## 주의사항

- ROADMAP.md는 사람이 직접 편집해도 무방하지만 `update` 시 형식이 깨지면 경고
- Phase 헤더 형식은 정규식 `## Phase N: <이름> (Wave a-b) <이모지>`로 엄격
- 마일스톤 이름은 semver 권장 (`v1.0.0`)이지만 강제하지 않음
```

- [ ] **Step 2: 스킬 lint 통과 확인**

```bash
cd /Users/jaybee/lab/AIFAB-harness && python3 scripts/skill_lint.py .claude/plugins/aifab 2>&1 | tail -3
```
Expected: `0 error(s), 0 warning(s)`

- [ ] **Step 3: 커밋**

```bash
git add .claude/plugins/aifab/skills/roadmap.md
git commit -m "feat(skills): add /aifab:roadmap (Phase index + milestone metadata)"
```

---

### Task 4: `/aifab:progress` 스킬 파일 생성

**Files:**
- Create: `.claude/plugins/aifab/skills/progress.md`

- [ ] **Step 1: 스킬 파일 생성**

```markdown
---
name: aifab:progress
description: Display project progress dashboard — milestone, phase progression, wave completion percentages, current position, and next recommended command. Reads ROADMAP.md and PLAN.md.
allowed-tools:
  - Bash
  - Read
---

# `/aifab:progress` — 진척률 대시보드

**담당 모델:** 없음 — Python 헬퍼가 계산, 출력만 표시

---

## 역할

ROADMAP.md와 PLAN.md를 읽어 마일스톤 진행률, Phase별 진척, 현재 위치, 다음 추천 명령어를 한 번에 표시한다.

---

## 동작

1. `ROADMAP.md` / `PLAN.md` 부재 시 안내 후 중단:
   > "ROADMAP.md 또는 PLAN.md 없음. `/aifab:roadmap init`을 먼저 실행하세요."

2. 헬퍼 스크립트 실행:

```bash
python3 scripts/aifab-progress.py
```

3. 출력 결과를 그대로 사용자에게 표시.

4. 다음 추천 명령어 표시:
   - 현재 Phase에 미완료 Wave 있음 → `/aifab:execute`
   - 현재 Phase 완료, 다음 Phase 있음 → `/aifab:plan phase N`
   - 모든 Phase 완료 → `/aifab:milestone audit`

---

## 출력 예시

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏷  마일스톤: v1.0.0  (시작 2026-05-08, 8일 경과)

📊 전체 진척: 5/12 Wave (42%)

Phase 1: 인증            ████████████  3/3   ✅
Phase 2: 데이터 모델      ██████░░░░░░  2/4   🟡 ← 현재
Phase 3: API 노출         ░░░░░░░░░░░░  0/5   ⬜

📍 현재 위치: Phase 2 (데이터 모델)
🎯 다음 명령어: /aifab:execute
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 주의사항

- 이 스킬은 LLM 추론 없이 Python 헬퍼 실행 결과만 표시한다 (예측 불가능성 제거)
- 헬퍼가 종료 코드 2를 반환하면 ROADMAP/PLAN 부재 안내
```

- [ ] **Step 2: lint 통과 확인**

```bash
cd /Users/jaybee/lab/AIFAB-harness && python3 scripts/skill_lint.py .claude/plugins/aifab 2>&1 | tail -3
```
Expected: `0 error(s), 0 warning(s)`

- [ ] **Step 3: 커밋**

```bash
git add .claude/plugins/aifab/skills/progress.md
git commit -m "feat(skills): add /aifab:progress (dashboard via aifab-progress.py)"
```

---

### Task 5: `/aifab:milestone` 스킬 파일 생성

**Files:**
- Create: `.claude/plugins/aifab/skills/milestone.md`

- [ ] **Step 1: 스킬 파일 생성**

```markdown
---
name: aifab:milestone
description: Manage project milestones (semver tags). Subcommands new/complete/audit handle milestone lifecycle from start to git tag. Use new at project start, audit before declaring done, complete to tag.
argument-hint: [new <semver> | complete | audit]
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
---

# `/aifab:milestone` — 마일스톤 라이프사이클

**담당 모델:** Advisor (claude-opus-4-7) — `complete`/`audit`는 판단 필요

---

## 역할

마일스톤(semver)을 생성·점검·완료한다. 완료 시 git tag를 생성하고 회고를 `MILESTONE-LOG.md`에 기록한다.

---

## 사용 방법

```
/aifab:milestone                # 현재 마일스톤 상태 표시
/aifab:milestone new <semver>   # 새 마일스톤 시작 (예: new v1.0.0)
/aifab:milestone audit          # 종료 직전 점검
/aifab:milestone complete       # 모든 Phase 완료 확인 → git tag → 회고
```

---

## new 동작

1. ROADMAP.md가 이미 있으면 안내 후 중단:
   > "현재 마일스톤이 진행 중입니다. 먼저 `/aifab:milestone complete`로 종료하세요."

2. 인자가 semver 형식인지 검증 (`vN.N.N`)

3. `/aifab:roadmap init <semver>` 호출 권장 메시지 출력:
   > "마일스톤 <semver> 시작 준비. 이제 `/aifab:roadmap init <semver>`로 ROADMAP.md를 생성하세요."

---

## audit 동작

ROADMAP.md를 읽어 다음 항목을 순서대로 점검:

1. **Phase 상태:** 모든 Phase가 `✅ complete`인가
2. **테스트:** 프로젝트에 테스트가 있다면 통과하는가
   ```bash
   # 자동 감지: package.json scripts.test, pytest, go test 등
   ```
3. **보안:** 마지막 Wave 후 `/aifab:security` 또는 `/security-audit` 실행 이력 확인
4. **UAT:** WORKLOG.md에 `/aifab:uat` 통과 기록 있는가
5. **문서:** README.md, CHANGELOG.md 갱신 여부

각 항목에 ✅/⚠️/❌ 표시하고 미완료 항목은 권장 액션 제시.

---

## complete 동작

1. `/aifab:milestone audit` 자동 실행. ❌ 항목 있으면 중단.

2. 회고 인터뷰 (Advisor):
   - "이 마일스톤에서 가장 잘된 결정은?"
   - "다음에 다르게 했으면 좋았을 부분은?"
   - "다음 마일스톤에 가져갈 결정은?"

3. `MILESTONE-LOG.md` 작성 (없으면 생성, 있으면 추가):

```markdown
## <semver> — <YYYY-MM-DD>

**기간:** <시작> ~ <종료> (N일)
**Phase:** N개 완료
**Wave:** N개 완료

### 잘된 점
- ...

### 개선할 점
- ...

### 다음 마일스톤 인계
- ...
```

4. git tag 생성:

```bash
git tag -a <semver> -m "milestone: <semver>"
```

5. ROADMAP.md를 archive 처리:
   - `archive/ROADMAP-<semver>.md`로 이동
   - 또는 ROADMAP.md 상단에 `> **상태:** complete` 갱신

6. 다음 명령어 안내:
   > "마일스톤 <semver> 완료. 다음 마일스톤은 `/aifab:milestone new vX.Y.Z`로 시작하세요."

---

## 주의사항

- semver 강제: `vN.N.N` 형식. 다른 형식은 거부
- git tag는 항상 annotated tag (`-a`)로 생성하여 메시지 보존
- `audit`는 비파괴적 (절대 수정 안 함)
- `complete`는 git tag 생성 전 사용자 확인 필수
```

- [ ] **Step 2: lint 통과 확인**

```bash
cd /Users/jaybee/lab/AIFAB-harness && python3 scripts/skill_lint.py .claude/plugins/aifab 2>&1 | tail -3
```
Expected: `0 error(s), 0 warning(s)`

- [ ] **Step 3: 커밋**

```bash
git add .claude/plugins/aifab/skills/milestone.md
git commit -m "feat(skills): add /aifab:milestone (semver lifecycle + git tag)"
```

---

### Task 6: `scripts/aifab-status.py` — 상태바 Phase·Wave 표시

**Files:**
- Modify: `scripts/aifab-status.py`

- [ ] **Step 1: 현재 wave 파싱 위치 확인**

```bash
cd /Users/jaybee/lab/AIFAB-harness && grep -n "wave_part\|get_wave_progress" scripts/aifab-status.py
```
Expected: line 118의 `get_wave_progress`, line 178~183의 wave_part 출력 코드

- [ ] **Step 2: ROADMAP.md 감지 + 짧은 형식 호출 추가**

`scripts/aifab-status.py`에서 `# wave progress` 주석으로 시작하는 블록을 찾아 다음으로 교체한다:

```python
    # wave progress (with optional ROADMAP.md awareness)
    roadmap_path = Path("ROADMAP.md")
    if roadmap_path.exists():
        # use aifab-progress.py --short for unified format
        try:
            import subprocess
            r = subprocess.run(
                ["python3", str(Path(__file__).parent / "aifab-progress.py"), "--short"],
                capture_output=True, text=True, timeout=2,
            )
            if r.returncode == 0 and r.stdout.strip():
                wave_part = f"{C_LABEL}{r.stdout.strip()}{C_RESET}"
            else:
                wave_done, wave_total = get_wave_progress()
                if wave_total > 0:
                    wave_pct = wave_done * 100 / wave_total
                    wave_part = f"{C_LABEL}wave{C_RESET} {bar(wave_pct)} {wave_done}/{wave_total}"
                else:
                    wave_part = f"{C_LABEL}wave{C_RESET} {bar(0)} -/-"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            wave_done, wave_total = get_wave_progress()
            if wave_total > 0:
                wave_pct = wave_done * 100 / wave_total
                wave_part = f"{C_LABEL}wave{C_RESET} {bar(wave_pct)} {wave_done}/{wave_total}"
            else:
                wave_part = f"{C_LABEL}wave{C_RESET} {bar(0)} -/-"
    else:
        wave_done, wave_total = get_wave_progress()
        if wave_total > 0:
            wave_pct = wave_done * 100 / wave_total
            wave_part = f"{C_LABEL}wave{C_RESET} {bar(wave_pct)} {wave_done}/{wave_total}"
        else:
            wave_part = f"{C_LABEL}wave{C_RESET} {bar(0)} -/-"
```

- [ ] **Step 3: ROADMAP 부재 시 회귀 없음 확인**

```bash
cd /tmp && mkdir -p aifab-status-test && cd aifab-status-test && touch WORKLOG.md && echo "- [x] wave 1" > WORKLOG.md && bash /Users/jaybee/lab/AIFAB-harness/scripts/aifab-status.sh < /dev/null 2>&1 | head -1
```
Expected: 기존 형식 (`wave [...] 1/1` 형태) 출력, 에러 없음

- [ ] **Step 4: ROADMAP 있을 시 새 형식 표시 확인**

```bash
cd /tmp/aifab-status-test && cat > ROADMAP.md << 'EOF'
> **마일스톤:** v1.0.0
> **시작일:** 2026-05-08

## Phase 1: 테스트 (Wave 1-1) 🟡 in_progress
- [x] Wave 1
EOF
cat > PLAN.md << 'EOF'
## Wave 1
- [x] done
EOF
bash /Users/jaybee/lab/AIFAB-harness/scripts/aifab-status.sh < /dev/null 2>&1 | head -1
```
Expected: `P1/1 W1/1 (100%)` 부분 포함된 한 줄

- [ ] **Step 5: 정리 + 커밋**

```bash
rm -rf /tmp/aifab-status-test
cd /Users/jaybee/lab/AIFAB-harness
git add scripts/aifab-status.py
git commit -m "feat(status): show Phase/Wave format when ROADMAP.md exists"
```

---

### Task 7: `/aifab:plan` ROADMAP 참조 로직 추가

**Files:**
- Modify: `.claude/plugins/aifab/skills/plan.md`

- [ ] **Step 1: 현재 plan.md 1단계 위치 확인**

```bash
cd /Users/jaybee/lab/AIFAB-harness && head -45 .claude/plugins/aifab/skills/plan.md
```
Expected: `## 1단계: 사전 조건 확인` 섹션이 line 26 근처

- [ ] **Step 2: 사전 조건 섹션에 ROADMAP 감지 추가**

`.claude/plugins/aifab/skills/plan.md`의 `## 1단계: 사전 조건 확인` 섹션 끝 (다음 `---` 직전)에 다음 단계를 추가한다:

```markdown

3. `ROADMAP.md` 존재 여부 확인 (선택적):
   - **있으면:**
     - 인자에 `phase N`이 있으면 해당 Phase의 Wave 범위만 분해 대상으로 한다.
     - 인자가 없으면 첫 `🟡 in_progress` 또는 `⬜ pending` Phase의 Wave 범위만 분해.
     - PLAN.md 헤더에 다음 메타를 추가한다:
       ```markdown
       > **Phase:** N (이름)
       > **Wave 범위:** a-b
       ```
   - **없으면:** 기존 동작 (전체 기능을 단일 Phase로 분해, 메타 추가 없음). 역호환 유지.

4. ROADMAP.md를 갱신해야 하는 경우 (Phase 1 완료 후 Phase 2 plan 호출 등) 마지막 단계에서 사용자에게 `/aifab:roadmap update` 실행을 안내한다.
```

- [ ] **Step 3: lint 통과 확인**

```bash
cd /Users/jaybee/lab/AIFAB-harness && python3 scripts/skill_lint.py .claude/plugins/aifab 2>&1 | tail -3
```
Expected: `0 error(s), 0 warning(s)`

- [ ] **Step 4: 커밋**

```bash
git add .claude/plugins/aifab/skills/plan.md
git commit -m "feat(plan): reference ROADMAP.md when present (backward compatible)"
```

---

### Task 8: CLAUDE.md / SKILLS.md 자동 갱신

**Files:**
- Modify: `CLAUDE.md` (auto-generated section)
- Modify: `.claude/plugins/aifab/SKILLS.md` (auto-generated section)

- [ ] **Step 1: 자동 생성기 실행**

```bash
cd /Users/jaybee/lab/AIFAB-harness && python3 scripts/gen_skills_index.py --write CLAUDE.md && python3 scripts/gen_skills_index.py --write .claude/plugins/aifab/SKILLS.md
```
Expected: `updated: CLAUDE.md`, `updated: .claude/plugins/aifab/SKILLS.md`

- [ ] **Step 2: 변경 사항 확인**

```bash
cd /Users/jaybee/lab/AIFAB-harness && git diff --stat CLAUDE.md .claude/plugins/aifab/SKILLS.md
```
Expected: 양쪽 파일에 새 스킬 3개(`roadmap`, `progress`, `milestone`) 항목 추가됨

- [ ] **Step 3: --check로 sync 확인**

```bash
cd /Users/jaybee/lab/AIFAB-harness && python3 scripts/gen_skills_index.py --check CLAUDE.md && python3 scripts/gen_skills_index.py --check .claude/plugins/aifab/SKILLS.md && echo "in sync"
```
Expected: `in sync`

- [ ] **Step 4: 커밋**

```bash
git add CLAUDE.md .claude/plugins/aifab/SKILLS.md
git commit -m "chore: regenerate skills index for roadmap/progress/milestone"
```

---

### Task 9: 전체 회귀 테스트 + WORKFLOW.md 업데이트

**Files:**
- Modify: `WORKFLOW.md`

- [ ] **Step 1: 전체 테스트 통과 확인**

```bash
cd /Users/jaybee/lab/AIFAB-harness && python3 scripts/skill_lint.py .claude/plugins/aifab && python3 scripts/gen_skills_index.py --check CLAUDE.md && python3 scripts/gen_skills_index.py --check .claude/plugins/aifab/SKILLS.md && python3 -m unittest discover -s scripts/tests 2>&1 | tail -5
```
Expected: `OK`, 0 errors, all green

- [ ] **Step 2: WORKFLOW.md 헤더 버전 갱신**

`WORKFLOW.md` 상단의 버전 줄을 다음으로 교체:

```
> **버전**: 2.1
> **하네스**: AI-Fab v2 — 23 스킬 (16 AIFAB + 4 mattpocock + 3 매니지먼트) + 보안 감사 스킬 + 자동 Hook
```

- [ ] **Step 3: WORKFLOW.md 빠른 참조 섹션에 새 명령어 3개 추가**

`## 빠른 참조 — 상황별 첫 명령어` 표 끝에 다음 행 추가:

```markdown
| Phase 단위 로드맵 만들기 | `/aifab:roadmap init <semver>` |
| 프로젝트 진행률 확인 | `/aifab:progress` |
| 마일스톤 시작/완료 | `/aifab:milestone new` / `/aifab:milestone complete` |
```

- [ ] **Step 4: WORKFLOW.md 시나리오 1 갱신**

`### 전체 흐름` (시나리오 1) 줄을 다음으로 교체:

```
milestone new → roadmap init → grill → discover → plan(phase) → [execute → (auto)security] × N
  → roadmap update → milestone audit → milestone complete (git tag) → playwright → uat
```

- [ ] **Step 5: WORKFLOW.md 변경 이력 추가**

`## 변경 이력` 섹션 상단에 다음 행 추가:

```markdown
- **v2.1 (2026-05-08)**: Phase·로드맵·진척률·마일스톤 매니지먼트 추가 (`/aifab:roadmap`, `/aifab:progress`, `/aifab:milestone`).
```

- [ ] **Step 6: 커밋**

```bash
cd /Users/jaybee/lab/AIFAB-harness && git add WORKFLOW.md && git commit -m "docs(workflow): document v2.1 roadmap/progress/milestone management layer"
```

- [ ] **Step 7: 최종 확인**

```bash
cd /Users/jaybee/lab/AIFAB-harness && git log --oneline -10
```
Expected: Task 1~9의 commit 9개가 순서대로 표시됨
