#!/usr/bin/env python3
"""
skill_lint.py — AI-Fab 스킬 markdown 정합성 검사기.

검증 항목:
  1. 각 skills/*.md 파일에 YAML frontmatter 존재 + 필수 필드(name, description)
  2. _shared/*.md 참조 링크가 실재 파일을 가리킴
  3. SKILLS.md에 모든 스킬이 등록됨 (orphan skill 없음)

CLI:
    python3 scripts/skill_lint.py [plugin_dir]
    (default: .claude/plugins/aifab)

exit 0 = clean, 1 = issues found.
"""

from __future__ import annotations

import enum
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple


class Severity(enum.Enum):
    ERROR = "error"
    WARNING = "warning"


@dataclass
class Issue:
    severity: Severity
    file: Path
    message: str


REQUIRED_FIELDS = ("name", "description")
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
SHARED_LINK_RE = re.compile(r"_shared/[A-Za-z0-9_\-./]+")


def parse_frontmatter(text: str) -> Tuple[Optional[dict], int]:
    """Parse simple YAML-ish frontmatter (single-line key: value pairs).

    Returns (meta_dict_or_None, body_char_offset).
    Multi-line list values are recorded as the literal "<list>" sentinel —
    we don't need their values, only the presence of the key.
    """
    if not text.startswith("---\n") and not text.startswith("---\r\n"):
        return None, 0

    lines = text.splitlines(keepends=True)
    end_idx = None
    for i in range(1, len(lines)):
        stripped = lines[i].rstrip("\r\n")
        if stripped == "---":
            end_idx = i
            break
    if end_idx is None:
        return None, 0

    meta: dict = {}
    current_key: Optional[str] = None
    for raw in lines[1:end_idx]:
        line = raw.rstrip("\r\n")
        if not line.strip():
            continue
        if line.startswith(("  ", "\t", "- ")):
            if current_key is not None:
                meta[current_key] = "<list>"
            continue
        m = re.match(r"^([A-Za-z0-9_\-]+):\s*(.*)$", line)
        if not m:
            continue
        key, value = m.group(1), m.group(2).strip()
        meta[key] = value if value else "<empty>"
        current_key = key

    body_offset = sum(len(l) for l in lines[: end_idx + 1])
    return meta, body_offset


def validate_skill_file(path: Path) -> list[Issue]:
    issues: list[Issue] = []
    text = path.read_text(encoding="utf-8")
    meta, _ = parse_frontmatter(text)
    if meta is None:
        issues.append(Issue(Severity.ERROR, path, "missing or unterminated YAML frontmatter"))
        return issues
    for field in REQUIRED_FIELDS:
        if field not in meta or meta[field] in ("", "<empty>"):
            issues.append(Issue(Severity.ERROR, path, f"frontmatter missing required field: {field}"))
    return issues


def validate_shared_links(text: str, skill_path: Path, plugin_root: Path) -> list[Issue]:
    issues: list[Issue] = []
    seen: set[str] = set()
    for m in LINK_RE.finditer(text):
        target = m.group(1).split("#", 1)[0]
        if not target.startswith("_shared/"):
            continue
        if target in seen:
            continue
        seen.add(target)
        resolved = (plugin_root / target).resolve()
        if not resolved.exists():
            issues.append(
                Issue(Severity.ERROR, skill_path, f"broken _shared link: {target}")
            )
    return issues


def validate_index(plugin_root: Path) -> list[Issue]:
    issues: list[Issue] = []
    skills_dir = plugin_root / "skills"
    index_path = plugin_root / "SKILLS.md"
    if not skills_dir.is_dir():
        return [Issue(Severity.ERROR, plugin_root, f"missing skills/ directory")]
    if not index_path.exists():
        return [Issue(Severity.ERROR, plugin_root, "missing SKILLS.md index")]

    index_text = index_path.read_text(encoding="utf-8")
    for skill_md in sorted(skills_dir.glob("*.md")):
        stem = skill_md.stem
        if stem not in index_text:
            issues.append(
                Issue(Severity.ERROR, index_path, f"skill not referenced in index: {stem}")
            )
    return issues


def lint_plugin(plugin_root: Path) -> list[Issue]:
    issues: list[Issue] = []
    skills_dir = plugin_root / "skills"
    if skills_dir.is_dir():
        for skill_md in sorted(skills_dir.glob("*.md")):
            issues.extend(validate_skill_file(skill_md))
            text = skill_md.read_text(encoding="utf-8")
            issues.extend(validate_shared_links(text, skill_md, plugin_root))
    issues.extend(validate_index(plugin_root))
    return issues


def main(argv: list[str]) -> int:
    plugin_dir = Path(argv[1]) if len(argv) > 1 else Path(".claude/plugins/aifab")
    if not plugin_dir.exists():
        print(f"error: plugin dir not found: {plugin_dir}", file=sys.stderr)
        return 1

    issues = lint_plugin(plugin_dir)
    errors = [i for i in issues if i.severity is Severity.ERROR]
    warnings = [i for i in issues if i.severity is Severity.WARNING]

    for issue in issues:
        try:
            rel = issue.file.relative_to(Path.cwd())
        except ValueError:
            rel = issue.file
        print(f"{issue.severity.value}: {rel}: {issue.message}")

    print(
        f"\n{len(errors)} error(s), {len(warnings)} warning(s) "
        f"across plugin: {plugin_dir}"
    )
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
