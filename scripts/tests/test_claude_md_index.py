"""Verify CLAUDE.md commands table is auto-indexed and stays in sync."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CLAUDE_MD = REPO_ROOT / "CLAUDE.md"
PLUGIN_DIR = REPO_ROOT / ".claude" / "plugins" / "aifab"
GEN = REPO_ROOT / "scripts" / "gen_skills_index.py"

sys.path.insert(0, str(REPO_ROOT / "scripts"))
from gen_skills_index import MARKER_END, MARKER_START  # noqa: E402


class TestClaudeMdMarkers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = CLAUDE_MD.read_text(encoding="utf-8")

    def test_markers_present(self):
        self.assertIn(MARKER_START, self.text, "CLAUDE.md missing AUTO-INDEX:start")
        self.assertIn(MARKER_END, self.text, "CLAUDE.md missing AUTO-INDEX:end")

    def test_markers_in_correct_order(self):
        s = self.text.find(MARKER_START)
        e = self.text.find(MARKER_END)
        self.assertGreater(e, s, "AUTO-INDEX:end appears before AUTO-INDEX:start")

    def test_check_subcommand_exits_zero(self):
        result = subprocess.run(
            ["python3", str(GEN), "--plugin", str(PLUGIN_DIR), "--check", str(CLAUDE_MD)],
            capture_output=True, text=True,
        )
        self.assertEqual(
            result.returncode, 0,
            msg=f"CLAUDE.md is stale:\n{result.stderr or result.stdout}",
        )


class TestGeneratorOnTwoFiles(unittest.TestCase):
    """Smoke-test that the generator handles both SKILLS.md and CLAUDE.md."""

    def test_independent_files_can_share_markers(self):
        with tempfile.TemporaryDirectory() as d:
            tmp_root = Path(d)
            plugin = tmp_root / "plug"
            (plugin / "skills").mkdir(parents=True)
            (plugin / "skills" / "x.md").write_text(
                "---\nname: aifab:x\ndescription: do x\n---\n",
                encoding="utf-8",
            )
            f1 = tmp_root / "A.md"
            f2 = tmp_root / "B.md"
            f1.write_text(f"head\n{MARKER_START}\nstale1\n{MARKER_END}\n", encoding="utf-8")
            f2.write_text(f"head\n{MARKER_START}\nstale2\n{MARKER_END}\n", encoding="utf-8")
            for path in (f1, f2):
                r = subprocess.run(
                    ["python3", str(GEN), "--plugin", str(plugin), "--write", str(path)],
                    capture_output=True, text=True,
                )
                self.assertEqual(r.returncode, 0, msg=r.stderr)
            for path in (f1, f2):
                self.assertIn("`/aifab:x`", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
