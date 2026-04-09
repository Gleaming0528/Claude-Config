---
description: 增量修复构建错误（Go + TypeScript）
---

# Build and Fix

增量修复构建错误，支持 Go 和 TypeScript 项目：

1. **检测项目类型**并运行构建：
   - Go 项目：`go build ./...`
   - 前端项目：`npm run build` 或 `pnpm build`

2. **逐个修复错误**：
   - 按文件分组，按严重度排序
   - 展示错误上下文（前后 5 行）
   - 提出修复方案 → 应用 → 重新构建 → 验证

3. **停止条件**：
   - 修复引入新错误
   - 同一错误尝试 3 次仍失败
   - 用户要求暂停

4. **输出报告**：已修复 / 剩余 / 新引入的错误数量

Fix one error at a time for safety!
