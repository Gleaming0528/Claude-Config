---
name: training-log-diagnosis
description: 分析 AI/ML 训练日志，诊断训练失败、训练卡住、性能下降、收敛异常。适用于排查训练 crash、梯度爆炸、GPU 利用率下降、NCCL heartbeat 超时。
---

# Training Failure Diagnosis

## Overview

Systematically diagnose AI/ML training failures across the full spectrum: crashes with errors, silent hangs, performance degradation, and convergence anomalies. Combine log analysis, monitoring data, and live system diagnostics.

**Core principle:** Logs are ONE information source, not the only one. When logs are silent, the system itself is the log.

## Phase 1: Triage

Before any analysis, classify the failure and inventory available information.

### 1.1 Failure Classification

| Type | Signature | Primary Diagnostic Path |
|------|-----------|------------------------|
| **Crash** | 日志有 traceback / error / signal | → Log Pattern Matching (Phase 3A) |
| **Silent Hang** | 日志停止更新，无错误信息 | → Live Diagnostics (Phase 3B) |
| **Performance Degradation** | 训练变慢但没崩，吞吐下降 | → Resource & Metric Analysis (Phase 3A + 3B) |
| **Convergence Anomaly** | 没报错但 loss 不下降或发散 | → Training Dynamics Analysis (Phase 3A) |

### 1.2 Context Gathering

Answer these before diving in:

1. **Framework & parallelism?** PyTorch / DeepSpeed / Megatron / FSDP / DDP / JAX...
2. **Scale?** 单卡 / 单机多卡 / 多机多卡（几个节点 × 几张卡）
3. **Final status?** Failed / Running(hung) / Completed(wrong result)
4. **Duration?** 跑了多久？预期跑多久？
5. **Crash position?** 启动 / 数据加载 / 训练中 / Eval / Checkpoint save / 结束阶段

### 1.3 Information Source Inventory

Check what's available — more sources = faster diagnosis:

```
[ ] 训练日志 (stdout/stderr)
[ ] 监控图表 (Grafana / TensorBoard / W&B)
[ ] Pod/进程还活着？（可以 exec 进去做 live 诊断）
[ ] 多节点日志？（只有异常节点的还是全部节点的）
[ ] 系统日志访问权限？（dmesg / syslog）
```

**Decision rule:** 如果日志有明确错误 → Phase 2A。如果日志沉默或信息不足 → Phase 2B。两者不互斥，复杂场景需要组合。

## Phase 2A: Log-Based Timeline Reconstruction

适用于日志信息充足的场景。

### 时间线骨架

```
Start → Init → Data Loading → Training Loop → [Event] → ...
                                   ↓
                             Epoch/Step 推进
                             Loss 轨迹
                             Grad norm 轨迹
                             Checkpoint saves
                             Eval phases
```

识别关键转折点：
- Normal → Abnormal（指标突变）
- Training → Eval（阶段切换）
- Running → Silent（日志中断）
- 某个操作的最后一条日志（这通常是 hang point）

### 指标量化

| Metric | Normal | Warning | Critical |
|--------|--------|---------|----------|
| grad_norm | 稳定, < 10 | > 50 | > 100 或瞬间 >10x |
| loss | 下降趋势 | 平台期 > 10 epochs | 突然 >2x 跳变 |
| lr | 按 schedule 变化 | 当前任务偏高 | — |
| memory | 稳定 | 缓慢增长 | OOM |
| throughput | 稳定 | 波动 >20% | 骤降 >50% |
| eval metric | 提升 | 停滞 | 极低 (< 0.1) |

## Phase 2B: Live System Diagnostics

适用于日志沉默、Pod 仍存活的场景。**进入 Pod 前确保有集群访问权限（proxy / kubeconfig）。**

### 诊断清单（按优先级执行）

