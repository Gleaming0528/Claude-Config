---
name: hpc-weekly-report
description: 采集 git 提交、Grafana GPU 数据、预算数据和发布记录，生成团队周报。适用于写周报、生成周报、本周总结。
---

# HPC 超算平台团队周报

## 定位

这是**给老板看的团队周报**，不是技术 changelog。
老板关心三件事：**钱花得对不对、资源用得好不好、团队在做对的事**。

周报结构：
1. **TL;DR**（顶部 3 秒区）：重点交付分点 + 核心指标 + 下周看点 + 本周专项排查（如有）
2. 关键指标（资源 + 预算 + 发布，带 Q2 目标对标）
3. 本周交付（代码自动采集 + 人工补充，翻译为业务语言）
4. 外部合作（需用户补充进展）
5. 下周计划（分点分子弹，不写一大段）

## 执行流程

### 第一步：采集数据

```bash
cd <repo-root>/weekly-report
# 默认生成本周（ISO 当前周），dry-run 先验数
python3 generate.py --dry-run 2>&1

# 指定周 + 自动拉取最新代码（推荐用法）
python3 generate.py --week 2026-W16 --fetch --dry-run 2>&1

# 看起来没问题再正式生成，--force-md 会覆盖手写版谨慎使用
python3 generate.py --week 2026-W16 2>&1
```

自动采集维度：
- `git`：22+ 个仓库本周提交（按功能域分组，支持 git submodule `.git` 文件）
- `deploy`：deploy 仓库生产发布次数（按服务分组，含版本号）
- `gpu`：**Grafana API 实时查询**生产 Prometheus，按 ISO 周锚点采样，含本周 + 上周同期数据
- `budget`：预算执行数据（文件不存在时静默跳过，不影响周报生成）

CLI 参数：
- `--week YYYY-WNN`：指定 ISO 周，默认当前周
- `--fetch`：采集前并发 `git fetch` 所有业务仓库 + deploy 子仓库
- `--dry-run`：只打印 JSON 不落盘
- `--force-md`：强制覆盖已有 Markdown（会抹掉手写版，谨慎）

### 第二步：采集口径铁律（踩过的坑）

**口径必须与前端 `hpc-ui/src/pages/ResourceAudit/components/OverviewCards.tsx` 完全一致**——老板看前端看板看周报看到不同数字会立刻失去信任。

#### ① 过滤语义：`and on()` 不要 `* on() group_left()`

- ❌ `DCGM_FI_DEV_GPU_UTIL * on(namespace, pod) group_left() kube_pod_labels{...}`
  - 这是**标签注入语义**，会把所有 labels 展开到每个 DCGM series 上，对高基数 series 会让 VictoriaMetrics 触发 HTTP 422 "not enough memory"
  - 在 sh01（1400+ aijob 卡）上会**静默失败**导致整个集群利用率数据返回 0
  - 后果：加权平均被严重拉低，出现"利用率从 69% 跌到 59%"的假像
- ✅ `DCGM_FI_DEV_GPU_UTIL and on(namespace, pod) kube_pod_labels{...}`
  - **集合过滤语义**，只按 (namespace, pod) 存在性筛选，不注入标签
  - VM 内存友好，不会触发 422
  - 前端 OverviewCards 用的就是这个

#### ② 利用率：`avg_over_time([7d:1h])` 主查 + 窗口降级兜底

```
avg_over_time((avg(max by (node, UUID) (DCGM_FI_DEV_GPU_UTIL and on(namespace, pod) kube_pod_labels{...})))[7d:1h])
```

即便用 `and on` 语义，sh01 偶尔还会在 7d 窗口 422。必须做降级链：
**7d → 3d → 1d → 6h → instant**（不带窗口的裸查询一定能过）。
`_query_util_with_fallback` 已实现该逻辑，新增指标沿用。

#### ③ 调度率：instant 查询，不做窗口

