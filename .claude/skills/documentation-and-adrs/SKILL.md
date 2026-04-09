---
name: documentation-and-adrs
description: 指导何时以及如何编写架构决策记录（ADR）、inline 注释、README 和 CHANGELOG。适用于架构决策、重大设计变更、或需要为后人记录"为什么"的场景。
---

# 文档与架构决策记录

## 概述

代码告诉你 **What**（做什么），注释告诉你 **Why**（为什么），ADR 告诉你 **Why not the alternatives**（为什么不选其他方案）。三者互补，不可替代。

## 适用场景

- 做出了重大架构或技术选型决策
- 多个候选方案之间做了权衡取舍
- 修改了现有架构（尤其是不可逆的改动）
- 被问到"为什么当时这样设计"而答不上来
- 新人入职需要理解系统演进历史

**不适用：** 纯实现细节、bug 修复、小范围重构。

## 架构决策记录（ADR）

### 何时写 ADR

```
ADR 决策树：
  这个决策影响多个服务/模块吗？ → 是 → 写 ADR
  这个决策难以逆转吗？ → 是 → 写 ADR
  团队成员对此有不同意见吗？ → 是 → 写 ADR
  半年后有人会问"为什么这样做"吗？ → 是 → 写 ADR
  以上都不是？ → 代码注释 + commit message 就够了
```

### ADR 模板

```markdown
# ADR-NNN: [决策标题]

## 状态
[Proposed | Accepted | Deprecated | Superseded by ADR-XXX]

## 背景
[什么情况下需要做这个决策？当前系统的约束是什么？]

## 决策
[选择了什么方案。用一两句话概括。]

## 方案比较

| 维度 | 方案 A | 方案 B (chosen) | 方案 C |
|------|--------|-----------------|--------|
| 复杂度 | 低 | 中 | 高 |
| 性能 | ... | ... | ... |
| 可维护性 | ... | ... | ... |

## 影响
[这个决策带来的正面和负面后果。]

## 参考
[相关文档、issue、RFC 链接]
```

### ADR 约定

- 存放位置：`docs/adr/` 或项目 Wiki
- 编号递增：`ADR-001`, `ADR-002`, ...
- **不要删除 ADR**——弃用的标记为 Deprecated 并链接到替代方案
- 每个 ADR 聚焦一个决策

## Inline 注释

### 何时写注释

```
好注释 = 解释 Why（为什么这么做）
坏注释 = 解释 What（代码在做什么）
```

```go
// 好：解释非显而易见的意图
// K8s API 限制单次 list 返回 500 条，分页获取避免超时
for {
    pods, err := client.CoreV1().Pods(ns).List(ctx, opts)
    ...
}

// 好：解释约束
// Replica 数量上限 10 是因为每个副本独占一块 GPU，
// 单节点最多 8 卡 + 允许跨 2 节点调度
const MaxReplicas = 10

// 坏：复述代码
// 如果 err 不为空，返回错误
if err != nil {
    return err
}

// 坏：注释已经过时，和代码不符
// 发送邮件通知用户
sendSlackNotification(user, msg) // 早就改成 Slack 了
```

### TODO / FIXME 约定

```go
// TODO(username): 描述 + 关联 issue
// TODO(zhangsan): 支持 GPU 亲和性调度 #1234

// FIXME(username): 描述已知问题
// FIXME(lisi): 并发场景下可能有竞态，需要加锁 #5678
```

## README

每个子项目必须有 README，至少包含：

```markdown
# 项目名

一句话描述这个项目做什么。

## 快速开始

\```bash
# 如何运行
make run
# 如何测试
make test
\```

## 架构

[简要描述模块结构，或链接到架构图]

## 配置

[关键环境变量和配置项]
```

## CHANGELOG

- 面向用户的变更才记录（不记录内部重构）
- 遵循 [Keep a Changelog](https://keepachangelog.com/) 格式
- 分类：Added / Changed / Fixed / Removed / Security

## 反合理化

| 借口 | 现实 |
|------|------|
| "代码即文档" | 代码说的是 What，不是 Why。三个月后你自己也忘了为什么选了方案 B。 |
| "写文档浪费时间" | 花 15 分钟写 ADR vs 花 2 小时在 Slack 反复解释同一个决策。 |
| "需求老变，文档马上就过时" | ADR 记录的是决策，不是需求。决策被推翻时标记 Deprecated，不删除。 |
| "注释太多影响阅读" | 坏注释影响阅读（复述代码的），好注释拯救阅读（解释为什么的）。 |
| "大家都知道为什么这么做" | 直到团队换了一半人。知识只在脑子里 = 不存在的知识。 |

## Red Flags

- 做了重大架构决策但没有任何书面记录
- ADR 只记录了"选了什么"而没有"为什么不选其他的"
- 注释和代码行为不一致（比代码 bug 更危险）
- README 里的"快速开始"步骤实际跑不通
- 所有 TODO 都没有关联 issue 号或负责人
- CHANGELOG 半年没更新

## 验证清单

- [ ] 重大决策有对应的 ADR
- [ ] ADR 包含方案比较和取舍理由
- [ ] Inline 注释只解释 Why，不复述 What
- [ ] TODO/FIXME 关联了 issue 号
- [ ] README 的"快速开始"步骤实际可执行
- [ ] 弃用的 ADR 标记了状态和替代方案链接
