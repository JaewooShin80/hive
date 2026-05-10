"""Tests for install.sh — harness installer."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
INSTALL_SH = REPO_ROOT / "install.sh"


class TestInstallScript(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not INSTALL_SH.exists():
            raise unittest.SkipTest("install.sh not found yet")

    def _run(self, *args, cwd=None, env_extra=None) -> subprocess.CompletedProcess:
        env = os.environ.copy()
        if env_extra:
            env.update(env_extra)
        return subprocess.run(
            ["bash", str(INSTALL_SH), *args],
            capture_output=True,
            text=True,
            cwd=cwd,
            env=env,
        )

    def test_help_flag_prints_usage_and_exits_zero(self):
        result = self._run("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("Usage:", result.stdout)
        self.assertIn("--global", result.stdout)
        self.assertIn("--dry-run", result.stdout)

    def test_unknown_flag_exits_nonzero(self):
        result = self._run("--bogus-flag")
        self.assertNotEqual(result.returncode, 0)

    def test_dry_run_makes_no_changes_to_target(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d)
            before = sorted(target.iterdir())
            result = self._run("--dry-run", "--target", str(target))
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            after = sorted(target.iterdir())
            self.assertEqual(before, after, "dry-run must not modify target")
            self.assertIn("[dry-run]", result.stdout)

    def test_install_creates_expected_files_in_empty_target(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d)
            result = self._run("--target", str(target))
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertTrue((target / "CLAUDE.md").exists(), "CLAUDE.md not installed")
            self.assertTrue((target / ".claude" / "settings.json").exists(), ".claude/settings.json not installed")
            self.assertTrue((target / "scripts" / "aifab-status.sh").exists())
            self.assertTrue((target / "scripts" / "aifab-status.py").exists())
            # plugin should be linked or copied under .claude/plugins/aifab
            plugin = target / ".claude" / "plugins" / "aifab"
            self.assertTrue(plugin.exists(), f"plugin missing at {plugin}")
            self.assertTrue((plugin / "SKILLS.md").exists())

    def test_install_protects_existing_claude_md(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d)
            existing = target / "CLAUDE.md"
            existing.write_text("# user's own rules\n", encoding="utf-8")
            result = self._run("--target", str(target))
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertEqual(
                existing.read_text(encoding="utf-8"),
                "# user's own rules\n",
                "existing CLAUDE.md must be preserved",
            )

    def test_install_protects_existing_settings_json(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d)
            (target / ".claude").mkdir()
            existing = target / ".claude" / "settings.json"
            existing.write_text('{"custom": true}', encoding="utf-8")
            result = self._run("--target", str(target))
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertEqual(existing.read_text(encoding="utf-8"), '{"custom": true}')


if __name__ == "__main__":
    unittest.main()
