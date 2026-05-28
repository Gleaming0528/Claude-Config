---
description: Restate requirements, assess risks, and create step-by-step implementation plan. WAIT for user CONFIRM before touching any code.
---

# Plan Command

This command invokes the **planner** agent to create a comprehensive implementation plan before writing any code.

## What This Command Does

1. **Restate Requirements** - Clarify what needs to be built
2. **Identify Risks** - Surface potential issues and blockers
3. **Create Step Plan** - Break down implementation into phases
4. **Wait for Confirmation** - MUST receive user approval before proceeding

## When to Use

Use `/plan` when:
- Starting a new feature
- Making significant architectural changes
- Working on complex refactoring
- Multiple files/components will be affected
- Requirements are unclear or ambiguous

## How It Works

The planner agent will:

1. **Analyze the request** and restate requirements in clear terms
2. **Break down into phases** with specific, actionable steps
3. **Identify dependencies** between components
4. **Assess risks** and potential blockers
5. **Estimate complexity** (High/Medium/Low)
6. **Present the plan** and WAIT for your explicit confirmation

## Example Usage

```
User: /plan 给训练任务添加自动 checkpoint 恢复功能

Agent (planner):
# Implementation Plan: 训练任务自动 Checkpoint 恢复

## Requirements Restatement
- 训练任务失败后自动检测最新可用 checkpoint
- 从最近的有效 checkpoint 恢复训练，无需用户手动干预
- 支持 DeepSpeed 和 PyTorch 原生 checkpoint 格式

## Implementation Phases

### Phase 1: Checkpoint 探测
- 在 Controller 中添加 checkpoint 路径探测逻辑
- 校验 checkpoint 完整性（文件大小、元数据一致性）
- 选择最新有效 checkpoint

### Phase 2: CRD 扩展
- Status 中增加 LastCheckpoint、RecoveryCount 字段
- 定义恢复策略（最大重试次数、退避间隔）

### Phase 3: Reconciler 集成
- Failed → Pending 状态回退逻辑（携带 checkpoint 路径）
- 注入恢复环境变量到 Pod spec

## Risks
- HIGH: checkpoint 损坏导致恢复后立即再次失败（需要最大重试限制）
- MEDIUM: 多节点 checkpoint 一致性校验耗时

## Estimated Complexity: MEDIUM

**WAITING FOR CONFIRMATION**: Proceed with this plan? (yes/no/modify)
```

## Important Notes

**CRITICAL**: The planner agent will **NOT** write any code until you explicitly confirm the plan with "yes" or "proceed" or similar affirmative response.

If you want changes, respond with:
- "modify: [your changes]"
- "different approach: [alternative]"
- "skip phase 2 and do phase 3 first"

## Integration with Other Commands

After planning:
- Use `/build-fix` if build errors occur
- Use `/code-review` to review completed implementation

## Related Agents

This command invokes the `planner` agent located at:
`.claude/agents/planner.md`
