---
name: hpc-training-diagnosis
description: HPC 分布式训练故障深度诊断方法论。适用于分析 NCCL 超时、GPU Xid 错误、训练 hang、多节点级联故障等复杂问题。当用户提供 Grafana 日志链接、要求分析训练失败原因、提到 NCCL timeout、GPU 错误、XID、训练卡住时自动激活。
---

# HPC 分布式训练故障深度诊断

## 适用场景

- 分析分布式训练任务失败/卡住的根因
- 多节点 NCCL 超时级联故障定位
- GPU Xid/SXid 硬件错误关联分析
- 从 Grafana/Loki 日志中提取故障因果链
- 训练运行 N 小时后突然失败的诊断

## 诊断流程（五步法）

### Step 1: 获取数据源信息

从 Grafana URL 解析或从用户输入中提取：
- namespace、pod 名称模式、时间范围
- 数据源 UID → 通过 Grafana API 获取 Loki 地址

```bash
# 获取 Loki 实际地址
curl -s "https://grafana.hellorobotaxi.top/api/datasources/uid/{datasource_uid}"
# 提取 url 字段即为 Loki Gateway 地址
```

### Step 2: 查询 AI Controller 日志（全局视角）

AI Controller 是任务的控制中枢，**必须第一个查**，它记录了完整生命周期。

```bash
# 查询 AI Controller 全量日志
QUERY='{namespace="<NS>", pod="<JOB_NAME>-ai-controller-0"}'
curl -s -G "<LOKI_URL>/loki/api/v1/query_range" \
  --data-urlencode "query=$QUERY" \
  --data-urlencode "start=<START_NS>" \
  --data-urlencode "end=<END_NS>" \
  --data-urlencode "limit=5000" \
  --data-urlencode "direction=forward"
```

**关键提取信息**：
- 任务规模：节点数 x GPU 数
- 阶段转换时间线：init → training → failed
- 失败原因：`failure_reason` 字段
- Pod → 主机名映射（从 `/etc/hosts` 写入日志中提取）
- VCJob 名称

### Step 3: 查询崩溃窗口日志（精准定位）

从 AI Controller 日志中确定崩溃时间，查前后 5 分钟的所有 worker 日志：

```bash
# 所有 worker 和 master 的日志
QUERY='{namespace="<NS>", pod=~"<VCJOB_NAME>-.*"}'
# 过滤掉 C++ stack frame 噪音，保留有意义的错误信息
```

**分析要点**：
1. **NCCL 超时**：提取 SeqNum、OpType、Timeout 值、受影响的 rank 列表
2. **首个退出进程**：`exitcode: 1` 中最早的 `time` 字段和 `host` = 根因节点
3. **错误传播链**：哪个 worker 先报错 → 其他 worker 级联失败的时间顺序
4. **CUDA 错误**：`unrecognized error code` 通常是连锁反应，不是根因

### Step 4: 查询 K8s Events（GPU 硬件证据）

通过 `hpc-event-exporter` 查询节点级别的 GPU 硬件事件：

```bash
# 查 GPU Xid/SXid 错误事件
QUERY='{namespace="hpc-system", app="hpc-event-exporter"} |~ "Xid|SXid|NvidiaXID|NvidiaSXID|GPUHealthy"'

# 查特定任务的所有事件
QUERY='{namespace="hpc-system", app="hpc-event-exporter"} |~ "<JOB_NAME>"'

# 查嫌疑节点的所有事件
QUERY='{namespace="hpc-system", app="hpc-event-exporter"} |~ "<ECS_ID>|<HOSTNAME>"'
```

**GPU 错误类型速查**：

| 错误 | 含义 | 严重性 |
|------|------|--------|
| Xid 13 | GPU 页面错误 | 可恢复 |
| Xid 31 | GPU 内存 ECC 错误（不可恢复） | 需要 reset |
| Xid 43 | GPU 被重置 | 需排查原因 |
| Xid 45 | GPU 预检失败 | 硬件问题 |
| Xid 48 | 双 bit ECC 错误 | 硬件问题 |
| Xid 63 | ECC row remapping 失败 | 需要更换 |
| Xid 64 | ECC row remapping 已满 | 需要更换 |
| **Xid 79** | GPU 不可用 | 硬件故障 |
| **Xid 94** | GPU contained ECC 错误 | GPU 计算可能出错 |
| **Xid 137** | GPU 显存页面退役 | 显存硬件损坏 |
| SXid 12028 | NVSwitch egress PRIV error | NVLink 链路异常 |
| SXid 12032 | NVSwitch ingress error | NVLink 链路异常 |

