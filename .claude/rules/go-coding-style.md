---
description: Go coding style — gofmt, naming, Gin handler conventions, error wrapping
globs: "**/*.go"
alwaysApply: false
---

# Go Coding Style

## Formatting

- **gofmt** and **goimports** are mandatory — no style debates
- Run `gofmt -w .` before every commit

## Design Principles

- Accept interfaces, return structs
- Keep interfaces small (1-3 methods)
- Make the zero value useful
- Context as first parameter: `func Foo(ctx context.Context, ...)`
- Return early, keep happy path unindented

## Error Handling

Always wrap errors with context using `%w`:

```go
if err != nil {
    return fmt.Errorf("create inference %s/%s: %w", ns, name, err)
}
```

- Error messages: lowercase, no punctuation
- Use `errors.Is` / `errors.As` for checking
- Never ignore errors with `_` unless explicitly justified

## Naming

- Package names: short, lowercase, no underscores (`inference`, not `inference_service`)
- Exported names: `GetUser`, not `GetUserFromDB`
- Acronyms: `userID`, `httpClient`, `apiURL`

## File Organization

- One handler file + one service file per domain (`handler.go`, `service.go`)
- Types in `model/` package
- Shared utilities in `pkg/`
- 200-400 lines typical, 800 max per file

## Gin Handler Convention

- Always validate path/query params before use
- Use `common.BadRequest` / `common.InternalError` consistently
- Add Swagger annotations on all exported handlers
- Don't pass `*gin.Context` to goroutines — use `c.Request.Context()`

## Reference

See skill: `golang-patterns` for comprehensive idioms and patterns.
