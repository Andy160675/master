# agi/core/drift_detector.py
from __future__ import annotations
import hashlib, sqlite3
from pathlib import Path
from typing import List, Dict

DB_PATH = Path(__file__).resolve().parent / "drift_store.sqlite"
FILES_TO_TRACK = [
    "SOVEREIGN_MODEL_POLICY.md",
    "agi/core/model_stack.yaml",
]

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS file_hashes (
            path TEXT PRIMARY KEY,
            hash TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.commit(); conn.close()

def record_hashes(root: Path) -> None:
    from datetime import datetime
    conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
    now = datetime.utcnow().isoformat() + "Z"
    for rel in FILES_TO_TRACK:
        p = (root / rel).resolve()
        if not p.exists():
            continue
        h = sha256_file(p)
        cur.execute(
            """
            INSERT INTO file_hashes (path, hash, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(path) DO UPDATE SET hash=excluded.hash, updated_at=excluded.updated_at
            """,
            (str(p), h, now),
        )
    conn.commit(); conn.close()

def detect_drift(root: Path) -> List[Dict]:
    conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
    drifts: List[Dict] = []
    for rel in FILES_TO_TRACK:
        p = (root / rel).resolve()
        if not p.exists():
            continue
        current = sha256_file(p)
        cur.execute("SELECT hash FROM file_hashes WHERE path = ?", (str(p),))
        row = cur.fetchone()
        if row and row[0] != current:
            drifts.append({"path": str(p), "old_hash": row[0], "new_hash": current})
    conn.close()
    return drifts

def baseline(root: Path) -> None:
    init_db(); record_hashes(root)
    print(f"[DRIFT] Baseline recorded for {len(FILES_TO_TRACK)} files under {root}")

if __name__ == "__main__":
    # repo root assumption two levels up
    here = Path(__file__).resolve().parent.parent.parent
    baseline(here)
