---
name: brainstorming
description: Use when needing to clarify requirements and design approaches before writing code. Trigger words include new feature, requirements, design discussion, solution design, feature planning, how to implement, tech decision.
---

# Brainstorming Ideas Into Designs

## Overview

Turn ideas into fully formed designs through collaborative dialogue before writing any code.

**Core principle:** One question at a time, incrementally converge on a clear design.

## The Process

### Understanding the Idea

1. Check current project state (files, docs, recent commits)
2. Ask questions **one at a time** to refine the idea
3. Prefer multiple choice questions (easier to answer than open-ended)
4. Focus on: purpose, constraints, success criteria

### Exploring Approaches

1. Propose 2-3 different approaches with trade-offs
2. Lead with recommended option and explain why
3. Apply YAGNI ruthlessly — remove unnecessary features from all designs

### Presenting the Design

1. Once you understand what to build, present the design
2. Break into sections of 200-300 words
3. After each section: "Does this look right so far?"
4. Cover: architecture, components, data flow, error handling, testing
5. Go back and clarify if something doesn't make sense

## Key Principles

| Principle | Description |
|-----------|-------------|
| One question at a time | Don't overwhelm with multiple questions |
| Multiple choice preferred | Easier to answer, faster convergence |
| YAGNI | Only design features that are certainly needed |
| Explore alternatives | Always propose 2+ approaches before deciding |
| Incremental validation | Present design in sections, validate each |
| Flexible backtracking | Go back and clarify when something is off |

## After Design is Confirmed

1. Ask: "Design confirmed. Ready to start implementation?"
2. If yes → use planner agent to create detailed implementation plan
3. Record design decisions in relevant module docs or comments
