---
name: hpc-k8s-deploy
description: Use when working with K8s deployment, Kustomize overlays, CRDs, config.yaml, or release manifests in HPC projects. Trigger words include deploy, kustomize, overlay, CRD, config.yaml, release, k8s, manifest, environment, cluster, prod, test, 部署, 发布, 环境, 集群.
---

# HPC K8s 部署规范

## 项目目录结构约定

所有 `hpc-*` 项目遵循统一的 Kustomize 布局：

```
k8s/
├── base/
│   ├── deployment/deployment.yaml + kustomization.yaml
│   ├── service/service.yaml + kustomization.yaml        # API 项目
│   ├── rbac/serviceaccount.yaml + role + binding         # 所有项目
│   ├── crd/*.yaml                                        # 仅 Controller 项目
│   ├── istio/virtualservice.yaml + authorizationpolicy   # 仅 API 项目
│   └── monitoring/servicemonitor.yaml                    # 部分项目
└── overlays/
    ├── prod/{集群名}/release/
    │   ├── config.yaml
    │   └── kustomization.yaml
    └── test/{集群名}/release/
        ├── config.yaml
        └── kustomization.yaml
```

## 项目分类

| 类型 | 有 CRD | 有 Istio | 有 Service | 副本数 | 项目列表 |
|------|:---:|:---:|:---:|:---:|---------|
| **Controller** | ✅ | ❌ | ❌ | 1（Leader Election） | job-controller, pipeline-controller, devspace-controller, inference-controller, tensorboard-controller |
| **API 服务** | ❌ | ✅ | ✅ | 2+ | auth-service, asset-api, studio-api, terminal-api, diagnosis-api, activity-api, notify-api |
| **后端服务** | ❌ | ❌ | ✅ | 1-2 | event-exporter, billing-service, culling-service |
| **前端** | ❌ | ✅ | ✅ | 2 | hpc-ui |

## 集群与环境

**生产集群（prod）：**
- `hpc-prod-al-sh01` — 阿里云上海 01（主集群）
- `hpc-prod-al-sh02` — 阿里云上海 02
- `hpc-prod-bd-su01` — 百度苏州 01
- `ack-hpc-pro-al01` — 阿里云（仅 billing-service）

**测试集群（test）：**
- `ack-hpc-test-al01` — 阿里云测试
- `hpc-test-al-sh01` — 上海测试（仅 pipeline-controller）

## CRD 清单

| Kind | API Group | 所属 Controller |
|------|----------|----------------|
| AIJob | hpc.org | hpc-job-controller |
| AIPipeline | hpc.org | hpc-pipeline-controller |
| Inference | hpc.org | hpc-inference-controller |
| Tensorboard | hpc.org | hpc-tensorboard-controller |
| DevSpace | hellorobotaxi.com | hpc-devspace-controller |

所有 CRD：Namespaced 作用域，启用 status 子资源，由 `controller-gen` 生成。

## Overlay kustomization.yaml 模板

### Controller 项目

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
namespace: hpc-system

resources:
  - ../../../../base/crd/
  - ../../../../base/rbac/
  - ../../../../base/deployment/

configMapGenerator:
  - name: {服务名}-config
    files:
      - config.yaml

images:
  - name: reg.hellorobotaxi.top/hpc-platform/{服务名}
    newTag: latest  # CI 会替换为实际版本

replicas:
  - name: {服务名}
    count: 1
```

### API 服务项目

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
namespace: hpc-system

resources:
  - ../../../../base/deployment/
  - ../../../../base/service/
  - ../../../../base/istio/

configMapGenerator:
  - name: {服务名}-config
    files:
      - config.yaml

commonLabels:
  environment: prod
  cluster: {集群名}
  app.kubernetes.io/name: {服务名}
  app.kubernetes.io/part-of: hpc-platform

replicas:
  - name: {服务名}
    count: 2
```

## config.yaml 约定

位于 `overlays/{环境}/{集群}/release/config.yaml`，通过 ConfigMap 挂载到 `/etc/config/config.yaml`。

常见配置段：

```yaml
# 日志
log:
  development: false
  level: info
  format: json

# Controller 专用（Leader Election）
controller:
  leaderElectionID: "{服务名}-controller-leader-election"
  maxConcurrentReconciles: 3

# 网络
network:
  domain: "hyper-ai.hellorobotaxi.top"

# SDK 集成
sdk:
  env: "prod"
  storageType: "oss-cn-shanghai-hpc-asset"

# 调度器
scheduling:
  schedulerName: "volcano"

# 工作负载初始化
workload:
  initImage: "reg.hellorobotaxi.top/hpc/setup:0.1.1"
```

## 硬性规则

- **命名空间：** 统一使用 `hpc-system`
- **镜像仓库：** `reg.hellorobotaxi.top/hpc-platform/{名称}` 或 `reg.hellorobotaxi.top/hpc/{名称}`
- **ConfigMap 挂载路径：** `/etc/config/config.yaml`
- **ConfigMap 名称：** `{服务名}-config`
- **节点选择器：** `hpc.org/pool: tools`
- **Controller 副本数：** 1（启用 Leader Election）
- **API 服务副本数：** 2+
- **RBAC 策略：** Controller 用 ClusterRole，API 用 Role（命名空间级别）
- **CRD 生成方式：** `make manifests`（controller-gen）

## 新增环境/集群操作步骤

1. 创建目录：`k8s/overlays/{环境}/{集群名}/release/`
2. 从相似集群复制 `config.yaml`，调整配置值
3. 从相似集群复制 `kustomization.yaml`
4. 按需更新 `images[].newTag`
5. 修改集群特定的配置（域名、存储、token 等）
6. 验证：`kustomize build k8s/overlays/{环境}/{集群}/release/`

## 新增服务操作步骤

1. 确定类型：Controller / API / 后端服务
2. 创建 `k8s/base/deployment/deployment.yaml`，参照已有项目
3. API 类型需增加 `k8s/base/service/`
4. API 类型需要入口时增加 `k8s/base/istio/`
5. 所有类型增加 `k8s/base/rbac/`，根据类型选择 ClusterRole 或 Role
6. Controller 类型增加 `k8s/base/crd/`
7. 为每个目标集群创建 overlay
8. 严格遵循命名约定
