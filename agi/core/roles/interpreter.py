# agi/core/roles/interpreter.py
from __future__ import annotations
from typing import Dict, Any
from ..model_runner import run_model_for_task

def build_interpreter_prompt(question: str, raw_answer: str) -> str:
    return (
        "You are the Sovereign interpreter.\n"
        "- Explain the given answer in simple, clear language.\n"
        "- Do NOT change its meaning or add new facts.\n"
        "- Use short sentences and a concrete example where possible.\n\n"
        f"Question:\n{question}\n\n"
        f"Answer:\n{raw_answer}\n\n"
        "Explain this for a non-technical person."
    )

def run_interpreter(question: str, raw_answer: str, context: Dict[str, Any]) -> Dict[str, Any]:
    prompt = build_interpreter_prompt(question, raw_answer)
    explained_answer = run_model_for_task(task_type="explanation", prompt=prompt)
    return {"role": "interpreter", "prompt": prompt, "explained_answer": explained_answer}
