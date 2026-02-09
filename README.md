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
| coding-style.md | 强制不可变性、文件大小限制、错误处理规范 |
| git-workflow.md | 规范 commit 格式、PR 流程 |
| security.md | 自动检查硬编码密钥、SQL注入、XSS等安全问题 |
| tdd.md | TDD 铁律：没有失败测试就不能写生产代码 |
| verification.md | 完成前验证：没跑过验证命令就不能说"搞定了" |

---

## Commands（命令）

在对话中输入 `/命令名` 调用。

| 命令 | 场景 |
|------|------|
| /plan | 开始写功能前，让 AI 先出方案 |
| /code-review | 写完代码一键审查 |
| /build-fix | 构建报错时一键修复 |
| /commit | 生成规范的 commit message |
| /sync-repos | 批量同步 GitLab 仓库 |

---

## Agents（子代理）

在对话中 `@agent名` 或让 AI 自动调用。

| 代理 | 用途 |
|------|------|
| planner | 功能规划、需求拆解 |
| code-reviewer | 代码质量与安全审查 |
| code-simplifier | 死代码清理、代码简化 |

---

## Skills（技能）

按需触发，提到相关关键词时自动加载。

| 技能 | 触发词 | 用途 |
|------|--------|------|
| systematic-debugging | debug、调试、排查、报错 | 系统化调试四阶段流程，禁止瞎猜 |
| frontend-design | UI、页面、组件、前端 | 前端设计约束，拒绝 AI 通用美学 |
| brainstorming | 新功能、需求、方案设计 | 需求澄清与方案设计流程 |

---

## 目录结构

```
.claude/
├── agents/                          # 子代理角色
│   ├── code-reviewer.md
│   ├── code-simplifier.md
│   └── planner.md
├── commands/                        # 斜杠命令
│   ├── build-fix.md
│   ├── code-review.md
│   ├── commit.md
│   ├── plan.md
│   └── sync-repos.md
├── rules/                           # 自动规则（每次对话生效）
│   ├── coding-style.md
│   ├── git-workflow.md
│   ├── security.md
│   ├── tdd.md
│   └── verification.md
└── skills/                          # 按需触发技能
    ├── brainstorming/SKILL.md
    ├── frontend-design/SKILL.md
    └── systematic-debugging/SKILL.md
CLAUDE.md                            # 项目级主配置
```

## 设计哲学

- **Rules** 管日常纪律 — 短约束，每次生效，< 50 行
- **Agents** 管角色分工 — 审查、简化、规划三个核心角色
- **Commands** 管操作效率 — 高频操作的快捷入口
- **Skills** 管专业深度 — 仅在需要时加载，不浪费上下文

## 来源

- Rules/Agents/Commands: 个人实践总结
- Skills: 提取自 [Anthropic Skills](https://github.com/anthropics/skills) 和 [superpowers](https://github.com/obra/superpowers)（47.8k star）的实战精华