### Step 5: 构建因果链 & 输出结论

将所有证据串联成时间线因果链：

```
[根因] 某节点 GPU/NVSwitch 硬件故障
  → [传播] NCCL 集合操作无法完成，其他 rank 等待
  → [超时] 600s 后 NCCL Watchdog 触发超时
  → [崩溃] 首个进程退出 (exitcode: 1)
  → [级联] torch.distributed 发现子进程失败，发 SIGTERM
  → [连锁] GPU 清理过程触发 CUDA error (Xid 94/137)
  → [终结] AI Controller 检测到失败，标记任务 failed
```

## 输出格式

### 任务概况表
| 项目 | 值 |
|---|---|
| 任务名 | ... |
| 规模 | N节点 x M GPU |
| 训练脚本 | ... |
| 持续时间 | ... |

### 时间线表
| 时间 | 事件 | 来源 |
|---|---|---|
| ... | ... | Controller / Worker / Event |

### 根因分析
- 根本原因（一句话）
- 关键证据列表
- 受影响节点/GPU 清单
- GPU Xid/SXid 错误详情

### 建议
- P0（立即）：节点隔离、报修
- P1（短期）：训练配置优化
- P2（长期）：架构改进

## Loki API 使用要点

1. **时间戳格式**：纳秒级 Unix 时间戳（Python: `int(dt.timestamp()) * 10**9`）
2. **方向**：`direction=forward`（正序）或 `backward`（倒序）
3. **Limit**：单次最多 5000 行，超过需要分页
4. **正则**：LogQL 支持 `|~` 正则过滤，`|=` 精确匹配
5. **JSON 解析**：event-exporter 输出 JSON，可用 `| json` 管道解析
6. **Pod 正则**：用 `pod=~"prefix.*"` 匹配一组 Pod
7. **多条件**：`{label1="v1", label2=~"v2.*"} |~ "pattern1" |~ "pattern2"`

## 常见故障模式

### 模式 1: 单节点 GPU 故障 → NCCL 超时
- 特征：一个节点的 Xid 错误早于其他节点
- 证据：只有一个节点的 SXid/Xid 在超时之前

### 模式 2: 多节点 NVSwitch 级联故障
- 特征：所有节点同时出现相同 GpuIds 的 Xid
- 证据：SXid 12028 在多节点的不同 Link 上同时出现
- 原因：通常是 IB 交换机/NVSwitch 固件 bug 或供电问题

### 模式 3: 网络闪断 → NCCL 重连失败
- 特征：SeqNum 一致（同一个集合操作），所有 rank 同时超时
- 证据：没有 Xid 错误，只有 NCCL 超时
- 原因：IB 链路抖动或交换机重启

### 模式 4: 存储 hang → DataLoader 卡住 → NCCL 超时
- 特征：只有部分 rank 超时，其他正常退出
- 证据：日志中有 IO 相关的等待或超时
- 原因：CPFS/Alluxio 存储性能问题

### 模式 5: 用户代码 bug → 单 rank 退出 → 全局超时
- 特征：exitcode=1 带有 Python traceback
- 证据：首个失败 rank 有完整异常栈
- 原因：代码 bug（除以零、shape mismatch、assertion 等）

## 节点映射

阿里云 H20 集群中，节点有三种 ID：
1. **K8s Node 名**：`hpc-prod-al-sh01.10.168.x.x`（VPC IP 拼接）
2. **ECS ID**：`e01-cn-xxxxxxxx`（阿里云实例 ID）
3. **主机名**：`hpc-prod-al-sh01-h20-141-XXXX`（机房物理编号）

AI Controller 日志中的 `/etc/hosts` 条目包含 IP → 主机名映射。
K8s Event 中的 `source.host` 是 ECS ID。
需要交叉关联来确定同一台机器。
