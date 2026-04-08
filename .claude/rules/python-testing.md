---
description: Python 测试规范（pytest）
globs: "**/test_*.py"
alwaysApply: false
---

# Python 测试规范

## 结构

- 测试文件放在 `tests/` 目录，命名 `test_<模块>.py`
- 测试函数命名 `test_<行为>_<场景>`
- 用 `pytest.fixture` 管理测试依赖，不在测试函数里初始化重量级对象

## 铁律

- 每个测试函数只验证一个行为
- 用 `pytest.raises` 断言异常，不用 try/except
- 外部依赖（K8s API、HTTP）用 mock 隔离，不做真实调用
- 参数化测试用 `@pytest.mark.parametrize`

```python
# ✅ 参数化测试
@pytest.mark.parametrize("size_gb,expected", [
    (1, True),
    (100, True),
    (501, False),
])
def test_validate_image_size(size_gb, expected):
    assert validate_size(size_gb) == expected

# ✅ 异常断言
def test_save_exceeds_limit():
    with pytest.raises(SaveError, match="超过"):
        save_image(size_gb=999)
```

## 反面示例

```python
# ❌ 测试名不表达意图
def test1(): ...

# ❌ 一个测试验证多个不相关行为
def test_everything():
    assert create() == ok
    assert delete() == ok
    assert list() == []

# ❌ 用 print 代替断言
def test_query():
    result = query()
    print(result)  # 永远不会失败

# ❌ 测试依赖执行顺序
def test_a_create(): global obj; obj = create()
def test_b_update(): update(obj)  # 依赖 test_a 先跑
```
