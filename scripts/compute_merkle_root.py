import json
import sys
from hashlib import sha256
from pathlib import Path

def load_ledger(path: Path):
    try:
        # PowerShell Out-File -Encoding utf8 writes UTF-8 with BOM; utf-8-sig strips it.
        text = path.read_text(encoding="utf-8-sig")
        return json.loads(text)
    except Exception as e:
        print(f"[ERROR] Failed to load ledger file: {e}", file=sys.stderr)
        sys.exit(1)

def canonical_json(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")

def merkle_hash(value: bytes) -> bytes:
    return sha256(value).digest()

def build_merkle_root(entries):
    leaves = [merkle_hash(canonical_json(e)) for e in entries]
    if not leaves:
        return sha256(b"").hexdigest()
    level = leaves
    while len(level) > 1:
        new = []
        for i in range(0, len(level), 2):
            left = level[i]
            right = level[i + 1] if i + 1 < len(level) else left
            new.append(merkle_hash(left + right))
        level = new
    return level[0].hex()

def main():
    if len(sys.argv) != 2:
        print("Usage: python scripts/compute_merkle_root.py <ledger.json>")
        sys.exit(1)
    ledger_path = Path(sys.argv[1])
    if not ledger_path.is_file():
        print(f"[ERROR] Ledger file not found: {ledger_path}", file=sys.stderr)
        sys.exit(2)
    data = load_ledger(ledger_path)
    if not isinstance(data, list):
        print("[ERROR] Ledger must be a list of event objects", file=sys.stderr)
        sys.exit(3)
    root = build_merkle_root(data)
    print(root)

if __name__ == "__main__":
    main()
