---
name: code-quality
description: 代码质量感知 + GC 垃圾回收。被动模式自动浮出质量数据；主动模式（/gc）对子项目执行结构性清理。触发词包括 code quality, 代码质量, lint, cleanup, 清理代码, 技术债, tech debt, 质量评分, quality score, 代码体检, gc, 垃圾回收, refactor suggestion, 重构建议。
---

# Code Quality — 代码质量感知 + GC

两种工作模式：
- **感知模式**：在合适时机浮出质量数据，辅助决策（自动触发）
- **GC 模式**：对指定子项目执行结构性代码清理（用户说 `/gc <项目>` 触发）

## 感知模式（自动触发）

### 场景 A：质量概览

用户问"代码质量怎么样"、"质量评分" 时：

1. 读取 `docs/quality-score.md`
2. 按等级排序，高亮 D/F 级
3. 给出优先治理建议 + 引导到 GC 模式

```
当前质量状况：
  🟢 A 级：hpc-activity-api, hpc-go-sdk
  🟡 B 级：hpc-terminal-api, hpc-culling-service, hpc-event-exporter
  🟠 C 级：hpc-studio-api, hpc-auth-service, ...
  🔴 D/F 级：hpc-asset-api(20), hpc-devspace-controller(27), hpc-job-controller(36)

建议：/gc hpc-asset-api（147 条 lint、96 个大函数）
```

### 场景 B：单项目提示

用户在某个子项目中工作时，自然间隙简要提示（不超过 2 行）：

```
📊 hpc-studio-api 质量 C 级(50分) — 14 个大函数、10 处深嵌套
```

### 场景 C：Refactor 前后对比

重构完成后，快速对比：

```bash
cd <project>
golangci-lint run --enable-only funlen --max-issues-per-linter 0 ./... 2>&1 | grep -c "funlen" || echo 0
golangci-lint run --enable-only nestif --max-issues-per-linter 0 ./... 2>&1 | grep -c "nestif" || echo 0
```

```
重构效果：大函数 14→11(↓3) ✅ | 深嵌套 10→8(↓2) ✅ | 预估评分 50→59(+9) 🎉
```

### 场景 D：技术债追踪

读取 `docs/exec-plans/tech-debt.md` 展示进展。

### 感知约束

- 只读，不改代码
- 不主动刷新评分（直接用 `docs/quality-score.md`）
- 不在紧急修 bug 时弹提示（commit message 含 fix/hotfix 时静默）

## GC 模式（用户触发 `/gc <项目>`）

用户说 `/gc hpc-studio-api` 或 "清理 hpc-studio-api 代码" 时执行。

### 流程

**1. 诊断**

进入项目目录，运行四类检查：

| 检查项 | 命令 | 阈值 |
|--------|------|------|
| Lint 警告 | `golangci-lint run --max-issues-per-linter 0 --max-same-issues 0 ./...` | 全部 |
| 大函数 | `golangci-lint run --enable-only funlen --max-issues-per-linter 0 ./...` | >60 行 |
| 深嵌套 | `golangci-lint run --enable-only nestif --max-issues-per-linter 0 ./...` | >3 层 |
| 重复模式 | 搜索签名相似、逻辑重复的函数 | 手动判断 |

汇总为问题表：

| # | 文件 | 行号 | 类型 | 描述 |
|---|------|------|------|------|

**2. 分组 + 确认**

同一文件同一类问题归一组，单次最多 **10 组**。
优先级：Lint > 大函数 > 深嵌套 > 重复。
展示分组结果，**等待用户确认**再继续。

**3. 逐组修复**

每组：
1. 创建分支 `gc/<project>/<type>-<seq>`
2. 只做结构性重构（不碰业务逻辑）：
   - 大函数 → 提取子函数
   - 深嵌套 → early return / guard clause
   - Lint → 按 linter 建议修复
   - 重复 → 提取公共函数
3. 验证：`go build ./...` + `go vet ./...` + `go test ./...`
4. 失败 → 回滚，标记「需人工」
5. 通过 → 提交（不推送），格式 `refactor(<scope>): <描述>`

**4. 输出报告**

```
## GC 报告 — hpc-studio-api
| # | 分支 | 类型 | 文件 | 描述 | 状态 |
|---|------|------|------|------|------|
| 1 | gc/.../funlen-01 | 大函数 | handler.go | 拆分 CreateJob | ✅ |
| 2 | gc/.../nestif-01 | 深嵌套 | service.go | early return | ✅ |
| 3 | gc/.../lint-01 | lint | client.go | errcheck | ❌ 需人工 |
已修复 2/3 | 待人工 1/3
```

### GC 约束

- 不碰业务逻辑，只做纯结构重构
- 不推送，所有分支留在本地等 review
- 不跳测试，每组必须编译+测试通过
- 原子性，每个分支只修一类问题
- 诊断用 60行/3层（比 CI 的 80/5 更严，目标持续收紧）
