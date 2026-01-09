"""
Sovereign Storage: Fractal Resource Graph with Embedded Policy
Version: 1.0.0
Constitutional Compliance: Baseline v1.2
Governance Model: Recursive Resource Sovereignty

ARCHITECTURAL PRINCIPLE:
- This module is part of the constitutional substrate (sovereign_os)
- NEVER executes on commodity hosting (execution surface)
- Generates constraints that execution surfaces must obey
- All receipts are cryptographically signed and stored offline
"""

import hashlib
import json
import time
import yaml
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from pathlib import Path

import networkx as nx
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.exceptions import InvalidSignature

from .sovereign_resource import SovereignResource, ResourceType, AccessLevel


# =========================
# Constitutional Exceptions
# =========================

class ConstitutionalViolationError(Exception):
    """Raised when an operation violates constitutional principles."""
    pass


class ResourceNotFoundError(Exception):
    """Raised when a requested resource does not exist."""
    pass


class AccessDeniedError(Exception):
    """Raised when access violates embedded resource governance."""
    pass


class FractalIntegrityError(Exception):
    """Raised when fractal graph integrity is compromised."""
    pass


# =========================
# Evidence Receipt
# =========================

@dataclass
class StorageReceipt:
    """
    Immutable cryptographic receipt for storage operations.

    Receipts are evidence only:
    - They do not grant authority
    - They do not drive behavior
    - They prove historical compliance
    """

    operation_id: str
    resource_id: str
    timestamp: float
    constitutional_hash: str
    policy_version: str
    storage_root_signature: str
    witness_signatures: List[str] = field(default_factory=list)
    fractal_depth: int = 0
    execution_surface_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def generate_hash(self) -> str:
        """
        Generate deterministic constitutional hash for the receipt.
        """
        data = (
            f"{self.operation_id}"
            f"{self.resource_id}"
            f"{self.timestamp}"
            f"{self.policy_version}"
            f"{self.execution_surface_id or ''}"
        )
        return hashlib.sha3_256(data.encode()).hexdigest()


# =========================
# Storage Policy
# =========================

