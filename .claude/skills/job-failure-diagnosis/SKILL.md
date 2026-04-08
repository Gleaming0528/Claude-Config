---
name: job-failure-diagnosis
description: Diagnose failed or problematic HPC training jobs by fetching logs from Grafana/Loki. Use when given a job URL from hyper-ai platform, or when asked to diagnose why a training job failed. Trigger words include job URL, training failed, job failure, diagnose job, 训练失败, 任务失败, 诊断任务, 为什么失败.
---

# Job Failure Diagnosis via Grafana

通过 hyper-ai API 获取任务信息，通过 Grafana Loki/Prometheus 获取日志和 GPU 指标，分析失败原因。

## 数据通道

| 通道 | 域名 | 认证 | 用途 |
|------|------|------|------|
| hyper-ai API | `hyper-ai.hellorobotaxi.top` | Bearer token | 资源信息（状态、Pod、镜像等） |
| Grafana Loki | `grafana.hellorobotaxi.top` | 匿名 | 日志查询 |
| Grafana Prometheus | `grafana.hellorobotaxi.top` | 匿名 | DCGM GPU 指标查询 |
| kubectl | K8s API Server (via SOCKS5) | kubeconfig | 节点状态、事件、标签 |

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
  --url "https://hyper-ai.hellorobotaxi.top/jobs/..." \
  --output /tmp/diag.json
```

**需要 `full_network` 权限**（Shell 工具传 `required_permissions: ["full_network"]`）。

脚本一次性输出结构化 JSON，包含完整的节点拓扑：

| 字段 | 说明 |
|------|------|
| `resource_info.pods` | 完整 pod 列表：name, role, **node_name**, **pod_ip**, phase |
| `resource_info.node_names` | 去重后的 K8s 节点名列表（`e01-cn-xxx` 格式） |
| `host_mapping` | pod→node 映射（含 training_hostname，通过日志自动关联） |
| `training_hostnames` | 从启动日志提取的旧格式训练主机名列表（`hpc-xxx-h20-96-xxx` 格式） |
| `error_logs` | 错误日志（Python 异常、CUDA/NCCL 错误等） |
| `recent_logs` | 最近日志（按时间倒序，末尾 200 行） |
| `startup_logs` | 启动日志（按时间正序，前 100 行） |

**关键**: `node_names` + `training_hostnames` 提供了 GPU 健康检查所需的双格式主机名（见 Step 4），无需手动解析。

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

### Step 4: GPU 健康排查（当检测到 NCCL/GPU 错误时）

当日志分析发现以下错误时，**必须执行 GPU 健康检查**：
- NCCL timeout / connection error
- CUDA error / GPU hang
- Xid 错误
- 进程被 SIGKILL / OOM

#### 4a. 从 Step 2 结果中提取主机名

Step 2 已自动输出双格式主机名：
- `resource_info.node_names`: K8s 节点名（`e01-cn-xxx`）
- `training_hostnames`: 训练日志主机名（`hpc-xxx-h20-96-xxx`）

**直接合并两者**传给 GPU 健康检查脚本：

```bash
python3 .claude/skills/job-failure-diagnosis/scripts/check_node_health.py \
  --cluster hpc-prod-al-sh01 \
  --hostnames e01-cn-xxx e01-cn-yyy hpc-prod-al-sh01-h20-96-0018 hpc-prod-al-sh01-h20-96-0051
```

**需要 `full_network` 权限**。

> **为何需要两种格式**：Prometheus 中不同 DCGM exporter 使用不同 Hostname 标签值。
> ECC/RowRemap 指标用 K8s 节点名，Xid 指标用旧格式训练主机名。

脚本查询的 DCGM 指标：

| 指标 | 含义 | 严重级别 |
|------|------|----------|
| `DCGM_FI_DEV_XID_ERRORS` | GPU Xid 错误码 | warning |
| `DCGM_FI_DEV_ECC_SBE_VOL_TOTAL` | 可纠正单比特 ECC 错误 | warning |
| `DCGM_FI_DEV_ECC_DBE_VOL_TOTAL` | 不可纠正双比特 ECC 错误 | **critical** |
| `DCGM_FI_DEV_ROW_REMAP_FAILURE` | 显存行重映射失败 | **critical** |
| `DCGM_FI_DEV_RETIRED_SBE` | 因 SBE 退役的显存页 | warning |
| `DCGM_FI_DEV_RETIRED_DBE` | 因 DBE 退役的显存页 | **critical** |
| `DCGM_FI_DEV_NVLINK_CRC_FLIT_ERROR_COUNT_TOTAL` | NVLink CRC 错误 | warning |

#### 4b. RDMA 网络排查（当检测到 NCCL socket 连接错误时）

**触发条件**：错误日志中出现以下任一模式时，**必须执行 RDMA 诊断**：

```
socketStartConnect: Connect to 200.33.x.x<port> failed
ncclSystemError: System call ... failed ... device error
Software caused connection abort
Connection timed out  （目标 IP 为 200.33.x.x 网段）
```

**关键判断**：如果 NCCL 报错中的目标 IP 属于 `200.33.0.0/16` 网段，这是 RDMA overlay 地址，不是 Pod CIDR（`10.168.x.x`），说明是 IB 网络层问题而非应用层。

**执行脚本**（需要 SOCKS5 代理隧道 + kubectl 权限）：

```bash
# 先确保代理隧道可用
lsof -i :1080 2>/dev/null | grep ssh
# 如果没有运行：
# ssh -D 1080 -N -f -o ServerAliveInterval=60 -o ServerAliveCountMax=3 root@10.169.128.46

