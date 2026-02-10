---
description: 将 .claude 目录和 CLAUDE.md 推送到 GitHub 仓库 Gleaming0528/Claude-Config
---

# Sync Config Command

将当前项目的 `.claude/` 和 `CLAUDE.md` 同步推送到 GitHub 备份仓库。

## 执行步骤

1. **创建临时目录并克隆仓库**：
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

6. **根据变更内容生成 commit message 并推送**：
   - 读取 `git status --short` 的输出
   - 分析变更文件，生成描述性 commit message，格式：
     ```
     sync: <概括变更内容>
     
     <逐行列出变更文件及原因>
     ```
   - 示例：
     ```
     sync: add Go rules frontmatter for Cursor compatibility
     
     - .claude/rules/go-*.md: add YAML frontmatter (description, globs)
     - .claude/rules/coding-style.md: add alwaysApply frontmatter
     ```
   - 提交并推送：
     ```bash
     git commit -m "<生成的 message>"
     git push origin main
     ```

7. **清理临时目录**：
   ```bash
   rm -rf /Users/gleaming/gitlab/_sync_tmp
   ```

6. **输出结果**：报告变更文件列表 + 推送状态

## 权限要求

- 需要完整权限 (`required_permissions: ["all"]`)
  - 网络访问：git clone / push
  - 文件系统：临时目录读写

## 注意事项

- 仓库地址：`git@github.com:Gleaming0528/Claude-Config.git`
- 认证方式：SSH key（已配置在 `~/.ssh/`）
- 临时目录：`/Users/gleaming/gitlab/_sync_tmp`，操作完毕后必须清理
- 如果临时目录已存在，先删除再克隆
