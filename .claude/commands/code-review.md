---
description: 调用 code-reviewer agent 对未提交变更做安全与质量审查
---

调用 **code-reviewer** agent（`.claude/agents/code-reviewer.md`）审查当前未提交的变更。

agent 会自动按文件类型路由到 Go 或 Frontend 专项清单，输出分级问题报告（CRITICAL/HIGH/MEDIUM），并给出 Approve / Warning / Block 结论。
