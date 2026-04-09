---
name: golang-testing
description: Drives Go development with tests using table-driven patterns, subtests, benchmarks, fuzzing, and HTTP handler testing. Use when writing tests, adding coverage, or following TDD in Go projects.
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

## 反合理化

| 借口 | 现实 |
|------|------|
| "之后再补测试" | 不会补的。事后写的测试倾向于验证实现细节而非行为，且覆盖率永远赶不上。 |
| "这个函数太简单了不用测" | 简单函数会变复杂。测试记录的是**期望行为**，不是代码复杂度。 |
| "手动测过了，能跑" | 手动测试不可重复、不可回归。明天的改动可能悄悄打破今天的行为。 |
| "测试拖慢开发速度" | 测试现在慢你 5 分钟，之后每次改动省你 2 小时的排查。TDD 是投资，不是开销。 |
| "mock 太多太麻烦" | 如果需要 mock 5 个依赖才能测一个函数，说明函数职责过重。难 mock = 设计问题。 |
| "这是 controller 代码，不好测" | Gin handler 用 `httptest.NewRecorder()` + `gin.CreateTestContext()` 就能测。没有"不好测"的代码，只有耦合过紧的设计。 |
| "error path 不重要" | 生产环境 80% 的 bug 在 error path 上。happy path 能跑 ≠ 代码正确。 |
| "CI 上跑就行了，本地不用跑" | CI 反馈慢。`go test ./...` 本地跑 2 秒，CI 等 5 分钟。先本地验证再 push。 |

## Red Flags

- 新增函数/方法没有对应的 `_test.go` 文件
- 修复 bug 时没有先写复现测试
- 测试名称是 `TestFunc1`、`TestIt` 等无意义命名
- 测试中使用 `time.Sleep()` 做同步
- 跳过 `-race` 检查提交并发代码
- 整个 package 没有任何测试文件
- 测试中 mock 了所有依赖（过度 mock 信号）
- `t.Skip()` 被用来"临时"跳过失败测试——临时 = 永久
- 测试只验证 happy path，error case 全部缺失

## 验证清单

完成代码实现后确认：

- [ ] 每个新函数/方法都有对应测试
- [ ] Bug 修复包含复现测试（修复前 FAIL，修复后 PASS）
- [ ] `go test ./...` 全部通过
- [ ] `go test -race ./...` 无 race condition
- [ ] 测试名描述了被验证的行为（不是实现细节）
- [ ] error path 有测试覆盖
- [ ] 测试覆盖率未下降：`go test -cover ./...`
