"""scripts/hive_evaluate.py — runnable /hive:evaluate fallback for user projects (H-29)."""

import json
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "hive_evaluate.py"


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        body = b"<h1>Decision Desk</h1>"
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


class TestHiveEvaluate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd = HTTPServer(("127.0.0.1", 0), _Handler)
        cls.url = f"http://127.0.0.1:{cls.httpd.server_address[1]}/"
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()

    def run_eval(self, d, features, *extra):
        Path(d, "feature-list.json").write_text(json.dumps(
            {"schema_version": "1.0", "milestone": "v0", "features": features}), encoding="utf-8")
        out = subprocess.run([sys.executable, str(SCRIPT), *extra], cwd=d, capture_output=True, text=True)
        data = json.loads(Path(d, "feature-list.json").read_text(encoding="utf-8"))
        return out, {f["id"]: f["status"] for f in data["features"]}

    def feat(self, fid, verify=None, wave=1):
        f = {"id": fid, "title": fid, "wave": wave, "pass_criteria": "x", "status": "pending"}
        if verify:
            f["verify"] = verify
        return f

    def test_cmd_url_and_manual_entries(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "page.html").write_text("hello OK", encoding="utf-8")
            out, st = self.run_eval(d, [
                self.feat("A", {"type": "cmd", "target": f'"{sys.executable}" -c "print(\'3 passed\')"', "assert": "passed"}),
                self.feat("B", {"type": "cmd", "target": f'"{sys.executable}" -c "import sys; sys.exit(1)"', "assert": ""}),
                self.feat("C", {"type": "url", "target": self.url, "assert": "Decision Desk"}),
                self.feat("D", {"type": "url", "target": "page.html", "assert": "OK"}),
                self.feat("E", {"type": "url", "target": "http://127.0.0.1:1/", "assert": "x"}),
                self.feat("F"),
            ])
            self.assertEqual(out.returncode, 0, out.stderr)
            self.assertEqual(st, {"A": "passing", "B": "failing", "C": "passing", "D": "passing",
                                  "E": "partial", "F": "pending"})
            self.assertIn("evaluate 완료: 3/6 passing, 1 failing, 1 partial, 1 manual", out.stdout)

    def test_dangerous_command_is_refused(self):
        with tempfile.TemporaryDirectory() as d:
            out, st = self.run_eval(d, [self.feat("X", {"type": "cmd", "target": "rm -rf /", "assert": ""})])
            self.assertEqual(st["X"], "failing")
            self.assertIn("refused", out.stdout)

    def test_wave_filter(self):
        with tempfile.TemporaryDirectory() as d:
            ok = {"type": "cmd", "target": f'"{sys.executable}" -c "print(1)"', "assert": "1"}
            _, st = self.run_eval(d, [self.feat("A", ok, wave=1), self.feat("B", ok, wave=2)], "--wave", "2")
            self.assertEqual(st, {"A": "pending", "B": "passing"})


if __name__ == "__main__":
    unittest.main()
