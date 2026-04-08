---
description: Kubernetes YAML / Helm / Kustomize 规范
globs: "**/*.{yaml,yml}"
alwaysApply: false
---

# K8s YAML 规范

## 铁律

- 资源名用小写 kebab-case: `hpc-devspace-controller`
- label 必须包含: `app.kubernetes.io/name`, `app.kubernetes.io/component`
- 容器必须设置 `resources.requests` 和 `resources.limits`
- 探针: `readinessProbe` 必配，`livenessProbe` 按需配置
- Secret 引用用 `secretKeyRef`，不硬编码在 YAML 中
- CRD 的 `additionalPrinterColumns` 至少包含 Phase 和 Age
- DaemonSet 用 `nodeSelector` 或 `affinity` 限制调度范围

## 反面示例

```yaml
# ❌ 不设 resource limits，Pod 可能吃光节点资源
containers:
  - name: worker
    image: my-image

# ✅ 必须声明 requests 和 limits
containers:
  - name: worker
    image: my-image
    resources:
      requests:
        cpu: "100m"
        memory: "128Mi"
      limits:
        cpu: "1"
        memory: "1Gi"

# ❌ 密码硬编码在 YAML 中
env:
  - name: DB_PASSWORD
    value: "p@ssw0rd123"

# ✅ 引用 Secret
env:
  - name: DB_PASSWORD
    valueFrom:
      secretKeyRef:
        name: db-credentials
        key: password

# ❌ 不设探针，K8s 无法判断容器健康状态
# ✅ 至少配 readinessProbe
readinessProbe:
  httpGet:
    path: /healthz
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 10

# ❌ CRD 没有 additionalPrinterColumns，kubectl get 看不到状态
# ✅ 至少包含 Phase 和 Age
additionalPrinterColumns:
  - name: Phase
    type: string
    jsonPath: .status.phase
  - name: Age
    type: date
    jsonPath: .metadata.creationTimestamp
```
