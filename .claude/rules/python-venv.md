---
description: Python / SDK 环境 — 强制使用 workspace venv，禁止系统 Python
alwaysApply: true
---

# Python / SDK 环境

所有 Python 和 hyper-ai SDK 操作必须使用 workspace 根目录下的 `.venv`。

**查找 venv**：从当前工作目录向上查找 `.venv/bin/python3`，或直接使用 `$WORKSPACE_ROOT/.venv/bin/python3`。

```bash
# 激活 venv（推荐）
source "$(git rev-parse --show-toplevel)/.venv/bin/activate"

# 或直接用完整路径
.venv/bin/python3 script.py
.venv/bin/hi inference list infra-ms
```

- **禁止**使用系统 `/usr/bin/python3`（版本旧，缺少依赖）
- CLI 工具：`hi`（新版）、`hpc`（旧版），均在 `.venv/bin/` 下
