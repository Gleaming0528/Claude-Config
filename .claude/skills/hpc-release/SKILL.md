---
name: hpc-release
description: 处理 HPC 平台子项目的发布流程。适用于部署、打 tag、发版、上线。
---

# HPC 平台发布流程

## 概述

通过 `deploy.sh` 脚本为 submodule 自动创建递增版本 tag 并推送到 GitLab，触发 CI/CD 流水线完成部署。

## 发布前置条件

1. 代码已合并到 `main`/`master` 分支
2. 已 push 到远端
3. TypeScript 项目需通过 `tsc --noEmit && vite build`
4. Go 项目需通过 `go build ./...`

## 发布命令

```bash
# 工作目录：workspace 根目录
cd <repo-root>

# 先 dry-run 确认
./deploy.sh --dry-run <submodule-name>

# 确认无误后正式发布
./deploy.sh <submodule-name>
```

## 快速参考

| 场景 | 命令 |
|------|------|
| 发布单个服务 | `./deploy.sh hpc-ui` |
| 发布多个服务 | `./deploy.sh hpc-ui hpc-studio-api` |
| 发布全部 platform 组 | `./deploy.sh --group platform` |
| 发布全部 sdk 组 | `./deploy.sh --group sdk` |
| 发布所有 | `./deploy.sh --group all` |
| 只检查不发布 | `./deploy.sh --dry-run hpc-ui` |

## 脚本行为

1. 从 `.gitmodules` 解析 submodule 列表
2. `git fetch` 更新远端信息
3. `git ls-remote --tags` 获取远端最新 tag（`vX.Y.Z` 格式）
4. 对比 `main` 分支 HEAD 与最新 tag 的 commit
5. 有新提交 → patch 版本 +1（`v0.2.186` → `v0.2.187`）
6. 无新提交 → 跳过
7. `git tag` + `git push` 推送 tag 到远端

## Submodule 分组

| 组 | URL 路径特征 | 包含 |
|----|------------|------|
| `platform` | `hpc/platform/*` | hpc-ui, hpc-studio-api, hpc-job-controller 等 |
| `sdk` | `hpc/sdk/*` | SDK 项目 |
| `root` | `hpc/*`（非上述） | 其他 |

## 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| "无变更，跳过" | main 的 HEAD 和最新 tag 指向同一 commit | 先 push 新代码 |
| "未初始化的 submodule" | submodule 未 clone | `git submodule update --init <name>` |
| "无法确定默认分支" | remote HEAD 未设置 | 确认仓库有 main/master 分支 |
| tag 已存在 | 版本号冲突 | 脚本自动跳过，需手动处理 |

## 完整发布流程示例

```bash
# 1. 在子项目中完成开发并提交
cd hpc-ui
git add . && git commit -m "feat: ..."
git push

# 2. 回到 workspace 根目录
cd <repo-root>

# 3. dry-run 确认
./deploy.sh --dry-run hpc-ui
# 输出: 将创建tag: v0.2.187

# 4. 正式发布
./deploy.sh hpc-ui
# 输出: Tag推送成功, URL: https://gitlab.../hpc-ui/-/tags/v0.2.187
```

## 反合理化

| 借口 | 现实 |
|------|------|
| "代码刚 push，直接发吧不用 dry-run" | dry-run 花 2 秒，发错版本回滚花 2 小时。每次必须 dry-run。 |
| "改动很小，不用走完整发布流程" | 小改动也触发 CI/CD 流水线。流程保证的是一致性，不是改动大小。 |
| "先发上去看看效果" | 生产环境不是测试环境。发上去出问题影响所有用户。 |
| "build 之前验过了不用再验" | commit 之后可能有 rebase、merge，代码状态可能已变。发布前再验一次。 |
| "这个服务没人用，随便发" | 今天没人用不代表没有下游依赖。按标准流程走，成本一样。 |

## Red Flags

- 跳过 `--dry-run` 直接发布
- 子项目代码未 push 到远端就尝试发布
- 发布前没有在子项目中跑 build 验证
- 一次性发布大量不相关的子项目
- 发布失败后没有检查原因，直接重试
- tag 推送成功但没有确认 CI/CD 流水线状态

## 发布验证清单

每次发布确认：

- [ ] 代码已 push 到远端 main/master 分支
- [ ] 子项目 build 通过（前端 `tsc + vite build`，Go `go build ./...`）
- [ ] `./deploy.sh --dry-run` 确认版本号和变更内容正确
- [ ] `./deploy.sh` 执行成功，tag 已推送
- [ ] GitLab CI/CD 流水线触发并成功完成
- [ ] （如需要）通知相关同事发布完成
