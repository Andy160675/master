# agi/core/assistant_channel.py
"""Layer 1 — Context Preservation & Decision Support (Paperclip / Rubber Stamp).

Frozen invariants (from Manus Transfer Package):
  - Advisory only. MUST NOT block, approve, or escalate.
  - MUST NOT alter Sovereign verdicts.
  - MUST NOT import or invoke Sentinel (Layer 2) modules.
  - Assistance must never imply approval.
  - If a serious error is detected, request a re-run — never override.

This module provides:
  1. Context preservation — surfaces relevant prior decisions from the ledger.
  2. Non-authoritative nudges — highlights potential inconsistencies without blocking.
  3. Thread management — persists discussion per answer_id.
"""
from __future__ import annotations

from typing import Dict, Any, List, Optional
import sqlite3

from .receipt import store_assistant_message, DB_PATH
from .model_runner import run_model_for_task

# ---------------------------------------------------------------------------
# Layer 4 enforcement: This module MUST NOT import from Sentinel components.
# The following imports are structurally forbidden:
#   from .mcp_gatekeeper import ...    # Layer 2 — Sentinel
#   from .diff_validator import ...    # Layer 2 — Sentinel
#   from .policy_signature import ...  # Layer 2 — Sentinel
#   from .empathy_engine import ...    # Layer 2 — Sentinel
# Violation of this boundary collapses Layer 1 into Layer 2.
# ---------------------------------------------------------------------------

# Maximum number of prior decisions to surface as context
MAX_PRIOR_CONTEXT = 5

# Maximum character length for each prior decision snippet
MAX_SNIPPET_LEN = 300

ASSISTANT_SYSTEM_PROMPT = (
    "You are Paperclip, the Sovereign decision-support companion (Layer 1).\n"
    "\n"
    "ROLE BOUNDARIES (frozen, non-negotiable):\n"
    "- You EXPLAIN and DISCUSS existing Sovereign answers.\n"
    "- You SURFACE relevant prior decisions when they may inform the current question.\n"
    "- You HIGHLIGHT potential inconsistencies between past and current answers.\n"
    "- You ASK clarifying questions that the human might not have considered.\n"
    "- You MUST NOT change, block, approve, or override the core verdict.\n"
    "- You MUST NOT escalate yourself into an enforcement or gating role.\n"
    "- You MUST NOT imply that your commentary constitutes approval.\n"
    "- If you detect a serious error or contradiction, say so clearly and\n"
    "  request a re-run. Do not attempt to fix it yourself.\n"
    "\n"
    "CONTEXT PRESERVATION:\n"
    "- When prior decisions are provided, reference them by date and topic.\n"
    "- Note any tension between prior positions and the current answer.\n"
    "- If no prior context is relevant, say so briefly and move on.\n"
    "\n"
    "TONE:\n"
    "- Concise, direct, low-ego.\n"
    "- You are the useful companion that notices things, not the authority that decides.\n"
    "- You exist to nudge, remind, and surface — then step back.\n"
)


def get_assistant_system_prompt() -> str:
    """Return the frozen Paperclip system prompt."""
    return ASSISTANT_SYSTEM_PROMPT


# ---------------------------------------------------------------------------
# Context Preservation — query past sovereign answers for related decisions
# ---------------------------------------------------------------------------

