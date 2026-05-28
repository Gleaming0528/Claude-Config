---
name: hyper-ai-sdk
description: >-
  Use when 操作 Hyper-AI、hyper-ai、hi 资源，或处理训练任务、开发环境、
  推理服务、数据集、模型、镜像、数据卷、代码仓库、队列、潮汐队列、Pipeline、
  GPU、集群、namespace、K8s 事件、诊断、上传、下载、预览、workspace 等平台能力。
---

# Hyper-AI SDK 能力参考

> 自动生成，版本 0.2.15

## 端到端工作流

### 提交训练任务

```python
from hyper_ai import HyperAI
client = HyperAI()

# 1. 确认队列和规格
queues = client.queues.list(namespace='<ns>')
specs = client.queues.specs('<队列名>')

# 2. 确认镜像存在（必须来自 reg.hellorobotaxi.top）
images = client.images.list(namespace='<ns>', name_like='<关键词>')

# 3. 创建任务
job = client.jobs.create(
    namespace='<ns>', name='<任务名>',
    queue='<队列>', spec='<规格>',
    image='reg.hellorobotaxi.top/...',
    command='torchrun train.py --data /mnt/data',
    mounts=[
        {'type': 'datasets', 'name': '<数据集>', 'version': 'v1', 'mountPath': '/mnt/data'},
        {'type': 'models', 'name': '<模型集>', 'version': 'v1', 'mountPath': '/mnt/models'},
    ],
)

# 4. 等待运行 + 跟踪日志
client.jobs.wait_until_running('<ns>', job.name)
for line in client.jobs.follow('<ns>', job.name):
    print(line)
```

### 从 HuggingFace 导入模型/数据集

```bash
# 导入模型（数据集同理，换 dataset）
hi model import-hf Qwen/Qwen2.5-7B -n <ns>
hi model list <ns> --name-like Qwen        # 拿到 UID
hi model version list <UID>                 # 等版本 status=Ready
# 挂载到任务
hi job create ... --mount models:Qwen2.5-7B:v1:/mnt/models
```

### 部署推理服务

```python
inf = client.inferences.create(
    namespace='<ns>', name='<服务名>',
    queue='<队列>', spec='<规格>',
    image='reg.hellorobotaxi.top/...',
    command='python serve.py --model /mnt/models',
    mounts=[{'type': 'models', 'name': '<模型>', 'version': 'v1', 'mountPath': '/mnt/models'}],
)
inf = client.inferences.wait_until_ready('<ns>', inf.name)
print(inf.endpoint)
```

### 创建开发环境

```python
ds = client.devspaces.create(
    namespace='<ns>', name='<环境名>',
    queue='<队列>', spec='<规格>',
    image='reg.hellorobotaxi.top/...',
)
ds = client.devspaces.wait_until_running('<ns>', ds.name)
print(ds.jupyter_url, ds.ssh_command)
```

### 诊断失败任务

```python
# 1. 查状态
job = client.jobs.get('<ns>', '<任务名>')
print(job.phase, job.is_terminal)

# 2. 查日志（最近 200 行）
logs = client.jobs.logs('<ns>', '<任务名>', tail=200)
for entry in logs:
    print(f'[{entry.pod}] {entry.line}')

# 3. 结构化诊断（AI 分析）
result = client.jobs.diagnose('<ns>', '<任务名>')

# 4. 丰富详情（pods、conditions、mounts）
detail = client.jobs.detail('<ns>', '<任务名>')
```

### 创建 Pipeline

```
1. 列出目标 ns 已有 pipeline  → 找最近 Succeeded 的作为参考
2. 检查 spec.templateRef.id   → 有模板则用 create_from_template（推荐）
3. 需要定制 tasks             → 从模板 API 取 tasks（队列名干净），修改后用 create
4. 创建成功后输出平台链接
```

**踩坑**：不要从运行过的 pipeline 取 tasks（`params.queue` 是内部 K8s 队列名会 404）；通知等轻量步骤用 CPU 队列 `cpu-common-al-sh01` + 规格 `1c-2g`。

## 挂载语法速查

所有 `--mount` 参数格式：`类型:名称:版本:容器内路径`

