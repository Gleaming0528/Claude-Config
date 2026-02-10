---
description: TDD constraints — red-green-refactor, no production code without failing test
alwaysApply: true
---

# TDD Constraints

## Iron Law: No production code without a failing test first

## Core Rules

- Write test first, watch it fail, then write minimal code to pass
- Wrote code before test? Delete the code, start over from test
- Each test covers one behavior, name must describe intent clearly
- After test passes, write only the minimal implementation (YAGNI)
- Bug fixes must start with a reproduction test, then fix the code

## Red-Green-Refactor Cycle

1. **RED** — Write one failing test, run it, confirm it fails for the right reason
2. **GREEN** — Write the least code to make the test pass
3. **REFACTOR** — Clean up while keeping tests green

## Common Excuses vs Reality

| Excuse | Reality |
|--------|---------|
| "Too simple to test" | Simple code breaks too. Test takes 30 seconds. |
| "I'll test after" | Tests-after pass immediately, proving nothing. |
| "Already manually tested" | Ad-hoc ≠ systematic. No record, can't re-run. |
| "TDD is too slow" | TDD is faster than debugging. Pragmatic = test-first. |
| "Need to explore first" | Fine. Throw away exploration, start fresh with TDD. |

## Exceptions (require explicit user consent)

- Throwaway prototypes
- Generated code
- Configuration files
