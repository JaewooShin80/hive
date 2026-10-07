"""Behavior tests for .claude/workflows/hive-wave.js (saved Claude Code workflow).

The Workflow runtime wraps the script body in an async function and injects
agent/pipeline/phase/log/args. We do the same with mocks to check dispatch order,
model routing, and BLOCKED handling without spawning real agents.

The mock pipeline mirrors the real runtime: a stage that throws OR returns
null/undefined drops the item and skips its remaining stages. (An earlier mock
kept going on null, which hid the stub:false bug — H-01 in the harness review.)
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
const seen = {};
// cfg.statuses[label] is a status string or a list consumed one call at a time.
const pick = (label) => {
  const v = (cfg.statuses || {})[label];
  if (Array.isArray(v)) { const i = seen[label] = (seen[label] || 0); seen[label]++; return v[Math.min(i, v.length - 1)]; }
  return v;
};
const agent = async (prompt, opts = {}) => {
  calls.push({ label: opts.label, model: opts.model, phase: opts.phase, effort: opts.effort, prompt });
  const v = pick(opts.label);
  if (opts.label && opts.label.startsWith("gate:")) {
    return { passed: v !== "FAIL", summary: v === "FAIL" ? "2 failed" : "all passed", out_of_scope: [] };
  }
  return { status: v || "DONE", files: [opts.label + ".out"], test_output: "out:" + opts.label, notes: "n:" + opts.label };
};
const pipeline = async (items, ...stages) =>
  Promise.all(items.map(async (item, idx) => {
    let prev = item;
    for (const s of stages) {
      try { prev = await s(prev, item, idx); } catch (e) { return null; }
      if (prev === null || prev === undefined) return null;
    }
    return prev;
  }));
const parallel = async (thunks) => Promise.all(thunks.map((t) => t().catch(() => null)));
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;
const fn = new AsyncFunction("agent", "pipeline", "parallel", "phase", "log", "args", src);
fn(agent, pipeline, parallel, () => {}, () => {}, cfg.args)
  .then((result) => process.stdout.write(JSON.stringify({ calls, result })))
  .catch((e) => { process.stdout.write(JSON.stringify({ calls, error: String(e && e.message || e) })); });
"""

ROOT = "/abs/project"


def task(tid, stub=False, **extra):
    t = {"id": tid, "title": f"task {tid}", "files": [f"src/{tid}.py"],
         "stub": stub, "test": f"tests/test_{tid}.py", "context": ["PLAN.md#wave-1"]}
    t.update(extra)
    return t


def wave(batches, **extra):
    a = {"wave": 1, "root": ROOT, "test_cmd": ".venv/bin/pytest -q", "batches": batches}
    a.update(extra)
    return a


