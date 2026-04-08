---
description: Go Kubernetes Controller 开发规范
globs: "**/*.go"
alwaysApply: false
---

# Go Controller 规范

## Reconciler 结构

```go
func (r *Reconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
    obj := &v1.YourCRD{}
    if err := r.Get(ctx, req.NamespacedName, obj); err != nil {
        return ctrl.Result{}, client.IgnoreNotFound(err)
    }
    // 分阶段 reconcile 子资源
    if err := r.reconcilePVC(ctx, obj); err != nil {
        return ctrl.Result{}, err
    }
    if err := r.reconcileDeployment(ctx, obj); err != nil {
        return ctrl.Result{}, err
    }
    return r.syncStatus(ctx, obj)
}
```

## 铁律

- Reconciler 单文件不超过 300 行，超出必须拆分
- 不在 Reconcile 中发起阻塞超过 30s 的操作，长耗时任务委托 Job
- Status 更新用 `r.Status().Update()`，不混在 Spec 更新里
- 错误重试用 `ctrl.Result{RequeueAfter: ...}` 而非 `time.Sleep`
- 用 `controllerutil.SetControllerReference` 绑定 owner，确保级联删除
- 日志用 `log.FromContext(ctx)`，带 `req.NamespacedName` 上下文
- Finalizer 在 Delete 时处理清理，不在 reconcile 主流程中混入删除逻辑

## 反面示例

```go
// ❌ 在 Reconcile 里 Sleep 等待
func (r *Reconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
    time.Sleep(10 * time.Second) // 阻塞整个 worker
    // ...
}
// ✅ 用 RequeueAfter
return ctrl.Result{RequeueAfter: 10 * time.Second}, nil

// ❌ Status 和 Spec 混在一起更新
obj.Spec.Replicas = 3
obj.Status.Phase = "Running"
r.Update(ctx, obj) // Status 不会被更新
// ✅ 分开更新
r.Update(ctx, obj)           // 只改 Spec
r.Status().Update(ctx, obj)  // 只改 Status

// ❌ 在 Reconcile 里裸 panic 或 log.Fatal
if err != nil {
    log.Fatal("无法创建资源") // 整个进程崩掉
}
// ✅ 返回 error，让 controller-runtime 处理重试
return ctrl.Result{}, fmt.Errorf("创建资源失败: %w", err)

// ❌ 不设 OwnerReference，导致资源泄漏
deployment := &appsv1.Deployment{...}
r.Create(ctx, deployment)
// ✅ 设置 OwnerReference
controllerutil.SetControllerReference(obj, deployment, r.Scheme)
r.Create(ctx, deployment)
```
