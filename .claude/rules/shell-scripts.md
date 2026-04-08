---
description: Shell 脚本开发规范
globs: "**/*.sh"
alwaysApply: false
---

# Shell 脚本规范

## 模板

```bash
#!/usr/bin/env bash
set -euo pipefail

# ==================== 参数 ====================
PARAM="${1:?用法: $0 <param>}"

# ==================== 工具函数 ====================
info()  { echo -e "\033[32m[INFO]\033[0m  $*"; }
warn()  { echo -e "\033[33m[WARN]\033[0m  $*"; }
error() { echo -e "\033[31m[ERROR]\033[0m $*"; exit 1; }

# ==================== 1. 步骤名 ====================
info "执行步骤 1..."
```

## 铁律

- 脚本首行 `#!/usr/bin/env bash` + `set -euo pipefail`
- 用 `# === N. 步骤名 ===` 分段注释
- 变量引用加双引号: `"$VAR"` 而非 `$VAR`
- 不用 `sleep` 做同步，用条件等待或轮询
- 清理操作用 `trap` 或 `|| true` 容错
- kubectl 输出用 `-o jsonpath` 或 `-o json | python3 -c` 解析，不用 awk/sed 做脆弱解析

## 反面示例

```bash
# ❌ 变量不加引号，空格路径会炸
cp $FILE /dest/    # 若 FILE="my file.txt" 则拆成两个参数
# ✅
cp "$FILE" /dest/

# ❌ 用 sleep 等 Pod 就绪
sleep 30
kubectl exec pod ...
# ✅ 条件等待
kubectl wait --for=condition=Ready pod/"$POD" --timeout=60s

# ❌ 用 awk/grep 解析 kubectl 输出（列位置随版本变化）
kubectl get pod | grep Running | awk '{print $1}'
# ✅ 结构化输出
kubectl get pod -o jsonpath='{.items[?(@.status.phase=="Running")].metadata.name}'

# ❌ 没有 set -e，错误静默继续
#!/bin/bash
rm -rf /important/dir
some_command_that_fails
echo "一切正常"  # 即使上一步失败也会执行
# ✅
#!/usr/bin/env bash
set -euo pipefail

# ❌ 临时文件不清理
TMPFILE=$(mktemp)
process "$TMPFILE"
# ✅ trap 保证清理
TMPFILE=$(mktemp)
trap 'rm -f "$TMPFILE"' EXIT
process "$TMPFILE"
```