| 资产类型     | CLI 语法                             | 容器内路径示例    | 说明       |
| ------------ | ------------------------------------ | ----------------- | ---------- |
| 数据集       | `--mount datasets:名称:v1:/mnt/data` | `/mnt/data`       | 版本必填   |
| 模型集       | `--mount models:名称:v1:/mnt/models` | `/mnt/models`     | 版本必填   |
| 数据卷       | `--mount volumes:名称:_:/mnt/vol`    | `/mnt/vol`        | 版本填 `_` |
| 运行时数据卷 | `--mount runtimes:名称:_:/mnt/rt`    | `/mnt/rt`         | 版本填 `_` |
| 代码仓库     | 创建任务时选择仓库/分支/commit       | `/workspace/code` | Git 挂载   |

SDK 等价调用：`client.jobs.create(..., mounts=[{'type': 'datasets', 'name': '...', 'version': 'v1', 'mountPath': '/mnt/data'}])`

## 常见错误排查

| 现象                                   | 根因                                           | 解决                                                              |
| -------------------------------------- | ---------------------------------------------- | ----------------------------------------------------------------- |
| `namespace not found` 或 `403`         | namespace 未设置或无权限                       | 优先用 `namespace/name`；创建时用 `-n <ns>` 指定                  |
| `queue not found` / `获取队列失败 404` | 队列名拼错或用了内部 K8s 队列名                | `hi queue list` 确认可用队列名                                    |
| `image pull failed` / 镜像拉取超时     | 镜像不在 `reg.hellorobotaxi.top` 或 tag 不存在 | `hi image list -A` + `hi image version list <UID>` 确认           |
| 任务卡在 Pending                       | 队列无可用资源或规格不匹配                     | `hi queue specs <队列>` 确认规格，`hi job diagnose <任务>` 查诊断 |
| 挂载的数据为空                         | 数据集/模型集版本未打或名称拼错                | `hi dataset list` + `hi dataset version list <UID>` 确认版本存在  |
| checkpoint 写失败（潮汐队列）          | 追加写或写到非 `/workspace/output/`            | 见潮汐队列约束：一次性写到 `/workspace/output/`                   |
| SDK `CredentialExpiredError`           | token 过期                                     | `hi login` 重新认证                                               |
| `hi` 命令无响应                        | 网络不通或 API 地址错误                        | `hi config show` 检查环境和 API 地址                              |

## 平台设计原则

### 事实优先

- 不要凭空补全平台行为、资源状态、失败原因或用户环境。缺少证据时说明未知，并引导用户查询平台资源、日志、诊断、事件和资产详情。
- 解释 K8s Event 时必须看发生时间、对象、原因和消息；事件对象仍存在不等于当前有错，历史 Warning 也不等于本次失败根因。先建立时间线，再判断事件与任务状态、日志、指标是否有关联。
- 平台已有结构化能力时优先使用：任务详情、诊断、日志、workspace、数据集、模型集、镜像、代码仓库、队列规格。不要用猜测替代平台查询结果。

### 资产优先

- 默认引导用户使用平台资产能力：数据放数据集，模型/权重放模型集，代码放代码仓库，镜像放镜像平台；训练任务、Pipeline、开发环境和推理服务通过挂载/选择这些资产来消费。
- 不要把数据卷当成默认推荐。数据卷不一定更好，成本高，大规模任务下通常无法线性扩展；能用数据集、模型集和代码仓库表达的输入，应优先走对象存储加速访问的资产方案。
- 只有用户明确需要 POSIX 语义、共享可写状态或短期交互式存储，并且确认成本与扩展性影响后，才考虑数据卷。

## 创建资源前的硬约束

### 镜像来源

- 训练任务、开发环境、推理服务、Pipeline 中使用的镜像必须先能在镜像平台查询到：`https://reg.hellorobotaxi.top/`。
- 容器镜像引用必须来自 `reg.hellorobotaxi.top/...`；不要直接使用 `docker.io/...`、`nvcr.io/...`、个人私有仓库或用户口述但平台查不到的镜像名。
- 提交资源前先查镜像：CLI 用 `hi image list -A` 和 `hi image version list <镜像UID>`；SDK 用 `client.images.list(...)` 和 `client.images.list_versions(image.uid)`。
- 查不到镜像时，先让用户在镜像平台注册/同步镜像；`client.images.create(..., image_url=...)` 只用于登记已在平台 registry 存在的镜像地址。

### 潮汐队列

当队列名称/描述包含“潮汐”，或用户明确要求使用潮汐队列时，按下面规则创建训练任务或 Pipeline：

