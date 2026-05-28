#!/usr/bin/env python3
"""
RDMA / InfiniBand 网络健康检查

当 NCCL 报 socket 连接错误且目标 IP 属于 RDMA overlay 网段（200.33.x.x）时，
通过 kubectl 定位故障节点并检查 IB 链路状态。

数据通道：
  kubectl → kube-proxy pod exec（/proc/net/fib_trie）→ RDMA IP 映射
  kubectl → debug node → dmesg（mlx5/bond 事件）

依赖：
  - kubectl + kubeconfig（已配置对应 context）
  - SOCKS5 代理隧道（端口 1080）

用法:
  python3 check_rdma_health.py \
    --cluster hpc-prod-al-sh01 \
    --nodes e01-cn-xxx e01-cn-yyy \
    --target-ip 200.33.8.30
"""

import argparse
import json
import os
import re
import subprocess
import sys
from typing import Optional


# ==================== 配置 ====================

HTTPS_PROXY = "socks5://127.0.0.1:1080"
KUBECTL_TIMEOUT = 20


# ==================== kubectl 封装 ====================


def _kubectl(args: list[str], cluster: str, timeout: int = KUBECTL_TIMEOUT) -> Optional[str]:
    env = os.environ.copy()
    env["HTTPS_PROXY"] = HTTPS_PROXY
    cmd = ["kubectl", "--context", cluster] + args
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)
        if result.returncode == 0:
            return result.stdout
        print(f"[WARN] kubectl 失败: {' '.join(args[:4])} -> {result.stderr.strip()[:200]}", file=sys.stderr)
        return None
    except subprocess.TimeoutExpired:
        print(f"[WARN] kubectl 超时: {' '.join(args[:4])}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"[WARN] kubectl 异常: {e}", file=sys.stderr)
        return None


# ==================== kube-proxy pod 发现 ====================


def find_kube_proxy_pods(nodes: list[str], cluster: str) -> dict[str, str]:
    """查找各节点上的 kube-proxy pod（hostNetwork，可读 /proc/net/*）"""
    output = _kubectl(["get", "pods", "-n", "kube-system", "-o", "wide", "--no-headers"], cluster)
    if not output:
        return {}

    node_set = set(nodes)
    result: dict[str, str] = {}

    for line in output.strip().split("\n"):
        parts = line.split()
        if len(parts) < 7:
            continue
        pod_name = parts[0]
        if "kube-proxy" not in pod_name:
            continue
        # -o wide 格式: NAME READY STATUS RESTARTS AGE IP NODE ...
        node_name = parts[6]
        if node_name in node_set:
            result[node_name] = pod_name

    return result


# ==================== RDMA IP 扫描 ====================


def get_rdma_ips_via_fib_trie(pod_name: str, cluster: str) -> list[str]:
    """通过 kube-proxy pod 读取 /proc/net/fib_trie，提取 200.33.x.x 本地 IP"""
    output = _kubectl(
        ["exec", "-n", "kube-system", pod_name, "--", "cat", "/proc/net/fib_trie"],
        cluster, timeout=15,
    )
    if not output:
        return []

    # fib_trie 中 "host LOCAL" 前一行包含本机 IP
    ips = []
    lines = output.split("\n")
    for i, line in enumerate(lines):
        if "host LOCAL" in line and i > 0:
            m = re.search(r"(200\.33\.\d+\.\d+)", lines[i - 1])
            if m:
                ips.append(m.group(1))
    return sorted(set(ips))


def scan_rdma_ips(nodes: list[str], cluster: str) -> dict[str, list[str]]:
    """扫描所有节点的 RDMA overlay IP"""
    proxy_pods = find_kube_proxy_pods(nodes, cluster)
    if not proxy_pods:
        print("[ERROR] 未找到任何 kube-proxy pod，无法扫描 RDMA IP", file=sys.stderr)
        return {}

    mapping: dict[str, list[str]] = {}
    for node in nodes:
        pod = proxy_pods.get(node)
        if not pod:
            print(f"[WARN] 节点 {node} 未找到 kube-proxy pod", file=sys.stderr)
            mapping[node] = []
            continue

        print(f"[INFO] 扫描 {node} (via {pod})...", file=sys.stderr)
        ips = get_rdma_ips_via_fib_trie(pod, cluster)
        mapping[node] = ips

    return mapping


def locate_rdma_ip(target_ip: str, rdma_map: dict[str, list[str]]) -> Optional[str]:
    """定位某个 RDMA IP 属于哪个节点"""
    for node, ips in rdma_map.items():
        if target_ip in ips:
            return node
    return None


# ==================== IB 链路健康检查（dmesg） ====================


def check_ib_dmesg(node: str, cluster: str) -> dict:
    """
    通过 kubectl debug node 读取 dmesg 中的 IB/mlx5/bond 事件。

    返回结构化结果：link_events, cable_events, bond_events, raw_lines
    """
    # kubectl debug 创建临时 pod，用 chroot 读宿主机 dmesg
    output = _kubectl(
        ["debug", f"node/{node}", "-it",
         "--image=busybox", "--profile=general",
         "--", "chroot", "/host", "dmesg"],
        cluster, timeout=30,
    )

    result = {
        "node": node,
        "link_down_events": [],
        "link_up_events": [],
        "cable_events": [],
        "bond_no_active": False,
        "raw_lines": [],
        "error": None,
    }

    if not output:
        result["error"] = "无法读取 dmesg（kubectl debug 失败）"
        return result

    # 过滤 IB 相关行
    patterns = re.compile(r"mlx5|bond\d+.*(?:link|slave|active|interface)|reth\d+.*Link", re.IGNORECASE)
    relevant_lines = [line for line in output.split("\n") if patterns.search(line)]
    result["raw_lines"] = relevant_lines[-80:]

    for line in relevant_lines:
        # Link down 事件
        if re.search(r"Link\s*(down|DOWN)", line):
            result["link_down_events"].append(line.strip())

        # Link up 事件
        if re.search(r"Link\s*(up|UP)", line):
            result["link_up_events"].append(line.strip())

        # 光模块拔插事件
        if "Cable unplugged" in line or "Cable plugged" in line:
            result["cable_events"].append(line.strip())

        # bond 无可用接口
        if "without any active interface" in line:
            result["bond_no_active"] = True

    return result


def cleanup_debug_pods(node: str, cluster: str):
    """清理 kubectl debug 创建的临时 pod"""
    output = _kubectl(
        ["get", "pods", "--all-namespaces", "--no-headers",
         "-o", "custom-columns=NS:.metadata.namespace,NAME:.metadata.name",
         "--field-selector", f"spec.nodeName={node}"],
        cluster,
    )
    if not output:
        return

    for line in output.strip().split("\n"):
        parts = line.split()
        if len(parts) == 2 and "node-debugger-" in parts[1]:
            print(f"[INFO] 清理 debug pod: {parts[1]}", file=sys.stderr)
            _kubectl(["delete", "pod", "-n", parts[0], parts[1], "--wait=false"], cluster)


# ==================== 综合诊断 ====================


def diagnose_rdma(nodes: list[str], cluster: str, target_ip: Optional[str]) -> dict:
    """
    完整 RDMA 诊断流程：
    1. 扫描所有节点 RDMA IP，建立映射
    2. 定位目标 IP 所属节点
    3. 检查故障节点的 IB 链路健康
    """
    report = {
        "cluster": cluster,
        "target_ip": target_ip,
        "target_node": None,
        "rdma_ip_map": {},
        "ib_health": None,
        "diagnosis": "unknown",
        "details": "",
    }

    # Step 1: 扫描 RDMA IP
    print(f"[INFO] 扫描 {len(nodes)} 个节点的 RDMA IP...", file=sys.stderr)
    rdma_map = scan_rdma_ips(nodes, cluster)
    report["rdma_ip_map"] = rdma_map

    # Step 2: 定位目标 IP
    target_node = None
    if target_ip:
        target_node = locate_rdma_ip(target_ip, rdma_map)
        report["target_node"] = target_node
        if target_node:
            print(f"[INFO] 目标 IP {target_ip} → 节点 {target_node}", file=sys.stderr)
        else:
            print(f"[WARN] 目标 IP {target_ip} 未在已扫描节点中找到", file=sys.stderr)
            report["diagnosis"] = "target_ip_not_found"
            report["details"] = f"RDMA IP {target_ip} 不属于本次任务的任何节点，可能属于其他任务的节点"
            return report

    # Step 3: 检查故障节点 IB 健康
    check_node = target_node or nodes[0]
    print(f"[INFO] 检查节点 {check_node} 的 IB 链路健康...", file=sys.stderr)
    ib_health = check_ib_dmesg(check_node, cluster)
    report["ib_health"] = ib_health

    # 清理 debug pod
    cleanup_debug_pods(check_node, cluster)

    # Step 4: 判定
    if ib_health.get("bond_no_active"):
        report["diagnosis"] = "bond_total_failure"
        report["details"] = (
            f"节点 {check_node} 的 RDMA bond 网卡完全断连（无可用 slave），"
            f"检测到 {len(ib_health.get('link_down_events', []))} 次 link down 事件、"
            f"{len(ib_health.get('cable_events', []))} 次光模块拔插事件。"
            f"需要更换光模块/线缆或检查交换机端口。"
        )
    elif len(ib_health.get("link_down_events", [])) > 3:
        report["diagnosis"] = "link_flapping"
        report["details"] = (
            f"节点 {check_node} 的 IB 链路频繁抖动，"
            f"检测到 {len(ib_health.get('link_down_events', []))} 次 link down、"
            f"{len(ib_health.get('cable_events', []))} 次光模块事件。"
            f"可能是光模块老化或线缆接触不良。"
        )
    elif len(ib_health.get("link_down_events", [])) > 0:
        report["diagnosis"] = "link_transient"
        report["details"] = (
            f"节点 {check_node} 有少量 link down 事件"
            f"（{len(ib_health.get('link_down_events', []))} 次），"
            f"可能是瞬时网络抖动。建议重试任务，如果反复失败再更换硬件。"
        )
    else:
        report["diagnosis"] = "healthy"
        report["details"] = f"节点 {check_node} 的 IB 链路无异常事件，dmesg 中未发现 link down。"

    return report


# ==================== 主流程 ====================


def main():
    parser = argparse.ArgumentParser(description="RDMA 网络健康检查")
    parser.add_argument("--cluster", required=True, help="集群名称")
    parser.add_argument("--nodes", nargs="+", required=True, help="K8s 节点名列表")
    parser.add_argument("--target-ip", help="NCCL 报错中的目标 RDMA IP（如 200.33.8.30）")
    parser.add_argument("--output", default="-", help="输出文件路径（默认 stdout）")
    args = parser.parse_args()

    report = diagnose_rdma(args.nodes, args.cluster, args.target_ip)

    output = json.dumps(report, ensure_ascii=False, indent=2, default=str)

    if args.output == "-":
        print(output)
    else:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"[INFO] 结果已写入: {args.output}", file=sys.stderr)

    # 摘要
    print(f"\n[SUMMARY]", file=sys.stderr)
    print(f"  诊断结论: {report['diagnosis']}", file=sys.stderr)
    if report["target_ip"] and report["target_node"]:
        print(f"  目标 IP:  {report['target_ip']} → {report['target_node']}", file=sys.stderr)
    print(f"  详情: {report['details']}", file=sys.stderr)

    # 非 healthy 时退出码为 1
    if report["diagnosis"] not in ("healthy",):
        sys.exit(1)


if __name__ == "__main__":
    main()
