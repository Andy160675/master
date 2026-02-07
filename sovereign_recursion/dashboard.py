from __future__ import annotations

import argparse
import html
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class LatestLayer:
    ts_unix: float
    ts_utc: str
    layer: str
    event_type: str
    data: dict[str, Any]


class SovereignDashboard:
    def __init__(self, ledger_path: str | Path = "validation/sovereign_recursion/ledger.jsonl") -> None:
        self.ledger_path = Path(ledger_path)
        self.latest_by_layer: dict[str, LatestLayer] = {}
        self.latest_score: dict[str, Any] | None = None
        self._load_latest()

    def _load_latest(self) -> None:
        if not self.ledger_path.exists():
            return

        with self.ledger_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                layer = entry.get("layer")
                if not isinstance(layer, str) or not layer:
                    continue

                ts_unix = entry.get("ts_unix")
                ts_utc = entry.get("ts_utc")
                event_type = entry.get("type")
                data = entry.get("data")

                if not isinstance(ts_unix, (int, float)):
                    continue
                if not isinstance(ts_utc, str):
                    ts_utc = ""
                if not isinstance(event_type, str):
                    event_type = ""
                if not isinstance(data, dict):
                    data = {}

                if layer == "meta" and event_type == "sovereign_score":
                    # Keep newest score
                    if (self.latest_score is None) or (ts_unix >= float(self.latest_score.get("ts_unix", -1))):
                        self.latest_score = {"ts_unix": ts_unix, "ts_utc": ts_utc, **data}

                current = self.latest_by_layer.get(layer)
                if (current is None) or (ts_unix >= current.ts_unix):
                    self.latest_by_layer[layer] = LatestLayer(
                        ts_unix=float(ts_unix),
                        ts_utc=ts_utc,
                        layer=layer,
                        event_type=event_type,
                        data=data,
                    )

    def calculate_score(self) -> dict[str, Any]:
        # Prefer the engine-computed score if available.
        if self.latest_score is not None:
            return {
                "total_capability": int(self.latest_score.get("total_capability", 100)),
                "dangerous_freedom": int(self.latest_score.get("dangerous_freedom", 0)),
                "stability": int(self.latest_score.get("stability", 100)),
                "ts_utc": self.latest_score.get("ts_utc", ""),
            }

        total_capability = 100
        dangerous_freedom = 0
        for latest in self.latest_by_layer.values():
            status = str(latest.data.get("status", "UNKNOWN")).upper()
            if status == "DEGRADED":
                dangerous_freedom += 10
            elif status == "WARNING":
                dangerous_freedom += 5
            elif status == "OVERLOADED":
                dangerous_freedom += 15
        return {
            "total_capability": total_capability,
            "dangerous_freedom": dangerous_freedom,
            "stability": total_capability - dangerous_freedom,
            "ts_utc": _utc_now_iso(),
        }

    def generate_html(self) -> str:
        score = self.calculate_score()

        def stability_bucket(stability: int) -> str:
            if stability >= 90:
                return "stability-100"
            if stability >= 75:
                return "stability-80"
            if stability >= 60:
                return "stability-60"
            if stability >= 40:
                return "stability-40"
            return "stability-20"

        stability = int(score.get("stability", 0))
        layer_order = ["physical", "digital", "codex", "cognitive", "collaborative", "meta"]

        layer_cards: list[str] = []
        for layer in layer_order:
            latest = self.latest_by_layer.get(layer)
            if latest is None:
                continue

            status = str(latest.data.get("status", "UNKNOWN")).upper()
            status_class = status.lower()
            ts_text = latest.ts_utc or datetime.fromtimestamp(latest.ts_unix, tz=timezone.utc).isoformat()
            data_json = json.dumps(latest.data, indent=2, ensure_ascii=False)

            layer_cards.append(
                f"""
                <div class=\"layer {status_class}\"> 
                  <h3>{html.escape(layer.upper())} LAYER</h3>
                  <div class=\"timestamp\">{html.escape(ts_text)}</div>
                  <div class=\"status\">Status: <strong>{html.escape(status)}</strong></div>
                  <pre>{html.escape(data_json)}</pre>
                </div>
                """
            )

        html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Sovereign Recursion Dashboard</title>
  <style>
    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; background: #0f172a; color: #e2e8f0; }}
    .container {{ max-width: 1200px; margin: 0 auto; }}
    header {{ text-align: center; padding: 20px; border-bottom: 2px solid #334155; }}
    .score-card {{ background: #1e293b; border-radius: 10px; padding: 20px; margin: 20px 0; text-align: center; }}
    .stability-score {{ font-size: 48px; font-weight: bold; margin: 10px 0; }}
    .stability-100 {{ color: #10b981; }}
    .stability-80 {{ color: #84cc16; }}
    .stability-60 {{ color: #f59e0b; }}
    .stability-40 {{ color: #f97316; }}
    .stability-20 {{ color: #ef4444; }}
    .layers-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 20px; margin: 20px 0; }}
    .layer {{ background: #1e293b; border-radius: 10px; padding: 15px; border-left: 5px solid; }}
    .layer.stable {{ border-color: #10b981; }}
    .layer.intact {{ border-color: #10b981; }}
    .layer.warning {{ border-color: #f59e0b; }}
    .layer.degraded {{ border-color: #ef4444; }}
    .layer.overloaded {{ border-color: #ef4444; }}
    .layer.corrupted {{ border-color: #ef4444; }}
    .layer.unknown {{ border-color: #64748b; }}
    .layer h3 {{ margin: 0 0 10px 0; color: #e2e8f0; }}
    .timestamp {{ font-size: 12px; color: #94a3b8; margin-bottom: 10px; }}
    .status {{ margin: 10px 0; font-size: 14px; }}
    pre {{ background: #0f172a; padding: 10px; border-radius: 5px; overflow-x: auto; font-size: 12px; margin: 10px 0; }}
    .metrics {{ display: flex; justify-content: space-around; margin-top: 10px; }}
    .metric {{ text-align: center; }}
    .metric-value {{ font-size: 24px; font-weight: bold; }}
    .metric-label {{ font-size: 12px; color: #94a3b8; }}
    footer {{ text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #334155; color: #64748b; font-size: 12px; }}
  </style>
</head>
<body>
  <div class=\"container\">
    <header>
      <h1>🌀 Sovereign Recursion Dashboard</h1>
      <p>Autonomous Sovereignty Verification System</p>
    </header>

    <div class=\"score-card\">
      <h2>Stability Score</h2>
      <div class=\"stability-score {stability_bucket(stability)}\">{stability}/100</div>
      <div class=\"metrics\">
        <div class=\"metric\"><div class=\"metric-value\">{int(score.get('total_capability', 100))}</div><div class=\"metric-label\">Total Capability</div></div>
        <div class=\"metric\"><div class=\"metric-value\">{int(score.get('dangerous_freedom', 0))}</div><div class=\"metric-label\">Dangerous Freedom</div></div>
      </div>
    </div>

    <div class=\"layers-grid\">
      {''.join(layer_cards)}
    </div>

    <footer>
      Generated: {_utc_now_iso()} | Ledger: {html.escape(str(self.ledger_path))} | Layers: {len(self.latest_by_layer)}
    </footer>
  </div>
</body>
</html>
"""
        return html_content


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Generate Sovereign Recursion HTML dashboard")
    p.add_argument("--ledger", default="validation/sovereign_recursion/ledger.jsonl", help="Ledger JSONL path")
    p.add_argument(
        "--output",
        default="validation/sovereign_recursion/sovereignty_dashboard.html",
        help="Output HTML path",
    )
    args = p.parse_args(argv)

    dashboard = SovereignDashboard(args.ledger)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(dashboard.generate_html(), encoding="utf-8")
    print(str(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
