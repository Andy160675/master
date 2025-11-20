from dataclasses import dataclass
from typing import List, Set
from .topology import Topology, Pod

@dataclass
class RouteCheck:
    valid: bool
    cvf_codes: List[str]
    reason: str | None = None


def _pods_for(topology: Topology, path: List[str]) -> List[Pod]:
    return [topology.pods[p] for p in path]


def validate_path(topology: Topology, path: List[str], critical: bool = False) -> RouteCheck:
    cvfs: List[str] = []

    # 0) existence
    for pid in path:
        if pid not in topology.pods:
            cvfs.append("CVF.TOPOLOGY_INVALID_POD")
            return RouteCheck(False, cvfs, f"Unknown pod {pid}")

    # 1) Sudoku: no repeats
    if len(path) != len(set(path)):
        cvfs.append("CVF.TOPOLOGY_SUDOKU_VIOLATION")
        return RouteCheck(False, cvfs, "Repeated pod in path")

    # 2) edges legal
    for a, b in zip(path, path[1:]):
        if b not in topology.neighbors(a):
            cvfs.append("CVF.TOPOLOGY_INVALID_PATH")
            return RouteCheck(False, cvfs, f"Illegal edge {a} -> {b}")

    if not critical:
        return RouteCheck(True, cvfs)

    # 3) critical requires >=3 distinct pods
    if len(path) < 3:
        cvfs.append("CVF.TOPOLOGY_INSUFFICIENT_PODS")
        return RouteCheck(False, cvfs, "Critical path has fewer than 3 pods")

    pods = _pods_for(topology, path)
    nodes: Set[str] = {p.node for p in pods}
    domains: Set[str] = {p.domain for p in pods}

    if len(nodes) < 2:
        cvfs.append("CVF.TOPOLOGY_MISSING_NODE_VARIETY")
    if len(domains) < 2:
        cvfs.append("CVF.TOPOLOGY_MISSING_DOMAIN_VARIETY")

    if cvfs:
        return RouteCheck(False, cvfs, "Critical path missing diversity")
    return RouteCheck(True, cvfs)
