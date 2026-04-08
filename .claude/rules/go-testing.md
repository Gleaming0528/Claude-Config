# Go 测试规范

## TDD 工作流

1. 写一个失败的测试（RED）
2. 写最少代码让测试通过（GREEN）
3. 保持绿灯重构（REFACTOR）
4. 重复

## 单元测试

- 表驱动测试为默认模式，每个 case 命名清晰
- 测试函数名：`Test<Service>_<Method>_<场景>`，如 `TestInferenceService_Create_DuplicateName`
- 用 `t.Run(name, func(t *testing.T) {...})` 分子测试
- 断言用 `testify` 或原生 `if got != want`，不用 `reflect.DeepEqual`

```go
func TestParse_InvalidInput(t *testing.T) {
    tests := []struct {
        name    string
        input   string
        wantErr bool
    }{
        {"空字符串", "", true},
        {"非法格式", "abc:::", true},
        {"正常输入", "valid", false},
    }
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            _, err := Parse(tt.input)
            if (err != nil) != tt.wantErr {
                t.Errorf("Parse(%q) error = %v, wantErr %v", tt.input, err, tt.wantErr)
            }
        })
    }
}
```

## Race Detection

始终使用 `-race` 标志：

```bash
go test -race ./...
```

## Coverage

```bash
go test -cover ./...
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out
```

目标：通用代码 80%+，handlers/APIs 90%+，关键业务逻辑 100%。

## Controller 集成测试（envtest）

- 使用 `envtest.Environment` 启动 API Server
- 用 `suite_test.go` 统一 Setup/Teardown
- 测试 Reconcile 结果而非内部实现：创建 CR → 等待 Status 变化 → 断言
- 用 `Eventually` / `Consistently`（gomega）做异步断言，不用 sleep

```go
// ❌ 用 sleep 等 reconcile 完成
time.Sleep(5 * time.Second)
// ✅ 用 Eventually 轮询
Eventually(func(g Gomega) {
    var obj v1.DevSpace
    g.Expect(k8sClient.Get(ctx, key, &obj)).To(Succeed())
    g.Expect(obj.Status.Phase).To(Equal("Running"))
}, timeout, interval).Should(Succeed())
```

## E2E 测试

- 放在 `test/e2e/` 目录
- 测试完整用户流程：创建 → 观察状态流转 → 清理
- 测试数据用随机名或带时间戳前缀，防止并发冲突

## 反面示例

```go
// ❌ 测试名不表达意图
func TestFunc1(t *testing.T) { ... }
// ✅
func TestImageSave_ExceedsSizeLimit(t *testing.T) { ... }

// ❌ 直接操作全局变量做 mock
originalClient = fakeClient
defer func() { originalClient = realClient }()
// ✅ 通过接口注入
type Reconciler struct {
    Client client.Client  // 测试时注入 fake
}

// ❌ 只测 happy path
func TestCreate(t *testing.T) {
    result := Create(validInput)
    assert.NoError(t, result)
}
// ✅ 也要测边界和错误
func TestCreate_DuplicateName(t *testing.T) { ... }
func TestCreate_ExceedsQuota(t *testing.T) { ... }
func TestCreate_InvalidSpec(t *testing.T) { ... }
```

## 参考

详见 skill: `golang-testing`。
