"""Small, deterministic heuristics for scoring.

Keep this intentionally simple; it's a stability indicator, not a truth metric.
"""

from __future__ import annotations


def score_response(text: str) -> dict:
    t = text or ""
    tl = t.lower()

    score = {
        "structure": int("situation snapshot" in tl and "structured priorities" in tl),
        "uncertainty": int("uncert" in tl or "unknown" in tl or "not sure" in tl),
        "handoff": int("your judgment" in tl or "you decide" in tl or "up to you" in tl),
    }

    score["total"] = int(score["structure"] + score["uncertainty"] + score["handoff"])
    return score
