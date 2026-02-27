---
name: job-failure-diagnosis
description: Diagnose failed or problematic HPC training jobs by fetching logs from Grafana/Loki. Use when given a job URL from hyper-ai platform, or when asked to diagnose why a training job failed. Trigger words include job URL, training failed, job failure, diagnose job, 训练失败, 任务失败, 诊断任务, 为什么失败.
---

# Job Failure Diagnosis via Grafana

通过 hyper-ai API 获取任务信息，通过 Grafana Loki 获取日志，分析失败原因。

## 数据通道

| 通道 | 域名 | 认证 | 用途 |
|------|------|------|------|
| hyper-ai API | `hyper-ai.hellorobotaxi.top` | Bearer token | 资源信息（状态、Pod、镜像等） |
| Grafana Loki | `grafana.hellorobotaxi.top` | 匿名 | 日志查询 |

## 工作流程

### Step 1: 解析 URL

从 URL 中提取三个关键字段：

```
https://hyper-ai.hellorobotaxi.top/jobs/{namespace}/{cluster}/{job-name}?namespace={ns}
```

| 片段 | 含义 | 示例 |
|------|------|------|
| 第一段路径 (after /jobs/) | namespace | `ad-perception` |
| 第二段路径 | cluster | `hpc-prod-al-sh01` |
| 第三段路径 | job_name | `maptr-tmp-cat-v2-hh2l2` |

### Step 2: 执行数据获取脚本

```bash
python3 .claude/skills/job-failure-diagnosis/scripts/fetch_job_data.py \
  --url "https://hyper-ai.hellorobotaxi.top/jobs/..."
```

**需要 `full_network` 权限**（Shell 工具传 `required_permissions: ["full_network"]`）。

脚本输出结构化 JSON：
- `resource_info`: 任务基本信息（状态、镜像、集群、规格等）
- `error_logs`: 错误日志（Python 异常、CUDA/NCCL 错误等）
- `recent_logs`: 最近日志（按时间倒序）

### Step 3: 分析诊断

基于获取的数据，按以下框架分析（参考 training-log-diagnosis skill）：

**优先级排序：**

1. **错误日志分析** — 应用层问题
   - Python 异常堆栈（Traceback）
   - CUDA/NCCL 错误（GPU 通信/显存）
   - RuntimeError / ValueError / FileNotFoundError
   - 梯度爆炸（grad_norm spike）
   - Loss 异常（NaN/Inf）

2. **训练动态分析** — 数值趋势
   - loss 趋势（是否收敛、是否突变）
   - grad_norm 趋势（是否爆炸）
   - 学习率调度是否合理

3. **时间线重建** — 串联因果链
   - 任务何时启动 → 何时出现异常 → 何时崩溃
   - 异常发生在训练阶段还是评估阶段

### Step 4: 输出报告

```
## 1. 概况
- 任务名称、命名空间、集群、状态、运行时长、镜像、GPU 规格

## 2. 致命错误
- 直接导致失败的错误
- 错误机制分析（WHY，不只是 WHAT）

## 3. 隐藏问题（如有）
- 训练动态问题（梯度爆炸、loss 异常）
- 可能导致未来失败的隐患

## 4. 修复建议
- P0（必须修复）
- P1（建议修复）
- P2（可选优化）
```

## 集群数据源映射

| 集群 | Loki UID | Prometheus UID |
|------|----------|----------------|
| hpc-test-al-sh01 | ef6h29oj7drlsd | df6h2brb3gidcd |
| hpc-prod-al-sh01 | cf6gzdzit6wowc | af6h2e37d6pkwf |
| hpc-prod-al-sh02 | ff7jqjxkpog00e | ff7jqiem43vuof |
| hpc-prod-bd-su01 | efax9ej7g7qwwa | afat7coqm6olca |

## API 端点参考

| 用途 | 域名 | 方法 | 路径 |
|------|------|------|------|
| 资源信息 | hyper-ai (Bearer) | GET | `/api/studio/namespaces/{ns}/aijobs/{name}?cluster={cluster}` |
| Loki 日志 | grafana (匿名) | POST | `/api/ds/query?ds_type=loki` |

## 关键原则

- **时间线优先**：先重建事件时间线，再做模式匹配
- **隐藏问题 > 表面错误**：梯度爆炸比 NCCL 超时更重要
- **修原因不修症状**：不要只修 NCCL timeout，要修导致 timeout 的慢 eval
- **量化分析**：提取实际数值，不只是 grep "error"
