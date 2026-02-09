---
name: using-git-worktrees
description: Use when starting feature work that needs isolation from current workspace. Trigger words include worktree, isolated workspace, parallel branch, feature branch setup, isolated development.
---

# Using Git Worktrees

## Overview

Git worktrees create isolated workspaces sharing the same repository, allowing work on multiple branches simultaneously without switching.

**Core principle:** Systematic directory selection + safety verification = reliable isolation.

## Directory Selection (Priority Order)

1. **Check existing:** `.worktrees/` or `worktrees/` directory
2. **Check CLAUDE.md** for worktree preferences
3. **Ask user** if nothing found

## Creation Steps

### 1. Detect Project

```bash
project=$(basename "$(git rev-parse --show-toplevel)")
```

### 2. Verify Directory is Git-Ignored

```bash
git check-ignore -q .worktrees 2>/dev/null
```

If NOT ignored → add to `.gitignore` and commit before proceeding.

### 3. Create Worktree

```bash
git worktree add .worktrees/$BRANCH_NAME -b $BRANCH_NAME
cd .worktrees/$BRANCH_NAME
```

### 4. Run Project Setup

Auto-detect and run:

```bash
# Go
[ -f go.mod ] && go mod download

# Node.js
[ -f package.json ] && npm install

# Python
[ -f requirements.txt ] && pip install -r requirements.txt
[ -f pyproject.toml ] && poetry install
```

### 5. Verify Clean Baseline

Run tests to ensure worktree starts clean:

```bash
# Use project-appropriate command
go test ./...
npm test
pytest
```

**If tests fail:** Report failures, ask whether to proceed.
**If tests pass:** Report ready.

### 6. Report

```
Worktree ready at <path>
Tests passing (N tests, 0 failures)
Ready to implement <feature>
```

## Cleanup

When work is done:

```bash
cd <original-project>
git worktree remove .worktrees/$BRANCH_NAME
```

## Red Flags

**Never:**
- Create worktree without verifying it's git-ignored (for project-local dirs)
- Skip baseline test verification
- Proceed with failing tests without asking
- Assume directory location when ambiguous
