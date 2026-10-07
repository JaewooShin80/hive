"""scripts/gen_feature_list.py — PLAN.md success criteria -> feature-list.json (H-33, H-16)."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from textwrap import dedent

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "gen_feature_list.py"

PLAN_P1 = dedent("""\
    # HIVE 개발 플랜 — demo
    ## Wave 상세

    ### Wave 1: 저장소 [Small]
    **완료 기준 (Success Criteria):**
    - [ ] init_db 가 테이블을 만든다
    - [ ] [F1] 업로드 API

    **테스트 기준:** tests/test_db.py
    - [ ] 이 줄은 완료 기준 블록 밖이므로 무시

    ### Wave 2: 이슈 [Medium]
    **완료 기준 (Success Criteria):**
    - [x] [F5] 상태 전이
    """)

PLAN_P2 = PLAN_P1 + dedent("""\

    ### Wave 3: UI [Medium]
    **완료 기준 (Success Criteria):**
    - [ ] [F9] 대시보드
    """)


class TestGenFeatureList(unittest.TestCase):
    def run_gen(self, d, *extra):
        return subprocess.run([sys.executable, str(SCRIPT), *extra], cwd=d, capture_output=True, text=True, encoding="utf-8")

    def load(self, d):
        return json.loads(Path(d, "feature-list.json").read_text(encoding="utf-8"))

    def test_extracts_only_success_criteria_per_wave(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "PLAN.md").write_text(PLAN_P1, encoding="utf-8")
            out = self.run_gen(d, "--milestone", "v0.1.0")
            self.assertEqual(out.returncode, 0, out.stderr)
            data = self.load(d)
            self.assertEqual(data["schema_version"], "1.0")
            self.assertEqual(data["milestone"], "v0.1.0")
            self.assertEqual([(f["id"], f["wave"], f["status"]) for f in data["features"]],
                             [("W1-F1", 1, "pending"), ("W1-F2", 1, "pending"), ("W2-F1", 2, "passing")])
            self.assertEqual(data["features"][1]["title"], "[F1] 업로드 API")
            self.assertEqual(data["features"][1]["pass_criteria"], "[F1] 업로드 API")

    def test_file_format_is_2_space_indent_with_trailing_newline(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "PLAN.md").write_text(PLAN_P1, encoding="utf-8")
            self.run_gen(d)
            raw = Path(d, "feature-list.json").read_text(encoding="utf-8")
            self.assertTrue(raw.endswith("}\n"))
            self.assertIn('\n  "features": [', raw)

    def test_milestone_defaults_from_roadmap(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "PLAN.md").write_text(PLAN_P1, encoding="utf-8")
            Path(d, "ROADMAP.md").write_text("# 로드맵\n\n> **마일스톤:** v2.0.0\n", encoding="utf-8")
            self.run_gen(d)
            self.assertEqual(self.load(d)["milestone"], "v2.0.0")

    def test_rerun_appends_new_waves_and_keeps_existing_status(self):  # H-16
        with tempfile.TemporaryDirectory() as d:
            Path(d, "PLAN.md").write_text(PLAN_P1, encoding="utf-8")
            self.run_gen(d)
            data = self.load(d)
            data["features"][0]["status"] = "failing"
            data["features"][0]["verify"] = {"type": "cmd", "target": "pytest", "assert": "passed"}
            Path(d, "feature-list.json").write_text(json.dumps(data), encoding="utf-8")
            Path(d, "PLAN.md").write_text(PLAN_P2, encoding="utf-8")
            out = self.run_gen(d)
            self.assertEqual(out.returncode, 0, out.stderr)
            feats = self.load(d)["features"]
            self.assertEqual([f["id"] for f in feats], ["W1-F1", "W1-F2", "W2-F1", "W3-F1"])
            self.assertEqual(feats[0]["status"], "failing")
            self.assertIn("verify", feats[0])
            self.assertIn("added 1", out.stdout)

    def test_verify_annotation_becomes_verify_object(self):  # H-29
        plan = PLAN_P1.replace("- [ ] [F1] 업로드 API", "- [ ] [F1] 업로드 API (verify: `.venv/bin/pytest -q tests/test_api.py`)")
        with tempfile.TemporaryDirectory() as d:
            Path(d, "PLAN.md").write_text(plan, encoding="utf-8")
            self.run_gen(d)
            f = self.load(d)["features"][1]
            self.assertEqual(f["title"], "[F1] 업로드 API")
            self.assertEqual(f["verify"], {"type": "cmd", "target": ".venv/bin/pytest -q tests/test_api.py",
                                           "assert": "passed"})

    def test_missing_plan_fails(self):
        with tempfile.TemporaryDirectory() as d:
            out = self.run_gen(d)
            self.assertEqual(out.returncode, 2)
            self.assertIn("PLAN.md", out.stderr)


if __name__ == "__main__":
    unittest.main()