1. **禁止数据卷。** 不使用 `volumes:` 挂载、`hi volume ...`、`client.volumes` 或 `/mnt/vol`。依赖数据必须先上传到数据集，模型/权重必须先上传到模型集，再用 `--mount datasets:名称:版本:/mnt/data`、`--mount models:名称:版本:/mnt/models` 挂载，并让代码读取这些挂载路径。
2. **必须 Git 挂载代码。** 先把 GitLab 仓库注册到代码管理：`hi code create ...` 或 `client.codes.create(...)`；创建任务时选择对应仓库、分支和 commit。不要依赖镜像内置代码、workspace 手动上传代码或数据卷代码目录。
3. **输出只能写到 `/workspace/output/`。** 潮汐队列中 `/workspace/output/` 是唯一可写且唯一可带回路径；启动命令、训练代码、日志、指标、checkpoint、模型产物、临时输出和中间文件都不得写到 `/workspace/logs`、`/tmp`、数据集、模型集、数据卷或其他路径。
4. **禁止依赖 reopen/append write。** 潮汐队列存储不支持重新打开同一文件追加写。提交前检查启动命令和训练代码，避免 `>>`、`tee -a`、`open(..., "a")`、JSONL 追加日志、反复覆盖同一 checkpoint 文件。实时日志走 stdout/stderr；需要带回的文件应在 `/workspace/output/` 下保存到新文件或新目录，checkpoint 先完整生成再一次性落到 `/workspace/output/`。

提交潮汐队列任务前，必须能回答：镜像是否可在镜像平台查询到、数据/模型是否已经资产化并挂载、GitLab 仓库/分支/commit 是否已选定、所有回收产物是否只写 `/workspace/output/` 且不追加写。

## 初始化

```python
from hyper_ai import HyperAI

client = HyperAI()                              # 从环境变量/配置文件
client = HyperAI(api_key="<token>")             # 显式 token
client = HyperAI(api_key="<token>", env="test") # 测试环境

# 绑定 namespace（推荐）
ns = client.ns("ad-perception")
jobs = ns.jobs.list()  # 不用再传 namespace
```

默认 namespace：`hi ns use <ns>`，或环境变量 `HYPER_AI_NAMESPACE`（优先级高于配置文件）

便捷函数：`import hyper_ai as hi` → `hi.train(...)` / `hi.dev(...)` / `hi.serve(...)` 等价于 `client.jobs.create` / `client.devspaces.create` / `client.inferences.create`。

## API 参考

**资产类通用方法**（适用于 `client.datasets` / `client.models` / `client.volumes` / `client.runtimes`）：

| 方法                                                  | 说明                       |
| ----------------------------------------------------- | -------------------------- |
| `create(...)`                                         | 创建资源                   |
| `delete(name_or_uid)`                                 | 删除                       |
| `get(name_or_uid)`                                    | 获取详情                   |
| `list(namespace, name_like, page, page_size)`         | 分页列表                   |
| `iter(namespace, name_like, page_size=100)`           | 自动分页迭代               |
| `ls(uid_or_name, path, version, recursive)`           | 列出文件                   |
| `upload(uid_or_name, local_path, remote_path, ...)`   | 上传（秒传+断点续传+并发） |
| `download(uid_or_name, remote_path, local_path, ...)` | 下载                       |
| `preview(uid_or_name, remote_path, max_bytes=4096)`   | 预览文件内容               |
| `storage(uid_or_name, use='download')`                | 获取 StorageClient         |

`datasets`/`models` 额外支持：`create_version`、`get_version`、`list_versions`（资产版本化）。

### client.jobs — 训练任务

