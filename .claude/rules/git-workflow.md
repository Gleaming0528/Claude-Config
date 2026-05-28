---
description: Git workflow — commit format, PR process
alwaysApply: true
---

# Git Workflow

## Commit Message Format

```
<type>: <description>
```

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `ci`

署名通过 prepare-commit-msg hook 自动剥离，禁止在 commit message 中写入 Co-Authored-By 行（hook 位于 .git/hooks/ 和 .git/modules/*/hooks/）。

## PR 流程

1. `git diff [base-branch]...HEAD` 查看全量变更
2. 分析完整 commit 历史（不只是最新 commit）
3. 写 PR summary + test plan
4. 新分支用 `-u` flag push

提交门禁、完整操作流程见 skill: `hpc-commit`。
