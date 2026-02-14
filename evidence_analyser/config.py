"""
Sovereign Evidence Analyser — Configuration
All paths and settings. Everything runs locally. No cloud.
"""
import os
from pathlib import Path

# --- Paths ---
APP_ROOT = Path(__file__).parent
DB_PATH = APP_ROOT / "data" / "evidence.db"
EXPORT_DIR = APP_ROOT / "exports"

# Default evidence source directories (user can override via UI)
DEFAULT_SOURCES = {
    "emails": r"C:\Users\andyj\OneDrive\Documents\Backup\Backup - Copy\Takeout",
    "chrome_downloads": r"C:\Users\andyj\OneDrive\Documents\Backup\Backup - Copy\Chrome",
    "evidence_annexes": r"C:\Users\andyj\OneDrive\Documents\Backup\Backup - Copy\03_Evidence_Annexes",
    "divorce_docs": r"C:\Users\andyj\OneDrive\Documents\Backup\Backup - Copy\Divorce",
}

# --- Database ---
DB_ENCRYPTION_KEY = os.environ.get("EVIDENCE_DB_KEY", "")  # Set via env var for safety

# --- Supported file types ---
EMAIL_EXTENSIONS = {".eml", ".mbox"}
DOCUMENT_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt", ".md"}

# --- Entity tags for pattern detection ---
KNOWN_ENTITIES = {
    "organisations": ["EDF", "GDLSUK", "GDL", "PHI", "Wendy Hopkins", "HMCTS", "CAFCASS", "SARU"],
    "people": [],  # populated from parsed data
    "keywords": [
        "coercive control", "abuse", "obstruction", "manipulation",
        "financial remedy", "DSAR", "subject access", "data protection",
        "safeguarding", "undertaking", "disclosure", "non-disclosure",
        "contempt", "without prejudice", "consent order",
    ],
}

# --- App settings ---
APP_TITLE = "Sovereign Evidence Analyser"
APP_HOST = "127.0.0.1"  # localhost only — never expose
APP_PORT = 7860