前端调度率就是"当下已调度 / 卡池总量"，不需要窗口均值。窗口只适合 utilization。

#### ④ 训练卡型号过滤

训练卡 = `H20 | H20-3e | A800 | A100 | H100 | H800`；其他（5880/4090/L40/T4/PPU）计为推理卡。
和前端 `isTrainingGpu` 模式完全对齐，不要自己改列表。

#### ⑤ vGPU 切片坑（5880 / L20 等 NVIDIA GRID 场景）

- DCGM 在 vGPU 模式（如 48Q、16Q）下把**每个 vGPU 片当成独立 UUID 上报**
- `count by (node, UUID)` 会把 1 张物理卡数成 N 张（N = 每卡切片数）
- 这会让"GPU 总量 / 推理卡总量"虚高数倍
- **识别方法**：modelName 带 `-48Q` / `-16Q` / `-8Q` / `-Ada-XXQ` 后缀的就是 vGPU
- **处理方法**（当前还未内建，需要专项改造）：
  - 按 `count by (node) (count by (node, UUID) (...))` 得到节点数
  - 按 modelName 的切片规格反推物理卡数
  - 或用 `kube_node_labels{label_nvidia_com_gpu_product=...}` 以节点为物理单位统计
- **误占用陷阱**：`monitoring/dcgm-exporter`、`node-exporter` 等 DaemonSet 只读 GPU metric 但 pod label 会匹配 `and on(namespace,pod)` 过滤，被误计为"占用"。过滤时加 `label_app_kubernetes_io_name!~"dcgm-exporter|node-exporter|.*-daemon"`

### 第三步：向用户收集不可自动化的信息

用 AskQuestion 工具收集（代码采集不到的）：

**必须收集：**
1. 外部合作本周进展（阿里云/百度云/蚂蚁云等）
2. 重大业务事件（生产任务量级、外部里程碑）
3. 下周重点（用户视角的优先级）

**可选收集：**
- 集群 / 资源归属归类（`hpc-prod-al-*` = 阿里云上海，`hpc-prod-bd-*` = 百度云，别记错）
- 外部交付节奏（"下周再交付 XX 卡"这类关键数字）
- 重大故障 / 事件

**集群前缀速查表：**
- `al-sh##` = 阿里云上海
- `al-sh03` / `al-sh##` 新集群 = 视 kustomization 归属判断
- `bd-su##` = 百度云苏州
- `bd-*` = 百度云其他
- `test-*` = 测试环境（不写进生产周报）

### 第四步：AI 分析与提炼

**commit 合并规则：**
1. 相同仓库+相同功能的重复提交合并为一条
2. revert + 原始提交对消，只保留最终状态
3. chore/lint 类提交不进入周报正文
4. 按业务影响力合并为 **3-5 个"重点交付"**（不超过 5 个），每个主项下 3-6 条 bullet
5. 跨仓库联动特性合并为统一方向（如"A6O 投产"横跨 job-controller + studio-api + ui，合并成一条）

**业务语言翻译（核心规则）：**
- 每个功能点回答"对业务意味着什么"，而非"技术上做了什么"
- 消灭所有需要读者"翻译"的内部技术名词（VCJob、podSpecPatch、syncStatus、AAD、CRD）
- 保留有业务共识的技术名词（Pipeline、GPU、NCCL、HF、ArgoCD、FIFO、vGPU）
- 用「支持」「上线」「打通」「加固」「投产」，不用「重构」「迁移」「注入」

翻译示例：
- 技术版：`动态优先级全链路落地（Label 化迁移 + VCJob 调度继承 + 前端筛选）`
- 老板版：`训练任务优先级体系上线——紧急任务可自动抢占低优先级资源，业务团队可按 P0-P3 管理训练队列`

