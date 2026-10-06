"""Sanity tests for settings.json — security policy guards."""

from __future__ import annotations

import json
import re
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

    def test_hook_and_status_commands_are_shell_neutral(self):
        # Windows runs these in Git Bash or PowerShell — only plain `node <file>` works in both
        cmds = [self.data["statusLine"]["command"]]
        for entries in self.data["hooks"].values():
            for entry in entries:
                cmds += [h["command"] for h in entry["hooks"]]
        for cmd in cmds:
            with self.subTest(cmd=cmd):
                self.assertTrue(cmd.startswith("node "), cmd)
                self.assertNotIn("python3", cmd)
                self.assertNotIn("$", cmd)

    def test_all_six_hive_hooks_registered(self):
        blob = json.dumps(self.data["hooks"])
        for f in sorted(p for p in (REPO_ROOT / ".claude" / "hooks").glob("hive-*.js")
                       if p.name != "hive-hook-dedupe.js"):  # shared helper, not a hook
            with self.subTest(hook=f.name):
                self.assertEqual(blob.count(f.name), 1)

    def test_models_use_aliases_not_pinned_ids(self):
        # aliases (opus/sonnet/haiku) auto-track the latest release
        pinned = re.compile(r"claude-(opus|sonnet|haiku|fable)-\d")
        files = [SETTINGS_FILE, REPO_ROOT / "CLAUDE.md"]
        files += list((REPO_ROOT / ".claude" / "plugins" / "hive").rglob("*.md"))
        for f in files:
            with self.subTest(file=str(f.relative_to(REPO_ROOT))):
                self.assertIsNone(pinned.search(f.read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
