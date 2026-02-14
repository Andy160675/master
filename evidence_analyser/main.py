"""
Sovereign Evidence Analyser — Main Entry Point
Run: python -m evidence_analyser.main

100% offline. All data stays on this machine.
"""
import sys
from pathlib import Path

# Ensure package is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from evidence_analyser.config import DB_PATH, DB_ENCRYPTION_KEY, APP_TITLE
from evidence_analyser.db.store import EvidenceStore
from evidence_analyser.ui.app import launch


def main():
    print(f"=== {APP_TITLE} ===")
    print(f"Database: {DB_PATH}")
    print(f"Encryption: {'enabled' if DB_ENCRYPTION_KEY else 'disabled (set EVIDENCE_DB_KEY env var)'}")
    print()

    # Ensure data directory exists
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Initialise store
    store = EvidenceStore(str(DB_PATH), DB_ENCRYPTION_KEY)
    stats = store.get_stats()
    print(f"Current evidence: {stats['documents']} docs, {stats['emails']} emails, "
          f"{stats['entities']} entities, {stats['events']} timeline events")
    print()

    print("Launching local UI at http://127.0.0.1:7860")
    print("Press Ctrl+C to stop.")
    print()

    try:
        launch(store)
    except KeyboardInterrupt:
        print("\nShutting down.")
    finally:
        store.close()


if __name__ == "__main__":
    main()