python3 .claude/skills/job-failure-diagnosis/scripts/check_rdma_health.py \
  --cluster hpc-prod-al-sh01 \
  --nodes e01-cn-xxx e01-cn-yyy e01-cn-zzz \
  --target-ip 200.33.8.30 \
  --output /tmp/rdma_diag.json
```

| 参数 | 来源 | 说明 |
|------|------|------|
| `--cluster` | URL 解析 | 集群名 |
| `--nodes` | `resource_info.node_names` | 任务涉及的所有 K8s 节点 |
| `--target-ip` | 错误日志中 `Connect to X.X.X.X` | NCCL 连接失败的目标 RDMA IP |

脚本自动执行三步：

1. **扫描 RDMA IP 映射**：通过各节点 kube-proxy pod 读取 `/proc/net/fib_trie`，提取 `200.33.x.x` 本地地址，建立「节点 → RDMA IPs」映射表
2. **定位故障节点**：将 `--target-ip` 与映射表匹配，找出 IP 所属节点
3. **检查 IB 链路健康**：通过 `kubectl debug node/` 读取故障节点 dmesg，提取 mlx5/bond 相关事件

**诊断结论**（`diagnosis` 字段）：

| 结论 | 含义 | 处理 |
|------|------|------|
| `bond_total_failure` | bond 网卡完全断连，无可用 slave | **P0** 更换光模块/线缆，cordon 节点 |
| `link_flapping` | IB 链路频繁抖动（>3 次 link down） | **P0** 检查光模块和线缆，可能老化 |
| `link_transient` | 少量 link down 事件 | **P1** 重试任务，反复失败再排查硬件 |
| `healthy` | dmesg 中无 IB 异常 | 可能是交换机侧或路由问题 |
| `target_ip_not_found` | 目标 IP 不属于任务节点 | 检查是否有跨任务干扰 |

**RDMA 网络架构参考**：

```
每台 H20 节点有 4 个 RDMA bond，对应 4 条独立 IB 链路：
  bond0 (reth0/reth1) → 200.33.x.{IP1}/30   PCI slot A
  bond1 (reth2/reth3) → 200.33.x.{IP2}/30   PCI slot B
  bond2 (reth4/reth5) → 200.33.x.{IP3}/30   PCI slot C
  bond3 (reth6/reth7) → 200.33.x.{IP4}/30   PCI slot D
每个 bond 包含 2 个 mlx5 slave（Mellanox ConnectX），200Gbps 每端口。
```

**dmesg 关键事件解读**：

| 事件 | 含义 | 严重性 |
|------|------|--------|
| `rethX: Link down` | IB 物理链路断开 | warning |
| `Cable unplugged / plugged` | 光模块被拔出/插入（也可能是接触不良） | warning |
| `bond_no_active: running without any active interface` | bond 的所有 slave 全部 down | **critical** |
| `mlx5_bond_X: Port: Y Link DOWN` | mlx5 bond 设备 link down | **critical** |
| `mlx5_pcie_event: PCIe slot advertised sufficient power` | PCIe 热插拔/重置事件 | info |
| `lag map: port X:Y` | bond 内部流量分布变化（slave 切换） | info |

#### 4c. kubectl 附加检查（可选）

当 Prometheus 数据和 RDMA 诊断不足以判断时：

```bash
# 节点状态和条件
HTTPS_PROXY=socks5://127.0.0.1:1080 kubectl --context {cluster} describe node {node_name}

# GPU 相关标签
HTTPS_PROXY=socks5://127.0.0.1:1080 kubectl --context {cluster} get node {node_name} \
  -o jsonpath='{.metadata.labels}' | python3 -c "
import json,sys
d=json.loads(sys.stdin.read())
for k,v in sorted(d.items()):
    if any(x in k.lower() for x in ['gpu','nvidia','accelerator','health']):
        print(f'  {k} = {v}')
"

