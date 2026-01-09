from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class AgentSpec:
    name: str
    description: str
    type: str  # python | powershell
    entry: str
    args: list[str]


def load_registry(path: Path) -> list[AgentSpec]:
    # NOTE: file is JSON-compatible YAML (valid JSON) for stdlib parsing.
    raw = json.loads(path.read_text(encoding="utf-8"))
    specs: list[AgentSpec] = []
    for item in raw:
        specs.append(
            AgentSpec(
                name=str(item["name"]),
                description=str(item.get("description", "")),
                type=str(item["type"]),
                entry=str(item["entry"]),
                args=[str(a) for a in item.get("args", [])],
            )
        )
    return specs


def load_states(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"schema_version": "0.1", "updated_utc": None, "agents": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def save_states(path: Path, states: dict[str, Any]) -> None:
    states["updated_utc"] = utc_now_iso()
    path.write_text(json.dumps(states, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_agent(spec: AgentSpec, repo_root: Path, dry_run: bool) -> int:
    entry_path = (repo_root / spec.entry).resolve()
    if not entry_path.exists():
        raise FileNotFoundError(f"Missing agent entry: {entry_path}")

    if spec.type == "python":
        cmd = [sys.executable, str(entry_path), *spec.args]
    elif spec.type == "powershell":
        # Use Windows PowerShell if available; pwsh also works, but keep it simple.
        cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(entry_path), *spec.args]
    else:
        raise ValueError(f"Unsupported agent type: {spec.type}")

    print(f"AGENT={spec.name}")
    print(f"DESC={spec.description}")
    print(f"CMD={' '.join(cmd)}")

    if dry_run:
        print("DRY_RUN=1")
        return 0

    proc = subprocess.run(cmd, cwd=str(repo_root))
    return int(proc.returncode)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Local agent runner (offline-safe)")
    parser.add_argument(
        "--registry",
        default="agents/orchestration/agent_registry.yaml",
        help="Path to agent registry (JSON-compatible YAML)",
    )
    parser.add_argument(
        "--state",
        default="agents/orchestration/agent_states.json",
        help="Path to state file",
    )
    parser.add_argument("--list", action="store_true", help="List agents")
    parser.add_argument("--agent", help="Run a single agent by name")
    parser.add_argument("--all", action="store_true", help="Run all agents in registry order")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without executing")

    args = parser.parse_args(argv)

    repo_root = Path.cwd()
    registry_path = (repo_root / args.registry).resolve()
    state_path = (repo_root / args.state).resolve()

    specs = load_registry(registry_path)
    states = load_states(state_path)

    if args.list:
        for spec in specs:
            print(f"- {spec.name}: {spec.description}")
        return 0

    # Default behavior: run the whole registry if no explicit selector flags are provided.
    if not args.list and not args.agent and not args.all:
        args.all = True

    to_run: list[AgentSpec] = []
    if args.agent:
        match = [s for s in specs if s.name == args.agent]
        if not match:
            print(f"ERROR: unknown agent '{args.agent}'", file=sys.stderr)
            return 2
        to_run = match
    elif args.all:
        to_run = specs
    else:
        print("ERROR: specify --list, --agent <name>, or --all", file=sys.stderr)
        return 2

    overall_rc = 0
    for spec in to_run:
        rc = run_agent(spec, repo_root=repo_root, dry_run=bool(args.dry_run))
        states.setdefault("agents", {}).setdefault(spec.name, {})
        states["agents"][spec.name] = {
            "last_run_utc": utc_now_iso(),
            "dry_run": bool(args.dry_run),
            "return_code": rc,
        }
        save_states(state_path, states)
        if rc != 0:
            overall_rc = rc
            break

    return overall_rc


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
