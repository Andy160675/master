"""
Sovereign Evidence Analyser — Email Parser
Parses .eml files from Google Takeout. 100% local.
"""
import email
import email.policy
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Optional
from datetime import datetime


def parse_eml(file_path: str) -> Optional[dict]:
    """Parse a single .eml file and return structured data."""
    try:
        path = Path(file_path)
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            msg = email.message_from_file(f, policy=email.policy.default)

        # Extract date
        date_str = msg.get("Date", "")
        try:
            date_obj = parsedate_to_datetime(date_str)
            date_iso = date_obj.isoformat()
        except Exception:
            date_iso = date_str

        # Extract body
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    payload = part.get_payload(decode=True)
                    if payload:
                        body = payload.decode("utf-8", errors="replace")
                        break
                elif content_type == "text/html" and not body:
                    payload = part.get_payload(decode=True)
                    if payload:
                        body = _strip_html(payload.decode("utf-8", errors="replace"))
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                body = payload.decode("utf-8", errors="replace")
                if msg.get_content_type() == "text/html":
                    body = _strip_html(body)

        # Check attachments
        has_attachments = any(
            part.get_content_disposition() == "attachment"
            for part in msg.walk()
        ) if msg.is_multipart() else False

        return {
            "file_path": str(path.resolve()),
            "message_id": msg.get("Message-ID", ""),
            "date": date_iso,
            "from_addr": msg.get("From", ""),
            "to_addr": msg.get("To", ""),
            "cc_addr": msg.get("Cc", ""),
            "subject": msg.get("Subject", ""),
            "body_text": body,
            "has_attachments": has_attachments,
        }
    except Exception as e:
        print(f"[EmailParser] Error parsing {file_path}: {e}")
        return None


def scan_email_directory(directory: str) -> list[dict]:
    """Scan a directory for .eml files and parse them all."""
    results = []
    dir_path = Path(directory)
    if not dir_path.exists():
        print(f"[EmailParser] Directory not found: {directory}")
        return results

    eml_files = list(dir_path.rglob("*.eml"))
    print(f"[EmailParser] Found {len(eml_files)} .eml files in {directory}")

    for eml_file in eml_files:
        parsed = parse_eml(str(eml_file))
        if parsed:
            results.append(parsed)

    return results


def _strip_html(html: str) -> str:
    """Basic HTML to text conversion."""
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        return soup.get_text(separator="\n", strip=True)
    except ImportError:
        import re
        text = re.sub(r"<[^>]+>", " ", html)
        text = re.sub(r"\s+", " ", text)
        return text.strip()
