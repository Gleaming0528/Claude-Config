---
description: 同步 .claude/rules 到 .cursor/rules，并将 .claude 目录和 CLAUDE.md 推送到 GitHub 仓库 Gleaming0528/Claude-Config
---

# Sync Config Command

两件事：① 将 `.claude/rules/` 同步到 `.cursor/rules/`（让 Cursor 能自动加载规则）；② 将配置推送到 GitHub 备份仓库。

## 执行步骤

### Part 1: 同步 rules 到 Cursor

1. **同步 `.claude/rules/` → `.cursor/rules/`**（完全覆盖，删除多余文件）：
   ```bash
   rm -rf /Users/gleaming/gitlab/hpc/.cursor/rules
   mkdir -p /Users/gleaming/gitlab/hpc/.cursor/rules
   cp /Users/gleaming/gitlab/hpc/.claude/rules/*.md /Users/gleaming/gitlab/hpc/.cursor/rules/
   ```

2. **输出同步结果**：列出已同步的规则文件

### Part 2: 推送到 GitHub 备份仓库

3. **创建临时目录并克隆仓库**：
   ```bash
   rm -rf /Users/gleaming/gitlab/_sync_tmp
   mkdir -p /Users/gleaming/gitlab/_sync_tmp
   cd /Users/gleaming/gitlab/_sync_tmp
   git clone git@github.com:Gleaming0528/Claude-Config.git .
   ```

4. **用最新文件覆盖**：
   ```bash
   rm -rf .claude
   cp -r /Users/gleaming/gitlab/hpc/.claude .
   cp /Users/gleaming/gitlab/hpc/CLAUDE.md .
   ```

5. **检查变更**：
   ```bash
   git add -A
   git status --short
   ```
   - 如果没有变更，提示用户"配置已是最新"并跳过后续步骤

6. **提交并推送**：
   ```bash
   git commit -m "sync: 同步最新 .claude 配置"
   git push origin main
   ```

7. **清理临时目录**：
   ```bash
   rm -rf /Users/gleaming/gitlab/_sync_tmp
   ```

8. **输出结果**：报告规则同步状态 + 变更文件列表 + 推送状态

## 权限要求

- 需要完整权限 (`required_permissions: ["all"]`)
  - 网络访问：git clone / push
  - 文件系统：临时目录读写

## 注意事项

- 仓库地址：`git@github.com:Gleaming0528/Claude-Config.git`
- 认证方式：SSH key（已配置在 `~/.ssh/`）
- 临时目录：`/Users/gleaming/gitlab/_sync_tmp`，操作完毕后必须清理
- 如果临时目录已存在，先删除再克隆
