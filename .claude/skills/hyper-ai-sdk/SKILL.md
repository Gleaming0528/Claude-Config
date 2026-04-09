---
name: hyper-ai-sdk
description: Hyper-AI 超算平台 SDK 完整能力参考。适用于操作训练任务、开发环境、推理服务、数据集、模型、镜像、数据卷、代码仓库、队列、Pipeline 等资源。
---

# Hyper-AI SDK 能力参考

> 自动生成，版本 0.0.0

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

默认 namespace：`hi ns use <ns>` / `hi config set-namespace`，或环境变量 `HYPER_AI_NAMESPACE`（优先级高于配置文件）

## 资源管理器

### client.jobs — 训练任务

AIJob 训练任务管理器。

| 方法 | 签名 | 返回 | 说明 |
|------|------|------|------|
| create | (namespace, name, *, queue: str, spec: str, framework: Framework = 'pytorch', i...) | Job | 创建 AIJob。cluster 从 queue 自动推导。framework 大小写不敏感（自动转小写），owner 未指定时自动填充当前登录用户。 |
| delete | (namespace, name, cluster: typing.Union[str, NoneType] = None) | NoneType | 删除 AIJob。 |
| detail | (namespace, name) | JobDetail | 获取 AIJob 丰富详情，包含解析后的 pods、mounts、conditions。 |
| diagnose | (namespace, name, cluster: typing.Union[str, NoneType] = N...) | dict[str, Any] | 调用诊断服务，返回结构化诊断结果。 |
| exec | (namespace, name, command, *, pod: typing.Union[str, NoneType] = None, container: typing.Union[str, NoneType] = None, ...) | str | 在任务 Pod 中执行命令并返回输出。 |
| exec_interactive | (namespace, name, *, pod: typing.Union[str, NoneType] = None, container: typing.Union[str, NoneType] = None) | NoneType | 交互式终端进入任务 Pod（类似 kubectl exec -it）。 |
| follow | (namespace, name, tail: int = 50, pod: typing.Union[str, N...) | Iterator[str] | 实时跟踪 AIJob 日志（类似 kubectl logs -f）。 |
| get | (namespace, name, cluster: typing.Union[str, NoneType] = None) | Job | 获取 AIJob 详情。 |
| iter | (namespace=None, status: typing.Union[str, NoneType] = Non...) | Iterator[Job] | 自动分页迭代所有 AIJob。 |
| list | (namespace=None, cluster: typing.Union[str, NoneType] = No...) | list[Job] | 列出 AIJob。 |
| logs | (namespace, name, tail: int = 100, from_ms: typing.Union[i...) | list[LogEntry] | 获取 AIJob 日志（通过 studio-api → Loki）。 |
| set_priority | (namespace, name, priority, cluster: typing.Union[str, Non...) | NoneType | 修改 AIJob 调度优先级。 |
| stop | (namespace, name, cluster: typing.Union[str, NoneType] = None) | NoneType | 停止 AIJob。 |
| workspace_download | (namespace, name, remote_path, local_path, progress_callba...) | str | 下载 AIJob workspace 中的文件。 |
| workspace_ls | (namespace, name, path='', recursive=False) | list[FileEntry] | 列出 AIJob workspace 中的文件。 |
| workspace_preview | (namespace, name, remote_path, max_bytes=4096) | bytes | 预览 AIJob workspace 中的文件内容。 |
| workspace_storage | (namespace, name, use='download') | StorageClient | 获取绑定 AIJob workspace 的 StorageClient 实例。 |
| workspace_upload | (namespace, name, local_path, remote_path='', progress_cal...) | str | 上传文件到 AIJob workspace。 |

### client.devspaces — 开发环境

DevSpace 开发环境管理器。

| 方法 | 签名 | 返回 | 说明 |
|------|------|------|------|
| create | (namespace, name, queue: str, spec: str, image: str, servi...) | DevSpace | 创建 DevSpace。cluster 从 queue 自动推导。 |
| delete | (namespace, name, cluster: typing.Union[str, NoneType] = None) | NoneType |  |
| exec | (namespace, name, command, container: str = '', timeout: f...) | str | 在 DevSpace Pod 中执行命令并返回输出。 |
| exec_interactive | (namespace, name, container: str = '') | NoneType | 交互式终端进入 DevSpace（类似 kubectl exec -it）。 |
| get | (namespace, name, cluster: typing.Union[str, NoneType] = None) | DevSpace |  |
| list | (namespace=None, owner: typing.Union[str, NoneType] = None...) | list[DevSpace] |  |
| start | (namespace, name, cluster: typing.Union[str, NoneType] = None) | DevSpace | 启动 DevSpace。 |
| stop | (namespace, name, cluster: typing.Union[str, NoneType] = None) | NoneType |  |

### client.inferences — 推理服务

Inference 推理服务管理器。

| 方法 | 签名 | 返回 | 说明 |
|------|------|------|------|
| create | (namespace, name, queue: str, spec: str, image: str, comma...) | Inference |  |
| delete | (namespace, name, cluster: typing.Union[str, NoneType] = None) | NoneType |  |
| get | (namespace, name, cluster: typing.Union[str, NoneType] = None) | Inference |  |
| list | (namespace=None, page: int = 1, page_size: int = 20) | list[Inference] |  |
| restart | (namespace, name, cluster: typing.Union[str, NoneType] = N...) | Inference | 重启推理服务。 |
| scale | (namespace, name, replicas, cluster: typing.Union[str, Non...) | NoneType |  |
| start | (namespace, name, cluster: typing.Union[str, NoneType] = None) | Inference |  |
| stop | (namespace, name, cluster: typing.Union[str, NoneType] = None) | Inference |  |

### client.tensorboards — TensorBoard

TensorBoard 可视化管理器。

| 方法 | 签名 | 返回 | 说明 |
|------|------|------|------|
| create | (namespace, name, queue: str, spec: str, log_sources: list...) | TensorBoard |  |
| delete | (namespace, name, cluster: typing.Union[str, NoneType] = None) | NoneType |  |
| get | (namespace, name, cluster: typing.Union[str, NoneType] = None) | TensorBoard |  |
| list | (namespace=None, page: int = 1, page_size: int = 20) | list[TensorBoard] |  |

### client.datasets — 数据集

Dataset 数据集管理器。

| 方法 | 签名 | 返回 | 说明 |
|------|------|------|------|
| create | (name, *, namespace=None, description: str = '', tags: typing.Unio...) | Dataset |  |
| create_version | (dataset_uid, version_name, description: str = '', labels:...) | AssetVersion |  |
| delete | (name_or_uid) | NoneType |  |
| download | (dataset_uid, remote_path, local_path, version: typing.Uni...) | str | 下载数据集中的文件。 |
| get | (name_or_uid) | Dataset |  |
| get_version | (dataset_uid, version_name) | AssetVersion |  |
| list | (namespace=None, name_like: typing.Union[str, NoneType] = ...) | list[Dataset] |  |
| list_versions | (dataset_uid, page: int = 1, page_size: int = 20) | list[AssetVersion] |  |
| ls | (dataset_uid, path='', *, version=None, recursive=False) | list[FileEntry] | 列出数据集中的文件。 |
| preview | (dataset_uid, remote_path, *, version=None, max_bytes=4096) | bytes | 预览数据集中的文件内容。 |
| storage | (dataset_uid, use: Literal['download','upload']='download', version=None) | StorageClient | 获取绑定数据集的 StorageClient 实例。 |
| upload | (dataset_uid, local_path, remote_path='', version: typing....) | str | 上传文件到数据集。 |

### client.models — 模型

Model 模型管理器。

| 方法 | 签名 | 返回 | 说明 |
|------|------|------|------|
| create | (name, *, namespace=None, description: str = '', tags: typing.Unio...) | Model |  |
| create_version | (model_uid, version_name, description: str = '', labels: t...) | AssetVersion |  |
| delete | (name_or_uid) | NoneType |  |
| download | (model_uid, remote_path, local_path, version: typing.Union...) | str | 下载模型中的文件。 |
| get | (name_or_uid) | Model |  |
| get_version | (model_uid, version_name) | AssetVersion |  |
| list | (namespace=None, name_like: typing.Union[str, NoneType] = ...) | list[Model] |  |
| list_versions | (model_uid, page: int = 1, page_size: int = 20) | list[AssetVersion] |  |
| ls | (model_uid, path='', *, version=None, recursive=False) | list[FileEntry] | 列出模型中的文件。 |
| preview | (model_uid, remote_path, *, version=None, max_bytes=4096) | bytes | 预览模型中的文件内容。 |
| storage | (model_uid, use: Literal['download','upload']='download', version=None) | StorageClient | 获取绑定模型的 StorageClient 实例。 |
| upload | (model_uid, local_path, remote_path='', version: typing.Un...) | str | 上传文件到模型。 |

### client.queues — 调度队列

Queue 调度队列管理器。

| 方法 | 签名 | 返回 | 说明 |
|------|------|------|------|
| get | (name) | Queue |  |
| list | (namespace=None, page: int = 1, page_size: int = 100) | list[Queue] |  |
| specs | (queue_name) | list[ResourceSpec] |  |

### client.pipelines — Pipeline

Pipeline 工作流管理器。

| 方法 | 签名 | 返回 | 说明 |
|------|------|------|------|
| cancel | (namespace, name, cluster: typing.Union[str, NoneType] = None) | NoneType |  |
| create | (namespace, name, queue: str, spec: str, tasks: list[dict[...) | dict[str, Any] |  |
| create_from_template | (namespace, name, queue: str, spec: str, template_id: str,...) | dict[str, Any] | 从模板创建 Pipeline。 |
| delete | (namespace, name, cluster: typing.Union[str, NoneType] = None) | NoneType |  |
| get | (namespace, name, cluster: typing.Union[str, NoneType] = None) | dict[str, Any] |  |
| list | (namespace=None, page: int = 1, page_size: int = 20) | list[dict[str, Any]] |  |

### client.namespaces — 命名空间

Namespace 命名空间管理器。

| 方法 | 签名 | 返回 | 说明 |
|------|------|------|------|
| get | (name) | Namespace |  |
| list | (tenant: typing.Union[str, NoneType] = None) | list[Namespace] |  |

### client.images — 容器镜像

Image 镜像管理器。

| 方法 | 签名 | 返回 | 说明 |
|------|------|------|------|
| create | (namespace, name, description: str = '', image_url: str = ...) | Image | 创建镜像。 |
| delete | (name_or_uid) | NoneType |  |
| get | (name_or_uid) | Image |  |
| list | (namespace=None, *, name_like=None, image_type: Literal['system','custom','backup']=None, ...) | list[Image] | image_type 支持按类型过滤：system / custom / backup |
| list_versions | (image_uid, page: int = 1, page_size: int = 20) | list[ImageVersion] |  |

### client.volumes — 数据卷

Volume 数据卷管理器 — CRUD + 文件操作。

| 方法 | 签名 | 返回 | 说明 |
|------|------|------|------|
| create | (namespace, name, description: str = '', tags: typing.Unio...) | Volume | 创建数据卷。 |
| delete | (name_or_uid) | NoneType |  |
| download | (name, remote_path, local_path, progress_callback: typing....) | str | 下载数据卷中的文件。 |
| get | (name_or_uid) | Volume |  |
| list | (namespace=None, name_like: typing.Union[str, NoneType] = ...) | list[Volume] |  |
| ls | (name, path='', recursive=False) | list[FileEntry] | 列出数据卷中的文件。 |
| preview | (name, remote_path, max_bytes=4096) | bytes | 预览数据卷中的文件内容。 |
| storage | (name, use='download') | StorageClient | 获取绑定数据卷的 StorageClient 实例。 |
| upload | (name, local_path, remote_path='', progress_callback: typi...) | str | 上传文件到数据卷。 |

### client.codes — 代码仓库

Code 代码仓库管理器。

| 方法 | 签名 | 返回 | 说明 |
|------|------|------|------|
| create | (namespace, name, git_url: str = '', description: str = ''...) | Code | 创建代码仓库。 |
| delete | (name_or_uid) | NoneType |  |
| get | (name_or_uid) | Code |  |
| list | (namespace=None, name_like: typing.Union[str, NoneType] = ...) | list[Code] |  |
| list_branches | (code_uid, name_like: typing.Union[str, NoneType] = None, ...) | list[GitBranch] | 列出代码仓库的分支。 |
| list_commits | (code_uid, ref: str = 'master', page: int = 1, page_size: ...) | list[GitCommit] | 列出代码仓库的提交（需指定 refName）。 |
| list_tags | (code_uid, name_like: typing.Union[str, NoneType] = None, ...) | list[GitTag] | 列出代码仓库的标签。 |

## 数据模型

### Job — 训练任务

| 属性 | 类型 | 说明 |
|------|------|------|
| kind | str |  |
| metadata | Metadata |  |
| spec | JobSpec |  |
| status | JobStatus |  |
| job_type | str | jobType |
| cluster_name | str | clusterName |
| progress | float |  |
| total_seconds | float | totalSeconds |
| cluster | str | (property) |
| created_at | typing.Union[str, NoneType] | (property) |
| is_running | bool | (property) |
| is_terminal | bool | (property) |
| name | str | (property) |
| namespace | typing.Union[str, NoneType] | (property) |
| owner | typing.Union[str, NoneType] | (property) |
| phase | str | (property) |
| queue | str | (property) |
| spec_name | str | (property) |
| uid | str | (property) |

### DevSpace — 开发环境

| 属性 | 类型 | 说明 |
|------|------|------|
| kind | str |  |
| metadata | Metadata |  |
| spec | DevSpaceSpec |  |
| status | DevSpaceStatus |  |
| created_at | typing.Union[str, NoneType] | (property) |
| jupyter_url | typing.Union[str, NoneType] | (property) |
| name | str | (property) |
| namespace | typing.Union[str, NoneType] | (property) |
| owner | typing.Union[str, NoneType] | (property) |
| phase | str | (property) |
| ssh_command | typing.Union[str, NoneType] | (property) |
| uid | str | (property) |

### Inference — 推理服务

| 属性 | 类型 | 说明 |
|------|------|------|
| kind | str |  |
| metadata | Metadata |  |
| spec | InferenceSpec |  |
| status | InferenceStatus |  |
| created_at | typing.Union[str, NoneType] | (property) |
| endpoint | typing.Union[str, NoneType] | (property) |
| name | str | (property) |
| namespace | typing.Union[str, NoneType] | (property) |
| owner | typing.Union[str, NoneType] | (property) |
| phase | str | (property) |
| uid | str | (property) |

### Queue — 调度队列

| 属性 | 类型 | 说明 |
|------|------|------|
| kind | str |  |
| metadata | Metadata |  |
| cluster | str |  |
| specs | list[ResourceSpec] |  |
| name | str | (property) |
| namespace | typing.Union[str, NoneType] | (property) |
| uid | str | (property) |

### Dataset — 数据集

| 属性 | 类型 | 说明 |
|------|------|------|
| kind | str |  |
| metadata | Metadata |  |
| description | str | (property) |
| name | str | (property) |
| namespace | typing.Union[str, NoneType] | (property) |
| uid | str | (property) |

### Model — 模型

| 属性 | 类型 | 说明 |
|------|------|------|
| kind | str |  |
| metadata | Metadata |  |
| description | str | (property) |
| name | str | (property) |
| namespace | typing.Union[str, NoneType] | (property) |
| uid | str | (property) |

### AssetVersion — 资产版本

| 属性 | 类型 | 说明 |
|------|------|------|
| kind | str |  |
| metadata | Metadata |  |
| spec | dict[str, Any] |  |
| format | str | (property) |
| name | str | (property) |
| namespace | typing.Union[str, NoneType] | (property) |
| s3_path | typing.Union[str, NoneType] | (property) |
| status_label | str | (property) |
| uid | str | (property) |

### Image — 容器镜像

| 属性 | 类型 | 说明 |
|------|------|------|
| kind | str |  |
| metadata | Metadata |  |
| description | str | (property) |
| image_type | str | (property) |
| name | str | (property) |
| namespace | typing.Union[str, NoneType] | (property) |
| uid | str | (property) |

### Volume — 数据卷

| 属性 | 类型 | 说明 |
|------|------|------|
| kind | str |  |
| metadata | Metadata |  |
| description | str | (property) |
| mounts | list[dict[str, str]] | (property) |
| name | str | (property) |
| namespace | typing.Union[str, NoneType] | (property) |
| uid | str | (property) |

### Code — 代码仓库

| 属性 | 类型 | 说明 |
|------|------|------|
| kind | str |  |
| metadata | Metadata |  |
| spec | dict[str, Any] |  |
| description | str | (property) |
| git_url | str | (property) |
| name | str | (property) |
| namespace | typing.Union[str, NoneType] | (property) |
| uid | str | (property) |

### StsToken — STS 临时凭证

| 属性 | 类型 | 说明 |
|------|------|------|
| endpoint | str |  |
| access_key_id | str | accessKeyId |
| secret_access_key | str | secretAccessKey |
| session_token | str | sessionToken |
| bucket | str |  |
| path | str |  |
| s3_path | str | s3Path |
| region | str |  |
| force_path_style | bool | forcePathStyle |
| expiration_timestamp | str | expirationTimestamp |

### FileEntry — 文件条目

| 属性 | 类型 | 说明 |
|------|------|------|
| name | str |  |
| path | str |  |
| size | int |  |
| is_dir | bool |  |
| last_modified | typing.Union[str, NoneType] |  |
| size_human | str | 人类可读的文件大小。 |

### LogEntry — 日志条目

| 属性 | 类型 | 说明 |
|------|------|------|
| timestamp | str |  |
| line | str |  |
| pod | str |  |
| container | str |  |

### JobDetail — 任务详情

| 属性 | 类型 | 说明 |
|------|------|------|
| job | Job |  |
| active_pods | list[dict[str, Any]] |  |
| pod_stats | dict[str, Any] |  |
| train_start_time | str |  |
| description | str |  |
| controller_phase | str |  |
| controller_message | str |  |

### TensorBoard — TensorBoard 实例

| 属性 | 类型 | 说明 |
|------|------|------|
| kind | str |  |
| metadata | Metadata |  |
| spec | TensorBoardSpec |  |
| status | TensorBoardStatus |  |
| name | str | (property) |
| namespace | typing.Union[str, NoneType] | (property) |
| owner | str | (property) |
| phase | str | (property) |
| uid | str | (property) |

## 便捷函数

```python
import hyper_ai as hi

# 提交训练任务 — 面向算法工程师的便捷接口。
result = hi.train(namespace, name, queue: str, spec: str, framework: str = ...)

# 创建开发环境 — 面向算法工程师的便捷接口。
result = hi.dev(namespace, name, queue: str, spec: str, image: str, servi...)

# 部署推理服务 — 面向算法工程师的便捷接口。
result = hi.serve(namespace, name, queue: str, spec: str, image: str, comma...)

```

## CLI 命令

```bash
    hi job list|get|logs|diagnose|create|stop|delete|priority|ls|download|upload|preview|exec|workspace ...  # 训练任务 — 创建、查看、日志、停止、删除
    hi devspace list|get|create|stop|start|delete|exec  # 开发环境 — GPU 工作站的创建、启停和管理
    hi inference list|get|create|scale|start|stop|restart|delete  # 推理服务 — 部署、伸缩和管理
    hi dataset list|get|create|delete|ls|download|upload|preview|version ...  # 数据集 — 创建、版本化、管理训练数据（含文件操作）
    hi model list|get|create|delete|ls|download|upload|preview|version ...  # 模型 — 创建、版本化、管理模型产物（含文件操作）
    hi queue list|get|specs  # 调度队列 — 查看队列和可用资源规格
    hi pipeline list|get|cancel|delete  # Pipeline — 多步骤训练工作流管理
    hi tb list|get|create|delete  # TensorBoard — 训练指标可视化管理
    hi tensorboard list|get|create|delete  # TensorBoard — 训练指标可视化管理
    hi namespace list|get|use|current|clear-default  # 命名空间 — 查看团队和资源组织
    hi ns list|get|use|current|clear-default  # 命名空间 — 查看团队和资源组织
    hi config show|set-env|set-token|set-namespace|clear-namespace  # 配置 — 查看和管理 SDK 配置
    hi skill generate  # Skill — SDK 能力自动导出为 Agent Skill
    hi image list|get|create|delete|versions  # 镜像 — 容器镜像的管理和版本查看（list 支持 --type system/custom/backup）
    hi volume list|get|create|delete|ls|download|upload|preview  # 数据卷 — 管理和文件操作（ls/download/upload/preview）
    hi code list|get|create|delete|branches|tags|commits  # 代码仓库 — Git 代码的管理和浏览
```

## 平台链接

### 环境域名

| 环境 | 域名 |
|------|------|
| prod | `https://hyper-ai.hellorobotaxi.top` |
| test | `https://hyper-ai-test.hellorobotaxi.top` |

### URL 映射表

创建/查询资源后**必须输出对应链接**。

| 资源 | URL 模式 | 关键参数来源 |
|------|---------|-------------|
| Job | `/jobs/{namespace}/{cluster}/{name}` | `job.namespace`, `job.cluster`, `job.name` |
| DevSpace | `/devspaces/{namespace}/{cluster}/{name}` | metadata |
| Inference | `/inferences/{namespace}/{cluster}/{name}` | metadata |
| Pipeline | `/pipeline/{namespace}/{name}` | `metadata.namespace`, `metadata.name` |
| Dataset | `/datasets/{uid}` | `metadata.uid` |
| Model | `/models/{uid}` | `metadata.uid` |
| Volume | `/volumes/{name}` | `metadata.name` |
| TensorBoard | `/tensorboards/{namespace}/{cluster}/{name}` | metadata |
| Image | `/images/{uid}` | `metadata.uid` |
| Code | `/codes/{uid}` | `metadata.uid` |

### 链接构造

```python
from hyper_ai import HyperAI
client = HyperAI()
base = client.base_url  # 自动取当前环境域名

# Job
job = client.jobs.get("ns", "name")
url = f"{base}/jobs/{job.namespace}/{job.cluster}/{job.name}"

# Pipeline（创建后立即输出链接）
result = client.pipelines.create_from_template(...)
meta = result['metadata']
url = f"{base}/pipeline/{meta['namespace']}/{meta['name']}"
print(f"查看: {url}")

# DevSpace / Inference / TensorBoard
ds = client.devspaces.get("ns", "name")
cluster = ds.spec.get('cluster', '') if isinstance(ds.spec, dict) else ''
url = f"{base}/devspaces/{ds.namespace}/{cluster}/{ds.name}"

# Dataset / Model / Image / Code（按 uid）
dataset = client.datasets.get("uid_or_name")
url = f"{base}/datasets/{dataset.uid}"
```

### 链接识别

当用户粘贴平台链接时，解析资源类型和坐标：

```python
import re

URL_PATTERNS = {
    "job":         re.compile(r"/(?:ai)?jobs/(?P<ns>[^/]+)/(?P<cluster>[^/]+)/(?P<name>[^/?#]+)"),
    "devspace":    re.compile(r"/devspaces/(?P<ns>[^/]+)/(?P<cluster>[^/]+)/(?P<name>[^/?#]+)"),
    "inference":   re.compile(r"/inferences/(?P<ns>[^/]+)/(?P<cluster>[^/]+)/(?P<name>[^/?#]+)"),
    "pipeline":    re.compile(r"/pipeline/(?P<ns>[^/]+)/(?P<name>[^/?#]+)"),
    "tensorboard": re.compile(r"/tensorboards/(?P<ns>[^/]+)/(?P<cluster>[^/]+)/(?P<name>[^/?#]+)"),
    "dataset":     re.compile(r"/datasets/(?P<uid>[^/?#]+)"),
    "model":       re.compile(r"/models/(?P<uid>[^/?#]+)"),
    "volume":      re.compile(r"/volumes/(?P<name>[^/?#]+)"),
    "image":       re.compile(r"/images/(?P<uid>[^/?#]+)"),
    "code":        re.compile(r"/codes/(?P<uid>[^/?#]+)"),
}

def parse_url(url: str) -> dict | None:
    """从平台 URL 提取资源类型和坐标。"""
    for kind, pat in URL_PATTERNS.items():
        m = pat.search(url)
        if m:
            return {"kind": kind, **m.groupdict()}
    return None

# 示例
info = parse_url("https://hyper-ai.hellorobotaxi.top/jobs/ad-e2e/hpc-prod-al-sh01/train-v3")
# → {'kind': 'job', 'ns': 'ad-e2e', 'cluster': 'hpc-prod-al-sh01', 'name': 'train-v3'}
info = parse_url("https://hyper-ai.hellorobotaxi.top/pipeline/ad-e2e/test-xxx-8pq9n")
# → {'kind': 'pipeline', 'ns': 'ad-e2e', 'name': 'test-xxx-8pq9n'}
```

## Pipeline 创建引导

创建 Pipeline 时**必须先参考同命名空间已有的成功 pipeline**，避免参数缺失或过期。

### 标准流程

```
1. 列出目标命名空间的 pipeline，找最近一次 Succeeded 的
2. 获取该 pipeline 的完整 spec（tasks、template、timeout）
3. 如有模板 templateRef → 用 create_from_template（推荐，队列自动解析）
4. 如需定制 → 从模板 API 获取干净 tasks，修改后用 create
5. 创建成功后立即输出平台链接
```

### 参考已有 Pipeline 并创建

```python
from hyper_ai import HyperAI
client = HyperAI()

# 步骤 1: 列出最近的 pipeline
pipelines = client.pipelines.list(namespace="ad-e2e", page_size=10)
succeeded = [p for p in pipelines if p['status'].get('phase') == 'Succeeded']
ref = succeeded[0]  # 最近成功的

# 步骤 2: 检查是否基于模板
template_ref = ref['spec'].get('templateRef', {})
template_id = template_ref.get('id')

# 步骤 3a: 从模板创建（推荐 — 队列自动解析，无过期风险）
if template_id:
    result = client.pipelines.create_from_template(
        namespace='ad-e2e',
        name='my-pipeline',
        queue='ad-e2e-common-al-sh01',  # 从 ref 的 userConfig.queue 取
        spec='h20-96-8gpu-150c-1600g',  # 从 ref 的 userConfig.specName 取
        template_id=template_id,
        timeout=ref['spec'].get('timeout', '1h'),
    )

# 步骤 3b: 需要定制 tasks（比如追加通知节点）
# 注意：必须从模板 API 取 tasks（队列名干净），不要从运行过的 pipeline 取
tpl = client.pipelines._get(f'/api/asset/pipeline-templates/{template_id}')
tasks = tpl['spec']['tasks']
tasks.append({  # 追加自定义步骤
    'name': 'notify',
    'template': 'hpc-container',
    'version': 'v1',
    'params': {'command': 'curl ...', 'cpu': '1', 'memory': '2Gi',
               'image': '...', 'queue': 'cpu-common-al-sh01', 'specName': '1c-2g'},
    'runAfter': ['last-step-name'],
    'userConfig': {'queue': 'cpu-common-al-sh01', 'specName': '1c-2g'},
})

# 步骤 4: 创建成功后输出链接
meta = result['metadata']
base = client.transport.base_url
print(f"Pipeline 已创建: {base}/pipeline/{meta['namespace']}/{meta['name']}")
```

### 关键注意事项

| 问题 | 原因 | 解决 |
|------|------|------|
| 500 `获取队列失败 404` | tasks 中 `params.queue` 是已过期的内部 K8s 队列名 | 从模板 API 获取 tasks（队列名为用户可见名） |
| 需要追加步骤 | `create_from_template` 不支持追加 task | 从模板 API 取 tasks → 手动追加 → 用 `create` |
| 通知步骤不需要 GPU | 用 CPU 队列 `cpu-common-al-sh01` + 规格 `1c-2g` | 在 params 和 userConfig 中都设置 |

## Agent 常用模式

```python
from hyper_ai import HyperAI
client = HyperAI()
base = client.base_url

# 列出运行中的任务并输出链接
ns = client.ns("ad-perception")
for job in ns.jobs.list(status="Training"):
    print(f"{job.name} → {base}/jobs/{job.namespace}/{job.cluster}/{job.name}")

# 获取详情并决策
detail = ns.jobs.detail("train-v3")
if detail.job.is_terminal:
    print(f"已结束: {detail.job.phase}")

# 实时日志监控
for line in ns.jobs.follow("train-v3"):
    if "ERROR" in line:
        ns.jobs.stop("train-v3")
        break

# 从 URL 识别资源并操作
# 用户粘贴 https://hyper-ai.hellorobotaxi.top/jobs/ad-e2e/hpc-prod-al-sh01/train-v3
# → 解析为 kind=job, ns=ad-e2e, cluster=hpc-prod-al-sh01, name=train-v3
# → 调用 client.jobs.get('ad-e2e', 'train-v3') 获取详情

# Pipeline 创建后输出链接
result = client.pipelines.create_from_template(...)
meta = result['metadata']
print(f"查看: {base}/pipeline/{meta['namespace']}/{meta['name']}")
```
