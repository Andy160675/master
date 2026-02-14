"""
Sovereign Evidence Analyser — Timeline Generator
Builds chronological event timeline from all parsed sources.
"""
from datetime import datetime
from typing import Optional
import re


def build_timeline_from_emails(store):
    """Create timeline events from parsed emails."""
    emails = store.conn.execute(
        "SELECT id, date, from_addr, to_addr, subject FROM emails WHERE date != '' ORDER BY date"
    ).fetchall()

    count = 0
    for em in emails:
        date = _normalise_date(em["date"])
        if not date:
            continue

        store.insert_event(
            event_date=date,
            event_type="email",
            title=f"Email: {em['subject'][:100]}" if em["subject"] else "Email (no subject)",
            description=f"From: {em['from_addr']} → To: {em['to_addr']}",
            source_type="email",
            source_id=em["id"],
            tags=["email", "communication"],
        )
        count += 1

    print(f"[Timeline] Added {count} email events")
    return count


def build_timeline_from_documents(store):
    """Create timeline events from documents that contain dates in filenames or content."""
    docs = store.conn.execute(
        "SELECT id, file_name, file_type, content_text, metadata_json FROM documents"
    ).fetchall()

    count = 0
    for doc in docs:
        # Try to extract date from filename
        date = _extract_date_from_filename(doc["file_name"])

        if date:
            store.insert_event(
                event_date=date,
                event_type=_infer_event_type(doc["file_name"]),
                title=f"Document: {doc['file_name']}",
                description=f"Type: {doc['file_type']}",
                source_type="document",
                source_id=doc["id"],
                tags=["document"],
            )
            count += 1

    print(f"[Timeline] Added {count} document events")
    return count


def _normalise_date(date_str: str) -> Optional[str]:
    """Try to normalise various date formats to YYYY-MM-DD."""
    if not date_str:
        return None

    # Already ISO format
    if re.match(r"^\d{4}-\d{2}-\d{2}", date_str):
        return date_str[:10]

    # Try parsing ISO datetime
    for fmt in [
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%d.%m.%Y",
        "%d %B %Y",
        "%d %b %Y",
        "%B %d, %Y",
    ]:
        try:
            dt = datetime.strptime(date_str.strip()[:30], fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue

    return None


def _extract_date_from_filename(filename: str) -> Optional[str]:
    """Try to extract a date from a filename."""
    # Pattern: dd-mm-yyyy or dd.mm.yyyy
    match = re.search(r"(\d{2})[-.](\d{2})[-.](\d{4})", filename)
    if match:
        day, month, year = match.groups()
        try:
            dt = datetime(int(year), int(month), int(day))
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass

    # Pattern: yyyy-mm-dd
    match = re.search(r"(\d{4})-(\d{2})-(\d{2})", filename)
    if match:
        return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"

    # Pattern: month names
    match = re.search(
        r"(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\s*(\d{2,4})",
        filename.upper()
    )
    if match:
        months = {"JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
                  "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12}
        month = months[match.group(1)]
        year = int(match.group(2))
        if year < 100:
            year += 2000
        return f"{year}-{month:02d}-01"

    return None


def _infer_event_type(filename: str) -> str:
    """Guess event type from filename."""
    name = filename.lower()
    if any(w in name for w in ["court", "bundle", "judge", "order", "application"]):
        return "court"
    if any(w in name for w in ["statement", "bank", "financial", "halifax", "hsbc", "pension"]):
        return "financial"
    if any(w in name for w in ["abuse", "safeguard", "saru", "coercive"]):
        return "incident"
    if any(w in name for w in ["letter", "email", "gmail"]):
        return "communication"
    return "document"