# GPU 设备插件和 DCGM exporter pod 状态
HTTPS_PROXY=socks5://127.0.0.1:1080 kubectl --context {cluster} get pods -A \
  --field-selector spec.nodeName={node_name} | grep -iE "nvidia|gpu|dcgm"

# 节点事件
HTTPS_PROXY=socks5://127.0.0.1:1080 kubectl --context {cluster} get events -A \
  --field-selector involvedObject.name={node_name}
```

### Step 5: 输出报告

```
## 1. 概况
- 任务名称、命名空间、集群、状态、运行时长、镜像、GPU 规格

## 2. 致命错误
- 直接导致失败的错误
- 错误机制分析（WHY，不只是 WHAT）

## 3. 隐藏问题（如有）
- 训练动态问题（梯度爆炸、loss 异常）
- 可能导致未来失败的隐患

## 4. GPU 健康状态（如果执行了检查）
- 各节点 DCGM 指标汇总表
- Xid 错误码解读
- 硬件级结论（硬件问题 vs 软件问题）

## 5. RDMA 网络健康（如果执行了检查）
- 故障 RDMA IP → 节点映射
- 故障节点 IB 链路状态（link down/cable 事件）
- 受影响 bond 和 PCI 设备
- 结论（硬件故障 / 链路抖动 / 瞬时问题）

## 6. 修复建议
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
| Prometheus 指标 | grafana (匿名) | POST | `/api/ds/query` |

## Xid 错误码速查

| Xid | 名称 | 级别 | 说明 |
|-----|------|------|------|
| 13 | Graphics Engine Exception | critical | GPU 硬件异常 |
| 31 | GPU memory page fault | warning | 显存页错误，通常是软件 bug |
| 43 | GPU stopped processing | **info** | GPU 停止处理，通常是**进程被杀的后果**，非原因 |
| 48 | DBE ECC error | critical | 双比特 ECC 错误，硬件问题 |
| 63/64 | ECC page retirement | warning | ECC 触发的页退役/行重映射 |
| 74 | NVLink error | critical | NVLink 通信错误 |
| 79 | GPU fallen off the bus | critical | GPU 从 PCIe 总线脱落 |
| 92 | High SBE ECC count | warning | 高频单比特 ECC 错误 |
| 94 | Contained ECC error | warning | 受控 ECC 错误（H100/H20 常见） |
| 95 | Uncontained ECC error | critical | 不受控 ECC 错误 |

**判断逻辑**：Xid 43 单独出现几乎总是训练崩溃的**后果**（进程被 SIGTERM/SIGKILL 后 GPU 上下文异常中断），不需要排查硬件。只有 Xid 13/48/74/79/95 需要紧急处理硬件问题。

## 已知陷阱

### Loki 查询中没有 `cluster` 标签

**错误写法**（会返回 0 条结果）：
```
{namespace="ad-e2e", cluster="hpc-prod-al-sh01", pod=~"job-name.*"}
```

**正确写法**：
```
{namespace="ad-e2e", pod=~"job-name.*"}
```

`cluster` 信息仅用于选择正确的 Loki datasource UID，不能作为 Loki 标签过滤。

### 双主机名格式（自动处理）

训练日志主机名（`hpc-prod-al-sh01-h20-96-XXXX`）和 K8s 节点名（`e01-cn-XXXX`）是两个不同命名系统。`fetch_job_data.py` 已自动提取两种格式并输出 `node_names` + `training_hostnames`，合并后传给 `check_node_health.py` 即可。

Prometheus 中不同 DCGM exporter 使用不同 Hostname：
- `ack-prometheus-gpu-exporter`（arms-prom 命名空间）→ 旧格式 `hpc-xxx`
- `dcgm-exporter`（monitoring 命名空间）→ K8s 节点名 `e01-cn-xxx`

### dateutil 不一定安装

`fetch_job_data.py` 不依赖 `python-dateutil`，使用 stdlib 解析 ISO 8601 时间戳。

## 关键原则

- **时间线优先**：先重建事件时间线，再做模式匹配
- **隐藏问题 > 表面错误**：梯度爆炸比 NCCL 超时更重要
- **修原因不修症状**：不要只修 NCCL timeout，要修导致 timeout 的慢 eval
- **量化分析**：提取实际数值，不只是 grep "error"
- **NCCL 超时必查 GPU**：出现 NCCL 错误时，必须执行 GPU 健康检查排除硬件因素
- **NCCL socket 错误必查 RDMA**：当 NCCL 报 `socketStartConnect` 失败且目标 IP 在 200.33.x.x 网段时，必须执行 RDMA 网络诊断（Step 4b）
- **Xid 43 是果不是因**：单独出现的 Xid 43 不代表硬件问题
- **GPU 健康 ≠ 全部健康**：GPU DCGM 指标全部正常时，如果有 NCCL 错误，还要排查 RDMA 网络层
