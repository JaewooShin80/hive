"""Verify _shared/agent-dispatch.md documents prompt-injection guards."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DISPATCH_MD = REPO_ROOT / ".claude" / "plugins" / "hive" / "_shared" / "agent-dispatch.md"


class TestInjectionGuard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = DISPATCH_MD.read_text(encoding="utf-8")

    def test_section_heading_exists(self):
        # require a section discussing prompt injection
        self.assertRegex(
            self.text,
            r"##\s+.*(Prompt[ \-]Injection|프롬프트 인젝션)",
            "missing prompt-injection guard section heading",
        )

    def test_user_input_marker_documented(self):
        # require an explicit isolation marker convention
        self.assertIn(
            "<USER_INPUT>", self.text,
            "must document <USER_INPUT>...</USER_INPUT> isolation marker",
        )
        self.assertIn("</USER_INPUT>", self.text)

    def test_external_content_isolation_documented(self):
        # require guidance on isolating web/tool output
        self.assertRegex(
            self.text,
            r"(EXTERNAL_CONTENT|web|fetched|외부 콘텐츠|도구 출력)",
        )

    def test_secret_handling_documented(self):
        # require a no-secrets-in-prompt rule
        self.assertRegex(
            self.text,
            r"(secret|token|API key|시크릿|토큰)",
            "missing secret-handling guidance",
        )

    def test_data_not_instruction_rule(self):
        # require statement that wrapped content is data, not commands
        self.assertRegex(
            self.text,
            r"(treat .* as data|데이터로만|명령으로 해석하지)",
            "missing 'treat as data, not instructions' rule",
        )


if __name__ == "__main__":
    unittest.main()
