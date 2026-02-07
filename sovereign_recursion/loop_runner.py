from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .ledger import UniversalLedger, utc_iso


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


@dataclass(frozen=True)
class ClassificationPolicy:
    hard_layers_on_degraded: set[str]
    hard_statuses: set[str]
    soft_statuses: set[str]
    treat_missing_report_as: str
    treat_missing_layers_as: str

    @staticmethod
    def defaults() -> "ClassificationPolicy":
        return ClassificationPolicy(
            hard_layers_on_degraded={"meta", "codex", "digital"},
            hard_statuses={"CORRUPTED", "OVERLOADED"},
            soft_statuses={"DEGRADED"},
            treat_missing_report_as="HARD_FAIL",
            treat_missing_layers_as="HARD_FAIL",
        )

    @staticmethod
    def from_json(obj: dict[str, Any]) -> "ClassificationPolicy":
        d = ClassificationPolicy.defaults()
        hard_layers = obj.get("hard_layers_on_degraded", list(d.hard_layers_on_degraded))
        hard_statuses = obj.get("hard_statuses", list(d.hard_statuses))
        soft_statuses = obj.get("soft_statuses", list(d.soft_statuses))

        def _as_set(x: Any) -> set[str]:
            if not isinstance(x, list):
                return set()
            out: set[str] = set()
            for item in x:
                if isinstance(item, str) and item.strip():
                    out.add(item.strip().upper() if item.isupper() else item.strip())
            return out

        # Keep layer names in lower-case for matching
        hard_layers_set = set(str(x).strip().lower() for x in hard_layers if isinstance(x, str) and x.strip())
        hard_statuses_set = set(str(x).strip().upper() for x in hard_statuses if isinstance(x, str) and x.strip())
        soft_statuses_set = set(str(x).strip().upper() for x in soft_statuses if isinstance(x, str) and x.strip())

        treat_missing_report_as = str(obj.get("treat_missing_report_as", d.treat_missing_report_as)).strip().upper()
        treat_missing_layers_as = str(obj.get("treat_missing_layers_as", d.treat_missing_layers_as)).strip().upper()

        if treat_missing_report_as not in {"PASS", "SOFT_FAIL", "HARD_FAIL"}:
            treat_missing_report_as = d.treat_missing_report_as
        if treat_missing_layers_as not in {"PASS", "SOFT_FAIL", "HARD_FAIL"}:
            treat_missing_layers_as = d.treat_missing_layers_as

        return ClassificationPolicy(
            hard_layers_on_degraded=hard_layers_set or d.hard_layers_on_degraded,
            hard_statuses=hard_statuses_set or d.hard_statuses,
            soft_statuses=soft_statuses_set or d.soft_statuses,
            treat_missing_report_as=treat_missing_report_as,
            treat_missing_layers_as=treat_missing_layers_as,
        )

    @staticmethod
    def load(path: str | Path | None) -> "ClassificationPolicy":
        if not path:
            return ClassificationPolicy.defaults()
        p = Path(path)
        if not p.exists():
            return ClassificationPolicy.defaults()
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(obj, dict):
                return ClassificationPolicy.from_json(obj)
        except Exception:
            return ClassificationPolicy.defaults()
        return ClassificationPolicy.defaults()


@dataclass
class IterationOutcome:
    iteration: int
    attempt: int
    rc: int
    out_dir: Path
    stability: int | None
    failing_layers: list[str]
    classification: str
    action: str
    ts_utc: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "ts_utc": self.ts_utc,
            "iteration": self.iteration,
            "attempt": self.attempt,
            "rc": self.rc,
            "out_dir": str(self.out_dir),
            "stability": self.stability,
            "failing_layers": self.failing_layers,
            "classification": self.classification,
            "action": self.action,
        }


