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
