---
description: Python 服务开发规范 (FastAPI / 脚本)
globs: "**/*.py"
alwaysApply: false
---

# Python 服务规范

## 类职责分离

```python
class KubeClient:     # K8s 交互
class Runtime:        # 容器运行时抽象
class ImageManager:   # 镜像操作
class AssetManager:   # 资产平台交互
```

每个类只负责一个关注点，通过构造函数注入依赖。

## 铁律

- 自定义异常携带业务语义：`raise SaveError(f"镜像超过 {MAX}GB")`
- 区分可重试错误和终止性错误，不用裸 `except:`
- 外部命令用 `subprocess.run(cmd_list)`，禁止 `shell=True`
- 超时必须按操作类型分级设置
- 环境变量用 `os.getenv("KEY") or "default"` 模式
- 注释用中文，变量/函数名用英文
- 函数超过 20 行必须检查是否可拆分

## 反面示例

```python
# ❌ 裸 except 吞掉所有异常
try:
    run_command()
except:
    pass
# ✅ 捕获具体异常，区分可重试和终止性
try:
    run_command()
except subprocess.TimeoutExpired:
    raise RetryableError("命令超时，可重试")
except FileNotFoundError as e:
    raise FatalError(f"文件不存在: {e}")

# ❌ shell=True 注入风险
subprocess.run(f"kubectl get pod {name}", shell=True)
# ✅ 参数列表
subprocess.run(["kubectl", "get", "pod", name], check=True)

# ❌ 上帝类：一个类干所有事
class Manager:
    def save_image(self): ...
    def query_k8s(self): ...
    def upload_harbor(self): ...
    def send_notification(self): ...
# ✅ 单一职责，每个类一个关注点
class ImageManager:
    def save(self): ...
class HarborClient:
    def upload(self): ...

# ❌ 硬编码超时
requests.get(url)  # 无超时，可能永久挂起
# ✅ 按操作分级
requests.get(url, timeout=API_TIMEOUT)     # API 调用 10s
requests.post(url, timeout=UPLOAD_TIMEOUT) # 上传 300s
```