**1. GPU 状态**
```bash
nvidia-smi --query-gpu=index,utilization.gpu,power.draw,temperature.gpu,ecc.errors.corrected.volatile.total,ecc.errors.uncorrected.volatile.total,clocks_throttle_reasons.active --format=csv
```
关注点：
- 利用率 vs 功耗是否匹配（100% 利用率 + 空转功耗 = NCCL spin-wait）
- ECC 错误计数
- 温度和降频

**2. 系统日志**
```bash
dmesg -T | grep -iE 'mce|hardware error|oom|nfs|fuse|ioerr|EIO|stale|timed out|reset|xid|nvrm'
```
关注点：
- MCE / Hardware Error → 硬件退化
- OOM → 内存不足
- NFS / FUSE / EIO → 存储故障
- Xid / NVRM → GPU 硬件故障

**3. 进程状态**
```bash
ps -eo pid,ppid,stat,%cpu,rss,etimes,args | grep -E 'python|train|torchrun'
```
```bash
cat /proc/<PID>/stack   # 查看内核栈，确认阻塞在哪个系统调用
```
关注点：
- D state（不可中断睡眠）→ I/O 阻塞
- futex_wait → 锁等待 / NCCL barrier
- 进程数是否与预期 rank 数一致

**4. 存储健康快测**
```bash
time dd if=/dev/zero of=<shared_path>/.io_test bs=1M count=100 oflag=direct 2>&1
time ls <shared_path>/ > /dev/null 2>&1
```
关注点：写入吞吐 < 10 MB/s 或 ls 延迟 > 1s 为异常

**5. 网络健康**（多节点场景）
```bash
cat /proc/net/tcp | wc -l   # TCP 连接数
```
关注点：NCCL socket 连接是否存在、是否有大量 CLOSE_WAIT

### 多节点必做：跨节点对比

分布式训练至少检查 3 个节点：master + 异常节点 + 一个正常节点。对比同一项指标，差异即线索。

## Phase 3: Pattern Library

### Category A: Training Dynamics（训练动态）

**A1: Gradient Explosion**
- Signal: grad_norm 瞬间飙升 >10x
- Consequence: Loss 跳变后不恢复
- Root cause: LR 过高 / 异常数据样本 / 数值不稳定
- Fix: grad_clip, 降 LR, 检查触发点附近的数据

**A2: Loss Plateau After Spike**
- Signal: Loss 跳变后长期持平
- Implication: 模型参数已损坏，clip 无法回溯修复
- Fix: 从 spike 前的 checkpoint 恢复，加 grad_clip + 降 LR

**A3: NaN / Inf Propagation**
- Signal: loss=nan 或 grad_norm=inf
- Consequence: 后续所有计算无意义
- Fix: AMP GradScaler, grad_clip, 降 LR, 检查数据归一化

**A4: Convergence Failure**
- Signal: Loss 长期不下降，或下降极慢
- Root cause: LR 不匹配 / 数据问题 / 模型架构问题 / 初始化问题
- Diagnosis: 对比已知正常训练的 loss 曲线，检查 LR schedule

### Category B: Distributed（分布式）

**B1: NCCL Heartbeat Timeout**
- Signal: Rank 0 正常，其他 rank 报 heartbeat timeout
- Mechanism: 常见于只有 rank 0 做 eval/save 时，其他 rank 空等超时
- Fix: `TORCH_NCCL_HEARTBEAT_TIMEOUT_SEC=1800`, 加速 eval, 所有 rank 参与

**B2: Distributed Barrier Deadlock**
- Signal: 所有日志同时沉默，无错误。进程阻塞在 futex_wait。GPU 功耗空转但利用率可能 100%（NCCL spin-wait）
- Mechanism: 某 rank 在集体操作（all-reduce / barrier / checkpoint save）中卡住 → 全体死锁
- Causes: 单 rank I/O 卡住 / 单 rank OOM 被 kill / 网络分区
- Fix: NCCL heartbeat timeout, checkpoint 加超时/重试, 错误处理让单 rank 失败不拖全体

