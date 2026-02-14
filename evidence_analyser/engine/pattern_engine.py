"""
Sovereign Evidence Analyser — Pattern Detection Engine
Finds entities, keywords, dates, and behavioural patterns across evidence.
100% local — no data leaves the machine.
"""
import re
from datetime import datetime
from typing import Optional

from ..config import KNOWN_ENTITIES


def extract_entities(text: str, source_type: str, source_id: int) -> list[dict]:
    """Extract known entities and keywords from text."""
    if not text:
        return []

    entities = []
    text_lower = text.lower()

    # Organisation matches
    for org in KNOWN_ENTITIES["organisations"]:
        if org.lower() in text_lower:
            context = _get_context(text, org)
            entities.append({
                "source_type": source_type,
                "source_id": source_id,
                "entity_type": "organisation",
                "entity_value": org,
                "context": context,
            })

    # Keyword matches
    for keyword in KNOWN_ENTITIES["keywords"]:
        if keyword.lower() in text_lower:
            context = _get_context(text, keyword)
            entities.append({
                "source_type": source_type,
                "source_id": source_id,
                "entity_type": "keyword",
                "entity_value": keyword,
                "context": context,
            })

    # Date extraction (UK format dd/mm/yyyy and ISO yyyy-mm-dd)
    date_patterns = [
        (r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b", "date_uk"),
        (r"\b(\d{4}-\d{2}-\d{2})\b", "date_iso"),
    ]
    for pattern, date_type in date_patterns:
        for match in re.finditer(pattern, text):
            entities.append({
                "source_type": source_type,
                "source_id": source_id,
                "entity_type": "date",
                "entity_value": match.group(1),
                "context": _get_context(text, match.group(1)),
            })

    # Email address extraction
    email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    for match in re.finditer(email_pattern, text):
        entities.append({
            "source_type": source_type,
            "source_id": source_id,
            "entity_type": "email_address",
            "entity_value": match.group(0),
            "context": _get_context(text, match.group(0)),
        })

    # Money amounts (GBP)
    money_pattern = r"£[\d,]+(?:\.\d{2})?"
    for match in re.finditer(money_pattern, text):
        entities.append({
            "source_type": source_type,
            "source_id": source_id,
            "entity_type": "financial_amount",
            "entity_value": match.group(0),
            "context": _get_context(text, match.group(0)),
        })

    return entities


def detect_patterns(store) -> list[dict]:
    """Analyse the database for cross-document behavioural patterns."""
    patterns = []

    # Pattern: Repeated keyword clusters over time
    keyword_counts = store.conn.execute("""
        SELECT entity_value, COUNT(*) as cnt,
               MIN(e.found_at) as first_seen, MAX(e.found_at) as last_seen
        FROM entities e
        WHERE entity_type = 'keyword'
        GROUP BY entity_value
        HAVING cnt >= 3
        ORDER BY cnt DESC
    """).fetchall()

    for row in keyword_counts:
        patterns.append({
            "pattern_name": f"Recurring theme: {row['entity_value']}",
            "description": f"Found {row['cnt']} times across evidence (first: {row['first_seen']}, last: {row['last_seen']})",
            "confidence": min(row["cnt"] / 10.0, 1.0),
        })

    # Pattern: Organisation involvement frequency
    org_counts = store.conn.execute("""
        SELECT entity_value, COUNT(*) as cnt
        FROM entities
        WHERE entity_type = 'organisation'
        GROUP BY entity_value
        ORDER BY cnt DESC
    """).fetchall()

    for row in org_counts:
        patterns.append({
            "pattern_name": f"Organisation involvement: {row['entity_value']}",
            "description": f"Referenced {row['cnt']} times across evidence",
            "confidence": min(row["cnt"] / 5.0, 1.0),
        })

    # Pattern: Communication clusters (emails from same sender)
    email_clusters = store.conn.execute("""
        SELECT from_addr, COUNT(*) as cnt,
               MIN(date) as first_email, MAX(date) as last_email
        FROM emails
        GROUP BY from_addr
        HAVING cnt >= 2
        ORDER BY cnt DESC
    """).fetchall()

    for row in email_clusters:
        patterns.append({
            "pattern_name": f"Communication cluster: {row['from_addr']}",
            "description": f"{row['cnt']} emails from {row['first_email']} to {row['last_email']}",
            "confidence": min(row["cnt"] / 10.0, 1.0),
        })

    return patterns


def _get_context(text: str, term: str, window: int = 100) -> str:
    """Get surrounding text around a matched term."""
    idx = text.lower().find(term.lower())
    if idx == -1:
        return ""
    start = max(0, idx - window)
    end = min(len(text), idx + len(term) + window)
    snippet = text[start:end].replace("\n", " ").strip()
    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet = snippet + "..."
    return snippet
