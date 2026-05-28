---
name: job-failure-diagnosis
description: 从 Grafana/Loki 拉取日志，诊断失败或异常的 HPC 训练任务。适用于收到任务 URL、或被要求分析训练失败原因。
---

# Job Failure Diagnosis

## 数据通道

| 通道 | 入口 | 认证 | 用途 |
|------|------|------|------|
| hyper-ai API | `hyper-ai.hellorobotaxi.top` | Bearer token | AIJob 资源信息 |
| Grafana Loki/Prom | `grafana.hellorobotaxi.top` | 匿名 | 日志、DCGM 指标 |
| kubectl | K8s API (via SOCKS5 `127.0.0.1:1080`) | kubeconfig | 节点、事件、标签 |
| PFS 取证 | `hpc-minio-api` pod (ns `hpc-system`) | kubectl exec | `.hpc-system/` 状态目录、用户脚本 |

## Step 1: 拉基础数据

URL 格式：`.../jobs/{ns}/{cluster}/{job-name}?namespace={ns}`

```bash
python3 .claude/skills/job-failure-diagnosis/scripts/fetch_job_data.py \
  --url "..." --output /tmp/diag.json     # 需 full_network 权限
```

输出 JSON 关键字段：

| 字段 | 用途 |
|------|------|
| `resource_info.node_names` | K8s 节点名（`e01-cn-xxx`） |
| `training_hostnames` | 训练日志主机名（`hpc-xxx-h20-96-xxx`） |
| `error_logs` / `recent_logs` / `startup_logs` | 日志三件套 |

## Step 2: PFS 取证（Loki 不全时）

每个 AIJob 在 PFS 上有独立状态目录，通过 `hpc-minio-api` pod 直读：

```bash
# 2.1 拿 pod + 挂载点（不同集群路径不同：pfs-hades / cpfs-hera / nas-nyx ...）
POD=$(kubectl --context {cluster} -n hpc-system \
  get pod -l app.kubernetes.io/name=hpc-minio-api \
  -o jsonpath='{.items[0].metadata.name}')
PFS=$(kubectl --context {cluster} -n hpc-system exec $POD -- \
  sh -c "mount | grep -E 'pfs|cpfs|nas' | awk '{print \$3}' | head -1")

# 2.2 取关键文件
BASE=$PFS/hpc/runtimes/{ns}-{cluster}/{job-name}/.hpc-system
kubectl --context {cluster} -n hpc-system exec $POD -- sh -c "
  cat $BASE/state.json
  ls -la $BASE/comm/status/ $BASE/logs/
  tail -200 $BASE/logs/*.stdout.log
"
```

容器路径 → PFS 路径的约定（`kubectl get aijob ... -o json` 看 `spec.volumeMounts` 确认）：

| 容器内 | PFS 上（挂载点之下） |
|---|---|
| `/workspace` | `hpc/runtimes/{ns}-{cluster}/` |
| `/mnt/volumes/{name}/` | `hpc/volumes/{name}/` |

`.hpc-system/` 目录（每个 AIJob 都有）：

```
├── state.json           ★ master 状态机（phase/restart_history/failure_reason）
├── comm/status/{pod}.status  ★ agent 上报的用户进程退出码
├── logs/{pod}.stdout.log     ★ 用户命令 stdout（注意重启时会被 unlink）
└── protocol.json / markers/ / comm/{restart,stop,done}/ / barrier/
```

证据速查：

| 现象 | 含义 |
|---|---|
| `restart_history[].name == "pod-level-restart"` + `exitCode: -1` | Volcano 触发 PodFailed→RestartPod；`-1` 是占位**不是真实退出码** |
| `comm/status/` 为空 | agent 没走完上报路径 → pod 被 SIGKILL / 外部 delete / 用户 `exec` 替换了 agent |
| `stdout.log` 很小 + mtime ≈ restart 时间 | 见陷阱"stdout.log 被 unlink" |
| `failure_reason == "Pod repeatedly killed: N restarts (max: 0)"` | `maxRetries=0` 放大偶发重启，建议加 retry |

## Step 3: 分析诊断

日志分析框架引用 [`training-log-diagnosis`](../training-log-diagnosis/SKILL.md) skill。本 skill 重点补充 HPC 平台特有的**时间线重建**：

```
Pod 启动 → setup.sh → torchrun/python 入口 → NCCL init → DDP wrap → 训练循环
     ↑                                                              ↑
   agent 启动                                          GPU 利用率起来才算真在训练
```

Loki 日志停在哪一步 + PFS `state.json.phase_history` 的时间戳 = 定位问题阶段。

## Step 4: 硬件排查

**触发条件**：日志里出现 NCCL timeout / CUDA error / Xid / 被 SIGKILL / OOM。

### 4a. GPU 健康（DCGM）