**B3: Checkpoint Save Deadlock**
- Signal: 最后日志是 "Saving checkpoint"，checkpoint 目录为空或不完整
- Mechanism: 分布式 checkpoint（FSDP/DeepSpeed）需所有 rank 参与写入 + barrier 同步。一个 rank 写入卡住 → 全体等待 → 死锁
- Diagnosis: 检查 checkpoint 目录内容、各 rank 日志最后条目、存储 I/O
- Fix: save 操作加超时, 各 rank 先写本地再同步, 异步 checkpoint

**B4: Rank Failure / Straggler**
- Signal: 某些 rank 日志落后或停止，其他 rank 最终超时
- Mechanism: 单 rank 的 GPU/CPU/存储问题导致该 rank 变慢或死亡
- Diagnosis: 跨节点对比 step 进度和资源使用
- Fix: 弹性训练（torch elastic）, 异常节点自动剔除

### Category C: Resource（资源）

**C1: GPU OOM**
- Signal: `CUDA out of memory`, `RuntimeError: ...tried to allocate...`
- Fix: 降 batch size, 启用 gradient checkpointing, 混合精度, offload

**C2: CPU / Host OOM**
- Signal: 进程被 kill（dmesg 有 oom_kill_process），或突然消失无日志
- Causes: DataLoader worker 内存泄漏, 数据预处理缓存膨胀
- Diagnosis: `dmesg | grep oom`, 检查 cgroup memory limit vs RSS
- Fix: 减少 num_workers, 限制 prefetch, 检查数据 pipeline 内存使用

**C3: Disk Full / Quota**
- Signal: `No space left on device`, `Disk quota exceeded`
- Diagnosis: `df -h`, `du -sh` 检查 checkpoint / log / tmp 目录
- Fix: 清理旧 checkpoint, 减少保存频率, 扩容

**C4: Shared Memory Insufficient**
- Signal: `ERROR: Unexpected bus error encountered in worker`
- Mechanism: DataLoader 多进程用 /dev/shm 做 IPC，默认 64MB 不够
- Fix: `--shm-size` 或 `--ipc=host`

### Category D: Infrastructure（基础设施）

**D1: Hardware Degradation (MCE / DIMM / ECC)**
- Signal: dmesg 有 `Machine Check Exception`, `Hardware Error`, memory scrubbing errors
- Severity: CE（Correctable）可观察；UE（Uncorrectable）需立即处理
- **Key:** 注意时间线！硬件错误可能是 hang 的原因，也可能是独立并发问题。先确认时序关系再下结论
- Fix: CE 监控频率，UE 立即 cordon 节点 + 更换硬件

**D2: GPU Hardware Fault**
- Signal: dmesg 有 `Xid` 错误（尤其 Xid 48/63/79）, nvidia-smi 有 retired pages
- Consequence: GPU 计算结果可能错误（silent data corruption）或 GPU hang
- Fix: 检查 retired pages 数量, 严重时更换 GPU

**D3: Storage I/O Stall**
- Signal: 训练在 I/O 密集操作（数据加载、checkpoint save）时卡住。dmesg 可能有 NFS/FUSE 超时。dd 写入吞吐异常低
- **Key:** 瞬时抖动可能不留 dmesg 记录（尤其 FUSE），只能通过排除法推断
- Fix: 存储侧开启慢请求日志, checkpoint 写入加超时, 数据预加载到本地 SSD

**D4: Network Disruption**
- Signal: NCCL 超时, `Connection reset`, `No route to host`
- Causes: 交换机故障 / 网卡 flapping / IB 链路降级
- Diagnosis: 检查 NCCL 日志（需 `NCCL_DEBUG=WARN`）, IB 端口状态
- Fix: 重启 NCCL, 检查网络拓扑和链路状态

### Category E: Lifecycle（生命周期）

**E1: Startup Failure**
- Signal: 进程启动后立即退出，import 错误, 环境不兼容
- Fix: 检查 CUDA / PyTorch / 驱动版本兼容性, 依赖完整性