class StoragePolicy:
    """
    Constitutional storage policy derived from baseline.yaml and guardrails.

    Policies are generated OFFLINE and enforced by execution surfaces.
    """

    def __init__(self, constitution_path: str, guardrails_path: str):
        self.constitution = self._load_yaml(constitution_path, required=["principles", "governance_model", "version"])
        self.guardrails = self._load_yaml(guardrails_path, required=None)

    @staticmethod
    def _load_yaml(path: str, required: Optional[List[str]]) -> Dict[str, Any]:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        if required:
            for key in required:
                if key not in data:
                    raise ValueError(f"Missing required constitutional section: {key}")

        return data

    def generate_constraints(
        self,
        operation: str,
        resource_type: ResourceType,
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate constraint set for an execution surface.
        """
        constraints: Dict[str, Any] = {
            "operation": operation,
            "resource_type": resource_type.value,
            "timestamp": time.time(),
            "constitutional_version": self.constitution.get("version", "1.0"),
            "constraints": [],
            "nonce": hashlib.sha256(str(time.time_ns()).encode()).hexdigest()[:16],
        }

        if not metadata.get("self_attested", False):
            constraints["constraints"].append({
                "type": "verification",
                "requirement": "self_attestation",
                "message": "Resource must include self-attestation",
            })

        access_level = metadata.get("access_level")
        if isinstance(access_level, AccessLevel):
            access_level = access_level.value

        if operation == "write" and access_level == AccessLevel.PUBLIC.value:
            quorum = self.guardrails.get("public_write_restrictions", {}).get("quorum_size", 3)
            constraints["constraints"].append({
                "type": "access_control",
                "requirement": "quorum_approval",
                "quorum_size": quorum,
                "message": "Public writes require quorum approval",
            })

        if operation == "delete":
            constraints["constraints"].append({
                "type": "consent",
                "requirement": "recursive_consent",
                "scope": "lineage",
                "message": "Deletion requires recursive lineage consent",
            })

        if operation in {"create", "update", "delete"}:
            constraints["constraints"].append({
                "type": "transparency",
                "requirement": "immutable_log",
                "message": "Mutation must be logged to evidence ledger",
            })

        return constraints

    def verify_compliance(
        self,
        execution_result: Dict[str, Any],
        constraints: Dict[str, Any],
    ) -> Tuple[bool, str]:
        """
        Verify execution-surface compliance OFFLINE.
        """
        violations: List[str] = []

        for rule in constraints.get("constraints", []):
            rtype = rule.get("type")

            if rtype == "verification":
                if not execution_result.get("verifications", {}).get("self_attestation"):
                    violations.append(rule["message"])

            elif rtype == "access_control":
                approvals = execution_result.get("approvals", [])
                if len(approvals) < rule.get("quorum_size", 1):
                    violations.append(rule["message"])

            elif rtype == "transparency":
                if not execution_result.get("evidence_logged"):
                    violations.append(rule["message"])

        if violations:
            return False, "; ".join(violations)

        return True, "Compliant"


# =========================
# Fractal Resource Graph
# =========================

class FractalGraph:
    """
    Fractal resource graph with embedded governance.

    The full graph NEVER exists on execution surfaces.
    """

    def __init__(self, evidence_path: str = "evidence/genealogy/"):
        self.graph = nx.DiGraph()
        self.resource_registry: Dict[str, SovereignResource] = {}
        self.evidence_path = Path(evidence_path)
        self.evidence_path.mkdir(parents=True, exist_ok=True)

        self._load_from_evidence()

    def _load_from_evidence(self) -> None:
        state_file = self.evidence_path / "graph_state.json"
        if not state_file.exists():
            return

        with open(state_file, "r", encoding="utf-8") as f:
            state = json.load(f)

        for node_id, node_data in state.get("nodes", {}).items():
            self.graph.add_node(
                node_id,
                constitutional_hash=node_data["constitutional_hash"],
                lineage_depth=node_data["lineage_depth"],
            )

        for edge in state.get("edges", []):
            self.graph.add_edge(edge["source"], edge["target"])

    def _persist_to_evidence(self) -> None:
        state = {
            "timestamp": time.time(),
            "nodes": {
                nid: {
                    "constitutional_hash": self.graph.nodes[nid]["constitutional_hash"],
                    "lineage_depth": self.graph.nodes[nid]["lineage_depth"],
                }
                for nid in self.graph.nodes
            },
            "edges": [{"source": s, "target": t} for s, t in self.graph.edges],
        }

        path = self.evidence_path / "graph_state.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, sort_keys=True)

    def add_resource(self, resource: SovereignResource, parent_id: Optional[str] = None) -> str:
        resource_id = resource.resource_id

        depth = 0
        if parent_id and parent_id in self.graph:
            depth = self.graph.nodes[parent_id]["lineage_depth"] + 1
            self.graph.add_edge(parent_id, resource_id)
            resource.embed_parent_governance(
                self.graph.nodes[parent_id]["constitutional_hash"],
                depth,
            )

        self.graph.add_node(
            resource_id,
            constitutional_hash=resource.constitutional_hash,
            lineage_depth=depth,
        )

        self.resource_registry[resource_id] = resource
        self._persist_to_evidence()
        return resource_id

    def get_verifiable_subset(self, resource_id: str, depth: int = 3) -> Dict[str, Any]:
        if resource_id not in self.graph:
            raise ResourceNotFoundError(resource_id)

        lineage: List[Dict[str, Any]] = []
        current = resource_id

        for _ in range(depth):
            if current not in self.graph:
                break
            node = self.graph.nodes[current]
            lineage.append({
                "resource_id": current,
                "constitutional_hash": node["constitutional_hash"],
                "depth": node["lineage_depth"],
            })
            parents = list(self.graph.predecessors(current))
            current = parents[0] if parents else None

        return {
            "root_id": resource_id,
            "timestamp": time.time(),
            "lineage": lineage,
            "merkle_root": self._merkle_root(lineage),
        }

    @staticmethod
    def _merkle_root(lineage: List[Dict[str, Any]]) -> str:
        if not lineage:
            return ""

        leaves = [
            hashlib.sha3_256(
                f"{n['resource_id']}:{n['constitutional_hash']}:{n['depth']}".encode()
            ).hexdigest()
            for n in sorted(lineage, key=lambda x: x["depth"])
        ]

        while len(leaves) > 1:
            if len(leaves) % 2:
                leaves.append(leaves[-1])
            leaves = [
                hashlib.sha3_256((leaves[i] + leaves[i + 1]).encode()).hexdigest()
                for i in range(0, len(leaves), 2)
            ]

        return leaves[0]


# =========================
# Sovereign Storage
# =========================

class SovereignStorage:
    """
    Constitutional storage substrate.

    Runs OFFLINE only.
    """

    def __init__(
        self,
        constitution_path: str,
        guardrails_path: str,
        storage_key_path: Optional[str] = None,
    ):
        self.policy = StoragePolicy(constitution_path, guardrails_path)
        self.graph = FractalGraph()

        if storage_key_path and Path(storage_key_path).exists():
            with open(storage_key_path, "rb") as f:
                self.private_key = load_pem_private_key(f.read(), password=None)
        else:
            self.private_key = ec.generate_private_key(ec.SECP384R1())

        self.public_key = self.private_key.public_key()
        self.public_key_pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode()

        self.operation_counter = 0
        self._create_genesis_resource()

    def _sign_data(self, data: bytes) -> str:
        return self.private_key.sign(data, ec.ECDSA(hashes.SHA256())).hex()

    def _create_genesis_resource(self) -> None:
        genesis = SovereignResource(
            resource_type=ResourceType.SYSTEM,
            data=b"Sovereign Storage Genesis",
            metadata={
                "self_attested": True,
                "is_genesis": True,
                "storage_root_public_key": self.public_key_pem,
            },
            governance_template="genesis",
        )

        self.graph.add_resource(genesis)

    def generate_read_authorization(
        self,
        resource_id: str,
        requester_context: Dict,
    ) -> Dict:
        """
        Generate read authorization for execution surface.
        Contains access constraints and cryptographic proofs.

        NOTE: Authorization packages are evidence-grade declarations generated OFFLINE.
        They do not grant power; they constrain execution surfaces.
        """
        if resource_id not in self.graph.graph:
            raise ResourceNotFoundError(f"Resource {resource_id} not found")

        resource = self.graph.resource_registry.get(resource_id)
        if resource is None:
            raise ResourceNotFoundError(
                f"Resource {resource_id} not available in offline registry (evidence missing or not loaded)"
            )

        constraints = self.policy.generate_constraints(
            "read",
            resource.resource_type,
            resource.metadata,
        )

        verifiable_subset = self.graph.get_verifiable_subset(resource_id, depth=3)

        auth_package: Dict[str, Any] = {
            "constraints": constraints,
            "verifiable_subset": verifiable_subset,
            "resource_id": resource_id,
            "requester_context": requester_context,
            "generated_at": time.time(),
            "constitutional_hash": resource.constitutional_hash,
        }

        package_json = json.dumps(auth_package, sort_keys=True)
        auth_package["signature"] = self._sign_data(package_json.encode())

        return auth_package

    def verify_read_completion(
        self,
        execution_result: Dict,
        auth_package: Dict,
    ) -> StorageReceipt:
        """
        Verify that execution surface completed a read according to the authorization package.
        Generates a cryptographic receipt (OFFLINE).

        execution_result is expected to include proofs of compliance (e.g., verifications, approvals, evidence_logged).
        """
        package_copy = dict(auth_package)
        provided_signature = package_copy.pop("signature", None)
        if not provided_signature:
            raise ConstitutionalViolationError("Missing authorization package signature")

        package_json = json.dumps(package_copy, sort_keys=True)
        try:
            self.public_key.verify(
                bytes.fromhex(provided_signature),
                package_json.encode(),
                ec.ECDSA(hashes.SHA256()),
            )
        except InvalidSignature:
            raise ConstitutionalViolationError("Invalid authorization package signature")

        compliant, reason = self.policy.verify_compliance(execution_result, auth_package["constraints"])
        if not compliant:
            raise ConstitutionalViolationError(f"Read execution non-compliant: {reason}")

        resource_id = str(auth_package.get("resource_id"))
        if resource_id not in self.graph.graph:
            raise ResourceNotFoundError(f"Resource {resource_id} not found")

        node = self.graph.graph.nodes[resource_id]
        depth = int(node.get("lineage_depth", 0))

        exec_surface_id = execution_result.get("execution_surface_id") or auth_package.get("execution_surface_id")
        if exec_surface_id is not None:
            exec_surface_id = str(exec_surface_id)

        receipt = StorageReceipt(
            operation_id=f"read_{self.operation_counter:08x}",
            resource_id=resource_id,
            timestamp=time.time(),
            constitutional_hash=str(auth_package.get("constitutional_hash", "")),
            policy_version=self.policy.constitution.get("version", "1.0"),
            storage_root_signature=self._sign_data(str(auth_package.get("constitutional_hash", "")).encode()),
            execution_surface_id=exec_surface_id,
            fractal_depth=depth,
        )
        receipt.constitutional_hash = receipt.generate_hash()

        self._log_operation(
            operation="read_verified",
            resource_id=resource_id,
            details={
                "receipt_hash": receipt.constitutional_hash,
                "compliance_verified": True,
            },
        )

        self.operation_counter += 1
        return receipt

    def _log_operation(self, operation: str, resource_id: str, details: Dict[str, Any]) -> None:
        """Append a single evidence-grade operation log entry (OFFLINE).

        Append-only by file semantics (JSONL).
        """
        log_dir = self.graph.evidence_path
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / "storage_operations.jsonl"

        entry = {
            "timestamp": time.time(),
            "operation": operation,
            "resource_id": resource_id,
            "details": details,
        }

        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
