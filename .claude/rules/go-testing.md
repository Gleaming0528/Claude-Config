# Go Testing

## Framework

Use standard `go test` with **table-driven tests** as the default pattern.

## TDD Workflow

1. Write a failing test (RED)
2. Write minimal code to pass (GREEN)
3. Refactor while keeping tests green (REFACTOR)
4. Repeat

## Race Detection

Always run with `-race` flag:

```bash
go test -race ./...
```

## Coverage

```bash
go test -cover ./...
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out
```

Target: 80%+ for general code, 90%+ for handlers/APIs, 100% for critical business logic.

## Test Naming

```go
func TestServiceName_MethodName_Scenario(t *testing.T) { ... }
// Example: TestInferenceService_Create_ValidRequest
// Example: TestInferenceService_Create_DuplicateName
```

## Reference

See skill: `golang-testing` for detailed patterns, helpers, and examples.
