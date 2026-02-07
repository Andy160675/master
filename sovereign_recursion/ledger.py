from __future__ import annotations

import hashlib
import json
import os
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


@contextmanager
def _exclusive_file_lock(f):
    """Best-effort cross-platform exclusive file lock.

    Prevents concurrent processes from appending with the same previous_hash.
    """

    try:
        if os.name == "nt":
            import msvcrt

            # Lock 1 byte at the start of the file.
            f.seek(0)
            msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl

            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
    except Exception:
        # If locking isn't available, continue without it.
        pass

    try:
        yield
    finally:
        try:
            if os.name == "nt":
                import msvcrt

                f.seek(0)
                msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except Exception:
            pass


def utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass
class LedgerEntry:
    ts_utc: str
    ts_unix: float
    layer: str
    event_type: str
    data: dict
    engine_version: str
    previous_hash: str
    layer_previous_hash: str
    proof: str | None = None
    hash: str | None = None

    def to_dict(self) -> dict:
        d = {
            "ts_utc": self.ts_utc,
            "ts_unix": self.ts_unix,
            "layer": self.layer,
            "type": self.event_type,
            "data": self.data,
            "engine_version": self.engine_version,
            "previous_hash": self.previous_hash,
            "layer_previous_hash": self.layer_previous_hash,
        }
        if self.proof is not None:
            d["proof"] = self.proof
        if self.hash is not None:
            d["hash"] = self.hash
        return d

    def compute_hash(self) -> str:
        d = self.to_dict()
        d.pop("hash", None)
        return _sha256_text(_canonical_json(d))


class UniversalLedger:
    """Append-only JSONL ledger with a global chain + per-layer chaining.

    - Global chain: previous_hash links every entry in file order.
    - Layer chain: layer_previous_hash links only entries of the same layer.

    This is still “one ledger for everything”, but supports per-layer semantics.
    """

    def __init__(
        self,
        ledger_path: str | Path = "validation/sovereign_recursion/ledger.jsonl",
        engine_version: str = "recursion-v1",
    ) -> None:
        self.ledger_path = Path(ledger_path)
        self.engine_version = engine_version

        self._last_global_hash = ""
        self._last_layer_hash: dict[str, str] = {}

        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        self._index_existing()

    def _index_existing(self) -> None:
        if not self.ledger_path.exists():
            return

        for entry in self._iter_entries():
            h = entry.get("hash")
            if isinstance(h, str):
                self._last_global_hash = h
                layer = entry.get("layer")
                if isinstance(layer, str):
                    self._last_layer_hash[layer] = h

    def _iter_entries(self) -> Iterable[dict]:
        if not self.ledger_path.exists():
            return
        with self.ledger_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    # Corruption is handled by verify(); keep iterator best-effort.
                    continue

    def append(self, layer: str, event_type: str, data: dict, proof: str | None = None) -> str:
        if not layer or not isinstance(layer, str):
            raise ValueError("layer must be a non-empty string")
        if not event_type or not isinstance(event_type, str):
            raise ValueError("event_type must be a non-empty string")
        if not isinstance(data, dict):
            raise ValueError("data must be a dict")

        # Inter-process safety: lock and re-index tail under the lock.
        # Without this, two concurrent processes can both append with the same previous_hash,
        # forking the chain and making verify() fail.
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        with self.ledger_path.open("a+", encoding="utf-8") as f:
            with _exclusive_file_lock(f):
                f.seek(0)
                prev_global = ""
                prev_layer: dict[str, str] = {}
                for line in f:
                    raw = line.strip()
                    if not raw:
                        continue
                    try:
                        obj = json.loads(raw)
                    except json.JSONDecodeError:
                        continue
                    h = obj.get("hash")
                    lyr = obj.get("layer")
                    if isinstance(h, str) and isinstance(lyr, str):
                        prev_global = h
                        prev_layer[lyr] = h

                ts_unix = time.time()
                entry = LedgerEntry(
                    ts_utc=utc_iso(),
                    ts_unix=ts_unix,
                    layer=layer,
                    event_type=event_type,
                    data=data,
                    engine_version=self.engine_version,
                    previous_hash=prev_global,
                    layer_previous_hash=prev_layer.get(layer, ""),
                    proof=proof,
                )
                entry.hash = entry.compute_hash()

                f.seek(0, os.SEEK_END)
                f.write(_canonical_json(entry.to_dict()) + "\n")
                f.flush()

                self._last_global_hash = entry.hash
                self._last_layer_hash[layer] = entry.hash
                return entry.hash

    def verify(self) -> dict:
        """Verify global and per-layer chaining and hash integrity.

        Returns a structured report.
        """

        ok = True
        reasons: list[str] = []
        total = 0

        prev_global = ""
        prev_layer: dict[str, str] = {}

        with self.ledger_path.open("r", encoding="utf-8") as f:
            for idx, line in enumerate(f, start=1):
                raw = line.strip()
                if not raw:
                    continue
                total += 1
                try:
                    obj = json.loads(raw)
                except json.JSONDecodeError:
                    ok = False
                    reasons.append(f"line {idx}: invalid json")
                    continue

                # Required fields
                h = obj.get("hash")
                layer = obj.get("layer")
                if not isinstance(h, str) or not isinstance(layer, str):
                    ok = False
                    reasons.append(f"line {idx}: missing hash/layer")
                    continue

                # Verify computed hash
                obj_copy = dict(obj)
                obj_copy.pop("hash", None)
                computed = _sha256_text(_canonical_json(obj_copy))
                if computed != h:
                    ok = False
                    reasons.append(f"line {idx}: hash mismatch")

                # Verify global chain
                if obj.get("previous_hash", "") != prev_global:
                    ok = False
                    reasons.append(f"line {idx}: global previous_hash mismatch")
                prev_global = h

                # Verify layer chain
                expected_layer_prev = prev_layer.get(layer, "")
                if obj.get("layer_previous_hash", "") != expected_layer_prev:
                    ok = False
                    reasons.append(f"line {idx}: layer_previous_hash mismatch")
                prev_layer[layer] = h

        return {
            "ok": ok,
            "ledger_path": str(self.ledger_path),
            "total_entries": total,
            "reasons": reasons,
            "ts_utc": utc_iso(),
        }

    def tail(self, n: int = 10) -> list[dict]:
        if n <= 0:
            return []
        entries = list(self._iter_entries())
        return entries[-n:]


def main(argv: list[str] | None = None) -> int:
    import argparse

    p = argparse.ArgumentParser(description="Universal Evidence Ledger (append-only JSONL)")
    p.add_argument("--ledger", default=os.getenv("SOVEREIGN_LEDGER", "validation/sovereign_recursion/ledger.jsonl"))
    sub = p.add_subparsers(dest="cmd", required=True)

    ap = sub.add_parser("append")
    ap.add_argument("layer")
    ap.add_argument("type")
    ap.add_argument("data_json")

    sub.add_parser("verify")

    tp = sub.add_parser("tail")
    tp.add_argument("-n", type=int, default=10)

    args = p.parse_args(argv)
    ledger = UniversalLedger(ledger_path=args.ledger)

    if args.cmd == "append":
        data = json.loads(args.data_json)
        h = ledger.append(args.layer, args.type, data)
        print(h)
        return 0

    if args.cmd == "verify":
        report = ledger.verify()
        print(json.dumps(report, indent=2))
        return 0 if report.get("ok") else 1

    if args.cmd == "tail":
        print(json.dumps(ledger.tail(args.n), indent=2))
        return 0

    raise SystemExit("unknown command")


if __name__ == "__main__":
    raise SystemExit(main())
