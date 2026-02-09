---
name: executing-plans
description: Use when you have a written implementation plan to execute with review checkpoints. Trigger words include execute plan, run plan, implement plan, start building, follow the plan.
---

# Executing Plans

## Overview

Load plan, review critically, execute tasks in batches, report for review between batches.

**Core principle:** Batch execution with checkpoints for architect review.

## The Process

### Step 1: Load and Review Plan

1. Read plan file
2. Review critically - identify questions or concerns
3. If concerns: raise them before starting
4. If clear: create TodoWrite with all tasks and proceed

### Step 2: Execute Batch (default: 3 tasks)

For each task:
1. Mark as in_progress in TodoWrite
2. Follow each step exactly (plan has bite-sized steps)
3. Run verifications as specified
4. Mark as completed

### Step 3: Report

When batch complete:
- Show what was implemented
- Show verification output
- Say: "Ready for feedback."

### Step 4: Continue

Based on feedback:
- Apply changes if needed
- Execute next batch
- Repeat until complete

### Step 5: Final Verification

After all tasks:
- Run full test suite
- Verify no regressions
- Report final status

## When to Stop and Ask

**STOP executing immediately when:**
- Hit a blocker (missing dependency, test fails, unclear instruction)
- Plan has critical gaps
- You don't understand an instruction
- Verification fails repeatedly

**Ask for clarification rather than guessing.**

## Red Flags

**Never:**
- Skip verifications specified in plan
- Guess when blocked (stop and ask)
- Start on main/master without explicit user consent
- Proceed past failing tests without reporting
- Combine or skip plan steps for "efficiency"
