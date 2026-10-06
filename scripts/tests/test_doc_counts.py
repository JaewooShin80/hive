"""Skill counts and entry docs must match the skills on disk (harness review H-18)."""

import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SKILLS = sorted(p.stem for p in (REPO / ".claude/plugins/hive/skills").glob("*.md"))
N = len(SKILLS)


def read(rel):
    return (REPO / rel).read_text(encoding="utf-8")


class TestSkillCounts(unittest.TestCase):
    def test_stated_counts_match_skill_files(self):
        checks = {
            "README.md": r"(\d+)개 스킬",
            "WORKFLOW.md": r"HIVE v2 — (\d+) 스킬",
            ".claude/plugins/hive/SKILLS.md": r"\*\*총 (\d+) 스킬\.\*\*",
            "CLAUDE.md": r"\*\*전체 (\d+) 스킬\.\*\*",
        }
        for rel, pattern in checks.items():
            with self.subTest(doc=rel):
                found = [int(x) for x in re.findall(pattern, read(rel))]
                self.assertTrue(found, f"no count found in {rel}")
                self.assertEqual(set(found), {N}, f"{rel} says {found}, skills on disk: {N}")

    def test_every_skill_is_in_a_skills_md_category(self):
        text = read(".claude/plugins/hive/SKILLS.md").split("<!-- AUTO-INDEX:start -->")[0]
        for name in SKILLS:
            with self.subTest(skill=name):
                self.assertIn(f"`/hive:{name}`", text)


class TestEntryPaths(unittest.TestCase):
    def test_readme_quick_start_names_three_entry_paths(self):
        text = read("README.md")
        quick = text[text.index("## 빠른 시작"):]
        for marker in ("아이디어", "요구문서", "기존 코드", "/hive:spec", "/hive:map-codebase", "--auto"):
            with self.subTest(marker=marker):
                self.assertIn(marker, quick)

    def test_workflow_order_runs_roadmap_after_discover(self):
        text = read("WORKFLOW.md")
        line = next(l for l in text.splitlines() if "spec" in l and "discover" in l and "→" in l and "milestone" in l)
        self.assertLess(line.index("discover"), line.index("milestone"), line)


if __name__ == "__main__":
    unittest.main()
