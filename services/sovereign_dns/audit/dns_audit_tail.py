from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import uuid4


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_hex(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def read_last_hash(ledger_path: Path) -> str:
    if not ledger_path.exists() or ledger_path.stat().st_size == 0:
        return "0" * 64
    try:
        last = ledger_path.read_text(encoding="utf-8").strip().splitlines()[-1]
        obj = json.loads(last)
        return str(obj.get("hash") or ("0" * 64))
    except Exception:
        return "0" * 64


def ensure_genesis(ledger_path: Path, *, agent: str, track: str) -> None:
    if ledger_path.exists() and ledger_path.stat().st_size > 0:
        return
    append_event(
        ledger_path,
        event_type="GENESIS",
        payload={"message": "Sovereign DNS Audit Ignited"},
        agent=agent,
        track=track,
    )


def append_event(
    ledger_path: Path,
    *,
    event_type: str,
    payload: Dict[str, Any],
    agent: str,
    track: str,
    timestamp: Optional[str] = None,
) -> str:
    prev_hash = read_last_hash(ledger_path)
    event: Dict[str, Any] = {
        "event_id": str(uuid4()),
        "event_type": event_type,
        "timestamp": timestamp or utc_now_iso(),
        "agent": agent,
        "track": track,
        "payload": payload,
        "prev_hash": prev_hash,
    }
    event_hash = sha256_hex(json.dumps(event, sort_keys=True))
    event["hash"] = event_hash

    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    with ledger_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")

    return event_hash


@dataclass
class TailState:
    inode: Optional[int] = None
    offset: int = 0


def stat_inode(path: Path) -> Optional[int]:
    try:
        st = path.stat()
        # Windows compatibility: inode may not exist; on Linux it does.
        return getattr(st, "st_ino", None)
    except FileNotFoundError:
        return None


def tail_loop(log_path: Path, ledger_path: Path, *, agent: str, track: str) -> None:
    state = TailState()

    ensure_genesis(ledger_path, agent=agent, track=track)
    append_event(
        ledger_path,
        event_type="DNS_AUDIT_START",
        payload={"log_path": str(log_path), "pid": os.getpid()},
        agent=agent,
        track=track,
    )

    while True:
        ino = stat_inode(log_path)
        if ino is None:
            time.sleep(1)
            continue

        if state.inode is None or (ino is not None and state.inode != ino):
            state.inode = ino
            state.offset = 0

        try:
            with log_path.open("r", encoding="utf-8", errors="replace") as f:
                f.seek(state.offset)
                while True:
                    line = f.readline()
                    if not line:
                        break
                    state.offset = f.tell()
                    line = line.rstrip("\r\n")
                    if not line:
                        continue

                    # Keep it simple: store raw line; parsing can be improved once format is confirmed.
                    append_event(
                        ledger_path,
                        event_type="DNS_QUERY_LOG",
                        payload={"raw": line},
                        agent=agent,
                        track=track,
                    )
        except Exception as exc:
            append_event(
                ledger_path,
                event_type="DNS_AUDIT_ERROR",
                payload={"error": repr(exc)},
                agent=agent,
                track=track,
            )
            time.sleep(2)

        time.sleep(0.25)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", required=True, help="Path to unbound log file")
    ap.add_argument("--ledger", required=True, help="Path to audit_chain.jsonl")
    ap.add_argument("--agent", default="dns_resolver")
    ap.add_argument("--track", default="insider")
    args = ap.parse_args()

    tail_loop(Path(args.log), Path(args.ledger), agent=args.agent, track=args.track)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