```bash
python3 .claude/skills/job-failure-diagnosis/scripts/check_node_health.py \
  --cluster {cluster} \
  --hostnames <node_names + training_hostnames 合并>
```

> 两种格式都要传：arms-prom 的 exporter 用老格式 `hpc-xxx`，monitoring 的 exporter 用 K8s 节点名 `e01-cn-xxx`。

**critical 指标**：`DCGM_FI_DEV_ECC_DBE_VOL_TOTAL`、`DCGM_FI_DEV_ROW_REMAP_FAILURE`、`DCGM_FI_DEV_RETIRED_DBE`（其他指标脚本自己会标级别）。

**Xid 判断**：只有 Xid 13/48/74/79/95 是硬件问题。**Xid 43 是果不是因**——进程被 SIGKILL 之后 GPU 上下文异常中断，不要当硬件故障排查。

### 4b. RDMA 网络（NCCL socket 失败时）

**触发条件**：NCCL 报错中目标 IP 在 `200.33.0.0/16` 网段（RDMA overlay，非 Pod CIDR `10.168.x.x`）。典型报错：

```
socketStartConnect: Connect to 200.33.x.x<port> failed
ncclSystemError: System call ... device error
```

```bash
# 先确保 SOCKS5 隧道在（没有的话启动 ssh -D 1080 -N -f ... root@10.169.128.46）
python3 .claude/skills/job-failure-diagnosis/scripts/check_node_health.py \
  --cluster {cluster} --nodes <node_names> \
  --target-ip 200.33.x.x --output /tmp/rdma.json
```

脚本做三步：扫 `/proc/net/fib_trie` 建 RDMA IP → 节点映射 → 定位故障节点 → 读 dmesg 抽 mlx5/bond 事件。

**结论字段**：

| `diagnosis` | 处理 |
|---|---|
| `bond_total_failure` | P0：bond 所有 slave 全 down，换光模块/线缆，cordon 节点 |
| `link_flapping` | P0：>3 次 link down，模块老化 |
| `link_transient` | P1：少量 link down，重试任务 |
| `healthy` | dmesg 无异常，查交换机/路由 |
| `target_ip_not_found` | IP 不属于任务节点，查跨任务干扰 |

## 集群数据源映射

| 集群 | Loki UID | Prometheus UID |
|------|----------|----------------|
| hpc-test-al-sh01 | ef6h29oj7drlsd | df6h2brb3gidcd |
| hpc-prod-al-sh01 | cf6gzdzit6wowc | af6h2e37d6pkwf |
| hpc-prod-al-sh02 | ff7jqjxkpog00e | ff7jqiem43vuof |
| hpc-prod-bd-su01 | efax9ej7g7qwwa | afat7coqm6olca |

## Xid 错误码速查

完整 Xid/SXid 错误码表见 skill: `hpc-training-diagnosis`（Step 4 GPU 错误类型速查）。

**关键判断逻辑**：Xid 43 单独出现几乎总是训练崩溃的**后果**（进程被杀后 GPU 上下文中断），不需要排查硬件。只有 Xid 13/48/74/79/95 需要紧急处理硬件问题。

## 已知陷阱

### Loki 标签里没有 `cluster`

`cluster` 只用来选 datasource UID，不能做 Loki 标签过滤：

```
# ❌ 返回 0 条       {namespace="x", cluster="y", pod=~"..."}
# ✅                 {namespace="x", pod=~"..."}
```

### Grafana 颜色不可信，看行首前缀

PyTorch/NCCL 把 warning 写 stderr，Loki 全塞进 `error` bucket。判断看**内容**：

| 前缀 | 级别 |
|------|------|
| `[W ...]` / `Warning:` / `NCCL INFO` | 忽略 |
| `[E ...]` / `Error:` / `Traceback` | 重点分析 |

### Agent 启动时 unlink stdout.log

`agent.py._cleanup_trigger_files()` 会 `unlink` 掉 `{pod}.stdout.log`。pod-level restart 后，**pod #1 的日志被 pod #2 清空**。

**识别**：stdout.log 很小 + mtime ≈ restart 时间 + 内容停在启动阶段。**补救**：只能回 Loki 捞，按 pod 实例 UID（不是 pod name）过滤，`maxLines` 拉满。

### `comm/status/` 空 ≠ 用户进程正常

Pod 被 SIGKILL / 用户 `exec` 替换 agent 进程 / agent 自己 crash 都会导致空。这时 `restart_history[0].exitCode = -1` 是 master 合成的占位，不是真实退出码。

## HPC 特定原则

- **NCCL 错误必查 GPU**，必要时再查 RDMA（200.33.x.x 网段）
- **Xid 43 单独出现不是硬件问题**
- **Loki 和 PFS 互为冗余**：stdout.log 被 unlink 时靠 Loki，Loki buffer 丢了靠 PFS
- 通用方法论（时间线/根因/量化）参考 `training-log-diagnosis` skill
