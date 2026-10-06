"""Tests for scripts/skill_lint.py — skill markdown integrity validator."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from skill_lint import (  # noqa: E402
    Issue,
    Severity,
    lint_plugin,
    parse_frontmatter,
    validate_index,
    validate_shared_links,
    validate_skill_file,
)


class TestParseFrontmatter(unittest.TestCase):
    def test_valid_frontmatter_returns_dict(self):
        text = "---\nname: foo\ndescription: bar baz\n---\n\n# Body"
        meta, body_offset = parse_frontmatter(text)
        self.assertEqual(meta["name"], "foo")
        self.assertEqual(meta["description"], "bar baz")
        self.assertGreater(body_offset, 0)

    def test_missing_frontmatter_returns_none(self):
        text = "# Just a heading\n\nNo frontmatter."
        meta, body_offset = parse_frontmatter(text)
        self.assertIsNone(meta)
        self.assertEqual(body_offset, 0)

    def test_unterminated_frontmatter_returns_none(self):
        text = "---\nname: foo\nno closing fence ever"
        meta, body_offset = parse_frontmatter(text)
        self.assertIsNone(meta)


class TestValidateSkillFile(unittest.TestCase):
    def _write(self, dirpath: Path, name: str, content: str) -> Path:
        p = dirpath / name
        p.write_text(content, encoding="utf-8")
        return p

    def test_valid_skill_passes(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            f = self._write(
                d, "ok.md",
                "---\nname: hive:ok\ndescription: a valid skill\n---\n\nbody\n",
            )
            issues = validate_skill_file(f)
            self.assertEqual(issues, [])

    def test_missing_frontmatter_is_error(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            f = self._write(d, "bad.md", "# no frontmatter\n")
            issues = validate_skill_file(f)
            self.assertTrue(any(i.severity is Severity.ERROR for i in issues))
            self.assertTrue(any("frontmatter" in i.message.lower() for i in issues))

    def test_missing_name_is_error(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            f = self._write(
                d, "bad.md",
                "---\ndescription: no name field\n---\nbody\n",
            )
            issues = validate_skill_file(f)
            self.assertTrue(any("name" in i.message for i in issues))

    def test_missing_description_is_error(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            f = self._write(
                d, "bad.md",
                "---\nname: hive:foo\n---\nbody\n",
            )
            issues = validate_skill_file(f)
            self.assertTrue(any("description" in i.message for i in issues))


class TestValidateSharedLinks(unittest.TestCase):
    def test_existing_shared_link_passes(self):
        with tempfile.TemporaryDirectory() as d:
            plugin = Path(d)
            shared = plugin / "_shared"
            shared.mkdir()
            (shared / "git-commit.md").write_text("ok", encoding="utf-8")
            skill_text = "see [commit](_shared/git-commit.md) for details."
            issues = validate_shared_links(
                skill_text, skill_path=plugin / "skills" / "x.md", plugin_root=plugin
            )
            self.assertEqual(issues, [])

    def test_broken_shared_link_is_error(self):
        with tempfile.TemporaryDirectory() as d:
            plugin = Path(d)
            (plugin / "_shared").mkdir()
            skill_text = "broken: [missing](_shared/does-not-exist.md)."
            issues = validate_shared_links(
                skill_text, skill_path=plugin / "skills" / "x.md", plugin_root=plugin
            )
            self.assertTrue(any(i.severity is Severity.ERROR for i in issues))
            self.assertTrue(any("does-not-exist" in i.message for i in issues))


class TestValidateIndex(unittest.TestCase):
    def test_all_skills_referenced_passes(self):
        with tempfile.TemporaryDirectory() as d:
            plugin = Path(d)
            (plugin / "skills").mkdir()
            (plugin / "skills" / "a.md").write_text("---\nname: a\ndescription: x\n---", encoding="utf-8")
            (plugin / "skills" / "b.md").write_text("---\nname: b\ndescription: x\n---", encoding="utf-8")
            (plugin / "SKILLS.md").write_text("- a.md\n- b.md\n", encoding="utf-8")
            issues = validate_index(plugin)
            self.assertEqual(issues, [])

    def test_unreferenced_skill_is_error(self):
        with tempfile.TemporaryDirectory() as d:
            plugin = Path(d)
            (plugin / "skills").mkdir()
            (plugin / "skills" / "a.md").write_text("---\nname: a\ndescription: x\n---", encoding="utf-8")
            (plugin / "skills" / "orphan.md").write_text("---\nname: orphan\ndescription: x\n---", encoding="utf-8")
            (plugin / "SKILLS.md").write_text("- a.md only\n", encoding="utf-8")
            issues = validate_index(plugin)
            self.assertTrue(any("orphan" in i.message for i in issues))


class TestLintPlugin(unittest.TestCase):
    def test_real_hive_plugin_passes(self):
        repo_root = Path(__file__).resolve().parents[2]
        plugin = repo_root / ".claude" / "plugins" / "hive"
        self.assertTrue(plugin.exists(), f"missing plugin dir: {plugin}")
        issues = lint_plugin(plugin)
        errors = [i for i in issues if i.severity is Severity.ERROR]
        self.assertEqual(errors, [], f"unexpected errors: {errors}")


if __name__ == "__main__":
    unittest.main()
