from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_text_lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [ln.strip() for ln in path.read_text(encoding="utf-8", errors="replace").splitlines() if ln.strip()]


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    root = Path.cwd()

    local_csv = root / "AI_LOCAL_INVENTORY.csv"
    git_txt = root / "AI_GIT_INVENTORY.txt"
    sg_txt = root / "AI_SITEGROUND_INVENTORY.txt"

    out_md = root / "AI_SYSTEM_TOPOGRAPHY.md"

    local_rows = read_csv_rows(local_csv)
    git_files = read_text_lines(git_txt)
    sg_files = read_text_lines(sg_txt)

    def count_nonempty(x) -> int:
        return len([v for v in x if v])

    lines: list[str] = []
    lines.append("# AI System Topography (Exploratory / Offline)")
    lines.append("")
    lines.append(f"TIMESTAMP_UTC={utc_now_iso()}")
    lines.append("")
    lines.append("## Inputs")
    lines.append(f"- AI_LOCAL_INVENTORY.csv: {'present' if local_csv.exists() else 'missing'}")
    lines.append(f"- AI_GIT_INVENTORY.txt: {'present' if git_txt.exists() else 'missing'}")
    lines.append(f"- AI_SITEGROUND_INVENTORY.txt: {'present' if sg_txt.exists() else 'missing'}")
    lines.append("")

    lines.append("## Summary")
    lines.append(f"- Local inventory rows: {len(local_rows)}")
    lines.append(f"- Git inventory paths: {len(git_files)}")
    lines.append(f"- SiteGround inventory paths: {len(sg_files)}")
    lines.append("")

    lines.append("## Local Inventory (sample)")
    show_root = any(("root" in r) and (r.get("root") or "").strip() for r in local_rows[:25])
    if show_root:
        lines.append("| root | path | ext | size_bytes |")
        lines.append("|---|---|---:|---:|")
    else:
        lines.append("| path | ext | size_bytes |")
        lines.append("|---|---:|---:|")
    for row in local_rows[:25]:
        if show_root:
            lines.append(
                f"| {row.get('root','')} | {row.get('path','')} | {row.get('ext','')} | {row.get('size_bytes','')} |"
            )
        else:
            lines.append(f"| {row.get('path','')} | {row.get('ext','')} | {row.get('size_bytes','')} |")
    if len(local_rows) > 25:
        lines.append(f"\n(Showing first 25 of {len(local_rows)})\n")
    lines.append("")

    lines.append("## Git Inventory (sample)")
    for p in git_files[:50]:
        lines.append(f"- {p}")
    if len(git_files) > 50:
        lines.append(f"\n(Showing first 50 of {len(git_files)})\n")
    lines.append("")

    lines.append("## SiteGround Inventory (sample)")
    for p in sg_files[:50]:
        lines.append(f"- {p}")
    if len(sg_files) > 50:
        lines.append(f"\n(Showing first 50 of {len(sg_files)})\n")

    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"TIMESTAMP_UTC={utc_now_iso()}")
    print(f"WROTE={out_md}")
    print(f"LOCAL_ROWS={len(local_rows)} GIT_PATHS={count_nonempty(git_files)} SITEGROUND_PATHS={count_nonempty(sg_files)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
