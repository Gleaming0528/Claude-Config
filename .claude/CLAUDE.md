# .claude/ Configuration

AI agent, skill, rule, and command configurations for the HPC platform.

## Directory Structure

```
.claude/
├── agents/                        # Subagents — invoke via /agent-name in Cursor
│   ├── code-reviewer.md           # Unified Go + Frontend reviewer (auto-routes by file type)
│   ├── go-reviewer.md             # Go-only reviewer (Gin, K8s, concurrency, error handling)
│   ├── frontend-reviewer.md       # Frontend-only reviewer (React, TS, Zustand, auth, a11y)
│   ├── code-simplifier.md         # Code simplification (Go + TS/React aware)
│   └── planner.md                 # Implementation planning for complex features
│
├── skills/                        # Domain knowledge (auto-loaded, triggered by keywords)
│   ├── brainstorming/             # Requirements clarification and design discussion
│   ├── executing-plans/           # Plan execution with review checkpoints
│   ├── frontend-design/           # Frontend UI/UX patterns
│   ├── golang-patterns/           # Idiomatic Go: error handling, concurrency, interfaces, Gin
│   ├── golang-testing/            # Go testing: table-driven, benchmarks, fuzz, mocks
│   ├── hpc-k8s-deploy/            # K8s deployment, Kustomize, CRDs
│   ├── subagent-driven-development/ # Multi-agent task dispatch with two-stage review
│   ├── systematic-debugging/      # Bug investigation methodology (4 phases)
│   ├── using-git-worktrees/       # Isolated feature development
│   └── writing-plans/             # Implementation plan authoring
│
├── rules/                         # Reference guidelines (NOT auto-loaded by Cursor)
│   ├── coding-style.md            # General style (immutability, file organization)
│   ├── git-workflow.md            # Commit format, PR process
│   ├── go-coding-style.md         # Go: gofmt, naming, Gin conventions
│   ├── go-security.md             # Go: secrets, input validation, race detection
│   ├── go-testing.md              # Go: TDD, table-driven, coverage targets
│   ├── security.md                # General security checklist
│   ├── tdd.md                     # TDD methodology (RED-GREEN-REFACTOR)
│   └── verification.md            # Verification before completion claims
│
├── commands/                      # Workflow instructions (readable by AI on request)
│   ├── build-fix.md               # Incremental build error resolution
│   ├── code-review.md             # Code review workflow
│   ├── commit.md                  # Commit workflow
│   ├── plan.md                    # Planning workflow
│   ├── sync-config.md             # Sync .claude/ to GitHub backup repo
│   └── sync-repos.md              # Sync all GitLab repos to local
│
└── CLAUDE.md                      # This file
```

## Agents — invoke via `/agent-name`

| Agent | Invoke | Scope |
|-------|--------|-------|
| `code-reviewer` | `/code-reviewer` | Auto-routes Go vs Frontend by file type |
| `go-reviewer` | `/go-reviewer` | Go only: security, concurrency, Gin, K8s, error handling |
| `frontend-reviewer` | `/frontend-reviewer` | Frontend only: React, TS, Zustand, auth, a11y |
| `code-simplifier` | `/code-simplifier` | Simplification — Go + TS/React aware |
| `planner` | `/planner` | Requirements → architecture → step breakdown |

## What Cursor Auto-Loads

| Source | Auto-loaded | How to use |
|--------|:-----------:|------------|
| `agents/*.md` | Yes | Invoke via `/agent-name` |
| `skills/*/SKILL.md` | Yes | Auto-triggered by keywords |
| `rules/*.md` | No | AI reads on request; consider migrating to root CLAUDE.md |
| `commands/*.md` | No | AI reads on request (e.g. "sync repos") |
| Root `CLAUDE.md` | Yes | Always-applied workspace rule |
