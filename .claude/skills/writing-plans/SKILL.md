---
name: writing-plans
description: Use when you have a spec or requirements for a multi-step task, before touching code. Trigger words include write plan, implementation plan, break down task, plan feature, task breakdown.
---

# Writing Plans

## Overview

Write comprehensive implementation plans assuming the engineer has zero context and questionable taste. Document everything: which files to touch, code, testing, verification commands. Bite-sized tasks. DRY. YAGNI. TDD. Frequent commits.

## Bite-Sized Task Granularity

**Each step is one action (2-5 minutes):**
- "Write the failing test" - step
- "Run it to make sure it fails" - step
- "Implement the minimal code to make the test pass" - step
- "Run the tests and make sure they pass" - step
- "Commit" - step

## Plan Document Structure

```markdown
# [Feature Name] Implementation Plan

**Goal:** [One sentence describing what this builds]
**Architecture:** [2-3 sentences about approach]
**Tech Stack:** [Key technologies/libraries]

---

### Task N: [Component Name]

**Files:**
- Create: `exact/path/to/file.go`
- Modify: `exact/path/to/existing.go`
- Test: `exact/path/to/file_test.go`

**Step 1: Write the failing test**
[Complete test code]

**Step 2: Run test to verify it fails**
Run: `go test ./path/... -run TestName -v`
Expected: FAIL

**Step 3: Write minimal implementation**
[Complete implementation code]

**Step 4: Run test to verify it passes**
Run: `go test ./path/... -run TestName -v`
Expected: PASS

**Step 5: Commit**
git add ... && git commit -m "feat: add specific feature"
```

## Key Rules

- **Exact file paths always** - no "add a file somewhere"
- **Complete code in plan** - not "add validation" but the actual code
- **Exact commands with expected output** - runnable, verifiable
- **DRY, YAGNI, TDD, frequent commits**

## Execution Handoff

After plan is complete, offer two options:

1. **Subagent-Driven (this session)** - dispatch fresh subagent per task, review between tasks
2. **Batch Execution (manual checkpoints)** - execute 3 tasks at a time, report for review

Ask: "Which approach?"
