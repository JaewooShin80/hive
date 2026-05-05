"""Sanity tests for VERSION + CHANGELOG.md consistency."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
VERSION_FILE = REPO_ROOT / "VERSION"
CHANGELOG_FILE = REPO_ROOT / "CHANGELOG.md"

SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:-[A-Za-z0-9.\-]+)?$")
HEADING_RE = re.compile(r"^##\s*\[(\d+\.\d+\.\d+)\]", re.MULTILINE)


class TestVersion(unittest.TestCase):
    def test_version_file_exists(self):
        self.assertTrue(VERSION_FILE.exists(), "VERSION file missing")

    def test_version_is_valid_semver(self):
        v = VERSION_FILE.read_text(encoding="utf-8").strip()
        self.assertRegex(v, SEMVER_RE, f"invalid semver: {v!r}")


class TestChangelog(unittest.TestCase):
    def test_changelog_exists(self):
        self.assertTrue(CHANGELOG_FILE.exists(), "CHANGELOG.md missing")

    def test_latest_versioned_heading_matches_version_file(self):
        text = CHANGELOG_FILE.read_text(encoding="utf-8")
        versions = HEADING_RE.findall(text)
        self.assertGreater(len(versions), 0, "no versioned ## [x.y.z] headings found")
        latest = versions[0]
        current = VERSION_FILE.read_text(encoding="utf-8").strip()
        self.assertEqual(
            latest, current,
            f"VERSION ({current}) does not match latest CHANGELOG heading ({latest})",
        )


if __name__ == "__main__":
    unittest.main()
