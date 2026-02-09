---
name: subagent-driven-development
description: Use when executing implementation plans with independent tasks. Trigger words include execute plan, run tasks, implement feature, subagent, dispatch tasks. Dispatches fresh subagent per task with two-stage review.
---

# Subagent-Driven Development

Execute plan by dispatching fresh subagent per task, with two-stage review after each: spec compliance review first, then code quality review.

**Core principle:** Fresh subagent per task + two-stage review (spec then quality) = high quality, fast iteration

## When to Use

- Have an implementation plan with mostly independent tasks
- Want to stay in the current session (no context switch)
- Want automatic review checkpoints between tasks

## The Process

1. **Read plan once**, extract all tasks with full text and context
2. **Create TodoWrite** with all tasks

### Per Task:

3. **Dispatch implementer subagent** with full task text + context
   - If subagent asks questions → answer before proceeding
   - Subagent implements, tests, commits, self-reviews

4. **Dispatch spec reviewer subagent**
   - Verifies code matches spec (nothing more, nothing less)
   - If issues found → implementer fixes → re-review
   - Must pass before proceeding

5. **Dispatch code quality reviewer subagent**
   - Reviews code quality, testing, maintainability
   - If issues found → implementer fixes → re-review
   - Must pass before proceeding

6. **Mark task complete**, move to next task

### After All Tasks:

7. **Dispatch final code reviewer** for entire implementation
8. **Verify all tests pass**

## Implementer Subagent Prompt Template

```
Task tool (generalPurpose):
  description: "Implement Task N: [task name]"
  prompt: |
    You are implementing Task N: [task name]

    ## Task Description
    [FULL TEXT of task - paste it, don't make subagent read file]

    ## Context
    [Where this fits, dependencies, architectural context]

    ## Before You Begin
    If you have questions about requirements, approach, or dependencies - ask now.

    ## Your Job
    1. Implement exactly what the task specifies
    2. Write tests (TDD if specified)
    3. Verify implementation works
    4. Commit your work
    5. Self-review: completeness, quality, YAGNI, testing
    6. Report: what you did, test results, files changed, concerns
```

## Spec Reviewer Prompt Template

```
Task tool (code-reviewer):
  description: "Review spec compliance for Task N"
  prompt: |
    You are reviewing whether implementation matches specification.

    ## What Was Requested
    [FULL TEXT of task requirements]

    ## What Implementer Claims
    [From implementer's report]

    ## CRITICAL: Do Not Trust the Report
    Verify everything independently by reading actual code.

    Check for:
    - Missing requirements (skipped or claimed but not done)
    - Extra/unneeded work (over-engineering, unrequested features)
    - Misunderstandings (wrong interpretation of requirements)

    Report: ✅ Spec compliant OR ❌ Issues found [with file:line references]
```

## Code Quality Reviewer

After spec compliance passes, dispatch the existing `code-reviewer` agent to review code quality, testing, and maintainability.

## Red Flags

**Never:**
- Skip reviews (spec compliance OR code quality)
- Proceed with unfixed issues
- Dispatch multiple implementers in parallel (conflicts)
- Make subagent read plan file (provide full text instead)
- Start code quality review before spec compliance passes
- Move to next task while either review has open issues
- Accept "close enough" on spec compliance

**If reviewer finds issues:**
- Implementer fixes them → reviewer reviews again → repeat until approved

**If subagent fails task:**
- Dispatch fix subagent with specific instructions
- Don't fix manually (context pollution)
