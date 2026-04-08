# .claude/ Configuration

AI agent, skill, rule, and command configurations for the HPC platform.

## Directory Structure

```
.claude/
├── agents/                          # Subagents
│   ├── code-reviewer.md             # Go + Frontend reviewer (auto-routes by file type)
│   ├── go-reviewer.md               # Go-only reviewer (Gin, K8s, concurrency)
│   ├── frontend-reviewer.md         # Frontend-only reviewer (React, TS, Zustand, a11y)
│   ├── code-simplifier.md           # Code simplification (Go + TS/React aware)
│   └── planner.md                   # Implementation planning for complex features
│
├── skills/                          # Domain knowledge (auto-triggered by keywords)
│   ├── code-quality/                # 代码质量感知 + GC 垃圾回收（感知模式 + /gc 主动清理）
│   ├── doc-gardening/               # 文档自动园丁（增量同步 + 全量扫描，两种模式合一）
│   ├── golang-patterns/             # Idiomatic Go: error handling, concurrency, Gin
│   ├── golang-testing/              # Go testing: table-driven, benchmarks, fuzz, mocks
│   ├── hpc-commit/                  # 代码提交流程（质量门禁 + conventional commits）
│   ├── hpc-k8s-deploy/              # K8s deployment, Kustomize, CRDs
│   ├── hpc-release/                 # Submodule 发布流程（deploy.sh tag & push）
│   ├── hpc-training-diagnosis/      # NCCL/Xid/Loki 平台级训练排障
│   ├── hpc-weekly-report/           # 团队周报生成（git + Grafana + 预算）
│   ├── hyper-ai-install/            # Hyper-AI SDK 安装配置
│   ├── hyper-ai-sdk/                # Hyper-AI SDK API 参考
│   ├── job-failure-diagnosis/       # 训练任务失败诊断（Grafana/Loki）
│   ├── k8s-proxy-tunnel/            # SSH SOCKS5 代理访问 K8s 集群
│   ├── pm-create-prd/               # PRD 文档生成
│   ├── pm-generate-tasks/           # 需求拆解为开发任务
│   ├── training-log-diagnosis/      # AI/ML 训练日志分析（loss, grad_norm, NCCL）
│   └── ui-design-brain/             # 60+ 组件最佳实践
│
├── rules/                           # Reference guidelines
│   ├── cross-module.md              # CRD Phase、错误码、Event 横切规范
│   ├── design-frontend/
│   │   ├── hpc-design-system.md     # HPC UI 设计系统（Ant Design + unified-theme）
│   │   └── product-design-principles.md  # HPC 产品设计原则
│   ├── git-workflow.md              # Commit format, PR process
│   ├── go-coding-style.md           # Go: gofmt, naming, Gin conventions
│   ├── go-controller.md             # K8s controller: Reconciler, Finalizer, RequeueAfter
│   ├── go-security.md               # Go: secrets, input validation, race detection
│   ├── go-testing.md                # Go: TDD, table-driven, envtest, coverage
│   ├── k8s-yaml.md                  # K8s: resource naming, probes, CRD
│   ├── python-service.md            # Python: FastAPI, subprocess, timeout
│   ├── python-testing.md            # Python: pytest conventions
│   ├── python-venv.md               # Workspace venv 配置
│   ├── react-frontend.md            # React: hpc-ui, Ant Design, TanStack Query, Zustand
│   ├── security.md                  # General security checklist
│   ├── shell-scripts.md             # Bash safety, kubectl parsing
│   └── verification.md              # Verification before completion
│
├── commands/                        # Workflow instructions
│   ├── build-fix.md                 # Incremental build error resolution
│   ├── code-review.md               # Code review workflow
│   ├── commit.md                    # Commit workflow
│   ├── plan.md                      # Planning workflow
│   ├── sync-config.md               # Sync .claude/ to GitHub backup repo
│   └── sync-repos.md                # Sync all GitLab repos to local
│
├── CLAUDE.md                        # This file
└── README.md                        # GitHub repo README
```

## Agents

| Agent | Scope |
|-------|-------|
| `code-reviewer` | Auto-routes Go vs Frontend by file type |
| `go-reviewer` | Go: security, concurrency, Gin, K8s, error handling |
| `frontend-reviewer` | Frontend: React, TS, Zustand, auth, a11y |
| `code-simplifier` | Simplification — Go + TS/React aware |
| `planner` | Requirements → architecture → step breakdown |
