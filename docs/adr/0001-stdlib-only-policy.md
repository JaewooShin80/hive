# 0001. Stdlib-only policy for harness scripts and tests

Date: 2026-05-05

## Status

Accepted.

## Context

The HIVE harness is intended to be **dropped into any user's project**
via `install.sh`. Every additional dependency the harness requires becomes
either:

- a setup step the user must run before using the harness, or
- a pinned version that may conflict with the user's own project deps.

Initial v1.x scripts already used Python 3 stdlib only (`scripts/hive-status.py`).
When P0 added a self-test layer, we faced a choice: adopt `pytest` for
ergonomic fixtures and parametrization, or stay on `unittest`.

`pytest` would have offered:

- Cleaner fixtures and parametrize decorators.
- Richer failure output.

But it would have introduced:

- A `requirements.txt` / `pyproject.toml` we did not have before.
- An expectation that `pip install` runs cleanly in any user environment.
- Version pinning surface (`pytest>=8`, plugin compatibility).

## Decision

All harness scripts and tests use **Python 3 standard library only**.
No `pytest`, no `pyyaml`, no third-party dependencies. Tests are written
with `unittest`. Frontmatter parsing is hand-rolled (~30 LoC) instead of
pulling `pyyaml` for the trivial subset of YAML we need.

This applies to:

- `scripts/*.py` (status bar, lint, generators)
- `scripts/tests/*.py` (all test modules)
- The `.github/workflows/ci.yml` matrix runs without any `pip install` step

User projects built *with* the harness are free to use any deps they want;
this policy applies only to the harness internals.

## Consequences

**Positive:**

- `git clone` + `python3 --version` is the entire dev setup.
- CI runs in seconds with no install step.
- Harness can be dropped into hostile environments (corporate networks
  without PyPI access, locked-down build agents).
- One less version pin to maintain.

**Negative:**

- Slightly more code per test (no parametrize sugar; we use `subTest()`).
- Hand-rolled YAML parser supports only a single-line `key: value` subset —
  if a skill ever needs nested YAML, we either expand the parser or revisit
  this decision.

**Mitigation:**

- The single-line frontmatter subset is documented in `scripts/skill_lint.py`.
- If a future skill genuinely requires structured frontmatter, that skill's
  ADR should propose superseding this one.
