"""
Sovereign Evidence Analyser — CLI & API Integration Layer
Provides JSON API for Manus AI, IDE extensions, and MCP hooks.
No PII leaves the machine — only anonymised queries and structure.
"""
import json
import argparse
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.store import EvidenceStore
from config import DB_PATH, DB_ENCRYPTION_KEY


def get_store() -> EvidenceStore:
    return EvidenceStore(str(DB_PATH), DB_ENCRYPTION_KEY)


def cmd_stats():
    """Return database statistics (safe — no PII)."""
    store = get_store()
    stats = store.get_stats()
    store.close()
    return stats


def cmd_search(query: str, source: str = "all"):
    """Search evidence by keyword. Returns IDs and snippets."""
    store = get_store()
    results = {"documents": [], "emails": []}

    if source in ("all", "documents"):
        for row in store.search_documents(query):
            results["documents"].append({
                "id": row["id"],
                "file_name": row["file_name"],
                "type": row["file_type"],
                "snippet": row["snippet"][:200],
            })

    if source in ("all", "emails"):
        for row in store.search_emails(query):
            results["emails"].append({
                "id": row["id"],
                "date": row["date"],
                "subject": row["subject"],
                "from": row["from_addr"],
                "snippet": row["snippet"][:200],
            })

    store.close()
    return results


def cmd_timeline(start=None, end=None, event_type=None):
    """Get timeline events (safe — structured data only)."""
    store = get_store()
    events = store.get_timeline(start, end, event_type)
    result = []
    for ev in events:
        result.append({
            "date": ev["event_date"],
            "type": ev["event_type"],
            "title": ev["title"],
            "description": ev["description"],
        })
    store.close()
    return result


def cmd_entities(entity_type=None):
    """Get extracted entities."""
    store = get_store()
    entities = store.get_entities(entity_type)
    result = []
    for ent in entities:
        result.append({
            "type": ent["entity_type"],
            "value": ent["entity_value"],
            "context": ent["context"][:150] if ent["context"] else "",
        })
    store.close()
    return result


def main():
    parser = argparse.ArgumentParser(description="Sovereign Evidence Analyser CLI")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("stats", help="Show database statistics")

    search_p = sub.add_parser("search", help="Search evidence")
    search_p.add_argument("query", help="Search term")
    search_p.add_argument("--source", choices=["all", "documents", "emails"], default="all")

    timeline_p = sub.add_parser("timeline", help="Get timeline events")
    timeline_p.add_argument("--start", help="Start date (YYYY-MM-DD)")
    timeline_p.add_argument("--end", help="End date (YYYY-MM-DD)")
    timeline_p.add_argument("--type", dest="event_type", help="Event type filter")

    entities_p = sub.add_parser("entities", help="List extracted entities")
    entities_p.add_argument("--type", dest="entity_type", help="Entity type filter")

    args = parser.parse_args()

    if args.command == "stats":
        result = cmd_stats()
    elif args.command == "search":
        result = cmd_search(args.query, args.source)
    elif args.command == "timeline":
        result = cmd_timeline(args.start, args.end, args.event_type)
    elif args.command == "entities":
        result = cmd_entities(args.entity_type)
    else:
        parser.print_help()
        return

    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
