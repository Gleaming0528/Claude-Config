---
description: Go security — secrets, input validation, context timeouts, race detection
globs: "**/*.go"
alwaysApply: false
---

# Go Security

## 禁止

- 硬编码密钥、token、密码（用环境变量或 K8s Secret）
- 用户输入直接拼入 `os/exec` 命令或 SQL
- 用户输入直接做 K8s label 值（用 `utils.SanitizeLabelValue()`）
- 生产环境 `InsecureSkipVerify: true`（内部服务需注释说明理由）

## 必须

- 所有外部调用设 context 超时：`context.WithTimeout(ctx, 5*time.Second)`
- Context 逐层传播：handler → service → K8s client
- `go test -race ./...` 常规运行
- `sync.Mutex` 配合 `defer mu.Unlock()`
- goroutine 中不共享 `*gin.Context`

## 扫描

```bash
go vet ./... && gosec ./... && govulncheck ./...
```