**关键指标状态判断：**
- GPU 数据自动含本周 + 上周同期（`prev_week`）
- "状态"列不是重复数字，而是一句判断：距目标多远、变化原因、下一步
- Q2 目标线：训练利用率 75~80%、开发空间人均 GPU <1.5 卡/人
- **数字突变（±5pp 以上）必须先问"是真变化还是口径问题"**：本周差点翻车就是 sh01 422 导致利用率假跌 10%，一定要交叉验证前端看板

### 第五步：输出格式要求

**TL;DR 分点结构（新规）：**

```markdown
## TL;DR

**三大重点交付**

1. **XXX 正式上线**：一句话说结果 + 关键数字变化
2. **YYY 投产**：...
3. **ZZZ 攻坚**：...

**核心指标**

- 训练利用率 **XX%（±Xpp）**——一句话解读
- 开发空间 XX 人、利用率 XX% → XX%
- 生产发布 XX 次，覆盖 N 大方向

**本周专项排查**（如有）

- XXX 根因 + 影响范围 + 下一步锚点

**下周看点**

- 最关键的 1~2 个外部交付 / 里程碑节点
```

**老板 30 秒规则：**
- 老板第一眼看 TL;DR → 判断"这周状态好不好"
- 老板第二眼看关键指标表 → 哪些在轨、哪些偏了
- 这两部分写好，周报就及格了，后面是给追问准备的

**严禁：**
- 顶部写一大段 100+ 字的连贯中文（老板不会读）
- "按仓库明细"大段列表（40 条 commit 全部罗列没人看）
- 技术动作堆砌，不给业务影响

### 第六步：写入文件 + 验证

1. 写 `weekly-report/reports/YYYY/W{nn}.md` — 精炼版周报
2. 对齐数字时，至少跑 2~3 次 `collect_gpu_metrics` 看是否稳定（不稳定说明有 422 / 抖动，要修）
3. 跟前端 ResourceAudit 看板对数字，差 >3pp 说明口径不一致
4. git 提交时单独提 weekly-report 改动，便于后续回滚或追溯

## 专项排查模式

当遇到"某个指标异常 / 某类资源调度紧张"类问题，周报要包含独立的"专项排查"章节：

1. **背景一句话**：被排查对象 + 疑似问题（别写成结论，写成假设）
2. **事实数据**：从 Prometheus 直接拉出来的原始数字，别手工算
3. **根因分层**：`口径错误` / `拓扑误报` / `业务实效问题` 分开列，不要糊在一起
4. **影响范围明确**：哪些指标受污染、哪些不受影响
5. **下一步锚点**：5 步以内具体动作（谁做、改哪个文件、验收标准），不要喊口号

**排查永远先问"是不是口径错了"**：80% 的"异常"是指标定义 / vGPU / DaemonSet 这类口径问题，不是真的业务出事。

## 上下文参考

- 上周周报：查找 `weekly-report/reports/` 下最近一期
- 预算计划：`cost_billing/2026_预算计划.md`（不存在时静默跳过）
- 前端口径权威：`hpc-ui/src/pages/ResourceAudit/components/OverviewCards.tsx`
- 采集器：`weekly-report/collectors/grafana.py`（修改口径要先改这里再改周报文字）
- 所有文件基于仓库根目录

## 质量标准

1. **老板 30 秒规则**：TL;DR + 指标表 = 老板能判断本周状态
2. **commit 压缩比 >= 3:1**（如 113 条 → 3-5 个重点交付）
3. **数字必须与前端对齐**：差 >3pp 一律视为 bug，不是"估算口径不同"
4. 不允许出现 commit hash、author、邮箱
5. 不允许原样复制 commit message
6. 不允许出现内部技术名词（VCJob、podSpecPatch、CRD 等）未翻译
7. 外部合作必须有具体进展 + 下步动作，不能只写状态词
8. 关键指标"状态"列必须是判断句，不是数字复读
9. **下周计划必须分点分子弹**，不要写连贯段落
10. 周报总长度 100~150 行（含专项排查），不含专项 60~100 行
11. 读者是非技术管理层
