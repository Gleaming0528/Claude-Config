---
name: systematic-debugging
description: Use when encountering any bug, test failure, or unexpected behavior, before proposing fixes. Trigger words include debug, fix bug, error, crash, test failure, unexpected behavior, troubleshoot.
---

# Systematic Debugging

## Overview

Random fixes waste time and create new bugs. Quick patches mask underlying issues.

**Core principle:** ALWAYS find root cause before attempting fixes. Symptom fixes are failure.

## Iron Law

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

## The Four Phases

Must complete each phase before proceeding to the next.

### Phase 1: Root Cause Investigation

Before attempting ANY fix:

1. **Read error messages carefully**
   - Don't skip past errors or warnings
   - Read stack traces completely
   - Note line numbers, file paths, error codes

2. **Reproduce consistently**
   - Can you trigger it reliably?
   - What are the exact steps?
   - If not reproducible → gather more data, don't guess

3. **Check recent changes**
   - What changed that could cause this?
   - git diff, recent commits
   - New dependencies, config changes, environment differences

4. **Multi-component diagnostics**

   When system has multiple components (API → Service → DB):

   ```
   For EACH component boundary:
   - Log what data enters component
   - Log what data exits component
   - Verify environment/config propagation
   - Check state at each layer

   Run once to gather evidence → identify failing component → investigate
   ```

5. **Trace data flow**
   - Where does the bad value originate?
   - What called this with the bad value?
   - Keep tracing up until you find the source
   - Fix at source, not at symptom

### Phase 2: Pattern Analysis

1. **Find working examples** — similar working code in same codebase
2. **Compare against references** — read reference implementation completely, don't skim
3. **Identify differences** — list every difference, however small
4. **Understand dependencies** — components, config, environment, assumptions

### Phase 3: Hypothesis and Testing

1. **Form single hypothesis** — "I think X is root cause because Y"
2. **Test minimally** — smallest possible change, one variable at a time
3. **Verify before continuing** — worked → Phase 4; didn't work → new hypothesis, don't stack fixes
4. **When you don't know** — say "I don't understand X", don't pretend

### Phase 4: Implementation

1. **Create failing test case** — simplest reproduction, must have before fixing
2. **Implement single fix** — address confirmed root cause, one change, no "while I'm here" improvements
3. **Verify fix** — test passes? other tests still pass? issue actually resolved?

### The 3-Fix Rule

If 3 consecutive fix attempts have failed:

**STOP. The problem is architectural, not code-level.**

Symptoms:
- Each fix reveals new coupling/shared state issues
- Fixes require "massive refactoring" to implement
- Each fix creates new symptoms elsewhere

**Discuss architecture with user before attempting fix #4.**

## Red Flags — Stop Immediately

If you catch yourself thinking:
- "Quick fix for now, investigate later"
- "Just try changing X and see"
- "Add multiple changes, run tests"
- "Skip the test, manually verify"
- "It's probably X, let me fix that"
- "I don't fully understand but this might work"

**ALL mean: STOP. Return to Phase 1.**

## Quick Reference

| Phase | Core Actions | Pass Criteria |
|-------|-------------|---------------|
| 1. Root Cause | Read errors, reproduce, check changes, add diagnostics | Understand WHAT and WHY |
| 2. Pattern | Find working examples, compare differences | Identify key differences |
| 3. Hypothesis | Form theory, test minimally | Confirmed or new hypothesis |
| 4. Implementation | Write test, fix, verify | Bug resolved, all tests pass |
