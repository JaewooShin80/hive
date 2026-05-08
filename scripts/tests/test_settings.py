"""Sanity tests for settings.json — security policy guards."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SETTINGS_FILE = REPO_ROOT / ".claude" / "settings.json"

DANGEROUS_PATTERNS_THAT_MUST_BE_DENIED = [
    "Bash(rm -rf *)",
    "Bash(git push --force *)",
    "Bash(git push -f *)",
    "Bash(git reset --hard *)",
    "Bash(curl * | bash)",
    "Bash(curl * | sh)",
    "Bash(wget * | bash)",
    "Bash(wget * | sh)",
]


class TestSettingsJson(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))

    def test_settings_is_valid_json(self):
        self.assertIsInstance(self.data, dict)

    def test_permissions_section_exists(self):
        self.assertIn("permissions", self.data)
        perms = self.data["permissions"]
        self.assertIn("allow", perms)
        self.assertIn("deny", perms)
        self.assertIsInstance(perms["allow"], list)
        self.assertIsInstance(perms["deny"], list)

    def test_dangerous_patterns_are_denied(self):
        deny = set(self.data["permissions"]["deny"])
        for pattern in DANGEROUS_PATTERNS_THAT_MUST_BE_DENIED:
            with self.subTest(pattern=pattern):
                self.assertIn(
                    pattern, deny,
                    f"missing critical deny rule: {pattern}",
                )

    def test_no_blanket_bash_allow(self):
        allow = self.data["permissions"]["allow"]
        # 'Bash' or 'Bash(*)' alone would defeat the deny rules
        self.assertNotIn("Bash", allow)
        self.assertNotIn("Bash(*)", allow)


if __name__ == "__main__":
    unittest.main()
