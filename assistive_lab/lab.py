from __future__ import annotations

import argparse
import hashlib
import os
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from openai import OpenAI

try:
    # Package-mode (python -m assistive_lab.lab)
    from .governor import cognitive_governor_with_threshold
    from .logger import LogPaths, log_run_csv, log_run_jsonl
    from .prompts import PROMPTS
    from .rubric import score_response
    from .validator import validate_json
except ImportError:
    # Script-mode (python assistive_lab/lab.py)
    from governor import cognitive_governor_with_threshold
    from logger import LogPaths, log_run_csv, log_run_jsonl
    from prompts import PROMPTS
    from rubric import score_response
    from validator import validate_json


OLLAMA_DEFAULT_BASE_URL = "http://localhost:11434/v1"


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def sha256_text(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def run_model(client: OpenAI, model: str, prompt: str, temperature: float, max_output_tokens: int) -> tuple[str, float]:
    start = time.perf_counter()
    resp = client.responses.create(
        model=model,
        input=prompt,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
    )
    elapsed_s = time.perf_counter() - start
    return resp.output_text or "", elapsed_s


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Assistive Intelligence Test Lab (minimal, IDE-friendly)")

    p.add_argument("--prompt", default="v1_assistive_baseline", help="Prompt key from prompts.PROMPTS")
    p.add_argument(
        "--provider",
        choices=["ollama", "openai"],
        default=os.getenv("ASSISTIVE_LAB_PROVIDER", "ollama"),
        help="API provider target (default: ASSISTIVE_LAB_PROVIDER or ollama)",
    )
    p.add_argument(
        "--base-url",
        default=os.getenv("OPENAI_BASE_URL", ""),
        help="Override OpenAI-compatible base URL (e.g., Ollama: http://localhost:11434/v1)",
    )
    p.add_argument(
        "--api-key",
        default=os.getenv("OPENAI_API_KEY", ""),
        help="API key (OpenAI). For Ollama this can be blank; a dummy key will be used.",
    )
    p.add_argument(
        "--models",
        default=os.getenv("OPENAI_MODELS", ""),
        help="Comma-separated model list. Defaults depend on --provider.",
    )
    p.add_argument("--runs", type=int, default=3, help="Load loop count (default: 3)")
    p.add_argument("--sleep", type=float, default=1.0, help="Seconds to sleep between model calls (default: 1.0)")

    p.add_argument("--temperature", "--temp", dest="temperature", type=float, default=0.0, help="Sampling temperature (default: 0.0)")
    p.add_argument("--max-output-tokens", type=int, default=450, help="Max output tokens (default: 450)")
    p.add_argument(
        "--min-score",
        type=int,
        default=2,
        help="Minimum rubric total score required for governor OK (default: 2)",
    )

    p.add_argument(
        "--log-root",
        default=str(Path("validation") / "assistive_lab"),
        help="Where to write append-only logs (default: validation/assistive_lab)",
    )
    p.add_argument("--truncate", type=int, default=300, help="Print only first N chars of output (default: 300)")
    p.add_argument(
        "--gate",
        action="store_true",
        help="Exit non-zero if governor reports drift or JSON validation fails when --expect-json is set.",
    )
    p.add_argument(
        "--expect-json",
        action="store_true",
        help="If set, validator.validate_json(output) must be True (useful for schema-based prompts).",
    )

    return p.parse_args()


def build_client(provider: str, base_url: str, api_key: str) -> OpenAI:
    if provider == "ollama":
        url = base_url.strip() or OLLAMA_DEFAULT_BASE_URL
        # Ollama's OpenAI-compatible endpoint doesn't require a real API key.
        key = api_key.strip() or "ollama"
        return OpenAI(base_url=url, api_key=key)

    # provider == "openai"
    key = api_key.strip()
    if not key:
        raise SystemExit("Missing OPENAI_API_KEY (or pass --api-key) for provider=openai")
    url = base_url.strip()
    return OpenAI(api_key=key, base_url=url or None)


def main() -> int:
    args = parse_args()

    prompt_key = args.prompt
    if prompt_key not in PROMPTS:
        raise SystemExit(f"Unknown prompt key: {prompt_key}. Available: {', '.join(sorted(PROMPTS.keys()))}")

    prompt = PROMPTS[prompt_key]
    prompt_hash = sha256_text(prompt)

    models = [m.strip() for m in (args.models or "").split(",") if m.strip()]
    if not models:
        if args.provider == "ollama":
            models = ["llama3", "mistral"]
        else:
            models = ["gpt-4.1", "gpt-4.1-mini"]
    if not models:
        raise SystemExit("No models specified")

    client = build_client(provider=args.provider, base_url=args.base_url, api_key=args.api_key)

    log_paths = LogPaths(root=Path(args.log_root))

    print("\n=== Assistive Lab Start ===\n")
    target = args.provider
    if args.provider == "ollama":
        target = f"ollama base_url={(args.base_url.strip() or OLLAMA_DEFAULT_BASE_URL)}"
    print(f"target={target}")
    print(f"prompt={prompt_key} prompt_sha256={prompt_hash[:12]} models={models} runs={args.runs}")

    run_id = utc_stamp()
    failures = 0

    for i in range(args.runs):
        print(f"\n--- Load Loop {i + 1}/{args.runs} ---")

        for model in models:
            output, elapsed_s = run_model(
                client=client,
                model=model,
                prompt=prompt,
                temperature=args.temperature,
                max_output_tokens=args.max_output_tokens,
            )

            score = score_response(output)
            gov = cognitive_governor_with_threshold(score=score, min_total=args.min_score)
            is_json = validate_json(output) if args.expect_json else False

            if args.truncate > 0:
                shown = output[: args.truncate].replace("\n", " ")
                print(
                    f"\nmodel={model} elapsed_s={elapsed_s:.3f} score={score} "
                    f"governor_status={gov.get('status')} governor_ok={gov.get('ok')}"
                )
                print(f"output_prefix={shown}{'...' if len(output) > args.truncate else ''}")
            else:
                print(
                    f"\nmodel={model} elapsed_s={elapsed_s:.3f} score={score} "
                    f"governor_status={gov.get('status')} governor_ok={gov.get('ok')}"
                )
                print(output)

            # Append-only logs
            row = {
                "ts_utc": datetime.now(timezone.utc).isoformat(),
                "run_id": run_id,
                "loop": i + 1,
                "model": model,
                "prompt": prompt_key,
                "prompt_sha256": prompt_hash,
                "elapsed_s": round(elapsed_s, 6),
                "score_total": score.get("total", 0),
                "score_structure": score.get("structure", 0),
                "score_uncertainty": score.get("uncertainty", 0),
                "score_handoff": score.get("handoff", 0),
                "governor_ok": bool(gov.get("ok", False)),
                "governor_status": gov.get("status", ""),
                "min_score": int(args.min_score),
                "expect_json": bool(args.expect_json),
                "json_ok": bool(is_json) if args.expect_json else "",
            }
            log_run_csv(log_paths, row)

            event = {
                **row,
                "temperature": args.temperature,
                "max_output_tokens": args.max_output_tokens,
                "output_text": output,
                "governor": gov,
                "score": score,
            }
            log_run_jsonl(log_paths, event)

            # Optional gate
            gated_fail = False
            if not gov.get("ok", False):
                gated_fail = True
            if args.expect_json and not is_json:
                gated_fail = True

            if gated_fail:
                failures += 1
                if args.gate:
                    print("\n[FAIL] Gate triggered")
                    return 1

            if args.sleep > 0:
                time.sleep(args.sleep)

    print("\n=== Lab Complete ===")
    if failures:
        print(f"Failures observed: {failures} (non-gating mode)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
