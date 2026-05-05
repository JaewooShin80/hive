# Contributing to AI-Fab

Thank you for considering a contribution. This harness is small and opinionated;
the rules below keep it simple to maintain.

---

## Development setup

```bash
git clone https://github.com/JaewooShin80/aifab.git
cd aifab
# No package manager needed — the harness is stdlib-only.
python3 --version   # 3.9 or newer
bash --version
```

There is **nothing to install** for development. All scripts and tests use
the Python standard library plus `bash` + `git`.

---

## Running tests

The full test suite runs in under a second:

```bash
# Skill markdown integrity
python3 scripts/skill_lint.py .claude/plugins/aifab

# SKILLS.md auto-index freshness
python3 scripts/gen_skills_index.py --check .claude/plugins/aifab/SKILLS.md

# Unit + integration tests
python3 -m unittest discover -s scripts/tests -v
```

CI runs the same three commands across Python 3.9 / 3.11 / 3.13.

---

## Adding a new skill

1. Create `.claude/plugins/aifab/skills/<name>.md` with valid YAML frontmatter:

   ```markdown
   ---
   name: aifab:<name>
   description: <one-line trigger description for Claude Code>
   ---

   # /aifab:<name>

   ...
   ```

2. Reference the skill in the appropriate category section of
   [`.claude/plugins/aifab/SKILLS.md`](.claude/plugins/aifab/SKILLS.md).

3. Regenerate the auto-index table:

   ```bash
   python3 scripts/gen_skills_index.py --write .claude/plugins/aifab/SKILLS.md
   ```

4. Run `python3 scripts/skill_lint.py .claude/plugins/aifab` — must report 0 errors.

5. If the skill introduces a new shared protocol, add a file under `_shared/`
   and link to it from the skill body.

---

## Commit style

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat(scope): summary` — user-visible feature
- `fix(scope): summary` — bug fix
- `docs(scope): summary` — docs only
- `chore(scope): summary` — tooling, infra
- `refactor(scope): summary` — behavior-preserving change

Scopes commonly used: `harness`, `status-bar`, `skills`, `_shared`, `ci`.

Each commit must:

- Pass all three CI commands above.
- Be self-contained — avoid mixing unrelated changes.
- Reference a Wave or PR thread in the body when applicable.

---

## Pull request checklist

Before opening a PR, run:

```bash
python3 scripts/skill_lint.py .claude/plugins/aifab
python3 scripts/gen_skills_index.py --check .claude/plugins/aifab/SKILLS.md
python3 -m unittest discover -s scripts/tests
```

In the PR description, fill in the [pull request template](.github/pull_request_template.md):

- **Summary** — what changed and why
- **Test plan** — exact commands run + what they verify
- **Security review** — any new permissions, deny rules, or external surfaces
- **Files (high-level)** — major paths touched

PRs that touch `settings.json` permissions, `_shared/agent-dispatch.md`, or
`install.sh` require an explicit security note. PRs that add a skill must
include a `gen_skills_index.py --write` regeneration in the same commit.

---

## Karpathy 4 principles (apply to every change)

1. **Think before coding** — make assumptions explicit, ask if unclear.
2. **Simplicity first** — minimum code that solves the requested problem.
3. **Surgical changes** — only touch lines traceable to the request.
4. **Goal-driven execution** — define WHAT, let the loop discover HOW.

See [`CLAUDE.md`](CLAUDE.md) for the full ruleset.