def _parse_run_report(stdout_text: str) -> dict[str, Any] | None:
    stdout_text = stdout_text.strip()
    if not stdout_text:
        return None
    try:
        return json.loads(stdout_text)
    except json.JSONDecodeError:
        # Sometimes other output gets mixed in; try last JSON object.
        last_brace = stdout_text.rfind("{")
        if last_brace >= 0:
            try:
                return json.loads(stdout_text[last_brace:])
            except json.JSONDecodeError:
                return None
        return None


def _failing_layers_from_report(report: dict[str, Any]) -> list[str]:
    layers = report.get("layers")
    if not isinstance(layers, dict):
        return []
    failing: list[str] = []
    for layer, data in layers.items():
        if not isinstance(data, dict):
            continue
        status = str(data.get("status", "")).upper()
        if status in {"DEGRADED", "OVERLOADED", "CORRUPTED"}:
            failing.append(str(layer))
    return failing


def _classify(
    report: dict[str, Any] | None,
    rc: int,
    policy: ClassificationPolicy,
) -> tuple[str, str, list[str]]:
    """Classify the iteration result and recommend a bounded next action.

    - PASS      → log only
    - SOFT_FAIL → retry (bounded)
    - HARD_FAIL → emit alert artifact (no retry)
    """

    if rc == 0:
        return "PASS", "log_only", []

    if report is None:
        cls = policy.treat_missing_report_as
        action = "emit_alert" if cls == "HARD_FAIL" else ("retry" if cls == "SOFT_FAIL" else "log_only")
        return cls, action, ["missing_or_unparseable_run_report"]

    failing_layers = _failing_layers_from_report(report)
    layers = report.get("layers") if isinstance(report, dict) else None
    if not isinstance(layers, dict):
        cls = policy.treat_missing_layers_as
        action = "emit_alert" if cls == "HARD_FAIL" else ("retry" if cls == "SOFT_FAIL" else "log_only")
        return cls, action, ["missing_layers_in_report"]

    hard_reasons: list[str] = []
    soft_reasons: list[str] = []

    for layer_name, layer_data in layers.items():
        if not isinstance(layer_data, dict):
            continue
        status = str(layer_data.get("status", "UNKNOWN")).upper()
        layer_key = str(layer_name).lower()

        if status in policy.hard_statuses:
            hard_reasons.append(f"{layer_name}:{status}")
        elif status == "DEGRADED":
            if layer_key in policy.hard_layers_on_degraded:
                hard_reasons.append(f"{layer_name}:DEGRADED")
            else:
                soft_reasons.append(f"{layer_name}:DEGRADED")
        elif status in policy.soft_statuses:
            soft_reasons.append(f"{layer_name}:{status}")

    if hard_reasons:
        return "HARD_FAIL", "emit_alert", hard_reasons
    if failing_layers or soft_reasons:
        return "SOFT_FAIL", "retry", soft_reasons or failing_layers

    # Non-zero rc but no explicit failing status → treat as soft by default.
    return "SOFT_FAIL", "retry", ["nonzero_rc_without_failing_layers"]


def _write_alert(out_dir: Path, payload: dict[str, Any]) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    alert_path = out_dir / "alert.json"
    alert_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return alert_path


