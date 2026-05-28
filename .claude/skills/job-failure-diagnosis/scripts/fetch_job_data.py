#!/usr/bin/env python3
"""
HPC 训练任务诊断数据采集

两条数据通道：
  1. hyper-ai API（Bearer 认证）→ 资源信息
  2. Grafana Loki（匿名）→ 日志

用法:
  python3 fetch_job_data.py --url "https://hyper-ai.hellorobotaxi.top/jobs/ns/cluster/name"
  python3 fetch_job_data.py --namespace ns --cluster cluster --job-name name
"""

import argparse
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from urllib.parse import urlparse, parse_qs
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


# ==================== 凭证加载 ====================

TOML_CONFIG_PATH = os.path.expanduser("~/.config/hpc/config.toml")
TOML_CONFIG_PATH_ALT = os.path.expanduser("~/.config/hpc.toml")


def _load_token() -> str:
    """
    Token 加载优先级：
      1. 环境变量 HPC_API_TOKEN / HPC_AUTH
      2. SDK TOML 配置 ~/.config/hpc/config.toml -> env.<current>.auth
      3. SDK TOML 备选 ~/.config/hpc.toml -> env.<current>.auth
    """
    for env_key in ("HPC_API_TOKEN", "HPC_AUTH"):
        token = os.environ.get(env_key)
        if token:
            return token if token.startswith("Bearer ") else f"Bearer {token}"

    for toml_path in (TOML_CONFIG_PATH, TOML_CONFIG_PATH_ALT):
        token = _load_token_from_toml(toml_path)
        if token:
            return token

    print(
        "[FATAL] 未找到 API Token，请先运行 `hi login` 或设置环境变量 HPC_AUTH",
        file=sys.stderr,
    )
    sys.exit(1)


