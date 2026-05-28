---
description: Go coding style — gofmt, naming, Gin handler conventions, error wrapping
globs: "**/*.go"
alwaysApply: false
---

# Go Coding Style

## 必须

- `gofmt` + `goimports`，无例外
- Context 做第一个参数：`func Foo(ctx context.Context, ...)`
- 错误用 `%w` 包装：`fmt.Errorf("create inference %s/%s: %w", ns, name, err)`
- 错误消息：小写、无标点
- 不忽略错误（`_`），除非有明确理由

## 设计

- Accept interfaces, return structs
- 接口小（1-3 方法）
- Make the zero value useful
- Return early，happy path 不缩进

## 命名

- 包名：短、小写、无下划线（`inference`，不是 `inference_service`）
- 导出名：`GetUser`，不是 `GetUserFromDB`
- 缩写：`userID`、`httpClient`、`apiURL`

## Gin Handler

- 校验 path/query 参数后再用
- 统一用 `common.BadRequest` / `common.InternalError`
- 导出 handler 加 Swagger 注解
- goroutine 中用 `c.Request.Context()`，不传 `*gin.Context`

## 文件组织

- 每个领域：`handler.go` + `service.go`，类型在 `model/`
- 200-400 行典型，800 行上限

详细模式与代码示例见 skill: `golang-patterns`。