@unittest.skipUnless(shutil.which("node"), "node not installed")
class TestHiveWave(unittest.TestCase):
    def run_wave(self, args, statuses=None):
        with tempfile.TemporaryDirectory() as d:
            harness = Path(d) / "harness.js"
            harness.write_text(HARNESS, encoding="utf-8")
            cfg = Path(d) / "cfg.json"
            cfg.write_text(json.dumps({"args": args, "statuses": statuses or {}}), encoding="utf-8")
            out = subprocess.run(["node", str(harness), str(SCRIPT), str(cfg)],
                                 capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(out.returncode, 0, out.stderr)
            return json.loads(out.stdout)

    def labels(self, r, prefix=None):
        ls = [c["label"] for c in r["calls"]]
        return [l for l in ls if not l.startswith("gate:")] if prefix is None else [l for l in ls if l.startswith(prefix)]

    def prompt(self, r, label):
        return next(c["prompt"] for c in r["calls"] if c["label"] == label)

    # --- meta / args -------------------------------------------------------

    def test_meta_is_pure_literal_named_hive_wave(self):
        src = SCRIPT.read_text(encoding="utf-8")
        self.assertTrue(src.lstrip().startswith("export const meta = {"))
        meta = src[src.index("{"): src.index("\n}\n") + 2]
        self.assertIn("name: 'hive-wave'", meta)
        self.assertIsNone(re.search(r"\$\{|\.\.\.|\w\(", meta), "meta must be a pure literal")

    def test_missing_batches_is_an_error(self):
        r = self.run_wave({"wave": 1, "root": ROOT, "test_cmd": "pytest"})
        self.assertIn("batches", r.get("error", ""))

    def test_root_and_test_cmd_are_required(self):  # H-05
        r = self.run_wave({"wave": 1, "batches": [[task("T1")]]})
        self.assertIn("root", r.get("error", ""))
        r = self.run_wave({"wave": 1, "root": ROOT, "batches": [[task("T1")]]})
        self.assertIn("test_cmd", r.get("error", ""))

    def test_root_must_be_absolute(self):  # H-05
        r = self.run_wave(wave([[task("T1")]], root="relative/dir"))
        self.assertIn("absolute", r.get("error", ""))

    # --- dispatch ----------------------------------------------------------

    def test_task_without_stub_still_runs_red_and_green(self):  # H-01
        r = self.run_wave(wave([[task("T1")]]))
        self.assertEqual(self.labels(r), ["T1:test", "T1:impl"])
        self.assertEqual([x["id"] for x in r["result"]["results"]], ["T1"])

    def test_stub_runs_only_when_requested_with_model_routing(self):
        r = self.run_wave(wave([[task("T1", stub=True), task("T2")]]))
        labels = {c["label"]: c["model"] for c in r["calls"] if not c["label"].startswith("gate:")}
        self.assertEqual(labels, {"T1:stub": "haiku", "T1:test": "sonnet", "T1:impl": "sonnet",
                                  "T2:test": "sonnet", "T2:impl": "sonnet"})

    def test_batches_run_in_order(self):
        r = self.run_wave(wave([[task("T1"), task("T2")], [task("T3")]]))
        labels = [c["label"] for c in r["calls"]]
        last_b1 = max(labels.index(l) for l in ("T1:impl", "T2:impl", "gate:1"))
        self.assertLess(last_b1, labels.index("T3:test"))

    def test_every_task_is_accounted_for(self):
        r = self.run_wave(wave([[task("T1"), task("T2")], [task("T3")]]))
        res = r["result"]
        self.assertEqual(len(res["results"]) + len(res["blocked"]) + len(res["skipped"]), 3)

    def test_result_shape(self):
        res = self.run_wave(wave([[task("T1")]], wave=2))["result"]
        self.assertEqual(res["wave"], 2)
        self.assertEqual([x["id"] for x in res["results"]], ["T1"])
        self.assertEqual(res["results"][0]["status"], "DONE")
        self.assertEqual(res["blocked"], [])
        self.assertEqual(res["skipped"], [])
        self.assertEqual([g["batch"] for g in res["gates"]], [1])

    # --- prompts -----------------------------------------------------------

    def test_every_prompt_carries_root_and_guardrails(self):  # H-05, H-06
        r = self.run_wave(wave([[task("T1", stub=True)]]))
        for c in r["calls"]:
            self.assertIn(ROOT, c["prompt"], c["label"])
            self.assertIn("Do NOT git commit", c["prompt"], c["label"])
            self.assertIn("WORKLOG.md", c["prompt"], c["label"])

    def test_stub_prompt_has_no_test_file_and_forbids_tests(self):  # H-02
        r = self.run_wave(wave([[task("T1", stub=True)]]))
        p = self.prompt(r, "T1:stub")
        self.assertNotIn("tests/test_T1.py", p)
        self.assertIn("Do not create or modify any test file", p)

    def test_stage_prompts_name_only_their_own_files(self):  # H-02
        r = self.run_wave(wave([[task("T1")]]))
        red, green = self.prompt(r, "T1:test"), self.prompt(r, "T1:impl")
        self.assertIn("You may write only: tests/test_T1.py", red)
        self.assertIn("You may write only: src/T1.py", green)

    def test_red_runs_only_its_own_test_file_and_checks_the_reason(self):  # H-22, H-23, H-04
        p = self.prompt(self.run_wave(wave([[task("T1")]])), "T1:test")
        self.assertIn('cd "/abs/project" && .venv/bin/pytest -q tests/test_T1.py', p)
        self.assertIn("right reason", p)

    def test_context_pointers_are_passed(self):
        p = self.prompt(self.run_wave(wave([[task("T1")]])), "T1:test")
        self.assertIn("PLAN.md#wave-1", p)

    # --- outcomes ----------------------------------------------------------

    def test_already_satisfied_skips_green_and_counts_as_done(self):  # H-03
        r = self.run_wave(wave([[task("T1")], [task("T2")]]), statuses={"T1:test": "ALREADY_SATISFIED"})
        self.assertNotIn("T1:impl", self.labels(r))
        self.assertIn("T2:impl", self.labels(r))
        res = r["result"]
        self.assertEqual([(x["id"], x["status"]) for x in res["results"]],
                         [("T1", "ALREADY_SATISFIED"), ("T2", "DONE")])
        self.assertEqual(res["blocked"], [])

    def test_test_defect_reruns_red_once_then_green(self):  # H-04
        r = self.run_wave(wave([[task("T1")]]), statuses={"T1:impl": ["TEST_DEFECT", "DONE"]})
        self.assertEqual(self.labels(r), ["T1:test", "T1:impl", "T1:test", "T1:impl"])
        self.assertIn("n:T1:impl", r["calls"][2]["prompt"], "rerun Red gets the defect reason")
        self.assertEqual(r["result"]["results"][0]["status"], "DONE")

    def test_second_test_defect_blocks(self):  # H-04
        r = self.run_wave(wave([[task("T1")]]), statuses={"T1:impl": "TEST_DEFECT"})
        self.assertEqual(self.labels(r).count("T1:test"), 2)
        b = r["result"]["blocked"][0]
        self.assertEqual((b["id"], b["stage"]), ("T1", "impl"))

    def test_blocked_keeps_files_and_output(self):  # H-03
        r = self.run_wave(wave([[task("T1")]]), statuses={"T1:impl": "BLOCKED"})
        b = r["result"]["blocked"][0]
        self.assertIn("T1:test.out", b["files"])
        self.assertTrue(b["notes"])

    def test_blocked_without_depends_on_skips_later_batches(self):
        r = self.run_wave(wave([[task("T1"), task("T2")], [task("T3")]]), statuses={"T1:test": "BLOCKED"})
        labels = self.labels(r)
        self.assertNotIn("T1:impl", labels)
        self.assertIn("T2:impl", labels, "sibling task in the same batch still finishes")
        self.assertNotIn("T3:test", labels)
        res = r["result"]
        self.assertEqual([b["id"] for b in res["blocked"]], ["T1"])
        self.assertEqual(res["blocked"][0]["stage"], "test")
        self.assertEqual(res["skipped"], ["T3"])

    def test_depends_on_lets_independent_later_tasks_run(self):  # H-03
        r = self.run_wave(wave([[task("T1"), task("T2")],
                                [task("T3", depends_on=["T2"]), task("T4", depends_on=["T1"])]]),
                          statuses={"T1:test": "BLOCKED"})
        labels = self.labels(r)
        self.assertIn("T3:impl", labels)
        self.assertNotIn("T4:test", labels)
        self.assertEqual(r["result"]["skipped"], ["T4"])

    # --- batch gate --------------------------------------------------------

    def test_gate_runs_full_suite_per_batch_on_cheap_model(self):  # H-22, H-23, H-02
        r = self.run_wave(wave([[task("T1")], [task("T2")]]))
        gates = [c for c in r["calls"] if c["label"].startswith("gate:")]
        self.assertEqual([g["label"] for g in gates], ["gate:1", "gate:2"])
        self.assertEqual(gates[0]["model"], "haiku")
        # commands carry the cd themselves: a smoke run showed the gate agent ran the
        # suite in the session cwd when only told "cd there first"
        self.assertIn('cd "/abs/project" && .venv/bin/pytest -q', gates[0]["prompt"])
        self.assertIn('cd "/abs/project" && git status --porcelain', gates[0]["prompt"])
        self.assertIn("src/T1.py", gates[0]["prompt"])

    def test_failed_gate_stops_later_batches(self):
        r = self.run_wave(wave([[task("T1")], [task("T2")]]), statuses={"gate:1": "FAIL"})
        self.assertNotIn("T2:test", self.labels(r))
        res = r["result"]
        self.assertEqual(res["skipped"], ["T2"])
        self.assertFalse(res["gates"][0]["passed"])


if __name__ == "__main__":
    unittest.main()
