# Changelog

All notable changes to the AI-Fab harness are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.2.0] — 2026-05-05

### Added
- `install.sh` single-entry installer (target/global/copy/dry-run modes)
- `VERSION` file + `CHANGELOG.md`
- `scripts/gen_skills_index.py` — auto-regenerate `SKILLS.md` AUTO-INDEX
  marker section from each skill's frontmatter
- `docs/WALKTHROUGH.md` — 5-minute end-to-end guide for new users
- Prompt-injection hardening section in `_shared/agent-dispatch.md`
  (USER_INPUT / EXTERNAL_CONTENT isolation markers, secret-handling rules,
  data-vs-instruction rule, BLOCKED-on-suspicion rule)
- +32 tests across install / version / gen_skills_index / settings /
  injection_guard / walkthrough — total 71

### Security
- `settings.json` deny rules for 8 high-impact patterns:
  `rm -rf *`, `git push --force *`, `git push -f *`, `git reset --hard *`,
  `curl * | bash`, `curl * | sh`, `wget * | bash`, `wget * | sh`

## [2.1.0] — 2026-05-05

### Added
- `scripts/skill_lint.py` — markdown integrity validator
  - Frontmatter required-field check (`name`, `description`)
  - `_shared/*.md` link resolution
  - `SKILLS.md` orphan-skill detection
- `scripts/tests/test_skill_lint.py` (12 tests)
- `scripts/tests/test_aifab_status.py` (27 tests covering bar/color_for/parsers/normalization)
- `.github/workflows/ci.yml` — GitHub Actions CI on Python 3.9/3.11/3.13

### Notes
- All tests use stdlib only (no external dependencies).

## [2.0.0] — 2026-05 (pre-tag)

### Added
- 5 v2 skills: `refactor`, `migrate`, `rollback`, `compare`, `adr` (total 16)
- `_shared/` standard protocols (5 files): prerequisites, output-format,
  worklog-update, agent-dispatch, git-commit
- YAML frontmatter on every skill for global registration
- Colored progress bars in CLI status bar (4-tier threshold)
- Real-time context/rate-limit tracking via stdin JSON

### Changed
- Status bar rewritten in Python 3 for Korean/CJK safety
- Status bar collapsed to single line to avoid overdraw

## [1.1.0] — earlier

### Added
- 4 enhancement skills: `debug`, `map-codebase`, `worktree`, `codex-review`

## [1.0.0] — initial

### Added
- 7 core skills: `discover`, `plan`, `execute`, `security`, `playwright`,
  `uat`, `worklog`
- `CLAUDE.md` with Karpathy 4 principles + Context 50% rule
- `settings.json` with multi-agent model assignment
- `scripts/aifab-status.sh` CLI status bar
- `README.md` installation guide (3 methods)
