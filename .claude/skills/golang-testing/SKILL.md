---
name: golang-testing
description: Go testing patterns including table-driven tests, subtests, benchmarks, fuzzing, HTTP handler testing, and interface mocking. Follows TDD with idiomatic Go practices.
---

# Go Testing Patterns

Comprehensive Go testing patterns for the HPC platform, following TDD methodology.

## When to Activate

- Writing new Go functions or methods
- Adding test coverage to existing code
- Creating benchmarks for performance-critical code
- Implementing fuzz tests for input validation
- Following TDD workflow in Go projects

## TDD Workflow

```
RED    → Write a failing test first
GREEN  → Write minimal code to pass
REFACTOR → Improve while keeping tests green
REPEAT → Continue with next requirement
```

## Table-Driven Tests

The standard Go test pattern. Use for all tests.

```go
func TestAdd(t *testing.T) {
    tests := []struct {
        name     string
        a, b     int
        expected int
    }{
        {"positive numbers", 2, 3, 5},
        {"negative numbers", -1, -2, -3},
        {"zero values", 0, 0, 0},
        {"mixed signs", -1, 1, 0},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            got := Add(tt.a, tt.b)
            if got != tt.expected {
                t.Errorf("Add(%d, %d) = %d; want %d", tt.a, tt.b, got, tt.expected)
            }
        })
    }
}
```

### With Error Cases

```go
func TestParseConfig(t *testing.T) {
    tests := []struct {
        name    string
        input   string
        want    *Config
        wantErr bool
    }{
        {
            name:  "valid config",
            input: `{"host": "localhost", "port": 8080}`,
            want:  &Config{Host: "localhost", Port: 8080},
        },
        {
            name:    "invalid JSON",
            input:   `{invalid}`,
            wantErr: true,
        },
        {
            name:    "empty input",
            input:   "",
            wantErr: true,
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            got, err := ParseConfig(tt.input)
            if tt.wantErr {
                if err == nil { t.Error("expected error, got nil") }
                return
            }
            if err != nil { t.Fatalf("unexpected error: %v", err) }
            if !reflect.DeepEqual(got, tt.want) {
                t.Errorf("got %+v; want %+v", got, tt.want)
            }
        })
    }
}
```

## Test Helpers

```go
func setupTestDB(t *testing.T) *sql.DB {
    t.Helper()
    db, err := sql.Open("sqlite3", ":memory:")
    if err != nil { t.Fatalf("open db: %v", err) }
    t.Cleanup(func() { db.Close() })
    return db
}

func assertEqual[T comparable](t *testing.T, got, want T) {
    t.Helper()
    if got != want { t.Errorf("got %v; want %v", got, want) }
}
```

## Parallel Subtests

```go
func TestParallel(t *testing.T) {
    tests := []struct{ name, input string }{
        {"case1", "input1"},
        {"case2", "input2"},
    }

    for _, tt := range tests {
        tt := tt // capture range variable
        t.Run(tt.name, func(t *testing.T) {
            t.Parallel()
            result := Process(tt.input)
            _ = result
        })
    }
}
```

## Interface-Based Mocking

```go
// Define interface
type UserRepository interface {
    GetUser(id string) (*User, error)
    SaveUser(user *User) error
}

// Mock implementation
type MockUserRepository struct {
    GetUserFunc  func(id string) (*User, error)
    SaveUserFunc func(user *User) error
}

func (m *MockUserRepository) GetUser(id string) (*User, error) {
    return m.GetUserFunc(id)
}

func (m *MockUserRepository) SaveUser(user *User) error {
    return m.SaveUserFunc(user)
}

// Test using mock
func TestUserService(t *testing.T) {
    mock := &MockUserRepository{
        GetUserFunc: func(id string) (*User, error) {
            if id == "123" {
                return &User{ID: "123", Name: "Alice"}, nil
            }
            return nil, ErrNotFound
        },
    }

    svc := NewUserService(mock)
    user, err := svc.GetUserProfile("123")
    if err != nil { t.Fatalf("unexpected error: %v", err) }
    assertEqual(t, user.Name, "Alice")
}
```

## HTTP Handler Testing (Gin)

