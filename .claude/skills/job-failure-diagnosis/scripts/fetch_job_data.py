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
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from urllib.parse import urlparse, parse_qs
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


# ==================== 凭证加载 ====================

CREDENTIALS_PATH = os.path.expanduser("~/.config/hpc/credentials")


def _load_token() -> str:
    """从环境变量或 ~/.config/hpc/credentials 读取 token"""
    token = os.environ.get("HPC_API_TOKEN")
    if token:
        return token

    try:
        with open(CREDENTIALS_PATH) as f:
            for line in f:
                line = line.strip()
                if line.startswith("HPC_API_TOKEN="):
                    return line.split("=", 1)[1]
    except FileNotFoundError:
        pass

    print(f"[FATAL] 未找到 HPC_API_TOKEN：设置环境变量或写入 {CREDENTIALS_PATH}", file=sys.stderr)
    sys.exit(1)


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

    pod_names = []
    active_pods_str = metadata.get("annotations", {}).get("hpc.org/active-pods", "")
    if active_pods_str:
        try:
            for p in json.loads(active_pods_str):
                if p.get("name"):
                    pod_names.append(p["name"])
        except (json.JSONDecodeError, TypeError):
            pass

    for p in status.get("activePods", []):
        name = p.get("name", "")
        if name and name not in pod_names:
            pod_names.append(name)

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
        "pod_names": pod_names[:10],
        "conditions": status.get("conditions", []),
        "pod_stats": status.get("podStats", {}),
        "max_retry": spec.get("maxRetry", 0),
        "current_round": status.get("currentRound"),
    }


# ==================== Loki 日志查询 ====================


def get_loki_uid(cluster: str) -> str:
    return CLUSTER_DATASOURCES.get(cluster, {}).get("loki", DEFAULT_LOKI_UID)


def query_loki(expr: str, start_ms: int, end_ms: int, max_lines: int, datasource_uid: str) -> dict:
    """查询 Grafana Loki（匿名，直连 Grafana）"""
    body = {
        "queries": [{
            "refId": "A",
            "expr": expr,
            "queryType": "range",
            "datasource": {"type": "loki", "uid": datasource_uid},
            "maxLines": max_lines,
            "direction": "backward",
        }],
        "from": str(start_ms),
        "to": str(end_ms),
    }
    return grafana_post("/api/ds/query", body, params={"ds_type": "loki"})


def parse_loki_response(response: dict) -> list[dict]:
    """解析 Loki 响应为日志条目列表"""
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

            time_idx = line_idx = -1
            for i, field in enumerate(fields):
                name = field.get("name", "").lower()
                if name in ("time", "timestamp", "tsns"):
                    time_idx = i
                elif name in ("line", "message", "log"):
                    line_idx = i

            if time_idx == -1 or line_idx == -1:
                continue

            timestamps = values[time_idx] if time_idx < len(values) else []
            lines = values[line_idx] if line_idx < len(values) else []

            labels = {}
            for field in fields:
                if field.get("labels"):
                    labels = field["labels"]
                    break

            for i in range(min(len(timestamps), len(lines))):
                ts = timestamps[i]
                line = lines[i]
                if not line:
                    continue

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
                    "pod": labels.get("pod", "unknown"),
                    "container": labels.get("container", "main"),
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

    if created_at:
        try:
            from dateutil import parser
            job_ts = parser.parse(created_at)
            if job_ts.tzinfo is None:
                job_ts = job_ts.replace(tzinfo=timezone.utc)
            start_ms = int(job_ts.timestamp() * 1000)
        except Exception:
            start_ms = int((now - timedelta(hours=6)).timestamp() * 1000)
    else:
        start_ms = int((now - timedelta(hours=6)).timestamp() * 1000)

    if start_ms > end_ms:
        start_ms = int((now - timedelta(hours=6)).timestamp() * 1000)

    base_query = '{' + f'namespace="{namespace}", cluster="{cluster}", pod=~"{pod_pattern}"' + '}'

    python_error_query = base_query + ' |~ "(?i)(OSError|IOError|RuntimeError|ValueError|TypeError|KeyError|AttributeError|MemoryError|FileNotFoundError|PermissionError|CUDA|NCCL|cuda|nccl)"'
    general_error_query = base_query + ' |~ "(?i)(Traceback|exception|failed|fatal|panic|killed|oom|error|Error)"'
    recent_query = base_query

    results: dict[str, Any] = {"error_logs": [], "recent_logs": [], "queries": {}}

    def _query(name: str, expr: str, max_lines: int) -> tuple[str, list[dict]]:
        try:
            raw = query_loki(expr, start_ms, end_ms, max_lines, loki_uid)
            return name, parse_loki_response(raw)
        except Exception as e:
            print(f"[WARN] Loki 查询 {name} 失败: {e}", file=sys.stderr)
            return name, []

    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = [
            pool.submit(_query, "python_errors", python_error_query, 200),
            pool.submit(_query, "general_errors", general_error_query, 100),
            pool.submit(_query, "recent", recent_query, 200),
        ]
        for f in as_completed(futures):
            name, logs = f.result()
            if name in ("python_errors", "general_errors"):
                results["error_logs"].extend(logs)
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
    log_data: dict[str, Any] = {"error_logs": [], "recent_logs": []}
    try:
        log_data = fetch_logs(namespace, cluster, pod_pattern, created_at)
    except Exception as e:
        print(f"[ERROR] 日志获取失败: {e}", file=sys.stderr)
        log_data["error"] = str(e)

    # 汇总结果
    result = {
        "target": {"namespace": namespace, "cluster": cluster, "job_name": job_name},
        "resource_info": resource_info,
        "error_logs": log_data.get("error_logs", []),
        "error_log_count": len(log_data.get("error_logs", [])),
        "recent_logs": log_data.get("recent_logs", []),
        "recent_log_count": len(log_data.get("recent_logs", [])),
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
    print(f"  错误日志: {len(log_data.get('error_logs', []))} 条", file=sys.stderr)
    print(f"  最近日志: {len(log_data.get('recent_logs', []))} 条", file=sys.stderr)


if __name__ == "__main__":
    main()