| 方法                                                                                                                                                                                 | 说明                                                         |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------ |
| `create(namespace, name, queue, spec, framework='pytorch', image, command, workers=0, owner, env, mounts, max_retries=0, code_source, model_output, template_id, annotations)` → Job | 创建 AIJob。cluster 从 queue 自动推导。                      |
| `delete(namespace, name, cluster)` → NoneType                                                                                                                                        | 删除 AIJob。                                                 |
| `detail(namespace, name)` → JobDetail                                                                                                                                                | 获取 AIJob 丰富详情，包含解析后的 pods、mounts、conditions。 |
| `diagnose(namespace, name, cluster, question, resource_type='aijob', timeout=600.0)` → dict[str, Any]                                                                                | 调用诊断服务，返回结构化诊断结果。                           |
| `exec(namespace, name, command, pod, container, timeout=30.0)` → str                                                                                                                 | 在任务 Pod 中执行命令并返回输出。                            |
| `exec_interactive(namespace, name, pod, container)` → NoneType                                                                                                                       | 交互式终端进入任务 Pod（类似 kubectl exec -it）。            |
| `follow(namespace, name, tail=50, pod)` → Iterator[str]                                                                                                                              | 实时跟踪 AIJob 日志（类似 kubectl logs -f）。                |
| `get(namespace, name, cluster)` → Job                                                                                                                                                | 获取 AIJob 详情。                                            |
| `iter(namespace, status, page_size=100)` → Iterator[Job]                                                                                                                             | 自动分页迭代所有 AIJob。                                     |
| `list(namespace, cluster, owner, status, name_like, page=1, page_size=20)` → PagedList[Job]                                                                                          | 列出 AIJob。                                                 |
| `logs(namespace, name, tail=100, from_ms, to_ms, search, pod)` → list[LogEntry]                                                                                                      | 获取 AIJob 日志（通过 studio-api → Loki）。                  |
| `set_priority(namespace, name, priority, cluster)` → NoneType                                                                                                                        | 修改 AIJob 调度优先级。                                      |
| `stop(namespace, name, cluster)` → NoneType                                                                                                                                          | 停止 AIJob。                                                 |
| `wait_until_done(namespace, name, timeout=7200.0, interval=10.0)` → Job                                                                                                              | 等待任务完成（成功、失败或停止）。                           |
| `wait_until_running(namespace, name, timeout=600.0, interval=5.0)` → Job                                                                                                             | 等待任务进入运行状态。                                       |
| `workspace_download(namespace, name, remote_path, local_path, progress_callback)` → str                                                                                              | 下载 AIJob workspace 中的文件。                              |
| `workspace_ls(namespace, name, path='', recursive=False)` → list[FileEntry]                                                                                                          | 列出 AIJob workspace 中的文件。                              |
| `workspace_preview(namespace, name, remote_path, max_bytes=4096)` → bytes                                                                                                            | 预览 AIJob workspace 中的文件内容。                          |
| `workspace_storage(namespace, name, use='download')` → StorageClient                                                                                                                 | 获取绑定 AIJob workspace 的 StorageClient 实例。             |
| `workspace_upload(namespace, name, local_path, remote_path='', progress_callback, skip_existing=True, enable_resume=True, concurrency=10, pattern)` → str                            | 上传文件到 AIJob workspace。支持秒传、断点续传、并发上传。   |

### client.devspaces — 开发环境

| 方法                                                                                   | 说明                                               |
| -------------------------------------------------------------------------------------- | -------------------------------------------------- |
| `create(namespace, name, queue, spec, image, services, mounts, env, owner)` → DevSpace | 创建 DevSpace。cluster 从 queue 自动推导。         |
| `delete(namespace, name, cluster)` → NoneType                                          |                                                    |
| `exec(namespace, name, command, container='', timeout=30.0)` → str                     | 在 DevSpace Pod 中执行命令并返回输出。             |
| `exec_interactive(namespace, name, container='')` → NoneType                           | 交互式终端进入 DevSpace（类似 kubectl exec -it）。 |
| `get(namespace, name, cluster)` → DevSpace                                             |                                                    |
| `iter(namespace, status, page_size=100)` → Iterator[DevSpace]                          | 自动分页迭代所有开发环境。                         |
| `list(namespace, owner, status, page=1, page_size=20)` → PagedList[DevSpace]           |                                                    |
| `start(namespace, name, cluster)` → DevSpace                                           | 启动 DevSpace。                                    |
| `stop(namespace, name, cluster)` → NoneType                                            |                                                    |
| `wait_until_running(namespace, name, timeout=300.0, interval=5.0)` → DevSpace          | 等待开发环境进入运行状态。                         |

### client.inferences — 推理服务

| 方法                                                                                               | 说明                       |
| -------------------------------------------------------------------------------------------------- | -------------------------- |
| `create(namespace, name, queue, spec, image, command, replicas=1, mounts, env, owner)` → Inference |                            |
| `delete(namespace, name, cluster)` → NoneType                                                      |                            |
| `get(namespace, name, cluster)` → Inference                                                        |                            |
| `iter(namespace, page_size=100)` → Iterator[Inference]                                             | 自动分页迭代所有推理服务。 |
| `list(namespace, page=1, page_size=20)` → PagedList[Inference]                                     |                            |
| `restart(namespace, name, cluster, strategy)` → Inference                                          | 重启推理服务。             |
| `scale(namespace, name, replicas, cluster)` → NoneType                                             |                            |
| `start(namespace, name, cluster)` → Inference                                                      |                            |
| `stop(namespace, name, cluster)` → Inference                                                       |                            |
| `wait_until_ready(namespace, name, timeout=300.0, interval=5.0)` → Inference                       | 等待推理服务就绪。         |

