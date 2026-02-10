---
description: Go security — secrets, input validation, context timeouts, race detection
globs: "**/*.go"
alwaysApply: false
---

# Go Security

## Secret Management

```go
apiKey := os.Getenv("API_KEY")
if apiKey == "" {
    log.Fatal("API_KEY not configured")
}
```

- NEVER hardcode secrets, tokens, or passwords
- Use environment variables or K8s secrets
- Rotate credentials regularly

## Input Validation

- Sanitize user input before using as K8s labels: `utils.SanitizeLabelValue()`
- Validate path parameters in Gin handlers before use
- Never use user input in `os/exec` commands without validation
- Never concatenate user input into SQL queries

## Context & Timeouts

Always use `context.Context` for timeout control:

```go
ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
defer cancel()
```

- Propagate context through all layers (handler → service → K8s client)
- Set timeouts on all external calls (HTTP, K8s API, database)

## Security Scanning

```bash
go vet ./...
gosec ./...
govulncheck ./...
```

## TLS

- Never use `InsecureSkipVerify: true` in production
- If needed for internal services, add explicit comment with justification

## Race Conditions

- Run `go test -race ./...` regularly
- Use `sync.Mutex` with `defer mu.Unlock()` pattern
- Don't share `*gin.Context` across goroutines
