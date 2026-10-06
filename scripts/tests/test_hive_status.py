"""Tests for scripts/hive-status.py — statusline rendering & parsing."""

from __future__ import annotations

import importlib.util
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path

# Force plain style BEFORE importing module so ANSI codes don't pollute assertions.
os.environ["HIVE_STATUS_STYLE"] = "plain"

_HERE = Path(__file__).resolve()
_SRC = _HERE.parent.parent / "hive-status.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("hive_status", _SRC)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod  # @dataclass resolves annotations via sys.modules
    spec.loader.exec_module(mod)
    return mod


hive_status = _load_module()


class TestBar(unittest.TestCase):
    def test_zero_percent_is_all_empty(self):
        self.assertEqual(hive_status.bar(0, width=10), "[----------]")

    def test_hundred_percent_is_all_filled(self):
        self.assertEqual(hive_status.bar(100, width=10), "[##########]")

    def test_fifty_percent_is_half_filled(self):
        self.assertEqual(hive_status.bar(50, width=10), "[#####-----]")

    def test_negative_is_clamped_to_zero(self):
        self.assertEqual(hive_status.bar(-25, width=8), "[--------]")

    def test_over_hundred_is_clamped(self):
        self.assertEqual(hive_status.bar(250, width=8), "[########]")

    def test_default_width_is_eight(self):
        out = hive_status.bar(100)
        # plain mode: "[" + 8 fills + "]"
        self.assertEqual(len(out), 10)


class TestPctLabel(unittest.TestCase):
    def test_zero(self):
        # plain mode: no color codes
        self.assertEqual(hive_status.pct_label(0), "  0%")

    def test_hundred(self):
        self.assertEqual(hive_status.pct_label(100), "100%")

    def test_rounds_to_int(self):
        self.assertEqual(hive_status.pct_label(42.4), " 42%")
        self.assertEqual(hive_status.pct_label(42.6), " 43%")


class TestGetModel(unittest.TestCase):
    def test_strips_claude_prefix(self):
        data = {"model": {"display_name": "claude-opus-4-7"}}
        self.assertEqual(hive_status.get_model(data)[0], "opus-4-7")

    def test_falls_back_to_id(self):
        data = {"model": {"id": "claude-sonnet-4-6"}}
        self.assertEqual(hive_status.get_model(data)[0], "sonnet-4-6")

    def test_strips_control_chars(self):
        data = {"model": {"display_name": "claude-\x01opus\x07"}}
        self.assertEqual(hive_status.get_model(data)[0], "opus")

    def test_truncates_to_20_chars(self):
        data = {"model": {"display_name": "x" * 50}}
        self.assertEqual(len(hive_status.get_model(data)[0]), 20)


class TestGetWaveProgress(unittest.TestCase):
    def test_no_worklog_returns_zero(self):
        with tempfile.TemporaryDirectory() as d:
            cwd = os.getcwd()
            os.chdir(d)
            try:
                self.assertEqual(hive_status.get_wave_progress_fallback({"cwd": d}), (0, 0))
            finally:
                os.chdir(cwd)

    def test_counts_completed_and_total(self):
        with tempfile.TemporaryDirectory() as d:
            cwd = os.getcwd()
            os.chdir(d)
            try:
                Path("WORKLOG.md").write_text(
                    "- [x] Wave 1: setup\n"
                    "- [x] Wave 2: api\n"
                    "- [ ] Wave 3: ui\n"
                    "- [ ] Wave 4: tests\n",
                    encoding="utf-8",
                )
                self.assertEqual(hive_status.get_wave_progress_fallback({"cwd": d}), (2, 4))
            finally:
                os.chdir(cwd)


class TestGetContextPct(unittest.TestCase):
    def test_missing_returns_none(self):
        self.assertIsNone(hive_status.get_context_pct({}))

    def test_full_remaining_is_zero_used(self):
        data = {"context_window": {"remaining_percentage": 100}}
        self.assertEqual(hive_status.get_context_pct(data), 0.0)

    def test_normalizes_against_auto_compact_buffer(self):
        # 16.5% reserved for auto-compact buffer.
        # remaining=83.5 → used=16.5 → normalized=(16.5/83.5)*100 ≈ 19.76
        data = {"context_window": {"remaining_percentage": 83.5}}
        result = hive_status.get_context_pct(data)
        self.assertAlmostEqual(result, 19.76, delta=0.05)

    def test_caps_at_100(self):
        data = {"context_window": {"remaining_percentage": 0}}
        self.assertEqual(hive_status.get_context_pct(data), 100.0)


class TestGetRateLimit(unittest.TestCase):
    def test_missing_returns_none(self):
        self.assertIsNone(hive_status.get_rate_limit({}, "five_hour")[0])

    def test_returns_used_percentage(self):
        data = {"rate_limits": {"five_hour": {"used_percentage": 42.5}}}
        self.assertEqual(hive_status.get_rate_limit(data, "five_hour")[0], 42.5)


class TestGetEffort(unittest.TestCase):
    def test_dict_effort_uses_level(self):
        os.environ.pop("HIVE_EFFORT", None)
        data = {"effort": {"level": "high"}}
        self.assertEqual(hive_status.get_effort(data)[0], "high")


class TestGetCost(unittest.TestCase):
    def test_missing_returns_none(self):
        self.assertIsNone(hive_status.get_cost({}))

    def test_returns_total_cost(self):
        data = {"cost": {"total_cost_usd": 0.123}}
        self.assertEqual(hive_status.get_cost(data), 0.123)


class TestColorFor(unittest.TestCase):
    """In plain mode all colors are empty strings — test thresholds in color mode."""

    def setUp(self):
        os.environ["HIVE_STATUS_STYLE"] = "color"
        self.mod = _load_module()

    def tearDown(self):
        os.environ["HIVE_STATUS_STYLE"] = "plain"

    def test_low_is_green(self):
        self.assertEqual(self.mod.color_for(0), self.mod.C_GREEN)
        self.assertEqual(self.mod.color_for(40), self.mod.C_GREEN)

    def test_mid_is_yellow(self):
        self.assertEqual(self.mod.color_for(41), self.mod.C_YELLOW)
        self.assertEqual(self.mod.color_for(60), self.mod.C_YELLOW)

    def test_high_is_orange(self):
        self.assertEqual(self.mod.color_for(61), self.mod.C_ORANGE)
        self.assertEqual(self.mod.color_for(80), self.mod.C_ORANGE)

    def test_critical_is_red(self):
        self.assertEqual(self.mod.color_for(81), self.mod.C_RED)
        self.assertEqual(self.mod.color_for(100), self.mod.C_RED)


if __name__ == "__main__":
    unittest.main()