```go
func TestHealthHandler(t *testing.T) {
    w := httptest.NewRecorder()
    c, _ := gin.CreateTestContext(w)
    c.Request = httptest.NewRequest(http.MethodGet, "/health", nil)

    HealthHandler(c)

    if w.Code != http.StatusOK {
        t.Errorf("got status %d; want %d", w.Code, http.StatusOK)
    }
}

func TestAPIHandler(t *testing.T) {
    tests := []struct {
        name       string
        method     string
        path       string
        body       string
        wantStatus int
    }{
        {"get resource", http.MethodGet, "/inferences/test", "", http.StatusOK},
        {"not found", http.MethodGet, "/inferences/missing", "", http.StatusNotFound},
        {"create", http.MethodPost, "/inferences", `{"name":"test"}`, http.StatusOK},
    }

    handler := setupTestHandler(t)

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            var body io.Reader
            if tt.body != "" { body = strings.NewReader(tt.body) }

            w := httptest.NewRecorder()
            c, _ := gin.CreateTestContext(w)
            c.Request = httptest.NewRequest(tt.method, tt.path, body)
            c.Request.Header.Set("Content-Type", "application/json")

            handler.ServeHTTP(w, c.Request)

            if w.Code != tt.wantStatus {
                t.Errorf("got status %d; want %d", w.Code, tt.wantStatus)
            }
        })
    }
}
```

## Benchmarks

```go
func BenchmarkProcess(b *testing.B) {
    data := generateTestData(1000)
    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        Process(data)
    }
}

// Benchmark with different sizes
func BenchmarkSort(b *testing.B) {
    for _, size := range []int{100, 1000, 10000} {
        b.Run(fmt.Sprintf("size=%d", size), func(b *testing.B) {
            data := generateSlice(size)
            b.ResetTimer()
            for i := 0; i < b.N; i++ {
                tmp := make([]int, len(data))
                copy(tmp, data)
                sort.Ints(tmp)
            }
        })
    }
}
```

## Fuzzing (Go 1.18+)

```go
func FuzzParseJSON(f *testing.F) {
    f.Add(`{"name": "test"}`)
    f.Add(`[]`)
    f.Add(`""`)

    f.Fuzz(func(t *testing.T, input string) {
        var result map[string]interface{}
        err := json.Unmarshal([]byte(input), &result)
        if err != nil { return }

        _, err = json.Marshal(result)
        if err != nil {
            t.Errorf("Marshal failed after Unmarshal: %v", err)
        }
    })
}
```

## Golden Files

```go
var update = flag.Bool("update", false, "update golden files")

func TestRender(t *testing.T) {
    got := Render(input)
    golden := filepath.Join("testdata", "output.golden")

    if *update {
        os.WriteFile(golden, got, 0644)
    }

    want, err := os.ReadFile(golden)
    if err != nil { t.Fatal(err) }

    if !bytes.Equal(got, want) {
        t.Errorf("mismatch:\ngot:\n%s\nwant:\n%s", got, want)
    }
}
```

## Coverage Targets

| Code Type | Target |
|-----------|--------|
| Critical business logic | 100% |
| Public APIs / handlers | 90%+ |
| General code | 80%+ |
| Generated code | Exclude |

## Test Commands

```bash
go test ./...                          # Run all tests
go test -v ./...                       # Verbose output
go test -run TestAdd ./...             # Run specific test
go test -run "TestUser/Create" ./...   # Run subtest
go test -race ./...                    # Race detector
go test -cover -coverprofile=c.out ./... # Coverage
go tool cover -html=c.out             # View in browser
go test -bench=. -benchmem ./...      # Benchmarks
go test -fuzz=FuzzParse -fuzztime=30s # Fuzzing
go test -count=10 ./...               # Flaky detection
go test -short ./...                   # Skip long tests
```

## Best Practices

**DO:**
- Write tests FIRST (TDD)
- Use table-driven tests
- Test behavior, not implementation
- Use `t.Helper()` in helpers
- Use `t.Parallel()` for independent tests
- Clean up with `t.Cleanup()`
- Use meaningful test names

**DON'T:**
- Test private functions directly
- Use `time.Sleep()` in tests
- Ignore flaky tests
- Mock everything (prefer integration tests when feasible)
- Skip error path testing
