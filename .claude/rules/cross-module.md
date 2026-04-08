---
description: HPC 平台跨模块集成规范（CRD 状态流转、错误码、事件、API 约定）
globs: "**/*.go"
alwaysApply: false
---

# 跨模块集成规范

## CRD Phase 状态机

所有 Controller 的 CRD Status.Phase 遵循统一生命周期语义：

```
Pending → Running/Training → Succeeded/Ready
                ↓
             Failed
                ↓
           (可选) Cancelled
```

Phase 命名约定：
- 初始态：`Pending`（资源刚创建，等待调度或初始化）
- 运行态：按业务语义选择 `Running` / `Training` / `Pulling`
- 终态成功：`Succeeded`（批处理）或 `Ready`（长驻服务）
- 终态失败：`Failed`
- 用户取消：`Cancelled`
- 降级态（仅长驻服务）：`Degraded`（部分副本不可用）
- 停止态（仅长驻服务）：`Stopped`

铁律：
- Phase 一旦进入终态（Succeeded/Failed/Cancelled），不允许回退到非终态
- 所有 Phase 变更必须同时更新 `LastUpdateTime`
- Status 必须携带 `Message` 和 `Reason` 字段辅助排障

## Reconciler 子资源模式

所有 Controller 遵循统一的 reconcile 子资源模式：

```
Reconcile → Get CR → 处理删除/Finalizer
  → reconcilePVC
  → reconcileDeployment/StatefulSet
  → reconcileService
  → reconcileVirtualService (如需)
  → syncStatus
```

铁律：
- 子资源 reconcile 函数命名统一：`reconcile<ResourceKind>`
- syncStatus 永远是最后一步，聚合所有子资源状态
- 子资源创建必须设 OwnerReference

## API 错误码约定

HTTP API 服务统一错误响应格式：

```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "用户可读的错误描述"
  }
}
```

错误码命名：大写蛇形 `RESOURCE_NOT_FOUND`，不用 HTTP 状态码做业务码。

标准错误码（所有 API 服务共享）：
- `INVALID_REQUEST` — 参数校验失败 (400)
- `UNAUTHORIZED` — 未认证 (401)
- `FORBIDDEN` — 无权限 (403)
- `RESOURCE_NOT_FOUND` — 资源不存在 (404)
- `RESOURCE_CONFLICT` — 资源冲突 (409)
- `QUOTA_EXCEEDED` — 超出配额 (422)
- `RATE_LIMITED` — 限流 (429)
- `INTERNAL_ERROR` — 内部错误 (500)

## K8s Event 规范

Controller 发送的 K8s Event 遵循统一格式：

```go
recorder.Eventf(obj, corev1.EventTypeNormal,
    "ReconcileSucceeded",   // Reason: PascalCase 动词+结果
    "资源 %s 创建成功",       // Message: 中文可读描述
    obj.Name,
)
```

Reason 命名约定：`<动作><结果>`
- 正常：`ReconcileSucceeded`, `PodCreated`, `ServiceReady`
- 警告：`ReconcileFailed`, `QuotaExceeded`, `ImagePullFailed`
