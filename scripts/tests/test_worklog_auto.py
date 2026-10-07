"""hive-worklog-auto.js records edits into the edited file's own project (H-32)."""

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parents[2] / ".claude" / "hooks" / "hive-worklog-auto.js"


@unittest.skipUnless(shutil.which("node"), "node not installed")
class TestWorklogAuto(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()
        self.proj = self.root / "proj"
        (self.proj / ".git").mkdir(parents=True)
        (self.proj / "app").mkdir()
        self.worklog = self.proj / "WORKLOG.md"
        self.worklog.write_text("# log\n", encoding="utf-8")
        self.other = self.root / "session-cwd"
        self.other.mkdir()

    def tearDown(self):
        self._tmp.cleanup()

    def fire(self, file_path, cwd):
        payload = {"tool_name": "Write", "tool_input": {"file_path": str(file_path)}, "cwd": str(cwd)}
        out = subprocess.run(["node", str(HOOK)], input=json.dumps(payload), capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(out.returncode, 0, out.stderr)

    def entries(self):
        return [l for l in self.worklog.read_text(encoding="utf-8").splitlines() if l.startswith("- ")]

    def test_edit_inside_session_cwd(self):
        self.fire(self.proj / "app" / "main.py", self.proj)
        self.assertEqual(len(self.entries()), 1)
        self.assertTrue(self.entries()[0].endswith(" app/main.py"))

    def test_edit_in_another_project_than_session_cwd(self):
        self.fire(self.proj / "app" / "main.py", self.other)
        self.assertEqual(len(self.entries()), 1)
        self.assertTrue(self.entries()[0].endswith(" app/main.py"))

    def test_no_worklog_up_to_git_root_records_nothing(self):
        bare = self.root / "bare"
        (bare / ".git").mkdir(parents=True)
        self.fire(bare / "x.py", self.other)
        self.assertFalse((bare / "WORKLOG.md").exists())
        self.assertEqual(self.entries(), [])

    def test_worklog_self_edit_and_git_dir_are_ignored(self):
        self.fire(self.worklog, self.proj)
        self.fire(self.proj / ".git" / "config", self.proj)
        self.assertEqual(self.entries(), [])


if __name__ == "__main__":
    unittest.main()
