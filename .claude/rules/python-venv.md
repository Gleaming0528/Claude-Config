# Python / SDK 环境

所有 Python 和 hyper-ai SDK 操作必须使用 workspace 的 venv：

- **Python**: `/Users/gleaming/gitlab/workspace/.venv/bin/python3` (3.13)
- **pip**: `/Users/gleaming/gitlab/workspace/.venv/bin/pip`
- **CLI**: `/Users/gleaming/gitlab/workspace/.venv/bin/hi`（新版）、`/Users/gleaming/gitlab/workspace/.venv/bin/hpc`（旧版）

执行 Python 脚本或 SDK 调用时，始终使用完整路径或先激活 venv：

```bash
# 直接用完整路径
/Users/gleaming/gitlab/workspace/.venv/bin/python3 script.py
/Users/gleaming/gitlab/workspace/.venv/bin/hi inference list -ns infra-ms

# 或在 Shell 中激活
source /Users/gleaming/gitlab/workspace/.venv/bin/activate
```

禁止使用系统 `/usr/bin/python3`（3.9.6，缺少依赖）。