def _load_token_from_toml(path: str) -> Optional[str]:
    """从 SDK 的 TOML 配置文件读取当前环境的 auth token"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = f.read()
    except (FileNotFoundError, OSError):
        return None

    data = None
    for loader in (_toml_load_stdlib, _toml_load_tomlkit, _toml_load_regex):
        data = loader(raw)
        if data is not None:
            break
    if data is None:
        return None

    env_name = data.get("current", {}).get("env", "prod")
    auth = data.get("env", {}).get(env_name, {}).get("auth", "")
    if not auth:
        return None
    return auth if auth.startswith("Bearer ") else f"Bearer {auth}"


def _toml_load_stdlib(raw: str) -> Optional[dict]:
    try:
        import tomllib  # Python 3.11+
        return tomllib.loads(raw)
    except Exception:
        return None


def _toml_load_tomlkit(raw: str) -> Optional[dict]:
    try:
        import tomlkit
        return tomlkit.loads(raw)
    except Exception:
        return None


def _toml_load_regex(raw: str) -> Optional[dict]:
    """零依赖 fallback：用正则从简单 TOML 中提取 current.env 和 env.{name}.auth"""
    result: dict[str, Any] = {}
    current_section = ""
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^\[([^\]]+)\]$", line)
        if m:
            current_section = m.group(1).strip()
            continue
        m = re.match(r'^(\w+)\s*=\s*"([^"]*)"$', line)
        if not m:
            m = re.match(r"^(\w+)\s*=\s*(\S+)$", line)
        if m:
            key, val = m.group(1), m.group(2)
            parts = current_section.split(".") if current_section else []
            node = result
            for p in parts:
                node = node.setdefault(p, {})
            node[key] = val
    return result if result else None


# ==================== 配置 ====================

# hyper-ai API Gateway（需 Bearer 认证）
HPC_API_URL = "https://hyper-ai.hellorobotaxi.top"
HPC_API_HEADERS = {
    "Authorization": _load_token(),
    "x-user-id": "hpc-diagnosis-api",
    "x-platform": "hyper-ai",
    "x-scopes": "platform:admin",
}

# Grafana（匿名访问）
GRAFANA_URL = "https://grafana.hellorobotaxi.top"
GRAFANA_HEADERS = {
    "Content-Type": "application/json",
    "x-grafana-org-id": "1",
    "x-plugin-id": "loki",
    "x-panel-plugin-id": "logs",
}

CLUSTER_DATASOURCES = {
    "hpc-test-al-sh01": {"loki": "ef6h29oj7drlsd", "prometheus": "df6h2brb3gidcd"},
    "hpc-prod-al-sh01": {"loki": "cf6gzdzit6wowc", "prometheus": "af6h2e37d6pkwf"},
    "hpc-prod-al-sh02": {"loki": "ff7jqjxkpog00e", "prometheus": "ff7jqiem43vuof"},
    "hpc-prod-bd-su01": {"loki": "efax9ej7g7qwwa", "prometheus": "afat7coqm6olca"},
}

DEFAULT_LOKI_UID = "ef6h29oj7drlsd"
TIMEOUT = 30


# ==================== 时间解析 ====================


def _parse_timestamp(ts_str: str) -> datetime:
    """解析 ISO 8601 时间戳，不依赖 dateutil"""
    ts_str = ts_str.strip()
    # 处理带时区偏移的格式: 2026-03-18T23:56:08+08:00
    m = re.match(
        r"(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2}:\d{2})(?:\.\d+)?"
        r"(?:Z|([+-]\d{2}):?(\d{2}))?$",
        ts_str,
    )
    if not m:
        raise ValueError(f"无法解析时间: {ts_str}")
    dt = datetime.strptime(f"{m.group(1)}T{m.group(2)}", "%Y-%m-%dT%H:%M:%S")
    if m.group(3) is not None:
        offset_h, offset_m = int(m.group(3)), int(m.group(4))
        tz = timezone(timedelta(hours=offset_h, minutes=offset_m if offset_h >= 0 else -offset_m))
        dt = dt.replace(tzinfo=tz)
    else:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


# ==================== URL 解析 ====================


def parse_job_url(url: str) -> dict[str, str]:
    """
    解析 HPC 平台任务 URL
    格式: /jobs/{namespace}/{cluster}/{job-name}?namespace=...
    """
    parsed = urlparse(url)
    path_parts = [p for p in parsed.path.split("/") if p]

    if len(path_parts) < 4 or path_parts[0] != "jobs":
        raise ValueError(f"URL 格式不正确，期望 /jobs/{{ns}}/{{cluster}}/{{name}}，实际: {parsed.path}")

    query = parse_qs(parsed.query)
    return {
        "namespace": query.get("namespace", [path_parts[1]])[0],
        "cluster": path_parts[2],
        "job_name": path_parts[3],
    }


# ==================== HTTP 请求 ====================


def _http(method: str, url: str, headers: dict, data: Optional[bytes] = None) -> dict:
    """通用 HTTP 请求"""
    req = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(req, timeout=TIMEOUT) as resp:
            return json.loads(resp.read())
    except HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"{method} {url} -> HTTP {e.code}: {body}") from e
    except URLError as e:
        raise RuntimeError(f"{method} {url} -> 连接失败: {e.reason}") from e


def hpc_api_get(path: str, params: Optional[dict] = None) -> dict:
    """hyper-ai API GET（Bearer 认证）"""
    url = f"{HPC_API_URL}{path}"
    if params:
        url += "?" + "&".join(f"{k}={v}" for k, v in params.items())
    return _http("GET", url, HPC_API_HEADERS)


def grafana_post(path: str, body: dict, params: Optional[dict] = None) -> dict:
    """Grafana POST（匿名）"""
    url = f"{GRAFANA_URL}{path}"
    if params:
        url += "?" + "&".join(f"{k}={v}" for k, v in params.items())
    return _http("POST", url, GRAFANA_HEADERS, json.dumps(body).encode("utf-8"))


# ==================== 资源信息 ====================


def _parse_annotation_pods(metadata: dict) -> list[dict]:
    """从 hpc.org/active-pods annotation 解析 pod 列表"""
    raw = metadata.get("annotations", {}).get("hpc.org/active-pods", "")
    if not raw:
        return []
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return []


def get_resource_info(namespace: str, cluster: str, job_name: str) -> dict[str, Any]:
    """获取 AIJob 资源信息（通过 hyper-ai API）"""
    data = hpc_api_get(
        f"/api/studio/namespaces/{namespace}/aijobs/{job_name}",
        params={"cluster": cluster},
    )

    spec = data.get("spec", {})
    status = data.get("status", {})
    metadata = data.get("metadata", {})

    vcjob_name = status.get("vcJobName", "")
    pod_pattern = f"{vcjob_name}.*" if vcjob_name else f".*{job_name}.*"

    # 提取完整 pod 信息（name, role, nodeName, podIP, phase）
    pods: list[dict] = []
    seen_pods: set[str] = set()

    for source in (status.get("activePods", []), _parse_annotation_pods(metadata)):
        for p in source:
            name = p.get("name", "")
            if name and name not in seen_pods:
                seen_pods.add(name)
                pods.append({
                    "name": name,
                    "role": p.get("role", ""),
                    "node_name": p.get("nodeName", ""),
                    "pod_ip": p.get("podIP", ""),
                    "phase": p.get("phase", ""),
                })

    pod_names = [p["name"] for p in pods]
    node_names = list({p["node_name"] for p in pods if p["node_name"]})

    return {
        "name": metadata.get("name"),
        "namespace": metadata.get("namespace"),
        "cluster": spec.get("cluster", cluster),
        "phase": status.get("phase"),
        "message": status.get("message", ""),
        "image": spec.get("image", ""),
        "framework": spec.get("framework", ""),
        "command": spec.get("command", ""),
        "queue": spec.get("queue", ""),
        "spec_name": spec.get("specName", ""),
        "owner": spec.get("owner", ""),
        "created_at": metadata.get("creationTimestamp", ""),
        "vcjob_name": vcjob_name,
        "pod_pattern": pod_pattern,
        "pods": pods,
        "pod_names": pod_names,
        "node_names": node_names,
        "conditions": status.get("conditions", []),
        "pod_stats": status.get("podStats", {}),
        "max_retry": spec.get("maxRetry", 0),
        "current_round": status.get("currentRound"),
    }


# ==================== Loki 日志查询 ====================


def get_loki_uid(cluster: str) -> str:
    return CLUSTER_DATASOURCES.get(cluster, {}).get("loki", DEFAULT_LOKI_UID)


def query_loki(expr: str, start_ms: int, end_ms: int, max_lines: int,
               datasource_uid: str, direction: str = "backward") -> dict:
    """查询 Grafana Loki（匿名，直连 Grafana）"""
    body = {
        "queries": [{
            "refId": "A",
            "expr": expr,
            "queryType": "range",
            "datasource": {"type": "loki", "uid": datasource_uid},
            "maxLines": max_lines,
            "direction": direction,
        }],
        "from": str(start_ms),
        "to": str(end_ms),
    }
    return grafana_post("/api/ds/query", body, params={"ds_type": "loki"})


def parse_loki_response(response: dict) -> list[dict]:
    """解析 Loki 响应为日志条目列表

    Grafana /api/ds/query 返回的 data frame 中，流标签有两种存放方式：
      1. 新版：独立的 name="labels" 列，values 是每行的 label dict
      2. 旧版：field schema 上的 field["labels"] 属性（所有行共享）
    两种都兼容。
    """
    logs = []
    try:
        frames = response.get("results", {}).get("A", {}).get("frames", [])
        for frame in frames:
            schema = frame.get("schema", {})
            data = frame.get("data", {})
            fields = schema.get("fields", [])
            values = data.get("values", [])

            if not fields or not values:
                continue

            time_idx = line_idx = labels_idx = -1
            for i, field in enumerate(fields):
                name = field.get("name", "").lower()
                if name in ("time", "timestamp", "tsns"):
                    time_idx = i
                elif name in ("line", "message", "log"):
                    line_idx = i
                elif name == "labels" and field.get("type") == "other":
                    labels_idx = i

            if time_idx == -1 or line_idx == -1:
                continue

            timestamps = values[time_idx] if time_idx < len(values) else []
            lines = values[line_idx] if line_idx < len(values) else []
            labels_col = values[labels_idx] if labels_idx != -1 and labels_idx < len(values) else []

            # 旧版 fallback：field schema 上的 labels
            schema_labels: dict = {}
            for field in fields:
                if field.get("labels"):
                    schema_labels = field["labels"]
                    break

            for i in range(min(len(timestamps), len(lines))):
                ts = timestamps[i]
                line = lines[i]
                if not line:
                    continue

                # 优先用 labels 列（每行独立），fallback 到 schema labels
                row_labels = labels_col[i] if i < len(labels_col) and isinstance(labels_col[i], dict) else schema_labels

                if isinstance(ts, (int, float)):
                    ts_ms = ts / 1e6 if ts > 1e15 else ts
                elif isinstance(ts, str):
                    try:
                        ts_num = int(ts)
                        ts_ms = ts_num / 1e6 if len(ts) >= 16 else ts_num
                    except ValueError:
                        ts_ms = time.time() * 1000
                else:
                    ts_ms = time.time() * 1000

                logs.append({
                    "timestamp": datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).isoformat(),
                    "pod": row_labels.get("pod", "unknown"),
                    "container": row_labels.get("container", "main"),
                    "message": str(line)[:3000],
                })
    except Exception as e:
        print(f"[WARN] 解析 Loki 响应失败: {e}", file=sys.stderr)

    return logs


def fetch_logs(namespace: str, cluster: str, pod_pattern: str, created_at: str) -> dict[str, Any]:
    """获取错误日志和最近日志"""
    loki_uid = get_loki_uid(cluster)

    now = datetime.now(timezone.utc)
    end_ms = int(now.timestamp() * 1000)
    fallback_ms = int((now - timedelta(hours=6)).timestamp() * 1000)

    start_ms = fallback_ms
    if created_at:
        try:
            job_ts = _parse_timestamp(created_at)
            start_ms = int(job_ts.timestamp() * 1000)
        except Exception:
            pass

    if start_ms > end_ms:
        start_ms = fallback_ms

    # 注意：Loki 中没有 cluster 标签，仅用 namespace + pod 过滤
    # cluster 信息已在选择 datasource UID 时使用
    base_query = '{' + f'namespace="{namespace}", pod=~"{pod_pattern}"' + '}'

    python_error_query = base_query + ' |~ "(?i)(OSError|IOError|RuntimeError|ValueError|TypeError|KeyError|AttributeError|MemoryError|FileNotFoundError|PermissionError|CUDA|NCCL|cuda|nccl)"'
    general_error_query = base_query + ' |~ "(?i)(Traceback|exception|failed|fatal|panic|killed|oom|error|Error)"'
    recent_query = base_query

    results: dict[str, Any] = {"error_logs": [], "recent_logs": [], "startup_logs": [], "queries": {}}

    def _query(name: str, expr: str, max_lines: int,
               direction: str = "backward") -> tuple[str, list[dict]]:
        try:
            raw = query_loki(expr, start_ms, end_ms, max_lines, loki_uid, direction)
            return name, parse_loki_response(raw)
        except Exception as e:
            print(f"[WARN] Loki 查询 {name} 失败: {e}", file=sys.stderr)
            return name, []

    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [
            pool.submit(_query, "python_errors", python_error_query, 200),
            pool.submit(_query, "general_errors", general_error_query, 100),
            pool.submit(_query, "recent", recent_query, 200),
            pool.submit(_query, "startup", recent_query, 100, "forward"),
        ]
        for f in as_completed(futures):
            name, logs = f.result()
            if name in ("python_errors", "general_errors"):
                results["error_logs"].extend(logs)
            elif name == "startup":
                results["startup_logs"] = logs
            else:
                results["recent_logs"] = logs

    # 错误日志去重
    seen: set[tuple[str, str]] = set()
    deduped = []
    for log in results["error_logs"]:
        key = (log["timestamp"], log["message"][:100])
        if key not in seen:
            seen.add(key)
            deduped.append(log)
    results["error_logs"] = sorted(deduped, key=lambda x: x["timestamp"], reverse=True)

    results["queries"] = {
        "base": base_query,
        "python_error": python_error_query,
        "general_error": general_error_query,
        "time_range": f"{datetime.fromtimestamp(start_ms/1000, tz=timezone.utc).isoformat()} ~ {datetime.fromtimestamp(end_ms/1000, tz=timezone.utc).isoformat()}",
    }

    return results


# ==================== 主机名映射 ====================


def _build_host_mapping(resource_info: dict, log_data: dict) -> tuple[list[dict], list[str]]:
    """
    合并 API pod 信息与日志中 /etc/hosts 条目，构建完整的主机名映射。

    API 提供:  pod_ip → node_name (K8s 格式，如 e01-cn-xxx)
    训练日志:  ip → training_hostname (旧格式，如 hpc-prod-al-sh01-h20-96-xxx)

    两种格式在 Prometheus DCGM 中被不同 exporter 使用，GPU 健康检查需要两者。
    """

    # 从 API pod 信息构建 ip→node_name 映射
    ip_to_node: dict[str, dict] = {}
    for pod in resource_info.get("pods", []):
        ip = pod.get("pod_ip", "")
        if ip:
            ip_to_node[ip] = {
                "pod_name": pod.get("name", ""),
                "role": pod.get("role", ""),
                "node_name": pod.get("node_name", ""),
                "pod_ip": ip,
                "training_hostname": "",
            }

    # 从日志中提取主机名，多种来源：
    #   1. /etc/hosts: "📝 /etc/hosts: {ip} → {hostname}"
    #   2. Smart Training Agent: "Host: hpc-prod-al-sh01-h20-96-0018"
    #   3. torchrun 错误: "host      : hpc-prod-al-sh01-h20-96-0018"
    hosts_pattern = re.compile(r"/etc/hosts:\s*([\d.]+)\s*(?:→|->)\s*(\S+)")
    # 匹配集群节点主机名: hpc-{env}-{az}-{zone}-{gpu}-{mem}-{id}
    # 例: hpc-prod-al-sh01-h20-96-0018 (7 段)
    node_hostname_pattern = re.compile(r"(hpc-\w+-\w+-\w+-\w+-\d+-\d+)")

    all_logs = log_data.get("startup_logs", []) + log_data.get("recent_logs", []) + log_data.get("error_logs", [])
    training_hostnames: set[str] = set()

    for log in all_logs:
        msg = log.get("message", "")

        # /etc/hosts → ip→hostname 精确映射
        m = hosts_pattern.search(msg)
        if m:
            ip, hostname = m.group(1), m.group(2)
            if ip in ip_to_node and "vcjob" not in hostname:
                ip_to_node[ip]["training_hostname"] = hostname

        # 收集所有出现的集群节点主机名
        for hostname in node_hostname_pattern.findall(msg):
            training_hostnames.add(hostname)

    mapping = list(ip_to_node.values())

    # 返回 (pod 映射列表, 全量训练主机名集合)
    # training_hostnames 用于 GPU 健康检查（与 node_names 合并覆盖双格式）
    return mapping, sorted(training_hostnames)


# ==================== 主流程 ====================


def main():
    parser = argparse.ArgumentParser(description="HPC 训练任务诊断数据采集")
    parser.add_argument("--url", help="HPC 平台任务 URL")
    parser.add_argument("--namespace", help="Kubernetes 命名空间")
    parser.add_argument("--cluster", help="集群名称")
    parser.add_argument("--job-name", help="任务名称")
    parser.add_argument("--output", default="-", help="输出文件路径（默认 stdout）")
    args = parser.parse_args()

    if args.url:
        parsed = parse_job_url(args.url)
        namespace = parsed["namespace"]
        cluster = parsed["cluster"]
        job_name = parsed["job_name"]
    elif args.namespace and args.cluster and args.job_name:
        namespace = args.namespace
        cluster = args.cluster
        job_name = args.job_name
    else:
        parser.error("请提供 --url 或 --namespace + --cluster + --job-name")

    print(f"[INFO] 诊断目标: {namespace}/{cluster}/{job_name}", file=sys.stderr)

    # Step 1: 获取资源信息（hyper-ai API, Bearer 认证）
    print("[INFO] 正在获取资源信息...", file=sys.stderr)
    try:
        resource_info = get_resource_info(namespace, cluster, job_name)
    except Exception as e:
        print(f"[ERROR] 获取资源信息失败: {e}", file=sys.stderr)
        resource_info = {
            "name": job_name,
            "namespace": namespace,
            "cluster": cluster,
            "phase": "Unknown",
            "pod_pattern": f".*{job_name}.*",
            "pod_names": [],
            "error": str(e),
        }

    pod_pattern = resource_info.get("pod_pattern", f".*{job_name}.*")
    created_at = resource_info.get("created_at", "")

    # Step 2: 获取日志（Grafana Loki, 匿名）
    print("[INFO] 正在获取 Loki 日志...", file=sys.stderr)
    log_data: dict[str, Any] = {"error_logs": [], "recent_logs": [], "startup_logs": []}
    try:
        log_data = fetch_logs(namespace, cluster, pod_pattern, created_at)
    except Exception as e:
        print(f"[ERROR] 日志获取失败: {e}", file=sys.stderr)
        log_data["error"] = str(e)

    # Step 3: 构建 host_mapping（合并 API pod 信息与日志中的主机名）
    host_mapping, training_hostnames = _build_host_mapping(resource_info, log_data)

    # 汇总结果
    result = {
        "target": {"namespace": namespace, "cluster": cluster, "job_name": job_name},
        "resource_info": resource_info,
        "host_mapping": host_mapping,
        "training_hostnames": training_hostnames,
        "error_logs": log_data.get("error_logs", []),
        "error_log_count": len(log_data.get("error_logs", [])),
        "recent_logs": log_data.get("recent_logs", []),
        "recent_log_count": len(log_data.get("recent_logs", [])),
        "startup_logs": log_data.get("startup_logs", []),
        "startup_log_count": len(log_data.get("startup_logs", [])),
        "queries": log_data.get("queries", {}),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }

    output = json.dumps(result, ensure_ascii=False, indent=2, default=str)

    if args.output == "-":
        print(output)
    else:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"[INFO] 结果已写入: {args.output}", file=sys.stderr)

    # 快速摘要
    print("\n[SUMMARY]", file=sys.stderr)
    print(f"  状态: {resource_info.get('phase', 'Unknown')}", file=sys.stderr)
    pods = resource_info.get("pods", [])
    if pods:
        print(f"  节点: {len(pods)} pods", file=sys.stderr)
        for p in pods:
            print(f"    {p['role']:8s} {p['name']}", file=sys.stderr)
            print(f"             → node={p['node_name']}  ip={p['pod_ip']}", file=sys.stderr)
    if training_hostnames:
        print(f"  训练主机名: {', '.join(training_hostnames)}", file=sys.stderr)
    print(f"  错误日志: {len(log_data.get('error_logs', []))} 条", file=sys.stderr)
    print(f"  启动日志: {len(log_data.get('startup_logs', []))} 条", file=sys.stderr)
    print(f"  最近日志: {len(log_data.get('recent_logs', []))} 条", file=sys.stderr)


if __name__ == "__main__":
    main()
