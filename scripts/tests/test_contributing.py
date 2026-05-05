"""Verify CONTRIBUTING.md and PR template structure."""

from __future__ import annotations

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRIBUTING = REPO_ROOT / "CONTRIBUTING.md"
PR_TEMPLATE = REPO_ROOT / ".github" / "pull_request_template.md"

CONTRIBUTING_REQUIRED_HEADINGS = [
    "## Development setup",
    "## Running tests",
    "## Adding a new skill",
    "## Commit style",
    "## Pull request checklist",
]


class TestContributing(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not CONTRIBUTING.exists():
            raise unittest.SkipTest("CONTRIBUTING.md not present yet")
        cls.text = CONTRIBUTING.read_text(encoding="utf-8")

    def test_has_required_headings(self):
        for h in CONTRIBUTING_REQUIRED_HEADINGS:
            with self.subTest(heading=h):
                self.assertIn(h, self.text, f"missing heading: {h}")

    def test_mentions_stdlib_only_rule(self):
        self.assertRegex(
            self.text,
            r"(stdlib[ -]only|standard library|\bno external dep)",
        )

    def test_mentions_skill_lint_in_workflow(self):
        self.assertIn("skill_lint", self.text)


class TestPRTemplate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not PR_TEMPLATE.exists():
            raise unittest.SkipTest("PR template not present yet")
        cls.text = PR_TEMPLATE.read_text(encoding="utf-8")

    def test_has_summary_section(self):
        self.assertIn("## Summary", self.text)

    def test_has_test_plan_section(self):
        self.assertIn("## Test plan", self.text)

    def test_has_checklist_items(self):
        # at least one - [ ] checklist
        self.assertRegex(self.text, r"- \[ \]")


if __name__ == "__main__":
    unittest.main()
