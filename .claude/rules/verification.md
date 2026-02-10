---
description: Verification — no completion claims without fresh evidence, forbidden phrases
alwaysApply: true
---

# Verification Before Completion

## Iron Law: No completion claims without fresh verification evidence

Before claiming ANY work is complete, fixed, or passing:

1. **Identify** — What command proves this claim?
2. **Run** — Execute the FULL command (fresh, complete)
3. **Read** — Full output, check exit code, count failures
4. **Verify** — Does output confirm the claim?
   - No → State actual status with evidence
   - Yes → State claim WITH evidence

Skip any step = false claim.

## Forbidden Phrases (without verification evidence)

- "Should work now"
- "Looks correct"
- "Should be fine"
- "Done"
- Any wording implying success without having run verification

## Verification Independence

| Claim | Required Evidence | Not Sufficient |
|-------|------------------|----------------|
| Tests pass | Test command output: 0 failures | Previous run, "should pass" |
| Build succeeds | Build command: exit 0 | Linter passing |
| Bug fixed | Original symptom test passes | Code changed, assumed fixed |
| Lint clean | Linter output: 0 errors | Partial check |

## Key Principles

- linter pass ≠ build pass ≠ test pass — verify each independently
- Agent/subagent reports success → must verify independently, never trust blindly
- Confidence ≠ evidence, exhaustion ≠ excuse
