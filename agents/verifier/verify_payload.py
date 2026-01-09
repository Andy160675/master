import json
import hashlib
import sys


def canonical_hash(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python verify_payload.py <json_file>")
        sys.exit(2)

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        data = json.load(f)

    expected = data.get("payload_sha256")
    actual = canonical_hash(data.get("payload", {}))

    if expected == actual:
        print("PASS")
        sys.exit(0)
    else:
        print("FAIL")
        sys.exit(1)
