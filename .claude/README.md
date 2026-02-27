# Claude Config

我的 Claude Code / Cursor AI 编程配置集合 — Rules、Agents、Commands、Skills 四层架构。

## 快速安装

在你的**项目根目录**下执行：

```bash
git clone git@github.com:Gleaming0528/Claude-Config.git /tmp/claude-config && \
  cp -r /tmp/claude-config/.claude /tmp/claude-config/CLAUDE.md . && \
  rm -rf /tmp/claude-config
```

执行完毕后 `.claude/` 和 `CLAUDE.md` 已就位，直接可用。临时文件在 `/tmp` 中，不会污染你的项目目录。

> 如果项目中已有同名文件，上述命令会覆盖。建议先备份。

---

## Rules（规则）

自动生效，无需手动调用。分为「全局生效」和「按文件类型触发」两类。

| 规则 | 作用 | 生效方式 |
|------|------|----------|
| coding-style.md | 不可变性、文件组织、错误处理、输入校验 | 始终生效 |
| git-workflow.md | commit 格式、PR 流程、feature 实现规范 | 始终生效 |
| security.md | 硬编码密钥、SQL 注入、XSS、CSRF、限流检查 | 始终生效 |
| tdd.md | TDD 红绿重构，没有失败测试不能写生产代码 | 始终生效 |
| verification.md | 完成前验证：没跑过验证命令不能说「搞定了」 | 始终生效 |
| go-coding-style.md | gofmt、命名、Gin handler 约定、错误包装 | `**/*.go` |
| go-testing.md | TDD、表驱动测试、race 检测、覆盖率目标 | `**/*_test.go` |
| go-security.md | 密钥、输入校验、context 超时、race 检测 | `**/*.go` |

---

## Agents（子代理）

在对话中 `@agent名` 或由 AI 自动调用。

| 代理 | 用途 |
|------|------|
| code-reviewer | 代码质量与安全审查，按文件类型路由到 Go / Frontend 审查 |
| code-simplifier | 死代码清理、代码简化，保持功能不变 |
| planner | 功能规划、需求拆解、复杂重构方案设计 |
| go-reviewer | Go 专项审查：惯用写法、Gin、client-go、并发、错误处理 |
| frontend-reviewer | 前端专项审查：React、TypeScript、Zustand、Axios、无障碍 |

---

## Commands（命令）

在对话中输入 `/命令名` 调用。

| 命令 | 场景 |
|------|------|
| /plan | 开始写功能前，让 AI 先出方案并等待确认 |
| /code-review | 写完代码一键安全与质量审查 |
| /build-fix | TypeScript / 构建报错时一键增量修复 |
| /commit | 生成规范的 commit message 并提交 |
| /sync-repos | 批量同步 GitLab hpc 下所有仓库到本地 |
| /sync-config | 将 .claude 配置同步推送到本 GitHub 仓库 |

---

## Skills（技能）

按需触发，提到相关关键词时自动加载。

| 技能 | 触发词 | 用途 |
|------|--------|------|
| brainstorming | 新功能、需求、方案设计 | 需求澄清与方案设计流程 |
| frontend-design | UI、页面、组件、前端 | 前端设计约束，拒绝 AI 通用美学 |
| systematic-debugging | debug、调试、排查、报错 | 系统化调试四阶段流程，禁止瞎猜 |
| golang-patterns | Go、错误处理、并发、Gin | Go 惯用模式与 HPC 后端最佳实践 |
| golang-testing | Go 测试、表驱动、benchmark | Go 测试模式：TDD、模拟、模糊测试 |
| writing-plans | 写计划、任务拆解 | 多步骤任务的实现计划编写 |
| executing-plans | 执行计划、开始构建 | 带审查检查点的计划执行 |
| subagent-driven-development | 子代理、分发任务 | 独立任务并行分发 + 两阶段审查 |
| using-git-worktrees | worktree、隔离开发 | 用 git worktree 隔离 feature 开发 |
| hpc-k8s-deploy | 部署、kustomize、集群 | K8s 部署、Kustomize overlay、CRD 管理 |
| job-failure-diagnosis | 训练失败、任务失败、诊断 | 从 Grafana/Loki 拉日志诊断 HPC 训练任务 |
| training-log-diagnosis | 训练日志、梯度爆炸、loss | AI/ML 训练日志分析与异常诊断 |

---

## 目录结构

```
.claude/
├── agents/
│   ├── code-reviewer.md
│   ├── code-simplifier.md
│   ├── frontend-reviewer.md
│   ├── go-reviewer.md
│   └── planner.md
├── commands/
│   ├── build-fix.md
│   ├── code-review.md
│   ├── commit.md
│   ├── plan.md
│   ├── sync-config.md
│   └── sync-repos.md
├── rules/
│   ├── coding-style.md
│   ├── git-workflow.md
│   ├── go-coding-style.md
│   ├── go-security.md
│   ├── go-testing.md
│   ├── security.md
│   ├── tdd.md
│   └── verification.md
├── skills/
│   ├── brainstorming/SKILL.md
│   ├── executing-plans/SKILL.md
│   ├── frontend-design/SKILL.md
│   ├── golang-patterns/SKILL.md
│   ├── golang-testing/SKILL.md
│   ├── hpc-k8s-deploy/SKILL.md
│   ├── job-failure-diagnosis/
│   │   ├── SKILL.md
│   │   └── scripts/fetch_job_data.py
│   ├── subagent-driven-development/SKILL.md
│   ├── systematic-debugging/SKILL.md
│   ├── training-log-diagnosis/SKILL.md
│   ├── using-git-worktrees/SKILL.md
│   └── writing-plans/SKILL.md
├── CLAUDE.md
└── README.md
CLAUDE.md                              # 项目级主配置
```

---

## 设计哲学

- **Rules** 管日常纪律 — 短约束，每次对话自动生效，< 50 行
- **Agents** 管角色分工 — 审查、简化、规划，按职责拆分子代理
- **Commands** 管操作效率 — 高频操作的快捷入口，`/` 一键触发
- **Skills** 管专业深度 — 仅在需要时按关键词加载，不浪费上下文

## 来源

- Rules / Agents / Commands：个人实践总结
- Skills：提取自 Anthropic Skills 和 [superpowers](https://github.com/NickHeap2/cursor-superpowers)（47.8k star）的实战精华
