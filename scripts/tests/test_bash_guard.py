"""Behavior tests for .claude/hooks/hive-bash-guard.js (exit 2 = block)."""

import json
import shutil
import subprocess
import unittest
from pathlib import Path

GUARD = Path(__file__).resolve().parents[2] / ".claude" / "hooks" / "hive-bash-guard.js"


def run_guard(command: str) -> int:
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}})
    return subprocess.run(
        ["node", str(GUARD)], input=payload, capture_output=True, text=True
    ).returncode


@unittest.skipUnless(shutil.which("node"), "node not installed")
class TestForcePush(unittest.TestCase):
    def test_blocks_force_flags(self):
        for cmd in ("git push -f", "git push origin main -f", "git push --force origin main"):
            with self.subTest(cmd=cmd):
                self.assertEqual(run_guard(cmd), 2)

    def test_allows_force_with_lease(self):
        self.assertEqual(run_guard("git push --force-with-lease origin main"), 0)

    def test_ignores_flags_after_shell_separator(self):
        for cmd in (
            "git push -q origin main && [ -f x ] && rm x",
            "git push origin main; test -f y",
            "git push origin main | grep -f pats",
            "git push --quiet origin main && ls --force-color",
        ):
            with self.subTest(cmd=cmd):
                self.assertEqual(run_guard(cmd), 0)

    def test_ignores_flags_on_later_lines(self):
        self.assertEqual(run_guard("git push origin main\n[ -f x ] && echo ok"), 0)


if __name__ == "__main__":
    unittest.main()