### client.tensorboards — TensorBoard

| 方法                                                                     | 说明 |
| ------------------------------------------------------------------------ | ---- |
| `create(namespace, name, queue, spec, log_sources, owner)` → TensorBoard |      |
| `delete(namespace, name, cluster)` → NoneType                            |      |
| `get(namespace, name, cluster)` → TensorBoard                            |      |
| `list(namespace, page=1, page_size=20)` → PagedList[TensorBoard]         |      |

### client.queues — 调度队列

| 方法                                                                                                         | 说明                              |
| ------------------------------------------------------------------------------------------------------------ | --------------------------------- |
| `create(name, cluster, tenant, namespaces, description='', specs, namespace_access_mode='ReadOnly')` → Queue | 创建调度队列。                    |
| `delete(name)` → NoneType                                                                                    | 删除队列。                        |
| `get(name)` → Queue                                                                                          | 获取队列详情。                    |
| `list(namespace, page=1, page_size=100)` → PagedList[Queue]                                                  | 列出队列（可按 namespace 过滤）。 |
| `specs(queue_name)` → list[ResourceSpec]                                                                     | 获取队列可用的资源规格列表。      |
| `update(name, specs, namespaces, namespace_access_mode='ReadOnly')` → Queue                                  | 更新队列资源规格或可见命名空间。  |

### client.pipelines — Pipeline

| 方法                                                                                                 | 说明                        |
| ---------------------------------------------------------------------------------------------------- | --------------------------- |
| `cancel(namespace, name, cluster)` → NoneType                                                        |                             |
| `create(namespace, name, queue, spec, tasks, params, template_ref, timeout, owner)` → Pipeline       |                             |
| `create_from_template(namespace, name, queue, spec, template_id, params, timeout, owner)` → Pipeline | 从模板创建 Pipeline。       |
| `create_template(name, tasks, namespace, description, params, cluster, timeout)` → dict[str, Any]    | 创建 Pipeline 模板。        |
| `delete(namespace, name, cluster)` → NoneType                                                        |                             |
| `delete_template(template_id)` → NoneType                                                            | 删除 Pipeline 模板。        |
| `finished(namespace, name, kwargs)` → bool                                                           | 判断 Pipeline 是否已结束。  |
| `get(namespace, name, cluster)` → Pipeline                                                           |                             |
| `get_template(template_id)` → dict[str, Any]                                                         |                             |
| `iter(namespace, page_size=100)` → Iterator[Pipeline]                                                | 自动分页迭代所有 Pipeline。 |
| `list(namespace, page=1, page_size=20)` → PagedList[Pipeline]                                        |                             |
| `list_templates(namespace, name_like, page=1, page_size=20)` → list[dict[str, Any]]                  |                             |
| `phase(namespace, name, kwargs)` → str                                                               | 获取 Pipeline 运行状态。    |
| `retry(namespace, name, cluster)` → NoneType                                                         | 重试失败的 Pipeline。       |
| `update_template(template_id, spec)` → dict[str, Any]                                                | 更新 Pipeline 模板。        |

### client.namespaces — 命名空间

| 方法                             | 说明 |
| -------------------------------- | ---- |
| `get(name)` → Namespace          |      |
| `list(tenant)` → list[Namespace] |      |

### client.images — 容器镜像

| 方法                                                                              | 说明       |
| --------------------------------------------------------------------------------- | ---------- |
| `create(namespace, name, description='', image_url='', tags, labels)` → Image     | 创建镜像。 |
| `delete(name_or_uid)` → NoneType                                                  |            |
| `get(name_or_uid)` → Image                                                        |            |
| `list(namespace, name_like, image_type, page=1, page_size=20)` → PagedList[Image] | 列出镜像。 |
| `list_versions(image_uid, page=1, page_size=20)` → PagedList[ImageVersion]        |            |

### client.codes — 代码仓库

