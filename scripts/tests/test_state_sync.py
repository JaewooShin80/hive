"""Wave progress must read the same way everywhere (harness review H-10..H-13).

PLAN.md success-criteria checkboxes are the single source of truth. The plan
template writes `### Wave N:` headers inside `## Wave 상세`, so every reader must
accept both `##` and `###`. A wave is complete only when all its boxes are checked.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from textwrap import dedent

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

from hive_progress import parse_plan  # noqa: E402

PLAN = dedent("""\
    # HIVE 개발 플랜 — demo

    ## 전체 Wave 목록
    | Wave | 제목 |

    ## Wave 상세

    ### Wave 1: 저장소 [Small]
    **완료 기준 (Success Criteria):**
    - [x] init_db 가 테이블을 만든다
    - [x] 업로드 API

    ### Wave 2: 이슈 [Medium]
    **완료 기준 (Success Criteria):**
    - [x] 상태 전이
    - [ ] 해시 체인

    ### Wave 3: UI [Medium]
    **완료 기준 (Success Criteria):**
    - [ ] 대시보드
    """)


class TestParsePlan(unittest.TestCase):
    def test_h3_wave_headers_are_counted(self):
        plan = parse_plan(PLAN)
        self.assertEqual(plan.total_waves, 3)

    def test_wave_complete_only_when_all_boxes_checked(self):
        self.assertEqual(parse_plan(PLAN).completed_waves, [1])


@unittest.skipUnless(shutil.which("node"), "node not installed")
class TestSessionStartHook(unittest.TestCase):
    def test_reports_current_wave_from_h3_plan(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "PLAN.md").write_text(PLAN, encoding="utf-8")
            out = subprocess.run(["node", str(REPO / ".claude/hooks/hive-session-start.js")],
                                 input=json.dumps({"cwd": d}), capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(out.returncode, 0, out.stderr)
            msg = json.loads(out.stdout)["hookSpecificOutput"]["additionalContext"]
            self.assertIn("현재 Wave: 2 / 3", msg)
            self.assertIn("1/3 Wave 완료", msg)


class TestProgressWithoutRoadmap(unittest.TestCase):
    def run_progress(self, d, *flags):
        return subprocess.run([sys.executable, str(REPO / "scripts/hive_progress.py"), *flags],
                              cwd=d, capture_output=True, text=True, encoding="utf-8")

    def test_plan_only_project_gets_a_dashboard(self):  # H-12
        with tempfile.TemporaryDirectory() as d:
            Path(d, "PLAN.md").write_text(PLAN, encoding="utf-8")
            out = self.run_progress(d)
            self.assertEqual(out.returncode, 0, out.stderr)
            self.assertIn("1/3 Wave", out.stdout)

    def test_plan_only_json(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "PLAN.md").write_text(PLAN, encoding="utf-8")
            payload = json.loads(self.run_progress(d, "--json").stdout)
            self.assertEqual((payload["completed_waves"], payload["total_waves"]), (1, 3))
            self.assertIsNone(payload["milestone"])

    def test_missing_plan_message_names_plan(self):
        with tempfile.TemporaryDirectory() as d:
            out = self.run_progress(d)
            self.assertEqual(out.returncode, 2)
            self.assertIn("PLAN.md", out.stderr)
            self.assertIn("/hive:plan", out.stderr)


@unittest.skipUnless(shutil.which("node"), "node not installed")
class TestWaveGateHook(unittest.TestCase):
    def fire(self, cmd):
        payload = {"tool_name": "Bash", "tool_input": {"command": cmd}, "tool_response": {"exit_code": 0}}
        out = subprocess.run(["node", str(REPO / ".claude/hooks/hive-wave-gate.js")],
                             input=json.dumps(payload), capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(out.returncode, 0, out.stderr)
        return out.stdout

    def test_detects_wave_commit_in_all_flag_styles(self):  # H-10
        for cmd in ['git commit -m "feat(wave-3): ui"',
                    'git commit -qm "feat(wave-3): ui"',
                    'git commit -am "feat(wave-3): ui"',
                    "git commit -m 'feat(wave-3): ui'",
                    'git commit --message="feat(wave-3): ui"',
                    'git add -A && git commit -q -m "feat(wave-3): ui" && echo ok']:
            self.assertIn("Wave 3", self.fire(cmd), cmd)

    def test_ignores_non_wave_commits(self):
        self.assertEqual(self.fire('git commit -m "docs: readme"'), "")


class TestExecuteDocUsesGateFormat(unittest.TestCase):
    def test_execute_commit_format_matches_gate(self):  # H-10
        text = (REPO / ".claude/plugins/hive/skills/execute.md").read_text(encoding="utf-8")
        self.assertIn("feat(wave-N): <wave 제목>", text)
        self.assertNotIn("feat: Wave N -", text)


if __name__ == "__main__":
    unittest.main()