**E2: Data Loading Stall**
- Signal: 训练开始前长时间无输出，或 DataLoader worker 全在 D state
- Causes: 数据路径不可达, 元数据文件过大, 存储慢
- Fix: 预热数据缓存, 检查数据路径可达性, 减少 worker 数

**E3: Post-Training Crash**
- Signal: 最终 checkpoint 已保存 → eval/save 阶段崩溃
- Implication: 训练数据未丢失，checkpoint 可用
- Fix: 修复后处理逻辑，checkpoint 可直接复用

## Phase 4: Cross-Validation

诊断不是找到一个可疑点就结束，需要交叉验证。

### 时间线对齐

将多个信息源的事件按时间排列在同一条轴上：

```
02:15:00  [log]   master-0: "Saving checkpoint..."
02:15:00  [log]   所有 rank 日志停止
02:15:xx  [storage] (假设) 存储出现瞬时抖动
06:17:00  [dmesg] worker-1: MCE Hardware Error 开始
06:42:00  [log]   master-0: 最后一条日志出现
09:00:00  [grafana] GPU 利用率从 100% 跌至 0%
```

**先发事件是原因候选，后发事件可能是结果或独立问题。**

### 假设检验

```
假设: "DIMM 故障导致 hang"
  ↓ 检查: MCE 时间 06:17 > Hang 时间 02:15
  ↓ 结论: 时间线不支持，排除

假设: "存储瞬时抖动导致 checkpoint 死锁"
  ↓ 检查: Hang 点恰在 checkpoint save
  ↓ 检查: Checkpoint 目录为空
  ↓ 检查: 当前存储正常（抖动已恢复）
  ↓ 检查: dmesg 无存储错误（FUSE 慢请求不记录 dmesg）
  ↓ 结论: 不能确认也不能排除，标记为 suspected
```

对每个假设，寻找：
- **支持证据**（至少 2 条才可 confirm）
- **反驳证据**（1 条即可 exclude）
- **无法判断**→ 标记 suspected 并说明需要什么额外信息才能确认

## Phase 5: Report Structure

```
1. 概况 (Overview)
   - 任务类型、框架、规模、持续时间

2. 根因 (Root Cause)
   - [Confirmed] 有充分证据支持的结论
   - [Suspected] 证据不足但最可能的推断，注明缺什么证据

3. 关联问题 (Related Issues)
   - 不是根因但需要处理的问题（如独立的硬件退化）

4. 基础设施状态 (Infrastructure)
   - 硬件、存储、网络的健康状态

5. 修复建议 (Recommendations)
   - P0: 必须立即处理（止血）
   - P1: 应该处理（防止复发）
   - P2: 建议处理（长期改善）
   每条建议附具体操作或配置
```

## Key Principles

| Principle | Description |
|-----------|-------------|
| 先分诊再深入 | 不同故障形态走不同路径，别所有问题都 grep error |
| 日志沉默不等于没问题 | Silent hang 是最难排查的故障，需要 live diagnostics |
| 时间线是因果的骨架 | 先发 ≠ 原因，但后发一定不是原因 |
| 跨节点对比是分布式诊断的核心 | 差异即线索 |
| 区分 confirmed 和 suspected | 对证据不足的结论诚实标注 |
| 定位到止血方案，而非完美答案 | 有时 80% 确定就够做决策了 |

## Anti-Patterns

- 只 grep "error" 就下结论（crash 的错误信息常常是症状而非原因）
- 日志没报错就说"没问题"（silent hang 不会有错误日志）
- 只看一个节点的日志（分布式训练必须跨节点关联）
- 把时间上靠后的事件当成原因（先 hang 后 MCE ≠ MCE 导致 hang）
- 忽略 INFO 级别日志（训练指标、checkpoint 进度都在 INFO 里）
- 跳过 Phase 1 直接 grep pattern（误诊率极高）
- 忽视 GPU 功耗信息（利用率 100% + 空转功耗 = 假繁忙/spin-wait）
