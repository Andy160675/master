"""Sovereign Resource (Phase 1)

Constitutional substrate only:
- Offline construction and hashing
- No execution-surface adapters
- No external I/O beyond deterministic serialization

This module provides the minimal, sealed primitives required by Phase 1
storage substrate (sovereign_storage.py).
"""

from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional
from uuid import uuid4


class ResourceType(str, Enum):
    SYSTEM = "system"
    DOCUMENT = "document"
    BLOB = "blob"


class AccessLevel(str, Enum):
    PRIVATE = "private"
    RESTRICTED = "restricted"
    PUBLIC = "public"


def _canonical_json(data: Dict[str, Any]) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha3_hex(value: str) -> str:
    return hashlib.sha3_256(value.encode("utf-8")).hexdigest()


@dataclass
class SovereignResource:
    """A minimal, policy-embedded resource object.

    This object is evidence-grade and deterministic:
    - `constitutional_hash` is derived from resource content + metadata + governance embedding.
    - `embed_parent_governance` tightens lineage integrity by updating the hash.
    """

    resource_type: ResourceType
    data: bytes
    metadata: Dict[str, Any]
    governance_template: str
    resource_id: str = ""
    constitutional_hash: str = ""

    def __post_init__(self) -> None:
        if not self.resource_id:
            self.resource_id = str(uuid4())
        if not self.constitutional_hash:
            self.constitutional_hash = self.compute_constitutional_hash()

    def compute_constitutional_hash(self) -> str:
        metadata = dict(self.metadata or {})
        if isinstance(metadata.get("access_level"), Enum):
            metadata["access_level"] = metadata["access_level"].value

        payload = {
            "resource_id": self.resource_id,
            "resource_type": self.resource_type.value,
            "governance_template": self.governance_template,
            "metadata": metadata,
            "data_sha3_256": hashlib.sha3_256(self.data).hexdigest(),
        }
        return _sha3_hex(_canonical_json(payload))

    def embed_parent_governance(self, parent_constitutional_hash: str, lineage_depth: int) -> None:
        """Embed parent governance into this resource.

        This mutates the resource's constitutional embedding (hash) but does not
        add any new powers or side effects.
        """
        md = dict(self.metadata or {})
        md["parent_constitutional_hash"] = parent_constitutional_hash
        md["lineage_depth"] = int(lineage_depth)
        self.metadata = md
        self.constitutional_hash = self.compute_constitutional_hash()

    def to_dict(self) -> Dict[str, Any]:
        metadata = dict(self.metadata or {})
        if isinstance(metadata.get("access_level"), Enum):
            metadata["access_level"] = metadata["access_level"].value

        return {
            "resource_id": self.resource_id,
            "resource_type": self.resource_type.value,
            "governance_template": self.governance_template,
            "metadata": metadata,
            "data_b64": base64.b64encode(self.data).decode("ascii"),
            "constitutional_hash": self.constitutional_hash,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SovereignResource":
        resource_type = ResourceType(str(data.get("resource_type")))
        raw = base64.b64decode(str(data.get("data_b64", "")) or "")
        metadata = dict(data.get("metadata") or {})
        access_level = metadata.get("access_level")
        if isinstance(access_level, str):
            try:
                metadata["access_level"] = AccessLevel(access_level)
            except Exception:
                pass

        obj = cls(
            resource_type=resource_type,
            data=raw,
            metadata=metadata,
            governance_template=str(data.get("governance_template") or ""),
            resource_id=str(data.get("resource_id") or ""),
            constitutional_hash=str(data.get("constitutional_hash") or ""),
        )
        if not obj.constitutional_hash:
            obj.constitutional_hash = obj.compute_constitutional_hash()
        return obj
