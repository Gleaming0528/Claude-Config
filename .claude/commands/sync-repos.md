---
description: 同步 GitLab hpc/platform 和 hpc/sdk 下的所有仓库到本地（submodule 模式）
---

# Sync Repos Command

从 GitLab 同步 `hpc/platform` 和 `hpc/sdk` 两个 group 下的所有非空仓库。
本仓库使用 **git submodule** 管理所有子仓库。

## 执行步骤

1. **调用 GitLab API** 获取两个 group 下的所有项目列表：
   - `https://gitlab.hellorobotaxi.top/api/v4/groups/hpc%2Fplatform/projects?per_page=100&include_subgroups=true`
   - `https://gitlab.hellorobotaxi.top/api/v4/groups/hpc%2Fsdk/projects?per_page=100&include_subgroups=true`
   - Token 从 `~/.netrc` 中获取 (`grep -A2 'gitlab.hellorobotaxi.top' ~/.netrc | grep password | awk '{print $2}'`)

2. **解析返回的 JSON**，提取每个项目的：
   - `path` (仓库名)
   - `http_url_to_repo` (clone URL)
   - `empty_repo` (是否为空仓库，跳过空仓库)
   - `path_with_namespace` (用于确定是 platform 还是 sdk)

3. **读取 `.gitmodules`**，获取已注册的 submodule 列表

4. **对每个远端仓库执行同步**：
   - 如果已是 submodule：执行 `git submodule update --remote --merge -- <path>`
   - 如果不是 submodule 且本地目录不存在：执行 `git submodule add <http_url_to_repo> <path>`
   - 跳过 `empty_repo: true` 的仓库

5. **初始化未初始化的 submodule**：`git submodule update --init`

6. **输出汇总结果**：列出所有仓库及其同步状态 (add/update/skipped)

7. **更新本文档**：将 API 返回的实际仓库列表与下方「当前已知仓库」对比，如有新增或删除，自动更新本文件（`.claude/commands/sync-repos.md`）中的列表和示例输出中的数量

## 当前已知仓库

### Platform Group (`hpc/platform`)
- hpc-activity-api
- hpc-argo-template
- hpc-asset-api
- hpc-auth-service
- hpc-budget-api
- hpc-culling-service
- hpc-devspace-controller
- hpc-diagnosis-api
- hpc-event-exporter
- hpc-inference-controller
- hpc-infra-api
- hpc-job-controller
- hpc-minio-api
- hpc-node-autoscaler
- hpc-notify-api
- hpc-ofs
- hpc-pipeline-controller
- hpc-studio-api
- hpc-tensorboard-controller
- hpc-terminal-api
- hpc-ui

### SDK Group (`hpc/sdk`)
- hpc-event-sdk
- hpc-go-sdk
- hpc-infer-engine
- hyper-ai

### 其他
- build
- hpc-doc

## 注意事项

- 需要完整权限 (`required_permissions: ["all"]`)
  - 网络访问：调用 GitLab API
  - Git 写入：执行 `git submodule add` 和 `git submodule update`
- 工作目录：`/Users/gleaming/gitlab/workspace`
- 认证信息存储在 `~/.netrc`
- 空仓库会被自动跳过
- 如果 API 返回新仓库，自动 `git submodule add`
- 使用 Python 解析 JSON（避免 shell 环境中 jq/base64 不可用问题）

## 日常拉取

不需要执行此命令，直接在 workspace 根目录运行 `pull` 即可：

```bash
pull    # alias → ~/scripts/pull.sh
        # 1. git pull（父仓库）
        # 2. git submodule update --remote --merge --jobs=8（所有子模块）
```

## 示例输出

```
====== Platform Group ======
[hpc-asset-api] update - Already up to date.
[hpc-approval-service] add - 添加为 submodule
[hpc-empty-repo] skipped - empty repo

====== SDK Group ======
[hyper-ai] update - Already up to date.

====== 完成 ======
Platform: 21 个仓库
SDK: 4 个仓库
其他: 2 个仓库
```
