from __future__ import annotations

import argparse
import csv
import os
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_INCLUDE_EXTS = {
    ".py",
    ".ps1",
    ".sh",
    ".js",
    ".ts",
    ".html",
    ".css",
    ".yml",
    ".yaml",
    ".json",
    ".md",
}

DEFAULT_EXCLUDE_DIRS = {
    ".git",
    ".vscode",
    "__pycache__",
    "node_modules",
    "env",
    "venv",
    "build",
    "dist",
    "obj",
    "bin",
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def should_skip_dir(path: Path) -> bool:
    parts = {p.lower() for p in path.parts}
    return any(d.lower() in parts for d in DEFAULT_EXCLUDE_DIRS)


def _split_roots(raw: str) -> list[str]:
    # Accept common Windows separators while keeping it simple.
    parts: list[str] = []
    for chunk in raw.replace("\n", ";").replace(",", ";").split(";"):
        chunk = chunk.strip().strip('"')
        if chunk:
            parts.append(chunk)
    return parts


def resolve_roots(cli_roots: list[str] | None) -> list[Path]:
    if cli_roots:
        raw_roots = cli_roots
    else:
        env_raw = os.environ.get("AI_INVENTORY_ROOTS", "").strip()
        raw_roots = _split_roots(env_raw) if env_raw else []

    if not raw_roots:
        return [Path.cwd()]

    resolved: list[Path] = []
    for r in raw_roots:
        p = Path(r).expanduser()
        if not p.is_absolute():
            p = (Path.cwd() / p).resolve()
        resolved.append(p)
    return resolved


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate AI_LOCAL_INVENTORY.csv (stdlib-only).")
    parser.add_argument(
        "--root",
        dest="roots",
        action="append",
        help=(
            "Root directory to scan. Repeatable. "
            "If omitted, uses AI_INVENTORY_ROOTS env var (semicolon-separated) or current working directory."
        ),
    )
    args = parser.parse_args()

    cwd = Path.cwd()
    out_path = cwd / "AI_LOCAL_INVENTORY.csv"

    roots = resolve_roots(args.roots)

    rows: list[dict[str, str]] = []
    for root in roots:
        if not root.exists() or not root.is_dir():
            raise SystemExit(f"Root does not exist or is not a directory: {root}")

        root_posix = root.as_posix()
        for file_path in root.rglob("*"):
            if not file_path.is_file():
                continue
            if should_skip_dir(file_path.parent):
                continue

            ext = file_path.suffix.lower()
            if ext not in DEFAULT_INCLUDE_EXTS:
                continue

            try:
                stat = file_path.stat()
                size_bytes = stat.st_size
            except OSError:
                size_bytes = -1

            rel = file_path.as_posix().replace(root_posix.rstrip("/") + "/", "")
            rows.append(
                {
                    "root": root_posix,
                    "path": rel,
                    "ext": ext,
                    "size_bytes": str(size_bytes),
                }
            )

    rows.sort(key=lambda r: (r.get("root", ""), r.get("path", "")))

    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["root", "path", "ext", "size_bytes"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"TIMESTAMP_UTC={utc_now_iso()}")
    print(f"WROTE={out_path}")
    print(f"ROOTS={len(roots)}")
    print(f"FILES={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
