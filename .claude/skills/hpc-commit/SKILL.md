---
name: hpc-commit
description: Use when committing code changes in HPC platform submodules. Trigger words include commit, 提交, 提交代码, git commit, push, 推送, rebase, 合并代码.
---

# HPC 平台代码提交流程

## 概述

HPC workspace 由 26 个 git submodule 组成，每个子项目独立提交。提交前必须通过该项目的质量门禁。

## 提交流程

```
1. cd 到子项目目录
2. 通过质量门禁检查
3. git add + commit（conventional commits 格式）
4. rebase main 并 push
5. （可选）回 workspace 根目录更新 submodule 指针
```

## 质量门禁

### 前端项目（hpc-ui）

hpc-ui 有 husky pre-commit hook，会依次执行：

| 步骤 | 命令 | 失败后果 |
|------|------|---------|
| lint-staged | `npx lint-staged`（eslint --fix + prettier） | commit 被拦截 |
| 全量 lint | `npm run lint` | commit 被拦截 |
| 构建检查 | `npm run build` | commit 被拦截 |

**提交前手动验证（推荐先跑一遍，避免 hook 半途失败）：**

```bash
cd hpc-ui
npx tsc --noEmit --skipLibCheck && npx vite build
```

**hook 失败处理：** 修复 lint/build 错误后重新 `git commit`，不要 `--no-verify`。

### Go 项目

Go 项目无 pre-commit hook，需手动验证：

```bash
cd hpc-studio-api  # 或其他 Go 子项目
go build ./...
# 有 golangci-lint 时：
golangci-lint run
```

## Commit Message 格式

```
<type>: <中文描述>

<可选正文>
```

| type | 场景 |
|------|------|
| `feat` | 新功能 |
| `fix` | 修复 bug |
| `refactor` | 重构（不改行为） |
| `perf` | 性能优化 |
| `chore` | 杂务（依赖、CI、配置） |
| `docs` | 文档 |
| `test` | 测试 |

**示例：**

```
feat(ui): TensorBoard 一键创建优化

- 去掉确认弹窗，零确认直接创建
- 空状态增加日志路径引导
```

## 完整操作示例

### 前端子项目提交

```bash
cd hpc-ui
git add -A
git commit -m "feat: 新增训练可视化卡片"
# hook 自动执行 lint + build，通过后 commit 成功
git pull --rebase origin main
git push
```

### Go 子项目提交

```bash
cd hpc-studio-api
go build ./...
git add -A
git commit -m "fix: TensorBoard patch 接口参数校验"
git pull --rebase origin main
git push
```

### 回 workspace 更新 submodule 指针

```bash
cd <repo-root>
git add hpc-ui hpc-studio-api
git commit -m "chore: 更新 hpc-ui、hpc-studio-api submodule 指针"
git push
```

## 常见问题

| 问题 | 解决 |
|------|------|
| pre-commit hook lint 失败 | 修复 eslint 报错，重新 commit |
| pre-commit hook build 失败 | 修复 TypeScript 类型错误，重新 commit |
| rebase 冲突 | 解决冲突 → `git add` → `git rebase --continue` |
| 忘了先 pull 导致 push 被拒 | `git pull --rebase origin main && git push` |
