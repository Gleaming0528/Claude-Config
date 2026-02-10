---
name: golang-patterns
description: Idiomatic Go patterns and best practices for HPC platform backend development. Covers error handling, concurrency, interfaces, Gin handlers, and K8s client-go.
---

# Go Development Patterns

Idiomatic Go patterns for building robust, efficient, and maintainable HPC platform services.

## When to Activate

- Writing new Go code in hpc-studio-api, hpc-gateway, or controllers
- Reviewing or refactoring existing Go code
- Designing new Go packages or modules

## Core Principles

### 1. Simplicity and Clarity

Go favors simplicity over cleverness. Code should be obvious.

```go
// Good: clear and direct
func GetUser(id string) (*User, error) {
    user, err := db.FindUser(id)
    if err != nil {
        return nil, fmt.Errorf("get user %s: %w", id, err)
    }
    return user, nil
}

// Bad: overly clever
func GetUser(id string) (*User, error) {
    return func() (*User, error) {
        if u, e := db.FindUser(id); e == nil { return u, nil } else { return nil, e }
    }()
}
```

### 2. Make the Zero Value Useful

Design types so their zero value is immediately usable.

```go
// Good: zero value is useful
type Counter struct {
    mu    sync.Mutex
    count int // zero is 0, ready to use
}

// Bad: requires initialization
type BadCounter struct {
    counts map[string]int // nil map panics on write
}
```

### 3. Accept Interfaces, Return Structs

```go
// Good
func ProcessData(r io.Reader) (*Result, error) {
    data, err := io.ReadAll(r)
    if err != nil { return nil, err }
    return &Result{Data: data}, nil
}

// Bad: returns interface (hides implementation)
func ProcessData(r io.Reader) (io.Reader, error) { ... }
```

## Error Handling Patterns

### Error Wrapping with Context

```go
func LoadConfig(path string) (*Config, error) {
    data, err := os.ReadFile(path)
    if err != nil {
        return nil, fmt.Errorf("load config %s: %w", path, err)
    }
    var cfg Config
    if err := json.Unmarshal(data, &cfg); err != nil {
        return nil, fmt.Errorf("parse config %s: %w", path, err)
    }
    return &cfg, nil
}
```

### Custom Error Types

```go
type ValidationError struct {
    Field   string
    Message string
}

func (e *ValidationError) Error() string {
    return fmt.Sprintf("validation failed on %s: %s", e.Field, e.Message)
}

var (
    ErrNotFound     = errors.New("resource not found")
    ErrUnauthorized = errors.New("unauthorized")
    ErrInvalidInput = errors.New("invalid input")
)
```

### Error Checking

```go
// Use errors.Is for sentinel errors
if errors.Is(err, sql.ErrNoRows) { ... }

// Use errors.As for error types
var validationErr *ValidationError
if errors.As(err, &validationErr) { ... }
```

## Concurrency Patterns

### Worker Pool

```go
func WorkerPool(ctx context.Context, jobs <-chan Job, results chan<- Result, n int) {
    var wg sync.WaitGroup
    for i := 0; i < n; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            for job := range jobs {
                select {
                case <-ctx.Done():
                    return
                case results <- process(job):
                }
            }
        }()
    }
    wg.Wait()
    close(results)
}
```

### errgroup for Coordinated Goroutines

```go
func FetchAll(ctx context.Context, urls []string) ([][]byte, error) {
    g, ctx := errgroup.WithContext(ctx)
    results := make([][]byte, len(urls))

    for i, url := range urls {
        i, url := i, url
        g.Go(func() error {
            data, err := fetchURL(ctx, url)
            if err != nil { return err }
            results[i] = data
            return nil
        })
    }

    if err := g.Wait(); err != nil { return nil, err }
    return results, nil
}
```

### Graceful Shutdown

```go
func GracefulShutdown(server *http.Server) {
    quit := make(chan os.Signal, 1)
    signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
    <-quit

    ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
    defer cancel()

    if err := server.Shutdown(ctx); err != nil {
        log.Fatalf("server forced shutdown: %v", err)
    }
}
```

### Avoiding Goroutine Leaks

```go
// Bad: goroutine leaks if context cancelled
func leaky(ctx context.Context) <-chan []byte {
    ch := make(chan []byte)
    go func() {
        data, _ := fetch()
        ch <- data // blocks forever if no receiver
    }()
    return ch
}

// Good: buffered channel + select
func safe(ctx context.Context) <-chan []byte {
    ch := make(chan []byte, 1)
    go func() {
        data, err := fetch()
        if err != nil { return }
        select {
        case ch <- data:
        case <-ctx.Done():
        }
    }()
    return ch
}
```

## Interface Design

