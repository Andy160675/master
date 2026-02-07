"""Append-only loggers (CSV + JSONL).

Logs go to validation/assistive_lab/ by default.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


def utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class LogPaths:
    root: Path

    @property
    def csv_path(self) -> Path:
        return self.root / "lab_log.csv"

    @property
    def jsonl_path(self) -> Path:
        return self.root / "lab_runs.jsonl"


def ensure_log_root(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)


def log_run_csv(paths: LogPaths, row: dict) -> None:
    ensure_log_root(paths.root)

    csv_path = paths.csv_path
    is_new = not csv_path.exists()

    with csv_path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        if is_new:
            writer.writeheader()
        writer.writerow(row)


def log_run_jsonl(paths: LogPaths, event: dict) -> None:
    ensure_log_root(paths.root)
    with paths.jsonl_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
