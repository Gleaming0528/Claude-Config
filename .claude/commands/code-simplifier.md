---
description: 调用 code-simplifier agent 简化和优化最近修改的代码
---

调用 **code-simplifier** agent（`.claude/agents/code-simplifier.md`）对最近修改的代码执行结构性简化。

agent 会自动检测语言（Go / TypeScript），按 Chesterton's Fence 原则逐项优化控制流、错误处理、函数拆分，保持功能不变。
