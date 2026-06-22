# Architecture Decision Records (ADRs) — Harness

This directory holds ADRs about the AI-Fab harness *itself* — decisions
that shape how the harness is built, distributed, and tested. They are
distinct from project-level ADRs that the `/aifab:adr` skill creates inside
user projects.

Format follows [Michael Nygard's template](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions):
Status / Context / Decision / Consequences.

## Index

| # | Title | Status |
|---|---|---|
| [0001](0001-stdlib-only-policy.md) | Stdlib-only policy for harness scripts and tests | Accepted |
| [0002](0002-skill-categorization.md) | Four-category skill taxonomy | Accepted |
| [0003](0003-karpathy-hook-enforcement.md) | Karpathy 4 principles enforced by Claude Code hooks | Proposed |

## Adding an ADR

1. Allocate the next four-digit number.
2. File name: `NNNN-kebab-case-title.md`.
3. Required sections: `## Status`, `## Context`, `## Decision`, `## Consequences`.
4. Append a row to the index table above.
5. Run `python3 -m unittest scripts.tests.test_adr` to verify structure.

When an ADR supersedes another, set the older one's `## Status` to
`Superseded by [NNNN](NNNN-...md)` and link back from the new ADR.
