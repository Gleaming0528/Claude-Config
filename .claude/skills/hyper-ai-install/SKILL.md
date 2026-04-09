---
name: hyper-ai-install
description: 引导 Hyper-AI Python SDK 的安装和配置。适用于安装 SDK、配置 CLI、hai 命令不可用、SDK 初始化。
---

# Hyper-AI SDK/CLI 安装与配置

当用户需要安装、配置或初始化 Hyper-AI Python SDK 和 CLI 时，按以下流程引导。

## 前置条件

- Python >= 3.9
- pip / pipx
- 网络可达 `hyper-ai.hellorobotaxi.top`（生产）或 `hyper-ai-test.hellorobotaxi.top`（测试）

## 安装流程

### Step 1: 安装 SDK

```bash
# 方式 A：从 GitLab Package Registry 安装（推荐）
pip install hyper_ai  --extra-index-url https://gitlab.hellorobotaxi.top/api/v4/projects/16/packages/pypi/simple  -U

# 方式 B：从源码（开发模式）
cd <repo-root>/hyper-ai
pip install -e .
```

安装后会自动注册两个 CLI 命令：
- `hai` — 新版 noun-verb CLI（推荐）
- `hpc` — 旧版兼容 CLI

### Step 2: 认证配置

三种方式（优先级从高到低）：

```bash
# 方式 1：环境变量（推荐 CI/CD 和 Agent 使用）
export HYPER_AI_TOKEN="<your-token>"

# 方式 2：CLI 命令
hai config set-token <your-token>

# 方式 3：配置文件
# 编辑 ~/.config/hpc/config.toml
# [env.prod]
# auth = "<your-token>"
```

Token 获取方式：登录 https://hyper-ai.hellorobotaxi.top → 右上角头像 → 开发者设置 → 复制 Token。

### Step 3: 环境配置（可选）

```bash
# 切换环境
hai config set-env prod    # 生产环境（默认）
hai config set-env test    # 测试环境

# 设置默认命名空间（避免每次 -ns）
export HYPER_AI_NAMESPACE="ad-perception"
```

### Step 4: 验证安装

```bash
# 检查版本
hai version

# 检查配置
hai config show

# 验证连通性（列出命名空间）
hai namespace list

# 列出任务（验证权限）
hai job list -ns ad-perception
```

## SDK 快速上手

```python
from hyper_ai import HyperAI

# 初始化客户端
client = HyperAI()                              # 从环境变量/配置文件读取
client = HyperAI(api_key="<token>")             # 显式指定 token
client = HyperAI(api_key="<token>", env="test") # 指定测试环境

# 绑定命名空间（推荐）
ns = client.ns("ad-perception")

# 列出训练任务
jobs = ns.jobs.list()
for j in jobs:
    print(f"{j.name}: {j.phase}")

# 查看任务详情
detail = ns.jobs.detail("train-v3")
print(detail.active_pods)

# 实时日志
for line in ns.jobs.follow("train-v3"):
    print(line)

# 极简模式
import hyper_ai as hai
job = hai.train("ad-perception", "train-v3",
    queue="default", spec="gpu-a100-8",
    image="train:v3", command="torchrun train.py")
```

## CLI 命令速查

| 资源 | 命令 | 说明 |
|------|------|------|
| 训练任务 | `hai job list\|get\|create\|stop\|delete\|logs\|priority` | 全生命周期管理 |
| 开发环境 | `hai devspace list\|get\|create\|start\|stop\|delete` | GPU 工作站 |
| 推理服务 | `hai inference list\|get\|create\|scale\|delete` | 模型部署 |
| TensorBoard | `hai tb list\|get\|create\|delete` | 训练可视化 |
| 数据集 | `hai dataset list\|get\|create\|delete + version` | 版本化数据 |
| 模型 | `hai model list\|get\|create\|delete + version` | 版本化模型 |
| 队列 | `hai queue list\|get\|specs` | 资源规格查询 |
| Pipeline | `hai pipeline list\|get\|cancel\|delete` | 工作流 |
| 命名空间 | `hai namespace list\|get` | 团队组织 |
| 配置 | `hai config show\|set-env\|set-token` | SDK 配置 |

## 通用参数

| 参数 | 说明 | 环境变量 |
|------|------|----------|
| `-ns` / `--namespace` | 命名空间 | `HYPER_AI_NAMESPACE` |
| `-o json` | JSON 输出 | — |
| `-y` / `--yes` | 跳过删除确认 | — |
| `--page` / `--page-size` | 分页 | — |

## 常见问题

### Token 过期
```
AuthenticationError: 认证失败
```
**解决**：重新获取 Token 并设置 `hai config set-token <new-token>`

### 模块找不到
```
ModuleNotFoundError: No module named 'hyper_ai'
```
**解决**：确认安装了正确的 Python 环境，运行 `pip install hyper-ai --extra-index-url https://gitlab.hellorobotaxi.top/api/v4/projects/16/packages/pypi/simple`

### 命名空间权限
```
RequestError: 权限不足
```
**解决**：确认当前用户有该命名空间的访问权限，联系管理员授权

## Agent 集成指南

AI Agent 使用 SDK 时的最佳实践：

```python
from hyper_ai import HyperAI

# 1. 通过环境变量注入 token（安全）
client = HyperAI()  # 自动读取 HYPER_AI_TOKEN

# 2. 绑定 namespace 减少参数传递
ns = client.ns("ad-perception")

# 3. 利用 typed model 做决策
for job in ns.jobs.list(status="Training"):
    detail = ns.jobs.detail(job.name)
    if detail.pod_stats.get("failed", 0) > 0:
        ns.jobs.stop(job.name)  # 自动止损

# 4. 流式日志用于实时监控
for line in ns.jobs.follow("train-v3"):
    if "ERROR" in line or "CUDA OOM" in line:
        ns.jobs.stop("train-v3")
        break

# 5. 所有 model 都是 Pydantic，可 .model_dump() 序列化
job_dict = job.model_dump()
```
