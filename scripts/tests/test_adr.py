"""Verify the harness's own ADRs are present and well-formed."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ADR_DIR = REPO_ROOT / "docs" / "adr"
INDEX = ADR_DIR / "README.md"

REQUIRED_SECTIONS = ["## Status", "## Context", "## Decision", "## Consequences"]
ADR_FILENAME_RE = re.compile(r"^\d{4}-[a-z0-9-]+\.md$")


class TestAdrDirectory(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not ADR_DIR.exists():
            raise unittest.SkipTest("docs/adr/ not present yet")

    def test_at_least_two_adrs(self):
        adrs = [p for p in ADR_DIR.glob("*.md") if p.name != "README.md"]
        self.assertGreaterEqual(len(adrs), 2, "expected at least 2 retrospective ADRs")

    def test_all_adrs_follow_filename_convention(self):
        adrs = [p for p in ADR_DIR.glob("*.md") if p.name != "README.md"]
        for p in adrs:
            with self.subTest(file=p.name):
                self.assertRegex(p.name, ADR_FILENAME_RE, f"bad filename: {p.name}")

    def test_all_adrs_have_required_sections(self):
        adrs = [p for p in ADR_DIR.glob("*.md") if p.name != "README.md"]
        for p in adrs:
            text = p.read_text(encoding="utf-8")
            for section in REQUIRED_SECTIONS:
                with self.subTest(file=p.name, section=section):
                    self.assertIn(section, text, f"{p.name} missing {section}")

    def test_adr_index_exists(self):
        self.assertTrue(INDEX.exists(), "docs/adr/README.md (index) missing")

    def test_index_references_each_adr(self):
        if not INDEX.exists():
            self.skipTest("index missing")
        text = INDEX.read_text(encoding="utf-8")
        adrs = [p for p in ADR_DIR.glob("*.md") if p.name != "README.md"]
        for p in adrs:
            with self.subTest(file=p.name):
                self.assertIn(
                    p.name, text,
                    f"index does not reference {p.name}",
                )


if __name__ == "__main__":
    unittest.main()
