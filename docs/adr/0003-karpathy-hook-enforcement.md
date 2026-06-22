# 0003. Karpathy 4 principles enforced by Claude Code hooks

Date: 2026-06-20

## Status

Proposed. Targets v3.0.

## Context

The harness centers on four principles defined in `CLAUDE.md` (Karpathy 4):

1. **Think Before Coding** — declare assumptions, ask when unclear.
2. **Simplicity First** — minimum code, no speculative abstraction.
3. **Surgical Changes** — touch only what the request demands.
4. **Goal-Driven Execution** — define WHAT, not HOW.

Today these principles live entirely in prompt context — every skill repeats
them in its body, and `CLAUDE.md` re-states them at session start. This makes
them *cultural* but not *structural*: the agent can drift away from them
mid-Wave, and there is no out-of-band check that catches the drift.

Two adjacent harnesses define the comparison surface:

- **Superpowers** (93k★ as of 2026-03) makes TDD structural by declaring a
  `test-driven-development` skill that *must* be invoked before any
  implementation. Discipline is enforced by a skill the agent has to call.
- **GSD** makes phase progression structural by gating advancement on
  artifact existence (`PHASE.md`, `PLAN.md`, `RESEARCH.md`). Discipline is
  enforced by file presence checks.

Neither targets *principles* directly. Both target *workflows*. AI-Fab's
Karpathy 4 sit at a different level: they constrain how *each individual
edit* should look, regardless of which workflow is running. A workflow-level
gate cannot catch a Wave that drifts into adding speculative abstractions on
edit #47 of 60.

Claude Code v2.1+ ships a hook system with PreToolUse / PostToolUse /
UserPromptSubmit / SessionStart / Stop events, JSON stdin payloads, and the
ability to block tool execution via exit code 2 or `additionalContext`
injection. This is the missing enforcement substrate.

Considered alternatives:

- **Status quo (prompt-only)**: cheap but produces the observed drift.
- **Skill-level enforcement** (Superpowers-style): forces the agent to call a
  `/aifab:karpathy-check` skill before edits. Reliable but adds friction to
  every operation and clutters the skill list. The principles apply
  continuously, not at discrete checkpoints.
- **Hook-level enforcement**: the harness watches tool calls and intervenes
  when a principle is being violated, without the agent needing to call
  anything. Friction is paid only when a violation actually fires.

## Decision

v3.0 introduces a **Karpathy enforcement layer** — a set of Claude Code
hooks bundled with the harness that map each principle to a tool event:

| Principle | Hook event | Behavior |
|---|---|---|
| 1. Think Before Coding | `UserPromptSubmit` | Heuristically detect ambiguous requests (multi-clause, missing acceptance criteria, "make it better"–class phrasing); inject `additionalContext` recommending `/aifab:grill` before implementation. Does not block. |
| 2. Simplicity First | `PostToolUse` (Write\|Edit) | Detect introductions of new abstraction surfaces (new `interface`, `abstract class`, generic factory, config-driven dispatcher) inside Wave scope; inject a justification request the agent must address in the next turn. Does not block. |
| 3. Surgical Changes | `PreToolUse` (Write\|Edit) | Compare the target path against the active Wave's declared file scope in `PLAN.md`. Out-of-scope paths exit code 2 (block) with a message pointing to `/aifab:plan` for scope amendment. Bypassable via an explicit `--scope-override` annotation in the Wave header. |
| 4. Goal-Driven | `SessionStart` | Parse the current `PLAN.md` and compute a HOW/WHAT ratio (imperative steps vs. success criteria). If HOW > 3× WHAT, inject a warning recommending a goal-mode rewrite. Does not block. |

Design constraints:

- **Stdlib only** — hooks are Python 3 scripts in `scripts/hooks/`, consistent
  with ADR-0001.
- **Fail-open** — any hook error exits 0 and logs to `~/.claude/logs/aifab-hooks.log`.
  A broken hook must never prevent the user from working.
- **Opt-in per principle** — each hook is independently enabled via
  `settings.json` flags (`aifab.enforce.think`, `.simplicity`, `.surgical`,
  `.goal`). Default in v3.0: surgical = on (only blocking one), others = warn.
- **Test coverage required** — each enforcement hook ships with `unittest`
  cases covering at least: positive trigger, negative (clean) case, error
  fallthrough. Added to CI matrix.
- **Cooperates with existing hooks** — does not replace the PostToolUse
  git-commit → `/aifab:security` notifier, runs alongside it.

This is a *targeted* enforcement layer, not a general policy engine. It does
not attempt to enforce arbitrary user rules. Each hook has one specific
heuristic mapped to one specific principle.

## Consequences

**Positive:**

- Principles move from *cultural* (re-stated every prompt) to *structural*
  (checked at the event boundary). Drift mid-Wave becomes visible.
- Stakes out a clear positioning: Superpowers enforces TDD, GSD enforces
  phase progression, AI-Fab enforces *principles*. No overlap.
- Surgical-changes block hook in particular protects against the most common
  failure mode observed in agent-driven refactors (silent scope creep).
- Per-principle toggles let teams adopt incrementally — start with surgical,
  add others as comfort grows.

**Negative:**

- Heuristics will have false positives. The Simplicity hook in particular —
  detecting "speculative" abstraction by static syntax is imperfect.
- A blocking hook (Surgical) raises the stakes of bugs in the harness itself.
  A broken scope parser could lock the user out of legitimate edits.
- The "Wave scope" concept must be machine-readable in `PLAN.md`. This
  pre-supposes the YAML-frontmatter `WORKLOG.md` / `PLAN.md` change tracked
  separately for v3.0 — a dependency this ADR makes explicit.
- Total surface area grows: 4 new hooks, 4 new configuration flags, 4 new
  test modules.

**Mitigation:**

- Surgical hook ships with the `--scope-override` escape hatch and
  off-by-default until at least one minor release of telemetry feedback.
- Heuristic false positives are logged with the input that triggered them,
  so the patterns can be tuned from real usage rather than guessed.
- Each hook is independent — disabling one does not affect the others, so
  partial rollback is trivial.
- Dependency on machine-readable `PLAN.md` is called out as a v3.0 blocker
  and gates the Surgical hook specifically; the other three can ship first.

## Open questions

- Should the Simplicity hook also catch *new file creation* under certain
  directories (e.g. `utils/`, `lib/`, `helpers/`) as a stronger signal than
  abstraction-syntax detection?
- How does this interact with `/aifab:refactor`, whose entire purpose is to
  introduce structure? Likely: refactor sets a session flag that suspends
  the Simplicity hook for its duration. Needs a separate decision.
- Telemetry: do we log enforcement triggers to `scripts/metric_log.py`'s
  JSONL stream so the heuristics can be measured? Probably yes, opt-in
  under the existing `AIFAB_METRICS=1` flag.

## Relationships

- Depends on a future ADR formalizing the machine-readable `PLAN.md` / `WORKLOG.md`
  schema (YAML frontmatter) — required by the Surgical hook.
- Does not supersede [0001](0001-stdlib-only-policy.md) or
  [0002](0002-skill-categorization.md). Adds a new structural layer above
  the skill taxonomy without changing it.
