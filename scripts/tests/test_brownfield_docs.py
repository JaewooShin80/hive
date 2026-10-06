"""Brownfield path stays wired end to end (harness review H-21)."""

import unittest
from pathlib import Path

SKILLS = Path(__file__).resolve().parents[2] / ".claude/plugins/hive/skills"


def read(name):
    return (SKILLS / name).read_text(encoding="utf-8")


class TestBrownfieldDocs(unittest.TestCase):
    def test_map_codebase_counts_tracked_files_and_commits_its_output(self):
        text = read("map-codebase.md")
        self.assertIn("git ls-files | wc -l", text)
        self.assertIn("node_modules", text)
        self.assertIn('git commit -m "docs: codebase map (hive:map-codebase)"', text)
        self.assertIn("테스트 기준선", text)

    def test_discover_b_reuses_the_map_and_judges_keep_refactor_rewrite(self):
        text = read("discover.md")
        self.assertIn("docs/codebase-map/00-SUMMARY.md", text)
        for verdict in ("현행 유지 + 국소 보강", "부분 재구성", "재작성", "## 변경 범위"):
            self.assertIn(verdict, text)

    def test_spec_has_change_request_mode(self):
        self.assertIn("변경 요구 모드", read("spec.md"))

    def test_plan_carries_regression_and_compat_rules(self):
        text = read("plan.md")
        self.assertIn("회귀 금지", text)
        self.assertIn("호환 유지", text)


if __name__ == "__main__":
    unittest.main()
