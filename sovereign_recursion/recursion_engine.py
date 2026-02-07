from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import socket
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .ledger import UniversalLedger, utc_iso


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _run(cmd: list[str], timeout_s: int = 10) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s)
        out = (p.stdout or "") + (p.stderr or "")
        return p.returncode, out.strip()
    except Exception as e:
        return 127, str(e)


def tcp_probe(host: str, port: int, timeout_s: float = 2.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout_s):
            return True
    except OSError:
        return False


def which(name: str) -> str | None:
    return shutil.which(name)


@dataclass
class LayerResult:
    status: str
    issues: list[str]
    details: dict[str, Any]

    def to_dict(self) -> dict:
        return {"status": self.status, "issues": self.issues, **self.details}


def check_physical(*, offline: bool = False) -> LayerResult:
    issues: list[str] = []
    details: dict[str, Any] = {}
    status = "STABLE"

    # Network: outbound DNS TCP probe (best-effort)
    if offline:
        details["network_outbound_ok"] = None
        issues.append("offline mode: network probe skipped")
        status = "UNKNOWN"
    else:
        net_ok = tcp_probe("1.1.1.1", 53) or tcp_probe("8.8.8.8", 53)
        details["network_outbound_ok"] = net_ok
        if not net_ok:
            status = "DEGRADED"
            issues.append("outbound network probe failed (tcp 53)")

    # Tailscale presence
    ts = which("tailscale")
    details["tailscale_present"] = bool(ts)
    if ts:
        code, out = _run(["tailscale", "status"], timeout_s=5)
        details["tailscale_status_rc"] = code
        details["tailscale_status_head"] = out.splitlines()[0] if out else ""
        if code != 0:
            status = "WARNING" if status in {"STABLE", "UNKNOWN"} else status
            issues.append("tailscale status non-zero")
    else:
        status = "WARNING" if status in {"STABLE", "UNKNOWN"} else status
        issues.append("tailscale not installed")

    return LayerResult(status=status, issues=issues, details=details)


def check_digital(repo_root: Path) -> LayerResult:
    issues: list[str] = []
    details: dict[str, Any] = {}
    status = "STABLE"

    codex_dir = repo_root / "Codex"
    details["codex_present"] = codex_dir.exists()
    if not codex_dir.exists():
        status = "DEGRADED"
        issues.append("Codex directory missing in repo")

    # Git
    git = which("git")
    details["git_present"] = bool(git)
    if git:
        code, out = _run(["git", "rev-parse", "--is-inside-work-tree"], timeout_s=5)
        details["git_is_repo"] = (code == 0 and out.strip() == "true")
        if code != 0:
            status = "DEGRADED"
            issues.append("git repo not detected")
    else:
        status = "DEGRADED"
        issues.append("git not installed")

    # Docker warning
    details["docker_present"] = bool(which("docker"))
    if details["docker_present"]:
        # Not a failure; caller may have policy.
        status = "WARNING" if status == "STABLE" else status
        issues.append("docker detected (policy warning)")

    return LayerResult(status=status, issues=issues, details=details)


def check_codex_integrity(repo_root: Path) -> LayerResult:
    issues: list[str] = []
    details: dict[str, Any] = {}
    status = "STABLE"

    codex_dir = repo_root / "Codex"
    details["codex_dir"] = str(codex_dir)
    if not codex_dir.exists():
        return LayerResult(status="DEGRADED", issues=["Codex directory missing"], details=details)

    required = [
        "CHARTER.md",
        "README.md",
        "QUICK_START.md",
        "IMPLEMENTATION_SUMMARY.md",
    ]
    missing: list[str] = []
    hashes: dict[str, str] = {}

    for rel in required:
        p = codex_dir / rel
        if not p.exists():
            missing.append(rel)
            continue
        try:
            b = p.read_bytes()
            import hashlib

            hashes[rel] = hashlib.sha256(b).hexdigest()
        except Exception as e:
            status = "WARNING" if status == "STABLE" else status
            issues.append(f"hash read failed for {rel}: {e}")

    details["required"] = required
    details["missing"] = missing
    details["sha256"] = hashes

    if missing:
        status = "DEGRADED"
        issues.append(f"missing required Codex files: {missing}")

    return LayerResult(status=status, issues=issues, details=details)


def check_cognitive(rating: int | None) -> LayerResult:
    details: dict[str, Any] = {}
    issues: list[str] = []

    if rating is None:
        return LayerResult(status="UNKNOWN", issues=["no rating provided"], details={"rating": None})

    details["rating"] = rating
    if rating <= 2:
        return LayerResult(status="OVERLOADED", issues=["self-rating low"], details=details)
    if rating == 3:
        return LayerResult(status="STRAINED", issues=[], details=details)
    if rating >= 4:
        return LayerResult(status="STABLE", issues=[], details=details)

    return LayerResult(status="UNKNOWN", issues=["rating out of range"], details=details)


