# agi/core/model_runner.py
"""Unified model runner for Sovereign model wrapper.

Provides a single entrypoint `run_model_for_task(task_type, prompt)` which:
- Loads model_stack.yaml (cached)
- Resolves the correct model key by task_type
- Calls provider (initially Ollama HTTP API)

Extend later for lmstudio / remote providers by inspecting model cfg `provider`.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import requests  # Requires: pip install requests
import yaml      # Requires: pip install pyyaml

ROOT_DIR = Path(__file__).resolve().parent
STACK_PATH = ROOT_DIR / "model_stack.yaml"
_StackCache: Dict[str, Any] | None = None

class ModelRunnerError(Exception):
    pass

def load_model_stack() -> Dict[str, Any]:
    global _StackCache
    if _StackCache is None:
        if not STACK_PATH.exists():
            raise ModelRunnerError(f"model_stack.yaml not found at {STACK_PATH}")
        with STACK_PATH.open("r", encoding="utf-8") as f:
            _StackCache = yaml.safe_load(f) or {}
    return _StackCache

def resolve_model_id(task_type: str) -> str:
    stack = load_model_stack()
    routing = stack.get("routing_rules", {})
    default_model_key = routing.get("default", "local_small")
    model_key = routing.get("by_task_type", {}).get(task_type, default_model_key)
    models = stack.get("models", {})
    model_cfg = models.get(model_key)
    if not model_cfg:
        raise ModelRunnerError(f"Unknown model key '{model_key}' for task_type '{task_type}'")
    return model_cfg["id"], model_cfg.get("provider", "ollama")

def call_ollama(model_id: str, prompt: str, **kwargs: Any) -> str:
    url = "http://localhost:11434/api/generate"
    payload = {"model": model_id, "prompt": prompt, "stream": False}
    payload.update(kwargs)
    try:
        resp = requests.post(url, json=payload, timeout=60)
    except Exception as e:
        raise ModelRunnerError(f"Ollama request failed: {e}") from e
    if resp.status_code != 200:
        raise ModelRunnerError(f"Ollama HTTP {resp.status_code}: {resp.text}")
    data = resp.json()
    text = data.get("response") or data.get("output") or ""
    return text.strip()

def run_model_for_task(task_type: str, prompt: str) -> str:
    model_id, provider = resolve_model_id(task_type)
    if provider == "ollama":
        return call_ollama(model_id=model_id, prompt=prompt)
    # Future providers can be added here.
    raise ModelRunnerError(f"Unsupported provider '{provider}' for model '{model_id}'")

if __name__ == "__main__":
    try:
        out = run_model_for_task("governance", "Test prompt for governance routing.")
        print(out)
    except Exception as e:
        print(f"[MODEL_RUNNER_ERROR] {e}")
