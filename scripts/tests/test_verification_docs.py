"""Verification skills match the stacks they run on (harness review H-09, H-26..H-29)."""

import unittest
from pathlib import Path

SKILLS = Path(__file__).resolve().parents[2] / ".claude/plugins/hive/skills"


def read(name):
    return (SKILLS / name).read_text(encoding="utf-8")


class TestSecurityDoc(unittest.TestCase):
    def setUp(self):
        self.text = read("security.md")

    def test_availability_is_critical(self):
        self.assertIn("### A8. 가용성", self.text)
        self.assertIn("ReDoS", self.text)

    def test_threat_model_and_na_domains(self):
        for marker in ("위협 모델", "N/A (사유)", "127.0.0.1"):
            self.assertIn(marker, self.text)

    def test_wave_scope_does_not_use_head_tilde_one(self):
        self.assertNotIn("git diff HEAD~1", self.text)

    def test_dependency_audit_uses_project_env_and_reports_missing_tool(self):
        self.assertIn("uvx pip-audit -r requirements.txt", self.text)
        self.assertNotIn("pip-audit 2>/dev/null", self.text)

    def test_report_is_saved_and_commit_is_optional(self):
        self.assertIn("docs/security/SECURITY-REVIEW-", self.text)
        self.assertIn("--no-commit", self.text)
        self.assertNotIn("(모두 즉시 수정 완료)", self.text)

    def test_no_js_syntax_in_python_cookie_example(self):
        self.assertNotIn("httpOnly: True", self.text)


class TestPlaywrightDoc(unittest.TestCase):
    def test_python_path_uses_project_venv_pytest_playwright(self):
        text = read("playwright.md")
        self.assertIn(".venv/bin/pip install pytest-playwright", text)
        self.assertIn("--screenshot=on --tracing=on", text)
        self.assertIn("Auth Flow** | 로그인/권한이 있을 때만", text)
        self.assertIn("- Playwright: 통과", text)  # uat precondition reads this line


class TestUatDoc(unittest.TestCase):
    def test_evidence_mode_and_no_hardcoded_tag(self):
        text = read("uat.md")
        self.assertIn("--evidence", text)
        self.assertIn("![<단계>](NN.png)", text)
        self.assertNotIn("git tag -a v1.0.0", text)


class TestEvaluateDoc(unittest.TestCase):
    def test_fallback_runner_is_shipped_script(self):
        text = read("evaluate.md")
        self.assertIn("python3 scripts/hive_evaluate.py", text)
        self.assertNotIn("tests/mock-app/evaluate_harness.py` 같은 stub harness", text)


if __name__ == "__main__":
    unittest.main()
