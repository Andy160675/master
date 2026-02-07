"""Optional validators.

Baseline prompts usually produce free text; JSON validation is for structured modes.
"""

from __future__ import annotations

import json


def validate_json(text: str) -> bool:
    try:
        json.loads(text)
        return True
    except Exception:
        return False