### Small, Focused Interfaces

```go
// Good: single-method interfaces
type Reader interface { Read(p []byte) (n int, err error) }
type Writer interface { Write(p []byte) (n int, err error) }

// Compose as needed
type ReadWriter interface { Reader; Writer }
```

### Define Interfaces Where They're Used

```go
// In the consumer package, not the provider
package service

type UserStore interface {
    GetUser(id string) (*User, error)
    SaveUser(user *User) error
}

type Service struct { store UserStore }
```

## Functional Options Pattern

```go
type Server struct {
    addr    string
    timeout time.Duration
    logger  *zap.Logger
}

type Option func(*Server)

func WithTimeout(d time.Duration) Option {
    return func(s *Server) { s.timeout = d }
}

func WithLogger(l *zap.Logger) Option {
    return func(s *Server) { s.logger = l }
}

func NewServer(addr string, opts ...Option) *Server {
    s := &Server{addr: addr, timeout: 30 * time.Second}
    for _, opt := range opts { opt(s) }
    return s
}
```

## Gin Handler Patterns

### Standard Handler Structure

```go
func (h *Handler) createResource(c *gin.Context) {
    // 1. Extract and validate path params
    namespace := c.Param("namespace")
    if namespace == "" {
        common.BadRequest(c, "invalid namespace")
        return
    }

    // 2. Bind and validate request body
    var req model.CreateRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        common.BadRequest(c, err.Error())
        return
    }

    // 3. Extract context (user, headers)
    user := c.GetHeader("x-user-id")

    // 4. Call service
    result, err := h.service.Create(c, namespace, &req)
    if err != nil {
        logger.Error(c, "failed to create resource", zap.Error(err))
        common.InternalError(c, err.Error())
        return
    }

    // 5. Return response
    c.JSON(http.StatusOK, result)
}
```

### Don't Pass *gin.Context to Goroutines

```go
// Bad: gin.Context is not goroutine-safe
go func() { h.service.Process(c, data) }()

// Good: extract what you need, use request context
ctx := c.Request.Context()
go func() { h.service.Process(ctx, data) }()
```

## Memory and Performance

### Preallocate Slices

```go
// Bad: grows slice multiple times
var results []Result
for _, item := range items {
    results = append(results, process(item))
}

// Good: single allocation
results := make([]Result, 0, len(items))
for _, item := range items {
    results = append(results, process(item))
}
```

### Use sync.Pool for Frequent Allocations

```go
var bufPool = sync.Pool{
    New: func() interface{} { return new(bytes.Buffer) },
}

func Process(data []byte) []byte {
    buf := bufPool.Get().(*bytes.Buffer)
    defer func() { buf.Reset(); bufPool.Put(buf) }()
    buf.Write(data)
    return buf.Bytes()
}
```

### Efficient String Building

```go
// Bad: O(n²) string concatenation
for _, s := range parts { result += s }

// Good: O(n) with Builder
var sb strings.Builder
for _, s := range parts { sb.WriteString(s) }
return sb.String()

// Best: use stdlib
return strings.Join(parts, ",")
```

## Package Organization

```text
hpc-studio-api/
├── cmd/server/main.go       # Entry point
├── internal/
│   ├── common/               # Shared response helpers
│   ├── inference/             # handler.go + service.go
│   ├── training/              # handler.go + service.go
│   ├── model/                 # Request/response types
│   └── config/                # Configuration
├── pkg/
│   ├── logger/                # Structured logging
│   └── utils/                 # Shared utilities
├── go.mod
└── Makefile
```

## Quick Reference: Go Idioms

| Idiom | Description |
|-------|-------------|
| Accept interfaces, return structs | Functions accept interface params, return concrete types |
| Errors are values | Treat errors as first-class, not exceptions |
| Don't communicate by sharing memory | Use channels for goroutine coordination |
| Make the zero value useful | Types should work without explicit init |
| Clear is better than clever | Readability over cleverness |
| Return early | Handle errors first, keep happy path unindented |
| Context as first param | Always `func Foo(ctx context.Context, ...)` |

## Anti-Patterns to Avoid

```go
// Bad: naked returns in long functions
func process() (result int, err error) {
    // ... 50 lines ...
    return // what is being returned?
}

// Bad: panic for control flow
func GetUser(id string) *User {
    user, err := db.Find(id)
    if err != nil { panic(err) }
    return user
}

// Bad: context in struct
type Request struct {
    ctx context.Context // should be first param
    ID  string
}

// Bad: mixing value and pointer receivers
type Counter struct{ n int }
func (c Counter) Value() int  { return c.n }
func (c *Counter) Increment() { c.n++ }
// Pick one and be consistent
```
