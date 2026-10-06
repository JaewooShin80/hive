"""Tests for scripts/metric_log.py and scripts/metric_summary.py — opt-in metrics."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from metric_log import log_event, is_enabled  # noqa: E402
from metric_summary import summarize  # noqa: E402


class TestLogEvent(unittest.TestCase):
    def test_no_op_when_disabled(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "metrics.jsonl"
            log_event("skill_start", skill="hive:plan", path=path, enabled=False)
            self.assertFalse(path.exists(), "must not write when disabled")

    def test_writes_jsonl_when_enabled(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "metrics.jsonl"
            log_event("skill_start", skill="hive:plan", path=path, enabled=True)
            self.assertTrue(path.exists())
            line = path.read_text(encoding="utf-8").strip()
            obj = json.loads(line)
            self.assertEqual(obj["event"], "skill_start")
            self.assertEqual(obj["skill"], "hive:plan")
            self.assertIn("ts", obj)

    def test_appends_multiple_events(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "metrics.jsonl"
            log_event("skill_start", skill="a", path=path, enabled=True)
            log_event("skill_end", skill="a", path=path, enabled=True)
            log_event("skill_start", skill="b", path=path, enabled=True)
            lines = path.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(lines), 3)
            for line in lines:
                json.loads(line)  # must be valid JSON

    def test_includes_extra_data(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "metrics.jsonl"
            log_event(
                "skill_end", skill="a", path=path, enabled=True,
                data={"duration_ms": 1234, "verdict": "DONE"},
            )
            obj = json.loads(path.read_text(encoding="utf-8").strip())
            self.assertEqual(obj["data"]["duration_ms"], 1234)
            self.assertEqual(obj["data"]["verdict"], "DONE")


class TestIsEnabled(unittest.TestCase):
    def setUp(self):
        self._saved = os.environ.pop("HIVE_METRICS", None)

    def tearDown(self):
        if self._saved is not None:
            os.environ["HIVE_METRICS"] = self._saved
        else:
            os.environ.pop("HIVE_METRICS", None)

    def test_default_disabled(self):
        self.assertFalse(is_enabled())

    def test_enabled_when_env_is_one(self):
        os.environ["HIVE_METRICS"] = "1"
        self.assertTrue(is_enabled())

    def test_disabled_when_env_is_zero(self):
        os.environ["HIVE_METRICS"] = "0"
        self.assertFalse(is_enabled())

    def test_enabled_when_env_is_true(self):
        os.environ["HIVE_METRICS"] = "true"
        self.assertTrue(is_enabled())


class TestSummarize(unittest.TestCase):
    def test_empty_file_returns_zero_counts(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "metrics.jsonl"
            path.write_text("", encoding="utf-8")
            result = summarize(path)
            self.assertEqual(result["total_events"], 0)
            self.assertEqual(result["events_by_type"], {})
            self.assertEqual(result["events_by_skill"], {})

    def test_missing_file_returns_zero(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "absent.jsonl"
            result = summarize(path)
            self.assertEqual(result["total_events"], 0)

    def test_counts_by_event_and_skill(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "metrics.jsonl"
            path.write_text(
                "\n".join([
                    json.dumps({"ts": "t1", "event": "skill_start", "skill": "a"}),
                    json.dumps({"ts": "t2", "event": "skill_end", "skill": "a"}),
                    json.dumps({"ts": "t3", "event": "skill_start", "skill": "b"}),
                    json.dumps({"ts": "t4", "event": "skill_start", "skill": "a"}),
                ]) + "\n",
                encoding="utf-8",
            )
            result = summarize(path)
            self.assertEqual(result["total_events"], 4)
            self.assertEqual(result["events_by_type"]["skill_start"], 3)
            self.assertEqual(result["events_by_type"]["skill_end"], 1)
            self.assertEqual(result["events_by_skill"]["a"], 3)
            self.assertEqual(result["events_by_skill"]["b"], 1)

    def test_skips_malformed_lines(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "metrics.jsonl"
            path.write_text(
                json.dumps({"ts": "t1", "event": "skill_start", "skill": "a"}) + "\n"
                + "not json\n"
                + json.dumps({"ts": "t2", "event": "skill_end", "skill": "a"}) + "\n",
                encoding="utf-8",
            )
            result = summarize(path)
            self.assertEqual(result["total_events"], 2)
            self.assertEqual(result["malformed_lines"], 1)


if __name__ == "__main__":
    unittest.main()
