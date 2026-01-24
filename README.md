# Claude Config

我的 Claude Code / Cursor 配置集合。

## 安装

```bash
git clone git@github.com:Gleaming0528/Claude-Config.git
```

将 `.claude` 目录和 `CLAUDE.md` 复制到你的项目根目录即可。

---

## Rules（规则）

自动生效，无需手动调用。

| 规则 | 作用 |
|------|------|
| `security.md` | 自动检查硬编码密钥、SQL注入、XSS等安全问题 |
| `coding-style.md` | 强制不可变性、文件大小限制、错误处理规范 |
| `git-workflow.md` | 规范 commit 格式、PR 流程 |

---

## Commands（命令）

在对话中输入 `/命令名` 调用。

| 命令 | 场景 |
|------|------|
| `/plan` | 开始写功能前，让 AI 先出方案 |
| `/code-review` | 写完代码一键审查 |
| `/build-fix` | 构建报错时一键修复 |
| `/commit` | 生成规范的 commit message |

---

## Agents（子代理）

在对话中 `@agent名` 或让 AI 自动调用。

| 代理 | 用途 |
|------|------|
| `planner` | 功能规划、需求拆解 |
| `code-reviewer` | 代码质量与安全审查 |
| `code-simplifier` | 死代码清理、代码简化 |

---

## Skills（技能）

高级功能，按需使用。

| 技能 | 用途 |
|------|------|
| `context-optimization` | 上下文优化、token 节省 |
| `context-compression` | 长对话压缩 |
| `evaluation` | AI 输出质量评估 |
| `memory-systems` | 跨会话记忆持久化 |
| `multi-agent-patterns` | 多代理协作模式 |
| `tool-design` | 工具设计最佳实践 |

---

## 目录结构

```
.claude/
├── agents/          # 子代理
├── commands/        # 斜杠命令
├── rules/           # 自动规则
└── skills/          # 高级技能
CLAUDE.md            # 项目级配置
```
