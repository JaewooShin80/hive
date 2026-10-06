## Summary

<!-- 1-3 bullets: what changed and why. Focus on intent, not implementation. -->

-
-

## Test plan

<!-- Exact commands run + what they verify. -->

- [ ] `python3 scripts/skill_lint.py .claude/plugins/hive` → 0 errors
- [ ] `python3 scripts/gen_skills_index.py --check .claude/plugins/hive/SKILLS.md` → exit 0
- [ ] `python3 -m unittest discover -s scripts/tests` → all green
- [ ] CI matrix (Python 3.9 / 3.11 / 3.13)

## Security review

<!-- If this PR touches settings.json permissions, _shared/agent-dispatch.md,
     install.sh, or shells out to user input, describe the surface here.
     Otherwise write "N/A". -->

## Files (high-level)

<!-- Group by major path. -->

```
```

## Karpathy 4 principles

- [ ] Think before coding — assumptions explicit
- [ ] Simplicity first — minimal change
- [ ] Surgical — every changed line traces to this PR's intent
- [ ] Goal-driven — verified outcome, not just "tests pass"