| 方法                                                                                                                                                       | 说明                                   |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------- |
| `clone(name_or_uid, path, ref_name, tag, depth=1, include_submodule=False, include_lfs=False, max_retries=3, retry_delay=5, timeout=300)` → GitCloneResult | 克隆代码仓库到本地路径。               |
| `create(namespace, name, git_url='', description='', tags, labels)` → Code                                                                                 | 创建代码仓库。                         |
| `delete(name_or_uid)` → NoneType                                                                                                                           |                                        |
| `get(name_or_uid)` → Code                                                                                                                                  |                                        |
| `iter(namespace, name_like, page_size=100)` → Iterator[Code]                                                                                               | 自动分页迭代所有代码仓库。             |
| `list(namespace, name_like, page=1, page_size=20)` → PagedList[Code]                                                                                       |                                        |
| `list_branches(code_uid, name_like, page=1, page_size=50)` → list[GitBranch]                                                                               | 列出代码仓库的分支。                   |
| `list_commits(code_uid, ref='master', page=1, page_size=20)` → list[GitCommit]                                                                             | 列出代码仓库的提交（需指定 refName）。 |
| `list_tags(code_uid, name_like, page=1, page_size=50)` → list[GitTag]                                                                                      | 列出代码仓库的标签。                   |

## 数据模型

**所有资源通用属性**：`name`, `uid`, `namespace`, `description`（property）。
有状态资源额外有 `phase`（str）、`created_at`（Optional[str]）、`owner`（Optional[str]）。
下面只列各模型的**差异字段**。

### Job — 训练任务

| 属性          | 类型  | 说明         |
| ------------- | ----- | ------------ |
| job_type      | str   | jobType      |
| cluster_name  | str   | clusterName  |
| progress      | float |              |
| total_seconds | float | totalSeconds |
| cluster       | str   | (property)   |
| is_running    | bool  | (property)   |
| is_terminal   | bool  | (property)   |
| queue         | str   | (property)   |
| spec_name     | str   | (property)   |

### AssetVersion — 资产版本

| 属性         | 类型          | 说明                                |
| ------------ | ------------- | ----------------------------------- |
| format       | str           | (property)                          |
| s3_path      | Optional[str] | (property)                          |
| source_label | str           | (property)                          |
| source_name  | str           | HF 导入时返回 repo ID，否则返回空。 |
| status_label | str           | (property)                          |

**DevSpace**：`jupyter_url`, `ssh_command` | **Inference**：`endpoint` | **Queue**：`cluster`, `specs` | **Image**：`image_type` | **Volume**：`mounts` | **Code**：`git_url`

### JobDetail — 任务详情

| 属性               | 类型                 | 说明 |
| ------------------ | -------------------- | ---- |
| job                | Job                  |      |
| active_pods        | list[dict[str, Any]] |      |
| pod_stats          | dict[str, Any]       |      |
| train_start_time   | str                  |      |
| description        | str                  |      |
| controller_phase   | str                  |      |
| controller_message | str                  |      |

### LogEntry — 日志条目

| 属性      | 类型 | 说明 |
| --------- | ---- | ---- |
| timestamp | str  |      |
| line      | str  |      |
| pod       | str  |      |
| container | str  |      |

## CLI

CLI 命令与 SDK 一一对应：`hi <资源> <操作>` ↔ `client.<资源>.<操作>(...)`。
例如 `hi job create` ↔ `client.jobs.create()`，`hi dataset upload` ↔ `client.datasets.upload()`。

完整命令列表：`hi --help`；子命令帮助：`hi <资源> <操作> --help`。

## 平台链接

| 环境 | 域名                                      |
| ---- | ----------------------------------------- |
| prod | `https://hyper-ai.hellorobotaxi.top`      |
| test | `https://hyper-ai-test.hellorobotaxi.top` |

创建/查询资源后**必须输出对应链接**，用 `client.base_url` 取域名。

| 资源        | URL 模式                                           |
| ----------- | -------------------------------------------------- |
| Job         | `{base}/jobs/{namespace}/{cluster}/{name}`         |
| DevSpace    | `{base}/devspaces/{namespace}/{cluster}/{name}`    |
| Inference   | `{base}/inferences/{namespace}/{cluster}/{name}`   |
| Pipeline    | `{base}/pipeline/{namespace}/{name}`               |
| Dataset     | `{base}/datasets/{uid}`                            |
| Model       | `{base}/models/{uid}`                              |
| Volume      | `{base}/volumes/{name}`                            |
| TensorBoard | `{base}/tensorboards/{namespace}/{cluster}/{name}` |
| Image       | `{base}/images/{uid}`                              |
| Code        | `{base}/codes/{uid}`                               |

用户粘贴平台链接时，从 URL path 解析资源类型（`/jobs/`→Job, `/datasets/`→Dataset 等）和坐标参数。
