"""A minimal 'cognitive governor' hook.

This is a lightweight drift detector: it doesn't block execution by default,
but returns a status you can choose to gate on.
"""

from __future__ import annotations


def cognitive_governor(score: dict) -> dict:
    return cognitive_governor_with_threshold(score=score, min_total=2)


def cognitive_governor_with_threshold(score: dict, min_total: int) -> dict:
    total = int(score.get("total", 0))

    if total < int(min_total):
        return {
            "ok": False,
            "status": "DRIFT",
            "reason": f"response drift detected (score_total={total} < min_total={min_total})",
            "min_total": int(min_total),
            "score_total": total,
        }

    return {
        "ok": True,
        "status": "OK",
        "reason": "response stable",
        "min_total": int(min_total),
        "score_total": total,
    }
