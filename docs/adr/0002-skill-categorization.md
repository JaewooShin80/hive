# 0002. Four-category skill taxonomy

Date: 2026-05-05

## Status

Accepted.

## Context

By v2 the harness had grown from 7 → 16 skills. A flat alphabetical list
in `SKILLS.md` made it harder for users (and for Claude itself when picking
which skill to invoke) to understand:

- Which skills are part of the standard project lifecycle vs. occasional tools
- Which skills mutate code vs. observe / advise
- Which skills require prerequisites (e.g. an existing PLAN.md)

A trigger-based recommendation engine was rejected as over-engineering
for 16 entries.

## Decision

Skills are organized into **exactly four categories** in `SKILLS.md`:

1. **🎯 Core workflow** — the standard lifecycle a project moves through
   (`discover` → `plan` → `execute` → `security` → `playwright` → `uat`,
   plus `worklog` for resume).
2. **🔧 Auxiliary tools** — invoked on demand, no required ordering
   (`debug`, `map-codebase`, `worktree`, `codex-review`).
3. **⚙️ Code manipulation** — behavior-preserving or migration changes that
   need extra safety (`refactor`, `migrate`, `rollback`).
4. **🤔 Decision / comparison** — supports judgement calls; produces docs,
   not code (`compare`, `adr`).

The categorization is maintained **by hand** in the categorized tables at
the top of `SKILLS.md`. The auto-generated table at the bottom
(`AUTO-INDEX` markers, populated by `scripts/gen_skills_index.py`) is a
flat alphabetical fallback and does not attempt to infer category.

## Consequences

**Positive:**

- New users skim four short tables instead of one 16-row alphabet.
- Onboarding via `WALKTHROUGH.md` follows the Core category top-to-bottom.
- Adding a skill forces an explicit category choice — surfacing whether
  it is a lifecycle step or an auxiliary tool.
- Auto-index keeps comprehensive coverage without polluting the curated view.

**Negative:**

- Adding / removing a skill requires editing two places: the categorized
  table (manual) and rerunning `gen_skills_index.py --write` (mechanical).
- Some skills could plausibly fit two categories (e.g. `worktree` is
  auxiliary but also affects execution). We pick one and accept blur.

**Mitigation:**

- `CONTRIBUTING.md` documents the two-place edit explicitly.
- CI's `gen_skills_index.py --check` catches a missed regeneration.
- `scripts/skill_lint.py` flags any skill whose stem is not referenced
  *anywhere* in `SKILLS.md` — guarding against an orphan in either view.
