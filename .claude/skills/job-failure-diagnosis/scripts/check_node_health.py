#!/usr/bin/env python3
"""
GPU 节点健康检查

通过 Grafana Prometheus 查询 DCGM 指标，评估 GPU 硬件健康状态。
可选通过 kubectl 获取 K8s 节点信息。

数据通道：
  1. Grafana Prometheus（匿名）→ DCGM GPU 指标
  2. kubectl（可选，需 SOCKS5 代理）→ 节点状态、事件、标签

用法:
  # 通过主机名查（训练日志中的 hostname）
  python3 check_node_health.py --cluster hpc-prod-al-sh01 \
    --hostnames hpc-prod-al-sh01-h20-96-0018 hpc-prod-al-sh01-h20-96-0051

  # 通过 IP 查
  python3 check_node_health.py --cluster hpc-prod-al-sh01 \
    --ips 10.168.3.84 10.168.7.146

  # 附加 kubectl 查询（需要代理隧道）
  python3 check_node_health.py --cluster hpc-prod-al-sh01 \
    --ips 10.168.3.84 --kubectl
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.request import Request, urlopen


# ==================== 配置 ====================

GRAFANA_URL = "https://grafana.hellorobotaxi.top"
GRAFANA_HEADERS = {
    "Content-Type": "application/json",
    "x-grafana-org-id": "1",
}

CLUSTER_DATASOURCES = {
    "hpc-test-al-sh01": {"prometheus": "df6h2brb3gidcd"},
    "hpc-prod-al-sh01": {"prometheus": "af6h2e37d6pkwf"},
    "hpc-prod-al-sh02": {"prometheus": "ff7jqiem43vuof"},
    "hpc-prod-bd-su01": {"prometheus": "afat7coqm6olca"},
}

HTTPS_PROXY = "socks5://127.0.0.1:1080"

# ==================== DCGM 指标定义 ====================

# 关键 GPU 健康指标及其含义
DCGM_HEALTH_METRICS = {
    "DCGM_FI_DEV_XID_ERRORS": {
        "name": "Xid Errors",
        "severity": "warning",
        "desc": "GPU Xid 错误码（非零表示有 GPU 事件）",
    },
    "DCGM_FI_DEV_ECC_SBE_VOL_TOTAL": {
        "name": "ECC Single-Bit Errors",
        "severity": "warning",
        "desc": "可纠正的单比特 ECC 错误",
    },
    "DCGM_FI_DEV_ECC_DBE_VOL_TOTAL": {
        "name": "ECC Double-Bit Errors",
        "severity": "critical",
        "desc": "不可纠正的双比特 ECC 错误（致命）",
    },
    "DCGM_FI_DEV_ROW_REMAP_FAILURE": {
        "name": "Row Remap Failure",
        "severity": "critical",
        "desc": "显存行重映射失败（硬件损坏）",
    },
    "DCGM_FI_DEV_RETIRED_SBE": {
        "name": "Retired Pages (SBE)",
        "severity": "warning",
        "desc": "因单比特错误退役的显存页数",
    },
    "DCGM_FI_DEV_RETIRED_DBE": {
        "name": "Retired Pages (DBE)",
        "severity": "critical",
        "desc": "因双比特错误退役的显存页数",
    },
    "DCGM_FI_DEV_NVLINK_CRC_FLIT_ERROR_COUNT_TOTAL": {
        "name": "NVLink CRC Errors",
        "severity": "warning",
        "desc": "NVLink CRC 校验错误",
    },
}

# Xid 错误码速查
XID_REFERENCE = {
    13: ("Graphics Engine Exception", "critical", "GPU 硬件异常"),
    31: ("GPU memory page fault", "warning", "显存页错误，通常是软件 bug"),
    43: ("GPU stopped processing", "info", "GPU 停止处理，通常是进程被杀的后果"),
    45: ("Preemptive cleanup", "info", "GPU 抢占清理"),
    48: ("DBE ECC error", "critical", "双比特 ECC 错误，硬件问题"),
    63: ("ECC page retirement/row remap", "warning", "ECC 触发的页退役/行重映射"),
    64: ("ECC page retirement/row remap", "warning", "ECC 触发的页退役/行重映射"),
    74: ("NVLink error", "critical", "NVLink 通信错误"),
    79: ("GPU fallen off the bus", "critical", "GPU 从 PCIe 总线脱落"),
    92: ("High SBE ECC count", "warning", "高频单比特 ECC 错误"),
    94: ("Contained ECC error", "warning", "受控 ECC 错误（常见于 H100/H20）"),
    95: ("Uncontained ECC error", "critical", "不受控 ECC 错误，硬件问题"),
}


# ==================== Prometheus 查询 ====================


def get_prom_uid(cluster: str) -> str:
    uid = CLUSTER_DATASOURCES.get(cluster, {}).get("prometheus")
    if not uid:
        raise ValueError(f"未知集群: {cluster}，可用: {list(CLUSTER_DATASOURCES)}")
    return uid


def prom_instant_query(expr: str, prom_uid: str) -> dict:
    """查询 Grafana Prometheus（匿名，即时查询）"""
    body = {
        "queries": [{
            "refId": "A",
            "expr": expr,
            "datasource": {"type": "prometheus", "uid": prom_uid},
            "instant": True,
            "maxDataPoints": 1,
        }],
        "from": "now-1h",
        "to": "now",
    }
    url = f"{GRAFANA_URL}/api/ds/query"
    req = Request(url, data=json.dumps(body).encode("utf-8"), headers=GRAFANA_HEADERS, method="POST")
    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def parse_prom_response(resp: dict) -> list[dict]:
    """解析 Prometheus 响应为 {hostname, gpu, value, labels} 列表"""
    results = []
    frames = resp.get("results", {}).get("A", {}).get("frames", [])
    for frame in frames:
        fields = frame.get("schema", {}).get("fields", [])
        values = frame.get("data", {}).get("values", [])

        labels = {}
        for field in fields:
            if field.get("labels"):
                labels = field["labels"]
                break

        val = None
        for i, field in enumerate(fields):
            if field.get("type") == "number" and i < len(values) and values[i]:
                raw = values[i]
                val = raw[-1] if isinstance(raw, list) else raw
                break

        if val is not None:
            results.append({
                "hostname": labels.get("Hostname", labels.get("hostname", labels.get("instance", "unknown"))),
                "gpu": labels.get("gpu", labels.get("GPU_I_ID", "?")),
                "value": float(val),
                "labels": labels,
            })
    return results


def query_dcgm_metric(metric: str, hostname_pattern: str, prom_uid: str) -> list[dict]:
    """查询单个 DCGM 指标，按 hostname 模式过滤"""
    for label_key in ("Hostname", "hostname"):
        expr = f'{metric}{{{label_key}=~"{hostname_pattern}"}}'
        try:
            resp = prom_instant_query(expr, prom_uid)
            results = parse_prom_response(resp)
            if results:
                return results
        except Exception:
            continue
    return []


# ==================== GPU 健康检查 ====================


def check_gpu_health(hostnames: list[str], cluster: str) -> dict[str, Any]:
    """对一组节点进行 GPU 健康检查"""
    prom_uid = get_prom_uid(cluster)
    pattern = "|".join(hostnames)

    report: dict[str, Any] = {
        "cluster": cluster,
        "hostnames": hostnames,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "metrics": {},
        "issues": [],
        "summary": "healthy",
    }

    for metric_name, meta in DCGM_HEALTH_METRICS.items():
        print(f"[INFO] 查询 {meta['name']}...", file=sys.stderr)
        results = query_dcgm_metric(metric_name, pattern, prom_uid)

        metric_data = {
            "name": meta["name"],
            "severity": meta["severity"],
            "results": [],
        }

        for r in results:
            entry = {
                "hostname": r["hostname"],
                "gpu": r["gpu"],
                "value": r["value"],
            }
            metric_data["results"].append(entry)

            if r["value"] > 0:
                issue = {
                    "metric": meta["name"],
                    "hostname": r["hostname"],
                    "gpu": r["gpu"],
                    "value": r["value"],
                    "severity": meta["severity"],
                    "desc": meta["desc"],
                }
                # Xid 错误附加错误码解释
                if metric_name == "DCGM_FI_DEV_XID_ERRORS":
                    xid_code = int(r["value"])
                    xid_info = XID_REFERENCE.get(xid_code)
                    if xid_info:
                        issue["xid_name"] = xid_info[0]
                        issue["xid_severity"] = xid_info[1]
                        issue["xid_desc"] = xid_info[2]
                        issue["severity"] = xid_info[1]

                report["issues"].append(issue)

        report["metrics"][metric_name] = metric_data

    # 判定整体健康状态
    severities = [i["severity"] for i in report["issues"]]
    if "critical" in severities:
        report["summary"] = "critical"
    elif "warning" in severities:
        report["summary"] = "warning"
    else:
        report["summary"] = "healthy"

    return report


# ==================== kubectl 节点信息 ====================


def _kubectl(args: list[str], cluster: str) -> Optional[str]:
    """执行 kubectl 命令（需要 SOCKS5 代理隧道）"""
    import os
    env = os.environ.copy()
    env["HTTPS_PROXY"] = HTTPS_PROXY
    cmd = ["kubectl", "--context", cluster] + args
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15, env=env)
        if result.returncode == 0:
            return result.stdout
        print(f"[WARN] kubectl 失败: {result.stderr.strip()}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"[WARN] kubectl 异常: {e}", file=sys.stderr)
        return None


def resolve_ips_to_nodes(ips: list[str], cluster: str) -> dict[str, dict]:
    """通过 IP 地址查找 K8s 节点名"""
    output = _kubectl(["get", "nodes", "-o", "wide", "--no-headers"], cluster)
    if not output:
        return {}

    mapping = {}
    for line in output.strip().split("\n"):
        parts = line.split()
        if len(parts) >= 6:
            node_name = parts[0]
            internal_ip = parts[5]
            if internal_ip in ips:
                mapping[internal_ip] = {
                    "node_name": node_name,
                    "status": parts[1],
                    "ip": internal_ip,
                }
    return mapping


def get_node_conditions(node_name: str, cluster: str) -> list[dict]:
    """获取节点 conditions"""
    output = _kubectl([
        "get", "node", node_name, "-o",
        "jsonpath={.status.conditions[*]}",
    ], cluster)
    if not output:
        return []

    # jsonpath 输出是空格分隔的 JSON 对象，需要包裹成数组
    try:
        # kubectl jsonpath 对 [*] 输出的是 map 序列，不是 JSON 数组
        # 直接用 describe 更可靠
        desc = _kubectl(["describe", "node", node_name], cluster)
        if not desc:
            return []
        conditions = []
        in_conditions = False
        for line in desc.split("\n"):
            if line.startswith("Conditions:"):
                in_conditions = True
                continue
            if in_conditions:
                if line.startswith("  ") and not line.startswith("    "):
                    # 新的顶层段落，退出
                    break
                parts = line.split()
                if len(parts) >= 3 and parts[0] not in ("Type", "----"):
                    conditions.append({
                        "type": parts[0],
                        "status": parts[1],
                    })
        return conditions
    except Exception:
        return []


def get_node_gpu_labels(node_name: str, cluster: str) -> dict:
    """获取节点 GPU 相关标签"""
    output = _kubectl([
        "get", "node", node_name, "-o",
        "jsonpath={.metadata.labels}",
    ], cluster)
    if not output:
        return {}

    try:
        all_labels = json.loads(output)
        keywords = ("gpu", "nvidia", "accelerator", "device", "health", "topology", "product", "hpc")
        return {k: v for k, v in all_labels.items() if any(w in k.lower() for w in keywords)}
    except Exception:
        return {}


def get_node_info(node_name: str, cluster: str) -> dict:
    """获取节点完整信息"""
    conditions = get_node_conditions(node_name, cluster)
    gpu_labels = get_node_gpu_labels(node_name, cluster)

    unhealthy = [c for c in conditions if c["type"] == "Ready" and c["status"] != "True"]
    unhealthy += [c for c in conditions if c["type"] != "Ready" and c["status"] == "True"
                  and c["type"] not in ("SufficientIP",)]

    return {
        "node_name": node_name,
        "conditions": conditions,
        "gpu_labels": gpu_labels,
        "unhealthy_conditions": unhealthy,
    }


# ==================== 主流程 ====================


def main():
    parser = argparse.ArgumentParser(description="GPU 节点健康检查")
    parser.add_argument("--cluster", required=True, help="集群名称")
    parser.add_argument("--hostnames", nargs="+", help="训练日志中的主机名")
    parser.add_argument("--ips", nargs="+", help="节点 IP 地址")
    parser.add_argument("--kubectl", action="store_true", help="附加 kubectl 查询")
    parser.add_argument("--output", default="-", help="输出文件路径")
    args = parser.parse_args()

    if not args.hostnames and not args.ips:
        parser.error("请提供 --hostnames 或 --ips")

    hostnames = args.hostnames or []

    # 如果提供了 IP，通过 kubectl 解析节点名
    node_map: dict[str, dict] = {}
    if args.ips:
        if args.kubectl:
            print("[INFO] 通过 kubectl 解析 IP → 节点名...", file=sys.stderr)
            node_map = resolve_ips_to_nodes(args.ips, args.cluster)
            for ip, info in node_map.items():
                print(f"  {ip} → {info['node_name']} ({info['status']})", file=sys.stderr)
                if info["node_name"] not in hostnames:
                    hostnames.append(info["node_name"])
        else:
            print("[WARN] 提供了 --ips 但未启用 --kubectl，无法解析节点名", file=sys.stderr)
            print("[WARN] Prometheus 中 hostname 可能与 IP 不匹配", file=sys.stderr)

    if not hostnames:
        print("[FATAL] 无可查询的主机名", file=sys.stderr)
        sys.exit(1)

    # Step 1: Prometheus DCGM 指标查询
    print(f"[INFO] GPU 健康检查: {hostnames}", file=sys.stderr)
    gpu_report = check_gpu_health(hostnames, args.cluster)

    # Step 2: kubectl 节点信息（可选）
    k8s_nodes = {}
    if args.kubectl:
        for ip, info in node_map.items():
            node_name = info["node_name"]
            print(f"[INFO] 查询节点信息: {node_name}...", file=sys.stderr)
            k8s_nodes[node_name] = get_node_info(node_name, args.cluster)

    # 汇总
    result = {
        "gpu_health": gpu_report,
        "k8s_nodes": k8s_nodes if k8s_nodes else None,
        "node_ip_mapping": node_map if node_map else None,
    }

    output = json.dumps(result, ensure_ascii=False, indent=2, default=str)

    if args.output == "-":
        print(output)
    else:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"[INFO] 结果已写入: {args.output}", file=sys.stderr)

    # 摘要
    print(f"\n[SUMMARY]", file=sys.stderr)
    print(f"  整体状态: {gpu_report['summary']}", file=sys.stderr)
    print(f"  检查节点: {len(hostnames)}", file=sys.stderr)
    print(f"  发现问题: {len(gpu_report['issues'])}", file=sys.stderr)
    for issue in gpu_report["issues"]:
        xid_hint = f" (Xid {int(issue['value'])}: {issue.get('xid_name', '?')})" if "xid_name" in issue else ""
        print(f"    [{issue['severity']}] {issue['hostname']} GPU{issue['gpu']}: "
              f"{issue['metric']}={issue['value']}{xid_hint}", file=sys.stderr)


if __name__ == "__main__":
    main()
