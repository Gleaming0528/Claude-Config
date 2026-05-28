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

基于 [Conventional Commits](https://www.conventionalcommits.org/) + [Chris Beams 七条规则](https://chris.beams.io/posts/git-commit/) 的融合标准。

### 结构

```
<type>[(<scope>)]: <主题行>

<正文（可选）>
```

### 主题行规则

| 规则 | 要求 | 说明 |
|------|------|------|
| 前缀 | `type:` 或 `type(scope):` | Conventional Commits 格式 |
| 长度 | **整行（含 type 前缀）≤ 72 字符** | 超长的 subject 在 `git log --oneline`、GitHub/GitLab 等处会被截断 |
| 语气 | **动词开头**，不加"了" | ✅ `新增`、`修复`、`移除`、`重构` ✗ `新增了`、`修复了`、`关于xx的改动` |
| 标点 | **末尾不加句号** | 节省空间，保持一致 |
| 内容 | 说清"做了什么"，一个 commit 一件事 | 写完后检查：三个月后看 `git log --oneline` 能否理解这条改了什么？ |

### 正文规则

| 规则 | 要求 |
|------|------|
| 与主题行之间 | **空一行** |
| 每行宽度 | **≤ 72 字符** |
| 内容重点 | 解释 **why**（为什么改）和 **what**（改了什么），不解释 how（怎么改的——代码本身说明了 how） |
| 何时需要正文 | 主题行无法完整传达改动意图时；一眼看不出"为什么要这么做"时 |

### Type 分类

| type | 场景 |
|------|------|
| `feat` | 新功能 |
| `fix` | 修复 bug |
| `refactor` | 重构（不改行为） |
| `perf` | 性能优化 |
| `chore` | 杂务（依赖、CI、配置） |
| `docs` | 文档 |
| `test` | 测试 |

### 示例

简单改动——主题行足够说明一切，无需正文：

```
fix: 修复训练日志时区偏移 8 小时
```

需要正文——为什么这么做不显而易见：

```
feat(ui): 去掉 TensorBoard 创建确认弹窗

用户反馈创建 TensorBoard 流程步骤太多。
确认弹窗没有不可逆操作，零确认直接创建即可。
同时在空状态增加日志路径引导，降低新用户困惑。
```

破坏性变更——正文说明影响范围：

```
refactor(api)!: 统一分页参数命名

将 pageNum/pageSize 重命名为 page/per_page，
与平台其他 API 保持一致。

BREAKING CHANGE: 前端需同步更新所有分页请求参数。
```

## 提交检查清单

每次提交前逐项确认：

- [ ] 质量门禁通过（前端：lint + build；Go：`go build ./...`）
- [ ] commit 只包含一个逻辑改动的相关文件
- [ ] 主题行：`<type>: <动词开头描述>`，整行 ≤ 72 字符，末尾无句号
- [ ] 正文（如有）：与主题行空一行，每行 ≤ 72 字符，讲 why 不讲 how
- [ ] `git pull --rebase origin main` 后 push
- [ ] submodule 指针更新（如需要）单独提交
- [ ] **禁止** `--no-verify`——跳过 hook 的 commit 进入 CI 会破坏他人的 main
