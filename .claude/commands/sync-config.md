---
description: 将 .claude 目录和 CLAUDE.md 同步到 GitHub 仓库 Gleaming0528/Claude-Config
---

# Sync Config Command

将当前项目的 `.claude/` 和 `CLAUDE.md` 同步推送到 GitHub 配置仓库。

## 执行步骤

1. **克隆仓库到临时目录**：
   ```bash
   git clone git@github.com:Gleaming0528/Claude-Config.git /tmp/Claude-Config
   ```

2. **用最新文件覆盖**：
   ```bash
   cd /tmp/Claude-Config
   rm -rf .claude
   cp -r /Users/gleaming/gitlab/hpc/.claude .
   cp /Users/gleaming/gitlab/hpc/CLAUDE.md .
   ```

3. **检查变更**：
   ```bash
   git status
   git diff --stat
   ```
   - 如果没有变更，提示用户"配置已是最新"并跳过后续步骤

4. **提交并推送**：
   ```bash
   git add -A
   git commit -m "sync: 同步最新 .claude 配置"
   git push origin main
   ```

5. **清理临时目录**：
   ```bash
   rm -rf /tmp/Claude-Config
   ```

6. **输出结果**：报告变更的文件列表和推送状态

## 权限要求

- 需要完整权限 (`required_permissions: ["all"]`)
  - 网络访问：git clone / push
  - 文件系统：临时目录读写

## 注意事项

- 仓库地址：`git@github.com:Gleaming0528/Claude-Config.git`
- 认证方式：SSH key（已配置在 `~/.ssh/`）
- 临时目录：`/tmp/Claude-Config`，操作完毕后必须清理
- 如果临时目录已存在，先删除再克隆
