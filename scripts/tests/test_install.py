"""Tests for the AI-Fab installer (install.sh / install.ps1 → scripts/aifab-install.js)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
INSTALL_SH = REPO_ROOT / "install.sh"
INSTALL_PS1 = REPO_ROOT / "install.ps1"
INSTALL_JS = REPO_ROOT / "scripts" / "aifab-install.js"
SKILLS_SRC = REPO_ROOT / ".claude" / "plugins" / "aifab" / "skills"

HOOK_FILES = [
    "aifab-secret-guard.js",
    "aifab-bash-guard.js",
    "aifab-ctx-guard.js",
    "aifab-worklog-auto.js",
    "aifab-session-start.js",
    "aifab-wave-gate.js",
]


def _posix(p: Path) -> str:
    return str(p).replace(os.sep, "/")


def _all_hook_commands(settings: dict) -> list:
    cmds = []
    for entries in settings.get("hooks", {}).values():
        for entry in entries:
            for h in entry.get("hooks", []):
                cmds.append(h.get("command", ""))
    return cmds


class _Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if shutil.which("node") is None:
            raise unittest.SkipTest("node not installed")

    def _run(self, *args, home=None) -> subprocess.CompletedProcess:
        env = os.environ.copy()
        if home is not None:
            env["HOME"] = str(home)
            env["USERPROFILE"] = str(home)
        return subprocess.run(
            ["bash", str(INSTALL_SH), *args],
            capture_output=True,
            text=True,
            env=env,
        )


class TestInstallCli(_Base):
    def test_help_flag_prints_usage_and_exits_zero(self):
        result = self._run("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("Usage:", result.stdout)
        self.assertIn("--global", result.stdout)
        self.assertIn("--dry-run", result.stdout)

    def test_unknown_flag_exits_nonzero(self):
        result = self._run("--bogus-flag")
        self.assertNotEqual(result.returncode, 0)

    def test_target_equal_to_source_is_refused(self):
        result = self._run("--target", str(REPO_ROOT))
        self.assertNotEqual(result.returncode, 0)

    def test_dry_run_makes_no_changes_to_target(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d)
            result = self._run("--dry-run", "--target", str(target))
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertEqual(list(target.iterdir()), [], "dry-run must not modify target")
            self.assertIn("[dry-run]", result.stdout)

    def test_ps1_and_sh_delegate_to_same_node_core(self):
        self.assertTrue(INSTALL_PS1.exists(), "install.ps1 missing")
        self.assertIn("aifab-install.js", INSTALL_PS1.read_text(encoding="utf-8"))
        self.assertIn("aifab-install.js", INSTALL_SH.read_text(encoding="utf-8"))


class TestProjectInstall(_Base):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.target = Path(self._tmp.name).resolve()
        result = self._run("--target", str(self.target))
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.settings = json.loads(
            (self.target / ".claude" / "settings.json").read_text(encoding="utf-8")
        )

    def tearDown(self):
        self._tmp.cleanup()

    def test_every_skill_is_a_slash_command(self):
        cmd_dir = self.target / ".claude" / "commands" / "aifab"
        for skill in SKILLS_SRC.glob("*.md"):
            with self.subTest(skill=skill.name):
                self.assertTrue((cmd_dir / skill.name).is_file())

    def test_shared_docs_live_outside_commands_tree(self):
        shared = self.target / ".claude" / "aifab" / "_shared"
        self.assertTrue((shared / "prerequisites.md").is_file())
        self.assertTrue((self.target / ".claude" / "aifab" / "SKILLS.md").is_file())
        cmd_root = self.target / ".claude" / "commands"
        self.assertEqual(list(cmd_root.rglob("_shared")), [], "_shared must not be loaded as commands")

    def test_shared_links_are_rewritten_to_existing_absolute_paths(self):
        text = (self.target / ".claude" / "commands" / "aifab" / "plan.md").read_text(encoding="utf-8")
        self.assertNotIn("](../_shared/", text)
        shared = _posix(self.target / ".claude" / "aifab" / "_shared")
        self.assertIn(f"]({shared}/prerequisites.md)", text)

    def test_progress_skill_points_to_installed_script(self):
        text = (self.target / ".claude" / "commands" / "aifab" / "progress.md").read_text(encoding="utf-8")
        script = self.target / "scripts" / "aifab_progress.py"
        self.assertTrue(script.is_file())
        self.assertIn(_posix(script), text)

    def test_hooks_and_scripts_are_copied(self):
        for name in HOOK_FILES:
            with self.subTest(hook=name):
                self.assertTrue((self.target / ".claude" / "hooks" / name).is_file())
        for name in ("aifab-status.js", "aifab-status.py", "aifab_progress.py"):
            with self.subTest(script=name):
                self.assertTrue((self.target / "scripts" / name).is_file())

    def test_all_six_hooks_registered_with_shell_neutral_node_commands(self):
        cmds = _all_hook_commands(self.settings)
        for name in HOOK_FILES:
            with self.subTest(hook=name):
                matching = [c for c in cmds if name in c]
                self.assertEqual(len(matching), 1, f"{name} must be registered exactly once")
                self.assertTrue(matching[0].startswith('node "'), matching[0])
                hook_path = matching[0][len('node "'):-1]
                self.assertTrue(Path(hook_path).is_file(), hook_path)
        for c in cmds:
            self.assertNotIn("python3", c, "hook commands must not depend on python3")

    def test_status_line_uses_node_launcher(self):
        cmd = self.settings["statusLine"]["command"]
        self.assertEqual(cmd, f'node "{_posix(self.target / "scripts" / "aifab-status.js")}"')

    def test_template_security_and_model_aliases_are_kept(self):
        self.assertIn("Bash(rm -rf *)", self.settings["permissions"]["deny"])
        env = self.settings["env"]
        self.assertEqual(env["AIFAB_ADVISOR_MODEL"], "opus")
        self.assertEqual(env["AIFAB_WORKER_MODEL"], "sonnet")
        self.assertEqual(env["AIFAB_BOILERPLATE_MODEL"], "haiku")

    def test_reinstall_is_idempotent(self):
        result = self._run("--target", str(self.target))
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        again = json.loads((self.target / ".claude" / "settings.json").read_text(encoding="utf-8"))
        self.assertEqual(again, self.settings)


class TestProjectInstallPreservesUserFiles(_Base):
    def test_existing_claude_md_is_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d)
            existing = target / "CLAUDE.md"
            existing.write_text("# user's own rules\n", encoding="utf-8")
            result = self._run("--target", str(target))
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertEqual(existing.read_text(encoding="utf-8"), "# user's own rules\n")

    def test_existing_settings_are_merged_not_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d)
            (target / ".claude").mkdir()
            existing = target / ".claude" / "settings.json"
            existing.write_text(
                json.dumps({
                    "custom": True,
                    "statusLine": {"type": "command", "command": "my-status"},
                    "env": {"AIFAB_WORKER_MODEL": "haiku"},
                }),
                encoding="utf-8",
            )
            result = self._run("--target", str(target))
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            merged = json.loads(existing.read_text(encoding="utf-8"))
            self.assertTrue(merged["custom"])
            self.assertEqual(merged["statusLine"]["command"], "my-status")
            self.assertEqual(merged["env"]["AIFAB_WORKER_MODEL"], "haiku", "user env must win")
            self.assertEqual(merged["env"]["AIFAB_ADVISOR_MODEL"], "opus")
            self.assertEqual(len(_all_hook_commands(merged)), len(HOOK_FILES))

    def test_pinned_model_id_triggers_warning(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d)
            (target / ".claude").mkdir()
            (target / ".claude" / "settings.json").write_text(
                json.dumps({"model": "claude-opus-4-7"}), encoding="utf-8"
            )
            result = self._run("--target", str(target))
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("claude-opus-4-7", result.stdout + result.stderr)


class TestGlobalInstall(_Base):
    def test_global_installs_under_home_claude(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d).resolve()
            result = self._run("--global", home=home)
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            base = home / ".claude"
            self.assertTrue((base / "commands" / "aifab" / "discover.md").is_file())
            self.assertTrue((base / "aifab" / "_shared" / "prerequisites.md").is_file())
            self.assertTrue((base / "hooks" / "aifab-bash-guard.js").is_file())
            self.assertTrue((base / "scripts" / "aifab" / "aifab-status.js").is_file())
            settings = json.loads((base / "settings.json").read_text(encoding="utf-8"))
            self.assertEqual(len(_all_hook_commands(settings)), len(HOOK_FILES))
            self.assertIn("aifab-status.js", settings["statusLine"]["command"])

    def test_global_refuses_to_write_through_symlink_into_source(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d).resolve()
            (home / ".claude" / "commands").mkdir(parents=True)
            (home / ".claude" / "commands" / "aifab").symlink_to(SKILLS_SRC)
            before = (SKILLS_SRC / "plan.md").read_text(encoding="utf-8")
            result = self._run("--global", home=home)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual((SKILLS_SRC / "plan.md").read_text(encoding="utf-8"), before)


if __name__ == "__main__":
    unittest.main()