def run_engine_once(
    *,
    python_exe: str,
    ledger_path: str,
    repo_root: str,
    rating: int | None,
    nas_host: str | None,
    offline: bool,
    gated: bool,
    out_dir: Path,
) -> tuple[int, dict[str, Any] | None, str]:
    args: list[str] = [
        python_exe,
        "-m",
        "sovereign_recursion",
        "--repo-root",
        repo_root,
        "--ledger",
        ledger_path,
        "--out-dir",
        str(out_dir),
    ]
    if rating is not None:
        args += ["--rating", str(rating)]
    if nas_host:
        args += ["--nas-host", nas_host]
    if offline:
        args.append("--offline")
    if gated:
        args.append("--gated")

    proc = subprocess.run(args, capture_output=True, text=True)
    report = _parse_run_report(proc.stdout)
    stderr = (proc.stderr or "").strip()
    return proc.returncode, report, stderr


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Unified Sovereign Loop Runner (sense → gate → act → record)")
    p.add_argument("--iterations", type=int, default=1, help="Number of loop iterations")
    p.add_argument("--interval-seconds", type=int, default=0, help="Sleep between iterations")
    p.add_argument("--max-retries", type=int, default=0, help="Retries per iteration if gate fails")
    p.add_argument(
        "--emit-alerts",
        action="store_true",
        help="Write alert.json artifacts for HARD_FAIL (or exhausted SOFT_FAIL)",
    )
    p.add_argument(
        "--policy",
        default="",
        help="Path to JSON classification policy (default: built-in; repo provides sovereign_recursion/policy.default.json)",
    )

    p.add_argument("--repo-root", default=str(Path.cwd()), help="Repo root")
    p.add_argument("--ledger", default="validation/sovereign_recursion/ledger.jsonl", help="Ledger path")
    p.add_argument("--nas-host", default="", help="NAS host/ip (optional)")
    p.add_argument("--rating", type=int, default=None, help="Cognitive self-rating 1-5")

    p.add_argument("--offline", action="store_true", help="Skip outbound probes")
    p.add_argument("--gated", action="store_true", help="Fail iteration if any layer is DEGRADED/OVERLOADED/CORRUPTED")

    p.add_argument(
        "--out-root",
        default="",
        help="Root folder for loop artifacts (default: validation/sovereign_recursion/loop_<stamp>)",
    )
    p.add_argument("--dashboard", action="store_true", help="Generate dashboard after loop")

    args = p.parse_args(argv)

    if args.iterations <= 0:
        raise SystemExit("--iterations must be >= 1")
    if args.interval_seconds < 0:
        raise SystemExit("--interval-seconds must be >= 0")
    if args.max_retries < 0:
        raise SystemExit("--max-retries must be >= 0")

    repo_root = str(Path(args.repo_root).resolve())
    ledger_path = str(Path(args.ledger))
    nas_host = (args.nas_host or "").strip() or None

    out_root = Path(args.out_root) if args.out_root else (Path("validation") / "sovereign_recursion" / f"loop_{utc_stamp()}")
    out_root.mkdir(parents=True, exist_ok=True)

    summary_path = out_root / "loop_summary.jsonl"

    # Loop-level evidence in the same ledger
    ledger = UniversalLedger(ledger_path=ledger_path)

    policy_path = (args.policy or "").strip() or None
    policy = ClassificationPolicy.load(policy_path)

    ledger.append(
        "meta",
        "loop_start",
        {
            "ts_utc": utc_iso(),
            "out_root": str(out_root),
            "iterations": args.iterations,
            "interval_seconds": args.interval_seconds,
            "max_retries": args.max_retries,
            "offline": bool(args.offline),
            "gated": bool(args.gated),
            "emit_alerts": bool(args.emit_alerts),
            "policy_path": str(policy_path) if policy_path else "",
            "policy": {
                "hard_layers_on_degraded": sorted(policy.hard_layers_on_degraded),
                "hard_statuses": sorted(policy.hard_statuses),
                "soft_statuses": sorted(policy.soft_statuses),
                "treat_missing_report_as": policy.treat_missing_report_as,
                "treat_missing_layers_as": policy.treat_missing_layers_as,
            },
            "repo_root": repo_root,
            "nas_host": nas_host,
        },
    )

    python_exe = sys.executable
    outcomes: list[IterationOutcome] = []

    for i in range(1, args.iterations + 1):
        attempt = 0
        last_rc = 0
        last_report: dict[str, Any] | None = None
        last_stderr = ""

        while True:
            attempt += 1
            iter_dir = out_root / f"iter_{i:04d}" / f"attempt_{attempt:02d}"
            iter_dir.mkdir(parents=True, exist_ok=True)

            rc, report, stderr = run_engine_once(
                python_exe=python_exe,
                ledger_path=ledger_path,
                repo_root=repo_root,
                rating=args.rating,
                nas_host=nas_host,
                offline=bool(args.offline),
                gated=bool(args.gated),
                out_dir=iter_dir,
            )

            last_rc, last_report, last_stderr = rc, report, stderr

            failing_layers: list[str] = []
            stability: int | None = None
            if report is not None:
                failing_layers = _failing_layers_from_report(report)
                score = report.get("score")
                if isinstance(score, dict):
                    try:
                        stability = int(score.get("stability"))
                    except Exception:
                        stability = None

            classification, action, reasons = _classify(report, rc, policy)

            outcome = IterationOutcome(
                iteration=i,
                attempt=attempt,
                rc=rc,
                out_dir=iter_dir,
                stability=stability,
                failing_layers=failing_layers,
                classification=classification,
                action=action,
                ts_utc=utc_iso(),
            )
            outcomes.append(outcome)

            # Append loop summary line
            with summary_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(outcome.to_dict(), sort_keys=True) + "\n")

            # Record loop iteration into ledger
            ledger.append(
                "meta",
                "loop_iteration",
                {
                    "iteration": i,
                    "attempt": attempt,
                    "rc": rc,
                    "out_dir": str(iter_dir),
                    "stability": stability,
                    "failing_layers": failing_layers,
                    "classification": classification,
                    "action": action,
                    "reasons": reasons,
                    "stderr_tail": last_stderr.splitlines()[-5:] if last_stderr else [],
                },
            )

            if rc == 0:
                break

            # Classification-driven bounded action
            if classification == "HARD_FAIL":
                if args.emit_alerts:
                    alert_path = _write_alert(
                        iter_dir,
                        {
                            "ts_utc": utc_iso(),
                            "kind": "HARD_FAIL",
                            "iteration": i,
                            "attempt": attempt,
                            "rc": rc,
                            "reasons": reasons,
                            "failing_layers": failing_layers,
                            "report_present": report is not None,
                        },
                    )
                    ledger.append(
                        "meta",
                        "loop_alert",
                        {
                            "kind": "HARD_FAIL",
                            "iteration": i,
                            "attempt": attempt,
                            "alert_path": str(alert_path),
                            "reasons": reasons,
                            "failing_layers": failing_layers,
                        },
                    )
                break

            # SOFT_FAIL: retry bounded
            if attempt > args.max_retries:
                if args.emit_alerts:
                    alert_path = _write_alert(
                        iter_dir,
                        {
                            "ts_utc": utc_iso(),
                            "kind": "SOFT_FAIL_EXHAUSTED",
                            "iteration": i,
                            "attempt": attempt,
                            "rc": rc,
                            "reasons": reasons,
                            "failing_layers": failing_layers,
                            "report_present": report is not None,
                        },
                    )
                    ledger.append(
                        "meta",
                        "loop_alert",
                        {
                            "kind": "SOFT_FAIL_EXHAUSTED",
                            "iteration": i,
                            "attempt": attempt,
                            "alert_path": str(alert_path),
                            "reasons": reasons,
                            "failing_layers": failing_layers,
                        },
                    )
                break

            time.sleep(min(5, max(1, args.interval_seconds or 1)))

        # Sleep between iterations
        if i < args.iterations and args.interval_seconds > 0:
            time.sleep(args.interval_seconds)

    ledger.append("meta", "loop_end", {"ts_utc": utc_iso(), "out_root": str(out_root)})

    # Optionally generate dashboard at end
    if args.dashboard:
        try:
            subprocess.run([python_exe, "-m", "sovereign_recursion.dashboard", "--ledger", ledger_path], check=False)
        except Exception:
            pass

    # Exit code: if gated, fail if any iteration ended non-zero.
    if args.gated and any(o.rc != 0 and o.attempt >= 1 for o in outcomes):
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
