"""Tests for scripts/gen_skills_index.py — auto-index generator."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gen_skills_index import (  # noqa: E402
    MARKER_END,
    MARKER_START,
    extract_catalog,
    render_table,
    update_marker_section,
)


def _write_skill(plugin: Path, fname: str, name: str, desc: str) -> None:
    skills = plugin / "skills"
    skills.mkdir(exist_ok=True)
    (skills / fname).write_text(
        f"---\nname: {name}\ndescription: {desc}\n---\n\nbody\n",
        encoding="utf-8",
    )


class TestExtractCatalog(unittest.TestCase):
    def test_returns_sorted_entries(self):
        with tempfile.TemporaryDirectory() as d:
            plugin = Path(d)
            _write_skill(plugin, "b.md", "aifab:b", "second skill")
            _write_skill(plugin, "a.md", "aifab:a", "first skill")
            entries = extract_catalog(plugin)
            self.assertEqual([e["name"] for e in entries], ["aifab:a", "aifab:b"])
            self.assertEqual(entries[0]["description"], "first skill")

    def test_skips_files_without_frontmatter(self):
        with tempfile.TemporaryDirectory() as d:
            plugin = Path(d)
            _write_skill(plugin, "ok.md", "aifab:ok", "valid")
            (plugin / "skills" / "broken.md").write_text("# no frontmatter", encoding="utf-8")
            entries = extract_catalog(plugin)
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0]["name"], "aifab:ok")


class TestRenderTable(unittest.TestCase):
    def test_renders_markdown_table(self):
        catalog = [
            {"name": "aifab:foo", "description": "do foo"},
            {"name": "aifab:bar", "description": "do bar"},
        ]
        out = render_table(catalog)
        self.assertIn("| Command | Description |", out)
        self.assertIn("| `/aifab:foo` | do foo |", out)
        self.assertIn("| `/aifab:bar` | do bar |", out)

    def test_escapes_pipe_in_description(self):
        catalog = [{"name": "aifab:x", "description": "use a | pipe"}]
        out = render_table(catalog)
        # raw | inside description must be escaped to \|
        self.assertIn(r"use a \| pipe", out)


class TestUpdateMarkerSection(unittest.TestCase):
    def test_replaces_content_between_markers(self):
        original = (
            f"# Title\n\nintro\n\n{MARKER_START}\nstale content\n{MARKER_END}\n\nouter footer\n"
        )
        new_block = "fresh content"
        out = update_marker_section(original, new_block)
        self.assertIn(f"{MARKER_START}\nfresh content\n{MARKER_END}", out)
        self.assertNotIn("stale content", out)
        self.assertIn("outer footer", out)
        self.assertIn("intro", out)

    def test_missing_markers_raises(self):
        with self.assertRaises(ValueError):
            update_marker_section("no markers here\n", "x")

    def test_idempotent(self):
        original = f"x\n{MARKER_START}\nA\n{MARKER_END}\ny\n"
        once = update_marker_section(original, "B")
        twice = update_marker_section(once, "B")
        self.assertEqual(once, twice)


class TestRealPluginCatalog(unittest.TestCase):
    def test_real_plugin_yields_all_skills(self):
        repo_root = Path(__file__).resolve().parents[2]
        plugin = repo_root / ".claude" / "plugins" / "aifab"
        entries = extract_catalog(plugin)
        skill_files = list((plugin / "skills").glob("*.md"))
        self.assertEqual(len(entries), len(skill_files))
        for e in entries:
            self.assertTrue(e["name"].startswith("aifab:"), f"unexpected name: {e['name']}")
            self.assertTrue(e["description"], "empty description")


if __name__ == "__main__":
    unittest.main()