def search_prior_decisions(question: str, limit: int = MAX_PRIOR_CONTEXT) -> List[Dict[str, Any]]:
    """Search sovereign_answers for prior decisions related to the current question.

    Uses simple keyword matching against stored questions. Returns the most
    recent matches up to `limit`. This is a read-only query — no mutations.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Extract meaningful words (>3 chars) for keyword search
    keywords = [w.lower() for w in question.split() if len(w) > 3]
    if not keywords:
        conn.close()
        return []

    # Build WHERE clause matching any keyword in question or raw_answer
    conditions = []
    params: List[str] = []
    for kw in keywords[:10]:  # cap to avoid excessive query complexity
        conditions.append("(LOWER(question) LIKE ? OR LOWER(raw_answer) LIKE ?)")
        params.extend([f"%{kw}%", f"%{kw}%"])

    where = " OR ".join(conditions)
    query = f"""
        SELECT answer_id, question, raw_answer, created_at
        FROM sovereign_answers
        WHERE {where}
        ORDER BY created_at DESC
        LIMIT ?
    """
    params.append(str(limit))

    try:
        cur.execute(query, params)
        rows = cur.fetchall()
    except sqlite3.OperationalError:
        # Table may not exist yet on first run
        rows = []
    finally:
        conn.close()

    results = []
    for answer_id, q, raw, created_at in rows:
        snippet = raw[:MAX_SNIPPET_LEN] + ("..." if len(raw) > MAX_SNIPPET_LEN else "")
        results.append({
            "answer_id": answer_id,
            "question": q,
            "answer_snippet": snippet,
            "created_at": created_at,
        })
    return results


def format_prior_context(priors: List[Dict[str, Any]]) -> str:
    """Format prior decisions into a human-readable context block for the prompt."""
    if not priors:
        return ""

    lines = ["\nRELEVANT PRIOR DECISIONS (for context only, not authority):\n"]
    for i, p in enumerate(priors, 1):
        lines.append(
            f"  [{i}] ({p['created_at']}) Q: {p['question']}\n"
            f"      A: {p['answer_snippet']}\n"
        )
    lines.append(
        "Note: Prior decisions are context, not precedent. "
        "Each question is assessed on its own merits.\n"
    )
    return "".join(lines)


# ---------------------------------------------------------------------------
# Thread Management — same as before, persists discussion per answer_id
# ---------------------------------------------------------------------------

def list_thread_messages(answer_id: str) -> List[Dict[str, Any]]:
    """Retrieve the full assistant discussion thread for a given answer."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT role, message, created_at
        FROM assistant_messages
        WHERE answer_id = ?
        ORDER BY id ASC
        """,
        (answer_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return [{"role": role, "message": msg, "created_at": created_at} for (role, msg, created_at) in rows]


def append_user_message(answer_id: str, receipt_id: str, message: str) -> None:
    """Record a user message in the discussion thread."""
    store_assistant_message(answer_id, receipt_id, "user", message)


def append_assistant_message(answer_id: str, receipt_id: str, message: str) -> None:
    """Record a Paperclip response in the discussion thread."""
    store_assistant_message(answer_id, receipt_id, "assistant", message)


# ---------------------------------------------------------------------------
# Prompt Construction — enriched with prior context
# ---------------------------------------------------------------------------

def build_assistant_prompt(
    system_prompt: str,
    sovereign_answer: str,
    thread: List[Dict[str, Any]],
    new_user_message: str,
    prior_context: str = "",
) -> str:
    """Build the full prompt for the Paperclip model call.

    Includes: system prompt, prior decision context (if any),
    the current sovereign answer, the discussion thread, and the new message.
    """
    lines: List[str] = [system_prompt]

    if prior_context:
        lines.append(prior_context)

    lines.append("\nCURRENT SOVEREIGN ANSWER (read-only, do not alter):\n")
    lines.append(sovereign_answer)
    lines.append("\nDISCUSSION THREAD:\n")

    for msg in thread:
        lines.append(f"{msg['role'].upper()}: {msg['message']}\n")

    lines.append(f"USER: {new_user_message}\nPAPERCLIP:")
    return "".join(lines)


# ---------------------------------------------------------------------------
# Main Entry Point — generate a Paperclip reply
# ---------------------------------------------------------------------------

def generate_assistant_reply(
    answer_id: str,
    receipt_id: str,
    sovereign_answer: str,
    new_user_message: str,
    question: Optional[str] = None,
) -> str:
    """Generate a Paperclip (Layer 1) reply for a sovereign answer discussion.

    If `question` is provided, prior decisions are searched and surfaced
    as context. The reply is advisory only — it cannot alter the verdict.

    Returns:
        The Paperclip reply text (also persisted to the thread).
    """
    thread = list_thread_messages(answer_id)

    # Context preservation: surface relevant prior decisions
    prior_context = ""
    if question:
        priors = search_prior_decisions(question)
        # Exclude the current answer from prior context
        priors = [p for p in priors if p["answer_id"] != answer_id]
        prior_context = format_prior_context(priors)

    prompt = build_assistant_prompt(
        get_assistant_system_prompt(),
        sovereign_answer,
        thread,
        new_user_message,
        prior_context=prior_context,
    )
    result = run_model_for_task(task_type="discussion", prompt=prompt)
    reply = result if isinstance(result, str) else result.get("text", str(result))
    append_assistant_message(answer_id, receipt_id, reply)
    return reply
