# Changelog

All notable changes to the AI-Fab harness are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed (BREAKING)
- Harness renamed **AI-Fab → HIVE**: commands `/aifab:*` → `/hive:*`, files `aifab-*` → `hive-*`,
  env `AIFAB_*` → `HIVE_*`, plugin dir `.claude/plugins/aifab` → `.claude/plugins/hive`.
  Re-running the installer migrates old settings (aifab hook entries, `AIFAB_*` env, statusLine)
  and warns about a leftover `commands/aifab` directory.
- Model ids use family aliases (`opus` / `sonnet` / `haiku`) so the latest release is picked up automatically.

### Added
- Cross-platform installer core `scripts/hive-install.js`; `install.sh` (bash) and new `install.ps1`
  (Windows PowerShell) are thin wrappers. Skills install as slash commands, `_shared` lives outside
  the commands tree, hooks + statusLine are registered as shell-neutral `node "<path>"` commands.
- `scripts/hive-status.js` statusLine launcher (python3 → python → py -3 discovery).

### Fixed — harness review (3 entry scenarios, H-01..H-34)
- `hive-wave` workflow: `stub:false` tasks no longer vanish silently; `root`/`test_cmd` args;
  guardrails in every prompt (no commit, no WORKLOG/PLAN edits, own files only); stub stage
  cannot write tests; Red may return ALREADY_SATISFIED; Green may return TEST_DEFECT (one Red
  rerun); `depends_on`; per-batch test gate with out-of-scope change check; accounting check.
- Progress has one source of truth — PLAN.md success-criteria checkboxes — read the same way by
  `/hive:execute`, session-start hook, `/hive:progress` (now works without ROADMAP.md) and
  `/hive:roadmap update`; `##`/`###` Wave headers both accepted.
- Wave commits use `feat(wave-N): …` everywhere; wave-gate detects `-qm`/`-am`/`--message`/heredoc.
- `/hive:security`: threat model + stack gate (N/A domains), availability/DoS (ReDoS, zip bomb,
  unbounded input) as Critical, project-env dependency audit, report file, `--no-commit`.
- `/hive:playwright` Python path (pytest-playwright in the project venv); `/hive:uat` no longer
  creates a hardcoded `v1.0.0` tag; `/hive:rollback` uses `git reset --keep` (`--hard` is denied).
- `hive-worklog-auto` records into the edited file's own project even when the session cwd differs.
- Global + project hook installs no longer run twice (`hive-hook-dedupe.js`).
- `/hive:progress` referenced a non-existent `scripts/aifab-progress.py`.

### Added — harness review
- `--auto` mode and batched questions (`_shared/auto-mode.md`); document input for docx/xlsx/pptx/
  pdf/hwp requirement docs (`_shared/document-input.md`).
- README quick start with three entry paths (idea / requirements doc / existing code); brownfield
  path map-codebase → spec (change mode) → discover (B: keep/restructure/rewrite) → plan.
- `/hive:uat --evidence` (Playwright screenshots, video, trace, report with embedded images).
- `scripts/gen_feature_list.py` (PLAN → feature-list.json, append-only, ``(verify: `cmd`)``),
  `scripts/hive_evaluate.py` (MCP-less `/hive:evaluate` runner) — both installed.
- Installer `--check` (drift report, exit 1) and `hive/INSTALLED` version stamp.

## [2.3.1] — 2026-05-05

### Changed
- `CLAUDE.md` workflow-commands table is now auto-generated from skill
  frontmatter (same `<!-- AUTO-INDEX -->` marker pattern as `SKILLS.md`).
  CI's `gen_skills_index.py --check` now covers both files, eliminating
  the previous risk of drift between the two views.
- The hand-written Korean one-line descriptions in the old `CLAUDE.md`
  table are replaced by the English `description` field in each skill's
  frontmatter (single source of truth). Korean prose around the table is
  unchanged.

### Added
- `scripts/tests/test_claude_md_index.py` — 4 tests covering marker
  presence, marker order, generator stale detection on `CLAUDE.md`,
  and a multi-file smoke test.

## [2.3.0] — 2026-05-05

### Added
- `CONTRIBUTING.md` — dev setup, test commands, skill addition workflow,
  commit style, PR checklist (Karpathy 4 principles enforced)
- `.github/pull_request_template.md` — Summary / Test plan / Security
  review / high-level files / Karpathy checkbox sections
- `docs/adr/` directory with retrospective ADRs:
  - `0001-stdlib-only-policy.md` — rationale for zero external deps
  - `0002-skill-categorization.md` — four-category taxonomy decision
  - `README.md` — index + ADR addition workflow
- `scripts/metric_log.py` — opt-in JSONL event logger
  (off by default; enabled by `AIFAB_METRICS=1`)
- `scripts/metric_summary.py` — read JSONL and emit per-event/per-skill
  counts (text or `--json`)
- +23 tests across contributing / adr / metrics — total 94

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
