# agi/core/triad_harness.py
from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, Literal, Optional
import time, json, hashlib, uuid

from .roles import interpreter
try:
    from .roles import specialist, validator, arbiter
except ImportError:
    class _Stub:
        @staticmethod
        def run_specialist(q, c): return {"answer": f"DRAFT:{q}"}
        @staticmethod
        def run_validator(d, c): return {"validated": True, "answer": d.get("answer")}
        @staticmethod
        def run_arbiter(d, v, c): return {"final_answer": v.get("answer")}
    specialist = _Stub
    validator = _Stub
    arbiter = _Stub

from .assistant_channel import get_assistant_system_prompt
from .receipt import SovereignReceipt, write_receipt_json, store_answer_and_receipt
try:
    from .drift_detector import detect_drift
except ImportError:
    def detect_drift(root: Path):
        return []

ResponseMode = Literal["raw", "explained"]
ROOT_DIR = Path(__file__).resolve().parent

def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def run_triad(question: str, mode: ResponseMode = "raw", parent_receipt_id: Optional[str] = None) -> Dict[str, Any]:
    context: Dict[str, Any] = {"policy_version": "v0.1a", "model_id": "local-small-1"}
    drifts = detect_drift(ROOT_DIR)
    drift_flag = len(drifts) > 0

    spec_out = specialist.run_specialist(question, context)
    val_out = validator.run_validator(spec_out, context)
    arb_out = arbiter.run_arbiter(spec_out, val_out, context)
    raw_answer = arb_out.get("final_answer") or spec_out.get("answer") or ""

    explained_answer: Optional[str] = None
    interpreter_prompt_hash: Optional[str] = None
    if mode == "explained":
        interp_out = interpreter.run_interpreter(question, raw_answer, context)
        explained_answer = interp_out.get("explained_answer", raw_answer)
        interpreter_prompt_hash = _hash_text(interp_out.get("prompt", ""))

    assistant_system_prompt = get_assistant_system_prompt()
    assistant_system_prompt_hash = _hash_text(assistant_system_prompt)

    answer_id = str(uuid.uuid4())
    receipt_id = str(uuid.uuid4())
    prompt_hash = _hash_text(question)
    answer_hash = _hash_text(raw_answer)
    ts = int(time.time())

    agent_path = ["specialist", "validator", "arbiter"]
    if mode == "explained":
        agent_path.append("interpreter")

    receipt = SovereignReceipt(
        receipt_id=receipt_id,
        answer_id=answer_id,
        model_id=context["model_id"],
        policy_version=context["policy_version"],
        mode=mode,
        agent_path=agent_path,
        prompt_hash=prompt_hash,
        answer_hash=answer_hash,
        interpreter_prompt_hash=interpreter_prompt_hash,
        assistant_system_prompt_hash=assistant_system_prompt_hash,
        parent_receipt_id=parent_receipt_id,
        drift_detected=drift_flag,
        drift_details=drifts,
        timestamp=ts,
    )

    receipt_path = write_receipt_json(receipt)
    store_answer_and_receipt(receipt, question, raw_answer, explained_answer)
    visible_answer = explained_answer if (mode == "explained" and explained_answer) else raw_answer

    return {
        "answer": visible_answer,
        "mode": mode,
        "answer_id": answer_id,
        "receipt_id": receipt_id,
        "receipt_path": str(receipt_path),
        "receipt": json.loads(Path(receipt_path).read_text(encoding="utf-8")),
    }

if __name__ == "__main__":
    from .receipt import init_db
    init_db()
    print(json.dumps(run_triad("What does the Sovereign Model do?", mode="explained"), indent=2))
