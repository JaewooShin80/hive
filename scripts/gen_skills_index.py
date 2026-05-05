#!/usr/bin/env python3
"""
gen_skills_index.py — Auto-generate the skill catalog table for SKILLS.md.

Source of truth = each skill's frontmatter `description`.
The output replaces content between the markers below.

CLI:
    python3 scripts/gen_skills_index.py [--plugin DIR] --write FILE
    python3 scripts/gen_skills_index.py [--plugin DIR] --check FILE

  --write FILE   rewrite FILE with refreshed table (idempotent)
  --check FILE   exit 1 if FILE's table is out of sync with frontmatter
  (no flag)      print refreshed table to stdout

exit 0 = ok, 1 = stale (--check) or error.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).resolve().parent))

from skill_lint import parse_frontmatter  # noqa: E402

MARKER_START = "<!-- AUTO-INDEX:start -->"
MARKER_END = "<!-- AUTO-INDEX:end -->"


def extract_catalog(plugin_dir: Path) -> List[dict]:
    skills_dir = plugin_dir / "skills"
    out: List[dict] = []
    if not skills_dir.is_dir():
        return out
    for md in sorted(skills_dir.glob("*.md")):
        text = md.read_text(encoding="utf-8")
        meta, _ = parse_frontmatter(text)
        if not meta or "name" not in meta or "description" not in meta:
            continue
        out.append({
            "name": meta["name"],
            "description": meta["description"],
            "file": str(md.relative_to(plugin_dir)),
        })
    out.sort(key=lambda e: e["name"])
    return out


def _escape_pipe(s: str) -> str:
    return s.replace("|", r"\|")


def render_table(catalog: List[dict]) -> str:
    lines = [
        "| Command | Description |",
        "| --- | --- |",
    ]
    for entry in catalog:
        name = entry["name"]
        desc = _escape_pipe(entry["description"])
        lines.append(f"| `/{name}` | {desc} |")
    return "\n".join(lines)


def update_marker_section(text: str, new_block: str) -> str:
    start_idx = text.find(MARKER_START)
    end_idx = text.find(MARKER_END)
    if start_idx == -1 or end_idx == -1 or end_idx < start_idx:
        raise ValueError(
            f"missing markers {MARKER_START} / {MARKER_END} in target file"
        )
    before = text[: start_idx + len(MARKER_START)]
    after = text[end_idx:]
    return f"{before}\n{new_block}\n{after}"


def main(argv: List[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument(
        "--plugin",
        default=".claude/plugins/aifab",
        help="plugin root directory (default: .claude/plugins/aifab)",
    )
    p.add_argument("--write", metavar="FILE", help="rewrite FILE with refreshed table")
    p.add_argument("--check", metavar="FILE", help="exit 1 if FILE is stale")
    args = p.parse_args(argv[1:])

    plugin = Path(args.plugin)
    if not plugin.exists():
        print(f"error: plugin dir not found: {plugin}", file=sys.stderr)
        return 1

    catalog = extract_catalog(plugin)
    table = render_table(catalog)

    if args.write:
        path = Path(args.write)
        original = path.read_text(encoding="utf-8")
        try:
            updated = update_marker_section(original, table)
        except ValueError as e:
            print(f"error: {e}", file=sys.stderr)
            return 1
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            print(f"updated: {path}")
        else:
            print(f"already in sync: {path}")
        return 0

    if args.check:
        path = Path(args.check)
        original = path.read_text(encoding="utf-8")
        try:
            updated = update_marker_section(original, table)
        except ValueError as e:
            print(f"error: {e}", file=sys.stderr)
            return 1
        if updated == original:
            return 0
        print(f"stale: {path} differs from generated index", file=sys.stderr)
        return 1

    print(table)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
