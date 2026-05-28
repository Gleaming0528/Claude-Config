# Claude Config

HPC 超算平台 AI 编程配置 — Rules、Agents、Commands、Skills 四层架构。

## 快速安装

```bash
git clone git@github.com:Gleaming0528/Claude-Config.git /tmp/claude-config && \
  cp -r /tmp/claude-config/.claude /tmp/claude-config/CLAUDE.md . && \
  rm -rf /tmp/claude-config
```

## 设计哲学

```
Rules  → 日常纪律（短约束，自动生效）
Agents → 角色分工（审查、简化、规划，作为 subagent 被派遣）
Commands → 操作效率（高频操作快捷入口）
Skills → 专业深度（按关键词按需加载，方法论 + 工作流）
```

四层之间互相引用但**不重复**：Rule 聚焦约束，Skill 聚焦流程，Agent 聚焦执行，Command 聚焦入口。

---

## Rules（规则）

### Go

| 规则 | 作用 | 生效范围 |
|------|------|----------|
| go-coding-style.md | gofmt、命名、Gin handler、错误包装 | `**/*.go` |
| go-testing.md | TDD、表驱动、envtest、race、覆盖率 | `**/*_test.go` |
| go-security.md | 密钥、输入校验、context 超时、安全扫描 | `**/*.go` |
| go-controller.md | K8s Reconciler 实现（Finalizer、RequeueAfter、Status 分离） | `**/*.go` |

### Python

| 规则 | 作用 | 生效范围 |
|------|------|----------|
| python-service.md | FastAPI、subprocess、超时、异常处理 | `**/*.py` |
| python-testing.md | pytest 约定（参数化、mock、命名） | `**/test_*.py` |
| python-venv.md | 强制 workspace venv，禁止系统 Python | `**/*.py` |

### 前端

| 规则 | 作用 | 生效范围 |
|------|------|----------|
| react-frontend.md | hpc-ui 工程规范（TanStack Query、Zustand、Ant Design） | `hpc-ui/**/*.{ts,tsx}` |
| design-frontend/product-design-principles.md | 产品设计原则（IA、表单模式、反模式） | `hpc-ui/**/*.{tsx,ts}` |
| design-frontend/hpc-design-system.md | 设计系统（Ant Design 令牌、组件规范） | `hpc-ui/**/*.{tsx,ts,css}` |

### 基础设施 & 横切

| 规则 | 作用 | 生效范围 |
|------|------|----------|
| cross-module.md | CRD Phase 状态机、错误码、Event、子资源约定 | `**/*.go` |
| k8s-yaml.md | K8s YAML 命名、label、探针、CRD | `**/*.{yaml,yml}` |
| shell-scripts.md | Bash 安全、set -euo pipefail、kubectl | `**/*.sh` |

### 始终生效

| 规则 | 作用 |
|------|------|
| git-workflow.md | commit 格式、PR 流程、Feature 实现工作流 |
| security.md | 安全检查清单（密钥、注入、XSS、CSRF） |
| verification.md | 完成前验证铁律（→ 详见 skill `verification-before-completion`） |

---

## Agents（子代理）

| 代理 | 用途 |
|------|------|
| code-reviewer | 代码审查路由器，按文件类型路由 Go / Frontend 清单 |
| go-reviewer | Go 专项：惯用写法、Gin、client-go、并发、错误处理 |
| frontend-reviewer | 前端专项：React、TS、Zustand、Axios、无障碍 |
| code-simplifier | 代码简化（Chesterton's Fence 原则），保持功能不变 |
| codebase-auditor | 子项目整体审计：命名一致性、重复代码、错误处理风格统一、批量修复 |
| planner | 功能规划、需求拆解、复杂重构方案 |

---

## Commands（命令）

| 命令 | 场景 |
|------|------|
| /plan | 功能开发前先出方案（调用 planner agent） |
| /code-review | 代码审查（调用 code-reviewer agent） |
| /build-fix | 构建报错增量修复（Go + TypeScript） |
| /commit | 规范 commit message 并提交（调用 hpc-commit skill） |
| /sync-repos | 批量同步 GitLab 仓库到本地（submodule 模式） |
| /sync-config | 同步 .claude 到 GitHub 备份仓库 |

---

## Skills（技能）

### 领域技能

| 技能 | 触发词 | 用途 |
|------|--------|------|
| golang-patterns | Go、错误处理、并发、Gin、API 设计 | Go 惯用模式 + API 设计原则 |
| golang-testing | Go 测试、表驱动、benchmark | Go 测试：TDD、模拟、模糊测试 |
| hpc-commit | 提交、commit、push | 代码提交流程（质量门禁） |
| hpc-k8s-deploy | 部署、kustomize、集群 | K8s 部署、Kustomize、CRD |
| hpc-release | 发布、tag、版本 | Submodule 发版流程 |
| hpc-training-diagnosis | NCCL、GPU 错误、训练 hang | 平台级训练故障深度诊断 |
| hpc-weekly-report | 周报、本周总结 | 团队周报自动生成 |
| hyper-ai-sdk | hyper-ai、hi、SDK | SDK API 参考 |
| hyper-ai-install | 安装 SDK、配置 CLI | SDK 安装配置 |
| job-failure-diagnosis | 训练失败、任务失败 | Grafana/Loki 日志诊断 |
| k8s-proxy-tunnel | kubectl、helm、集群 | SSH 代理访问 K8s |
| training-log-diagnosis | 训练日志、梯度爆炸、loss | AI/ML 训练日志分析 |
| pm-create-prd | PRD、需求文档 | PRD 文档生成 |
| pm-generate-tasks | 任务拆解、拆分任务 | 需求转开发任务 |
| ui-design-brain | UI 设计、组件设计 | 60+ 组件最佳实践 |
| code-quality | 代码质量、lint、gc、技术债 | 代码质量感知 + GC 垃圾回收 |
| doc-gardening | 重构、重命名、文档同步 | 代码变更后自动同步文档引用 |

### 工作流技能

| 技能 | 触发时机 | 用途 |
|------|----------|------|
| brainstorming | 创建功能、构建组件前 | 探索用户意图、需求与设计 |
| writing-plans | 有需求/规格待实现时 | 编写多步骤实现方案 |
| executing-plans | 有方案待执行时 | 按方案执行并设置审查检查点 |
| incremental-implementation | 多文件改动、新功能、重构 | 薄切片递增实现（实现→测试→验证→提交） |
| test-driven-development | 实现功能或修复前 | TDD 驱动开发 |
| systematic-debugging | 遇到 bug 或测试失败时 | 系统性调试方法论 |
| documentation-and-adrs | 架构决策、重大设计变更 | ADR 模板 + 注释纪律 |
| dispatching-parallel-agents | 2+ 独立任务时 | 并行子代理调度 |
| subagent-driven-development | 执行含独立任务的方案时 | 子代理驱动开发 |
| requesting-code-review | 完成任务或合并前 | 请求代码审查 |
| receiving-code-review | 收到审查反馈时 | 技术严谨地处理审查意见 |
| finishing-a-development-branch | 实现完成、测试通过后 | 分支集成决策（merge/PR/cleanup） |
| verification-before-completion | 声称完成前 | 验证通过才能宣告完成 |
| using-superpowers | 对话开始时 | 发现和使用可用技能 |
| using-git-worktrees | 需要隔离环境开发时 | Git worktree 管理 |
| writing-skills | 创建/编辑技能时 | 技能编写与测试 |
