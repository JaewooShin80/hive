"""Scripts that print Korean/emoji must not crash on a non-UTF-8 console (Windows cp1252).

CI on windows-latest failed with UnicodeEncodeError; PYTHONIOENCODING=cp1252 reproduces it anywhere.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PLAN = "### Wave 1: 저장소\n**완료 기준 (Success Criteria):**\n- [x] 테이블 생성\n"


def run(script, cwd, *args):
    env = dict(os.environ, PYTHONIOENCODING="cp1252")
    return subprocess.run([sys.executable, str(REPO / "scripts" / script), *args], cwd=cwd, env=env,
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


class TestScriptsOnCp1252Console(unittest.TestCase):
    def test_progress(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "PLAN.md").write_text(PLAN, encoding="utf-8")
            out = run("hive_progress.py", d)
            self.assertEqual(out.returncode, 0, out.stderr)
            self.assertIn("1/1 Wave", out.stdout)

    def test_gen_feature_list(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "PLAN.md").write_text(PLAN, encoding="utf-8")
            out = run("gen_feature_list.py", d)
            self.assertEqual(out.returncode, 0, out.stderr)

    def test_evaluate(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "feature-list.json").write_text(json.dumps({"features": [
                {"id": "A", "title": "한글 기능", "wave": 1, "status": "pending"}]}), encoding="utf-8")
            out = run("hive_evaluate.py", d)
            self.assertEqual(out.returncode, 0, out.stderr)
            self.assertIn("한글 기능", out.stdout)


if __name__ == "__main__":
    unittest.main()
