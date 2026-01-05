from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _repo_root() -> Path:
    # <root>/governance/phase2_5_engine/pipeline_manager.py -> parents[2] == <root>
    return Path(__file__).resolve().parents[2]


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _write_json_atomic(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
    tmp.replace(path)


def _next_sequential_id(existing_ids: list[str], prefix: str) -> str:
    max_n = 0
    for _id in existing_ids:
        if _id.startswith(prefix):
            tail = _id[len(prefix) :]
            if tail.isdigit():
                max_n = max(max_n, int(tail))
    return f"{prefix}{max_n + 1:03d}"


@dataclass(frozen=True)
class Lead:
    lead_id: str
    name: str
    contact: str
    source: str
    created_at: str


class PipelineManager:
    """Minimal pipeline manager.

    Persists:
    - data/pipeline/leads.json
    - data/pipeline/outreach_log.csv
    """

    def __init__(self, root: Optional[Path] = None) -> None:
        self.root = root or _repo_root()
        self.leads_path = self.root / "data" / "pipeline" / "leads.json"
        self.outreach_path = self.root / "data" / "pipeline" / "outreach_log.csv"

    def add_lead(self, name: str, contact: str, source: str) -> str:
        data: Dict[str, Any] = _read_json(self.leads_path, {"leads": {}})
        leads: Dict[str, Any] = data.get("leads", {})

        lead_id = _next_sequential_id(list(leads.keys()), prefix="lead_")
        lead = Lead(
            lead_id=lead_id,
            name=name,
            contact=contact,
            source=source,
            created_at=_utc_now_iso(),
        )

        leads[lead_id] = {
            "lead_id": lead.lead_id,
            "name": lead.name,
            "contact": lead.contact,
            "source": lead.source,
            "created_at": lead.created_at,
        }
        data["leads"] = leads
        data.setdefault("meta", {})
        data["meta"].setdefault("created_at", _utc_now_iso())
        data["meta"]["updated_at"] = _utc_now_iso()

        _write_json_atomic(self.leads_path, data)
        return lead_id

    def log_outreach(self, lead_id: str, campaign: str, channel: str, note: str) -> None:
        data: Dict[str, Any] = _read_json(self.leads_path, {"leads": {}})
        leads: Dict[str, Any] = data.get("leads", {})
        if lead_id not in leads:
            raise ValueError(f"Unknown lead_id: {lead_id}")

        self.outreach_path.parent.mkdir(parents=True, exist_ok=True)
        file_exists = self.outreach_path.exists()

        with self.outreach_path.open("a", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["timestamp_utc", "lead_id", "campaign", "channel", "note"])
            writer.writerow([_utc_now_iso(), lead_id, campaign, channel, note])
