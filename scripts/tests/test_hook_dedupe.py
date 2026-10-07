"""A global hook copy steps aside when the project registers the same hook (H-14)."""

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
HOOKS = REPO / ".claude" / "hooks"
WAVE_COMMIT = {"tool_name": "Bash", "tool_input": {"command": 'git commit -m "feat(wave-2): x"'},
               "tool_response": {"exit_code": 0}}


@unittest.skipUnless(shutil.which("node"), "node not installed")
class TestHookDedupe(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name).resolve()
        self.home = root / "home"
        self.global_hooks = self.home / ".claude" / "hooks"
        self.global_hooks.mkdir(parents=True)
        for f in ("hive-wave-gate.js", "hive-hook-dedupe.js"):
            shutil.copy(HOOKS / f, self.global_hooks / f)
        self.project = root / "project"
        (self.project / ".claude").mkdir(parents=True)

    def tearDown(self):
        self._tmp.cleanup()

    def fire(self, hook_path):
        payload = dict(WAVE_COMMIT, cwd=str(self.project))
        env = dict(os.environ, HOME=str(self.home), USERPROFILE=str(self.home))
        out = subprocess.run([shutil.which("node"), str(hook_path)], input=json.dumps(payload), capture_output=True,
                             text=True, encoding="utf-8", env=env)
        self.assertEqual(out.returncode, 0, out.stderr)
        return out.stdout

    def register_in_project(self):
        (self.project / ".claude" / "settings.json").write_text(json.dumps({"hooks": {"PostToolUse": [
            {"matcher": "Bash", "hooks": [{"type": "command", "command": "node .claude/hooks/hive-wave-gate.js"}]}]}}),
            encoding="utf-8")

    def test_global_copy_runs_when_project_has_no_registration(self):
        self.assertIn("Wave 2", self.fire(self.global_hooks / "hive-wave-gate.js"))

    def test_global_copy_steps_aside_when_project_registers_it(self):
        self.register_in_project()
        self.assertEqual(self.fire(self.global_hooks / "hive-wave-gate.js"), "")

    def test_project_copy_always_runs(self):
        self.register_in_project()
        self.assertIn("Wave 2", self.fire(HOOKS / "hive-wave-gate.js"))

    def test_every_hook_uses_the_dedupe_helper(self):
        for f in sorted(HOOKS.glob("hive-*.js")):
            if f.name == "hive-hook-dedupe.js":
                continue
            with self.subTest(hook=f.name):
                self.assertIn('require("./hive-hook-dedupe")', f.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
