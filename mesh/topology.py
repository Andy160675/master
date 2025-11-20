from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List
import yaml

TOPOLOGY_PATH = Path("config/topology.yaml")

@dataclass(frozen=True)
class Pod:
    id: str
    node: str
    domain: str

class Topology:
    def __init__(self, path: Path = TOPOLOGY_PATH):
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        self.pods: Dict[str, Pod] = {p["id"]: Pod(id=p["id"], node=p["node"], domain=p["domain"]) for p in raw["pods"]}
        self.edges: Dict[str, List[str]] = {}
        for e in raw.get("edges", []):
            src = e["from"]; dst = e["to"]
            self.edges.setdefault(src, []).append(dst)

    def neighbors(self, pod_id: str) -> List[str]:
        return self.edges.get(pod_id, [])

    def all_pods(self) -> List[str]:
        return list(self.pods.keys())
