---
name: doc-gardening
description: 文档自动园丁。代码变更后自动同步文档引用，也可全量扫描仓库文档新鲜度。触发词包括 refactor, 重构, 重命名, rename, move, 移动文件, 删除文件, 目录调整, 更新文档, sync docs, 文档同步, doc update, 文档过时, stale docs, 架构变更, doc freshness, 文档检查, 全量扫描文档。
---

# Doc Gardening — 文档自动园丁

代码变了，文档没跟上 = 系统失忆。

两种工作模式：
- **增量模式**：代码变更后自动同步受影响的文档（默认）
- **全量模式**：用户明确要求时，扫描全仓库文档新鲜度

## 增量模式（自动触发）

以下操作完成后自动执行，无需用户指示：
- 文件重命名/移动/删除
- 函数/类型重命名
- 目录结构调整（新增/删除/合并 package）

### 流程

**1. 识别变更**

```bash
git diff --name-status HEAD
```

构建映射表（关注 R/D/A 状态）：

| 变更类型 | 旧路径/名称 | 新路径/名称 |
|----------|-------------|-------------|
| rename | `internal/old/handler.go` | `internal/new/handler.go` |
| delete | `internal/deprecated/client.go` | — |

**2. 定向扫描文档**

必扫：`CLAUDE.md`、`ARCHITECTURE.md`、`.claude/CLAUDE.md`
按范围扩展：变更在哪个子项目 → 该项目 `README.md`；涉及架构层 → `docs/**/*.md`

搜索模式：反引号路径、Markdown 链接、目录树（`├──`）、import 路径、符号名引用。

**3. 分级修复**

| 级别 | 场景 | 动作 |
|------|------|------|
| 自动 | 路径 rename、链接目标、import 路径、目录树 | 直接替换，不问 |
| 半自动 | 函数/类型名引用、描述中嵌入的路径 | 替换后高亮告知 |
| 人工 | 被删除文件的引用、语义性描述 | 标记 `<!-- TODO -->` |

**4. 更新目录树**

CLAUDE.md / ARCHITECTURE.md 中的目录树（`├──` 格式）自动同步：
- 新增架构级文件 → 追加（附一句话职责）
- 删除文件 → 移除
- 移动文件 → 更新位置

**5. 输出同步报告**

```
📝 文档同步完成
  自动修复：CLAUDE.md(2处)、ARCHITECTURE.md(1处)
  需人工确认：docs/exec-plans/active/EP-001.md:32 — 引用已删除的 internal/old/client.go
```

### 跳过条件

变更量很小（只改了函数内部逻辑，没动路径/名称）→ 跳过。

## 全量模式（用户触发）

用户说"全量扫描文档"、"检查文档新鲜度"、"doc freshness" 时执行。

### 流程

**1. 收集文档**

- `docs/**/*.md`
- `CLAUDE.md`（根目录）、`ARCHITECTURE.md`
- `.claude/**/*.md`
- 各子项目 `README.md`

**2. 提取引用**

从每个文档提取：
- 反引号路径：`` `path/to/file.go` ``
- Markdown 链接：`[text](./path/to/file)`
- import 路径：`import "project/internal/..."`
- 函数/类型名：`` `FuncName` `` 出现在描述性上下文中

**3. 验证存在性**

| 状态 | 条件 |
|------|------|
| 🔴 已失效 | 文件路径不存在 |
| 🟡 疑似过时 | 路径存在但引用的符号找不到 |
| 🟢 正常 | 一切匹配 |

**4. 输出报告 + 修复建议**

```
## 文档新鲜度报告
扫描 N 个文件 | 提取 M 个引用 | 发现 K 个问题

🔴 已失效：
  docs/design-docs/foo.md:23 → `internal/old/handler.go` — 文件已删除
🟡 疑似过时：
  ARCHITECTURE.md:45 → `ProcessJob` — 函数已重命名为 HandleJob
```

对每个问题给修复建议（能确定新路径 → 建议更新；已删除 → 建议删除描述；不确定 → 标记人工）。

**用户确认后**逐个应用修复。

## CLAUDE.md 维护规则

CLAUDE.md 是仓库「目录表」，维护优先级最高：

- 新增架构级文件（新 package/service/controller）→ 追加
- 删除文件 → 移除
- 职责变更 → 更新描述
- 普通代码改动（handler 加个函数）→ 不更新

## 约束

- 只修改 `.md` 文件，不碰代码
- 自动修复限于确定性替换（旧路径 → 新路径），不做语义推断
- 忽略外部 URL（http/https 不检查）
- 忽略示例代码块内的路径
- 每次修复后列出所有改动
