---
name: requesting-code-review
description: Dispatches code review subagent to evaluate work quality. Use when completing tasks, implementing major features, or before merging to verify work meets requirements.
---

# Requesting Code Review

Dispatch superpowers:code-reviewer subagent to catch issues before they cascade. The reviewer gets precisely crafted context for evaluation — never your session's history. This keeps the reviewer focused on the work product, not your thought process, and preserves your own context for continued work.

**Core principle:** Review early, review often.

## When to Request Review

**Mandatory:**
- After each task in subagent-driven development
- After completing major feature
- Before merge to main

**Optional but valuable:**
- When stuck (fresh perspective)
- Before refactoring (baseline check)
- After fixing complex bug

## How to Request

**1. Get git SHAs:**
```bash
BASE_SHA=$(git rev-parse HEAD~1)  # or origin/main
HEAD_SHA=$(git rev-parse HEAD)
```

**2. Dispatch code-reviewer subagent:**

Use Task tool with superpowers:code-reviewer type, fill template at `code-reviewer.md`

**Placeholders:**
- `{WHAT_WAS_IMPLEMENTED}` - What you just built
- `{PLAN_OR_REQUIREMENTS}` - What it should do
- `{BASE_SHA}` - Starting commit
- `{HEAD_SHA}` - Ending commit
- `{DESCRIPTION}` - Brief summary

**3. Act on feedback:**
- Fix Critical issues immediately
- Fix Important issues before proceeding
- Note Minor issues for later
- Push back if reviewer is wrong (with reasoning)

## Example

```
[Just completed Task 2: Add verification function]

You: Let me request code review before proceeding.

BASE_SHA=$(git log --oneline | grep "Task 1" | head -1 | awk '{print $1}')
HEAD_SHA=$(git rev-parse HEAD)

[Dispatch superpowers:code-reviewer subagent]
  WHAT_WAS_IMPLEMENTED: Verification and repair functions for conversation index
  PLAN_OR_REQUIREMENTS: Task 2 from docs/superpowers/plans/deployment-plan.md
  BASE_SHA: a7981ec
  HEAD_SHA: 3df7661
  DESCRIPTION: Added verifyIndex() and repairIndex() with 4 issue types

[Subagent returns]:
  Strengths: Clean architecture, real tests
  Issues:
    Important: Missing progress indicators
    Minor: Magic number (100) for reporting interval
  Assessment: Ready to proceed

You: [Fix progress indicators]
[Continue to Task 3]
```

## Integration with Workflows

**Subagent-Driven Development:**
- Review after EACH task
- Catch issues before they compound
- Fix before moving to next task

**Executing Plans:**
- Review after each batch (3 tasks)
- Get feedback, apply, continue

**Ad-Hoc Development:**
- Review before merge
- Review when stuck

## 反合理化

| 借口 | 现实 |
|------|------|
| "改动很小，不需要 review" | 小改动也能引入大 bug。一行 off-by-one 就能搞挂生产。review 成本和改动大小不成正比。 |
| "时间紧，先合再说" | 没 review 的代码上线出事，修复成本是 review 成本的 10-100 倍。越紧急越需要 review。 |
| "是我自己写的，我知道没问题" | 作者对自己的假设是盲区。你测试了 happy path，reviewer 会发现你忘了 error path。 |
| "AI 写的代码应该没问题" | AI 代码自信且合理，即使在错误时也是。AI 代码需要**更多**审查，而非更少。 |
| "reviewer 说的我不同意，算了" | 如果有技术依据就 push back，没有就照做。"算了"不是解决分歧的方式。 |
| "测试都过了，review 是形式" | 测试不能覆盖架构问题、安全漏洞、可读性缺陷。测试是必要条件，不是充分条件。 |

## Red Flags

- 代码直接 push 到 main 没有经过任何 review
- review 只看"测试过了"就批准（忽略其他维度）
- Critical 级别的问题被标记为 "之后修"
- 安全相关改动没有安全视角的 review
- 超过 300 行的改动没有要求拆分
- Bug 修复的 PR 没有附带回归测试
- Review 反馈无严重性标签——作者无法区分哪些必须修、哪些可选
- "LGTM" 但没有任何具体评论证明确实看了代码

## 验证清单

Review 完成后确认：

- [ ] 所有 Critical 问题已修复
- [ ] 所有 Important 问题已修复或有明确的延期理由
- [ ] 测试通过：`go test ./...` 或前端 `npm run build`
- [ ] 构建成功
- [ ] Reviewer 的反馈已逐条回应（修复 / push back / 承认延期）
- [ ] 改动有充分的验证记录（改了什么、怎么验证的）

See template at: requesting-code-review/code-reviewer.md
