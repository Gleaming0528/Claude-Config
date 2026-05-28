---
description: Go 测试规范 — TDD、表驱动、envtest、race detection、覆盖率
globs: "**/*_test.go"
alwaysApply: false
---

# Go 测试规范

## TDD

RED → GREEN → REFACTOR → 重复。先写失败测试，再写最少代码通过。

## 必须

- 表驱动测试为默认模式，每个 case 有清晰命名
- 测试名：`Test<Service>_<Method>_<场景>`
- 始终 `go test -race ./...`
- 覆盖率：通用 80%+，handler 90%+，关键逻辑 100%

## 禁止

- 测试名无意义（`TestFunc1`）
- 用 `time.Sleep` 做同步（用 `Eventually` / `Consistently`）
- 用 `reflect.DeepEqual`（用 `testify` 或原生比较）
- 全局变量做 mock（通过接口注入）
- 只测 happy path

## Controller 集成测试

- `envtest.Environment` 启动 API Server
- `suite_test.go` 统一 Setup/Teardown
- 测试 Reconcile 结果，不测内部实现

详细模式、代码示例、fuzz、benchmark 见 skill: `golang-testing`。
