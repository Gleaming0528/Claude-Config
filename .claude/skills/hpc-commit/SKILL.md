---
name: hpc-commit
description: 引导 HPC 平台子项目的代码提交流程与质量门禁。适用于提交代码、push、rebase、合并代码。
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

## 反合理化

| 借口 | 现实 |
|------|------|
| "改动很小，不用跑 build" | 一行 import 改错就能让整个项目编译失败。门禁不论改动大小。 |
| "先 `--no-verify` 提上去，之后再修" | 跳过 hook 的 commit 会进入 CI，破坏他人的 main 分支。从来没有"之后"。 |
| "这个 lint 警告不重要" | 警告累积 = 噪声淹没真正的错误。现在修 1 个 vs 以后修 50 个。 |
| "commit message 随便写就行" | 三个月后 `git log` 全是 "fix" "update"，谁也看不懂历史。message 是给未来的自己看的。 |
| "我先 push，rebase 太麻烦了" | merge commit 污染历史，冲突只会越拖越大。rebase 是当下最便宜的操作。 |
| "这个文件不是我改的，一起提了吧" | 不相关的文件混入 commit，review 时干扰、revert 时灾难。一个 commit 只做一件事。 |

## Red Flags

- `git commit --no-verify` 出现在命令历史中
- 单个 commit 混入多个不相关子项目的改动
- commit message 是 "fix"、"update"、"wip" 等无意义描述
- push 前没有 `git pull --rebase`
- Go 项目提交前没跑 `go build ./...`
- 修改了文件但 commit message 没反映实际改动内容
- submodule 指针更新和子项目代码改动混在同一个 commit

## 提交验证清单

每次提交前确认：

- [ ] 质量门禁通过（前端：lint + build；Go：`go build ./...`）
- [ ] commit 只包含一个逻辑改动的相关文件
- [ ] commit message 符合 `<type>: <描述>` 格式，描述准确反映改动
- [ ] `git pull --rebase origin main` 成功，无冲突
- [ ] push 后确认远程分支状态正确
- [ ] submodule 指针更新（如需要）单独提交
