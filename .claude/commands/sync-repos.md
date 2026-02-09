---
description: 同步 GitLab hpc/platform 和 hpc/sdk 下的所有仓库到本地
---

# Sync Repos Command

从 GitLab 同步 `hpc/platform` 和 `hpc/sdk` 两个 group 下的所有非空仓库。

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

3. **对每个仓库执行同步**：
   - 如果本地目录已存在：执行 `git pull --ff-only`
   - 如果本地目录不存在：执行 `git clone <http_url_to_repo>`
   - 跳过 `empty_repo: true` 的仓库

4. **输出汇总结果**：列出所有仓库及其同步状态 (clone/pull/skipped)

## 当前已知仓库

### Platform Group (`hpc/platform`)
- hpc-activity-api
- hpc-asset-api
- hpc-auth-service
- hpc-billing-service
- hpc-culling-service
- hpc-devspace-controller
- hpc-diagnosis-api
- hpc-event-exporter
- hpc-inference-controller
- hpc-infra-api
- hpc-job-controller
- hpc-minio-api
- hpc-notify-api
- hpc-ofs
- hpc-studio-api
- hpc-tensorboard-controller
- hpc-terminal-api
- hpc-ui

### SDK Group (`hpc/sdk`)
- hpc-go-sdk
- hpc-infer-engine
- hpc-py-sdk

## 注意事项

- 需要完整权限 (`required_permissions: ["all"]`)
  - 网络访问：调用 GitLab API
  - Git 写入：执行 `git clone` 和 `git pull`
- 工作目录：`/Users/gleaming/gitlab/hpc`
- 认证信息存储在 `~/.netrc`
- 空仓库会被自动跳过
- 如果 API 返回新仓库，自动 clone
- 使用 Python 解析 JSON（避免 shell 环境中 jq/base64 不可用问题）

## 示例输出

```
====== Platform Group ======
[hpc-asset-api] pull - Already up to date.
[hpc-infra-api] clone - Cloning into 'hpc-infra-api'...
[hpc-approval-service] skipped - empty repo

====== SDK Group ======
[hpc-py-sdk] clone - Cloning into 'hpc-py-sdk'...

====== 完成 ======
Platform: 17 个仓库
SDK: 3 个仓库
```
