from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _utc_now_iso() -> str:
    return _utc_now().isoformat().replace("+00:00", "Z")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _sha256_file(path: Path) -> Optional[str]:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _safe_git(cmd: list[str], cwd: Path) -> Optional[str]:
    try:
        out = subprocess.check_output(["git", *cmd], cwd=str(cwd), stderr=subprocess.DEVNULL)
        return out.decode("utf-8", errors="replace").strip() or None
    except Exception:
        return None


def generate_daily_report(root: Optional[Path] = None) -> Path:
    """Generate an auditable JSON evidence report under reports/."""

    root = root or _repo_root()

    leads_path = root / "data" / "pipeline" / "leads.json"
    outreach_path = root / "data" / "pipeline" / "outreach_log.csv"
    ledger_path = root / "data" / "financial" / "ledger.json"

    leads = _read_json(leads_path, {"leads": {}}).get("leads", {})
    ledger = _read_json(ledger_path, {"transactions": []}).get("transactions", [])

    outreach_count = 0
    if outreach_path.exists():
        with outreach_path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            for i, _row in enumerate(reader):
                if i == 0:
                    continue
                outreach_count += 1

    now = _utc_now()
    stamp = now.isoformat().replace("+00:00", "Z").replace(":", "").replace("-", "")
    reports_dir = root / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    report_path = reports_dir / f"daily_report_{stamp}.json"

    payload: Dict[str, Any] = {
        "timestamp_utc": _utc_now_iso(),
        "git": {
            "head": _safe_git(["rev-parse", "HEAD"], root),
            "branch": _safe_git(["rev-parse", "--abbrev-ref", "HEAD"], root),
        },
        "counts": {
            "leads": len(leads),
            "outreach_events": outreach_count,
            "transactions": len(ledger),
        },
        "latest": {
            "lead_id": (sorted(leads.keys())[-1] if leads else None),
            "txn_id": (ledger[-1].get("txn_id") if ledger else None),
        },
        "files": {
            "data/pipeline/leads.json": _sha256_file(leads_path),
            "data/pipeline/outreach_log.csv": _sha256_file(outreach_path),
            "data/financial/ledger.json": _sha256_file(ledger_path),
        },
    }

    with report_path.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")

    return report_path