def check_collaborative(nas_host: str | None, *, offline: bool = False) -> LayerResult:
    issues: list[str] = []
    details: dict[str, Any] = {}
    status = "STABLE"

    details["node0"] = {"name": platform.node(), "status": "PRESENT"}

    if offline:
        details["nas_host"] = nas_host
        details["nas_reachable"] = None
        status = "UNKNOWN"
        issues.append("offline mode: NAS probe skipped")
    elif nas_host:
        ok = tcp_probe(nas_host, 445) or tcp_probe(nas_host, 22)
        details["nas_host"] = nas_host
        details["nas_reachable"] = ok
        if not ok:
            status = "DEGRADED"
            issues.append("NAS not reachable (tcp 445/22 probe)")
    else:
        status = "UNKNOWN"
        issues.append("no NAS host provided")

    # Cloud witness (best-effort): outbound HTTPS probe
    if offline:
        details["cloud_witness_reachable"] = None
        issues.append("offline mode: cloud witness probe skipped")
        status = "UNKNOWN" if status == "STABLE" else status
    else:
        cloud_ok = tcp_probe("api.ipify.org", 443)
        details["cloud_witness_reachable"] = cloud_ok
        if not cloud_ok:
            status = "DEGRADED" if status == "STABLE" else status
            issues.append("cloud witness probe failed (tcp 443)")

    return LayerResult(status=status, issues=issues, details=details)


def check_meta(ledger: UniversalLedger) -> LayerResult:
    report = ledger.verify()
    ok = bool(report.get("ok"))
    status = "INTACT" if ok else "CORRUPTED"
    return LayerResult(status=status, issues=[] if ok else report.get("reasons", []), details={"ledger": report})


def compute_sovereign_score(latest_by_layer: dict[str, LayerResult]) -> dict[str, Any]:
    total_capability = 100
    dangerous_freedom = 0
    for layer, res in latest_by_layer.items():
        if res.status == "DEGRADED":
            dangerous_freedom += 10
        elif res.status == "WARNING":
            dangerous_freedom += 5
        elif res.status in {"OVERLOADED"}:
            dangerous_freedom += 15
    stability = total_capability - dangerous_freedom
    return {
        "total_capability": total_capability,
        "dangerous_freedom": dangerous_freedom,
        "stability": stability,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Sovereign Recursion Engine (repo-local)")
    p.add_argument("--repo-root", default=str(Path.cwd()), help="Repo root (default: cwd)")
    p.add_argument(
        "--ledger",
        default=os.getenv("SOVEREIGN_LEDGER", "validation/sovereign_recursion/ledger.jsonl"),
        help="Ledger path (default: validation/sovereign_recursion/ledger.jsonl)",
    )
    p.add_argument("--nas-host", default=os.getenv("SOVEREIGN_NAS_HOST", ""), help="NAS host/ip for reachability probe")
    p.add_argument("--rating", type=int, default=None, help="Optional cognitive self-rating 1-5")
    p.add_argument("--offline", action="store_true", help="Skip outbound probes (for deterministic runs/tests)")
    p.add_argument(
        "--gated",
        action="store_true",
        help="Exit non-zero if any layer is DEGRADED/OVERLOADED/CORRUPTED",
    )
    p.add_argument(
        "--out-dir",
        default="",
        help="Write a run report JSON here (default: validation/sovereign_recursion/run_<stamp>)",
    )
    args = p.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    nas_host = (args.nas_host or "").strip() or None

    out_dir = Path(args.out_dir) if args.out_dir else (Path("validation") / "sovereign_recursion" / f"run_{utc_stamp()}")
    out_dir.mkdir(parents=True, exist_ok=True)

    ledger = UniversalLedger(ledger_path=args.ledger)

    run_meta = {
        "ts_utc": utc_iso(),
        "host": platform.node(),
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "repo_root": str(repo_root),
        "nas_host": nas_host,
    }

    # Record intent
    ledger.append("meta", "engine_start", {**run_meta, "out_dir": str(out_dir)})

    results: dict[str, LayerResult] = {}

    results["physical"] = check_physical(offline=bool(args.offline))
    ledger.append("physical", "check", results["physical"].to_dict())

    results["digital"] = check_digital(repo_root)
    ledger.append("digital", "check", results["digital"].to_dict())

    results["codex"] = check_codex_integrity(repo_root)
    ledger.append("codex", "check", results["codex"].to_dict())

    results["cognitive"] = check_cognitive(args.rating)
    ledger.append("cognitive", "checkpoint", results["cognitive"].to_dict())

    results["collaborative"] = check_collaborative(nas_host, offline=bool(args.offline))
    ledger.append("collaborative", "node_check", results["collaborative"].to_dict())

    results["meta"] = check_meta(ledger)
    ledger.append("meta", "self_check", results["meta"].to_dict())

    score = compute_sovereign_score(results)
    ledger.append("meta", "sovereign_score", score)

    run_report = {
        **run_meta,
        "out_dir": str(out_dir),
        "layers": {k: v.to_dict() for k, v in results.items()},
        "score": score,
        "ledger_path": str(Path(args.ledger)),
    }

    report_path = out_dir / "run_report.json"
    report_path.write_text(json.dumps(run_report, indent=2), encoding="utf-8")

    # Final record
    ledger.append("meta", "engine_end", {"ok": True, "report": str(report_path)})

    print(json.dumps(run_report, indent=2))

    if args.gated:
        gate_fail_statuses = {"DEGRADED", "OVERLOADED", "CORRUPTED"}
        failing = [k for k, v in results.items() if v.status in gate_fail_statuses]
        if failing:
            for layer in failing:
                print(f"GATE_FAIL layer={layer} status={results[layer].status}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
