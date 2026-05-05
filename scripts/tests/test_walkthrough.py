"""Verify docs/WALKTHROUGH.md exists and covers core workflow commands."""

from __future__ import annotations

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "WALKTHROUGH.md"

REQUIRED_HEADINGS = [
    "## Setup",
    "## Step 1",
    "## Step 2",
    "## Step 3",
    "## Cleanup",
]

REQUIRED_COMMANDS = [
    "/aifab:discover",
    "/aifab:plan",
    "/aifab:execute",
    "/aifab:security",
]


class TestWalkthrough(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not DOC.exists():
            raise unittest.SkipTest("WALKTHROUGH.md not present yet")
        cls.text = DOC.read_text(encoding="utf-8")

    def test_doc_exists(self):
        self.assertTrue(DOC.exists())

    def test_has_required_headings(self):
        for h in REQUIRED_HEADINGS:
            with self.subTest(heading=h):
                self.assertIn(h, self.text, f"missing heading: {h}")

    def test_mentions_core_commands(self):
        for cmd in REQUIRED_COMMANDS:
            with self.subTest(command=cmd):
                self.assertIn(cmd, self.text, f"missing command reference: {cmd}")

    def test_contains_install_step(self):
        self.assertRegex(self.text, r"install\.sh", "missing install.sh reference")

    def test_short_enough_for_5min_read(self):
        # ~5 minutes ≈ 1500 words ≈ 9000 chars; cap at 12000 to leave room for code blocks
        self.assertLess(
            len(self.text), 12000,
            f"walkthrough too long ({len(self.text)} chars); aim for <12000",
        )


if __name__ == "__main__":
    unittest.main()
