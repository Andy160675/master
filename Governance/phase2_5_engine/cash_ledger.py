from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Dict, Optional


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _repo_root() -> Path:
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
    return f"{prefix}{max_n + 1:06d}"


def _quantize_money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class CashLedger:
    """Minimal cash ledger with deterministic allocations.

    Persists:
    - data/financial/ledger.json

    Allocation rules can be overridden by creating:
    - data/financial/allocation_rules.json

    Format:
    {"currency": "GBP", "rules": {"bucket": 0.25, ...}}
    """

    def __init__(self, root: Optional[Path] = None) -> None:
        self.root = root or _repo_root()
        self.ledger_path = self.root / "data" / "financial" / "ledger.json"
        self.rules_path = self.root / "data" / "financial" / "allocation_rules.json"

    def _load_rules(self) -> Dict[str, Any]:
        default = {
            "currency": "GBP",
            "rules": {
                "ops": 0.30,
                "tax": 0.20,
                "savings": 0.20,
                "owner_draw": 0.30,
            },
        }
        data = _read_json(self.rules_path, default)
        # Basic validation / normalization
        rules = data.get("rules", {})
        total = sum(float(v) for v in rules.values()) if rules else 0.0
        if rules and abs(total - 1.0) > 1e-6:
            raise ValueError(f"Allocation rules must sum to 1.0, got {total}")
        return data

    def record_transaction(self, amount: float, category: str, lead_id: str) -> str:
        amount_dec = _quantize_money(Decimal(str(amount)))
        if amount_dec <= 0:
            raise ValueError("amount must be > 0")

        ledger: Dict[str, Any] = _read_json(self.ledger_path, {"transactions": [], "meta": {}})
        txns = list(ledger.get("transactions", []))

        txn_id = _next_sequential_id([t.get("txn_id", "") for t in txns], prefix="txn_")
        rules_blob = self._load_rules()
        currency = rules_blob.get("currency", "GBP")
        rules = rules_blob.get("rules", {})

        allocations: Dict[str, str] = {}
        allocated_total = Decimal("0.00")
        buckets = list(rules.items())
        for i, (bucket, pct) in enumerate(buckets):
            if i == len(buckets) - 1:
                alloc = amount_dec - allocated_total
            else:
                alloc = _quantize_money(amount_dec * Decimal(str(pct)))
                allocated_total += alloc
            allocations[bucket] = str(alloc)

        entry = {
            "txn_id": txn_id,
            "timestamp_utc": _utc_now_iso(),
            "amount": str(amount_dec),
            "currency": currency,
            "category": category,
            "lead_id": lead_id,
            "allocations": allocations,
        }

        txns.append(entry)
        ledger["transactions"] = txns
        ledger.setdefault("meta", {})
        ledger["meta"].setdefault("created_at", _utc_now_iso())
        ledger["meta"]["updated_at"] = _utc_now_iso()

        _write_json_atomic(self.ledger_path, ledger)
        return txn_id
