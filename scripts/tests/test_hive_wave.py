"""Behavior tests for .claude/workflows/hive-wave.js (saved Claude Code workflow).

The Workflow runtime wraps the script body in an async function and injects
agent/pipeline/phase/log/args. We do the same with mocks to check dispatch order,
model routing, and BLOCKED handling without spawning real agents.
"""

import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / ".claude" / "workflows" / "hive-wave.js"

HARNESS = r"""
const fs = require("fs");
const [scriptPath, cfgPath] = process.argv.slice(2);
const cfg = JSON.parse(fs.readFileSync(cfgPath, "utf8"));
const src = fs.readFileSync(scriptPath, "utf8").replace(/^export const meta/m, "const meta");
const calls = [];
const agent = async (prompt, opts = {}) => {
  calls.push({ label: opts.label, model: opts.model, phase: opts.phase, prompt });
  const status = (cfg.statuses || {})[opts.label] || "DONE";
  return { status, files: [opts.label + ".out"], test_output: "", notes: "" };
};
const pipeline = async (items, ...stages) =>
  Promise.all(items.map(async (item, idx) => {
    let prev = item;
    for (const s of stages) {
      try { prev = await s(prev, item, idx); } catch (e) { return null; }
    }
    return prev;
  }));
const parallel = async (thunks) => Promise.all(thunks.map((t) => t().catch(() => null)));
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;
// Run the real body; its own top-level `return` yields the workflow result.
const fn = new AsyncFunction("agent", "pipeline", "parallel", "phase", "log", "args", src);
fn(agent, pipeline, parallel, () => {}, () => {}, cfg.args)
  .then((result) => process.stdout.write(JSON.stringify({ calls, result })))
  .catch((e) => { process.stdout.write(JSON.stringify({ calls, error: String(e && e.message || e) })); });
"""


def task(tid, stub=False):
    return {"id": tid, "title": f"task {tid}", "files": [f"src/{tid}.py"],
            "stub": stub, "test": f"tests/test_{tid}.py", "context": ["PLAN.md#wave-1"]}


@unittest.skipUnless(shutil.which("node"), "node not installed")
class TestHiveWave(unittest.TestCase):
    def run_wave(self, args, statuses=None):
        with tempfile.TemporaryDirectory() as d:
            harness = Path(d) / "harness.js"
            harness.write_text(HARNESS, encoding="utf-8")
            cfg = Path(d) / "cfg.json"
            cfg.write_text(json.dumps({"args": args, "statuses": statuses or {}}), encoding="utf-8")
            out = subprocess.run(["node", str(harness), str(SCRIPT), str(cfg)],
                                 capture_output=True, text=True)
            self.assertEqual(out.returncode, 0, out.stderr)
            return json.loads(out.stdout)

    def test_meta_is_pure_literal_named_hive_wave(self):
        src = SCRIPT.read_text(encoding="utf-8")
        self.assertTrue(src.lstrip().startswith("export const meta = {"))
        meta = src[src.index("{"): src.index("\n}\n") + 2]
        self.assertIn("name: 'hive-wave'", meta)
        self.assertIsNone(re.search(r"\$\{|\.\.\.|\w\(", meta), "meta must be a pure literal")

    def test_stub_runs_only_when_requested_with_model_routing(self):
        r = self.run_wave({"wave": 1, "batches": [[task("T1", stub=True), task("T2")]]})
        labels = {c["label"]: c["model"] for c in r["calls"]}
        self.assertEqual(labels, {"T1:stub": "haiku", "T1:test": "sonnet", "T1:impl": "sonnet",
                                  "T2:test": "sonnet", "T2:impl": "sonnet"})

    def test_red_before_green_per_task(self):
        r = self.run_wave({"wave": 1, "batches": [[task("T1")]]})
        self.assertEqual([c["label"] for c in r["calls"]], ["T1:test", "T1:impl"])

    def test_prompts_carry_pointers_not_code(self):
        r = self.run_wave({"wave": 1, "batches": [[task("T1")]]})
        self.assertIn("PLAN.md#wave-1", r["calls"][0]["prompt"])
        self.assertIn("tests/test_T1.py", r["calls"][0]["prompt"])

    def test_batches_run_in_order(self):
        r = self.run_wave({"wave": 1, "batches": [[task("T1"), task("T2")], [task("T3")]]})
        labels = [c["label"] for c in r["calls"]]
        last_b1 = max(labels.index(l) for l in ("T1:impl", "T2:impl"))
        self.assertLess(last_b1, labels.index("T3:test"))

    def test_result_shape(self):
        r = self.run_wave({"wave": 2, "batches": [[task("T1")]]})["result"]
        self.assertEqual(r["wave"], 2)
        self.assertEqual([x["id"] for x in r["results"]], ["T1"])
        self.assertEqual(r["results"][0]["status"], "DONE")
        self.assertEqual(r["blocked"], [])
        self.assertEqual(r["skipped"], [])

    def test_blocked_stops_task_and_later_batches(self):
        r = self.run_wave({"wave": 1, "batches": [[task("T1"), task("T2")], [task("T3")]]},
                          statuses={"T1:test": "BLOCKED"})
        labels = [c["label"] for c in r["calls"]]
        self.assertNotIn("T1:impl", labels)
        self.assertIn("T2:impl", labels, "sibling task in the same batch still finishes")
        self.assertNotIn("T3:test", labels)
        res = r["result"]
        self.assertEqual([b["id"] for b in res["blocked"]], ["T1"])
        self.assertEqual(res["blocked"][0]["stage"], "test")
        self.assertEqual(res["skipped"], ["T3"])

    def test_missing_batches_is_an_error(self):
        r = self.run_wave({"wave": 1})
        self.assertIn("batches", r.get("error", ""))


if __name__ == "__main__":
    unittest.main()
