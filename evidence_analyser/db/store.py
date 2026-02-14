"""
Sovereign Evidence Analyser — Database Layer
Encrypted SQLite storage. All data stays local.
"""
import sqlite3
import json
import os
from pathlib import Path
from datetime import datetime

# Try sqlcipher for encryption, fall back to plain sqlite3
try:
    from pysqlcipher3 import dbapi2 as sqlcipher
    HAS_ENCRYPTION = True
except ImportError:
    sqlcipher = None
    HAS_ENCRYPTION = False


def get_connection(db_path: str, encryption_key: str = "") -> sqlite3.Connection:
    db_dir = Path(db_path).parent
    db_dir.mkdir(parents=True, exist_ok=True)

    if HAS_ENCRYPTION and encryption_key:
        conn = sqlcipher.connect(db_path)
        conn.execute(f"PRAGMA key='{encryption_key}'")
    else:
        conn = sqlite3.connect(db_path)

    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(conn: sqlite3.Connection):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT UNIQUE NOT NULL,
            file_name TEXT NOT NULL,
            file_type TEXT NOT NULL,
            source_dir TEXT,
            file_size INTEGER,
            file_hash TEXT,
            parsed_at TEXT NOT NULL,
            content_text TEXT,
            metadata_json TEXT
        );

        CREATE TABLE IF NOT EXISTS emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT UNIQUE NOT NULL,
            message_id TEXT,
            date TEXT,
            from_addr TEXT,
            to_addr TEXT,
            cc_addr TEXT,
            subject TEXT,
            body_text TEXT,
            has_attachments INTEGER DEFAULT 0,
            parsed_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS entities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_type TEXT NOT NULL,  -- 'document' or 'email'
            source_id INTEGER NOT NULL,
            entity_type TEXT NOT NULL,  -- 'person', 'organisation', 'keyword', 'date'
            entity_value TEXT NOT NULL,
            context TEXT,               -- surrounding text snippet
            found_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS timeline_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_date TEXT NOT NULL,
            event_type TEXT,            -- 'email', 'court', 'financial', 'incident'
            title TEXT NOT NULL,
            description TEXT,
            source_type TEXT,
            source_id INTEGER,
            tags TEXT                   -- JSON array of tags
        );

        CREATE TABLE IF NOT EXISTS patterns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pattern_name TEXT NOT NULL,
            description TEXT,
            entity_ids TEXT,            -- JSON array of entity IDs
            event_ids TEXT,             -- JSON array of timeline event IDs
            detected_at TEXT NOT NULL,
            confidence REAL DEFAULT 0.0
        );

        CREATE INDEX IF NOT EXISTS idx_docs_type ON documents(file_type);
        CREATE INDEX IF NOT EXISTS idx_emails_date ON emails(date);
        CREATE INDEX IF NOT EXISTS idx_emails_from ON emails(from_addr);
        CREATE INDEX IF NOT EXISTS idx_entities_value ON entities(entity_value);
        CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(entity_type);
        CREATE INDEX IF NOT EXISTS idx_timeline_date ON timeline_events(event_date);
    """)
    conn.commit()


class EvidenceStore:
    def __init__(self, db_path: str, encryption_key: str = ""):
        self.conn = get_connection(db_path, encryption_key)
        init_db(self.conn)

    def close(self):
        self.conn.close()

    # --- Documents ---
    def insert_document(self, file_path, file_name, file_type, source_dir,
                        file_size, file_hash, content_text, metadata=None):
        now = datetime.utcnow().isoformat()
        meta_json = json.dumps(metadata) if metadata else None
        try:
            self.conn.execute(
                """INSERT OR REPLACE INTO documents
                   (file_path, file_name, file_type, source_dir, file_size,
                    file_hash, parsed_at, content_text, metadata_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (file_path, file_name, file_type, source_dir, file_size,
                 file_hash, now, content_text, meta_json)
            )
            self.conn.commit()
            return self.conn.execute(
                "SELECT id FROM documents WHERE file_path=?", (file_path,)
            ).fetchone()[0]
        except Exception as e:
            print(f"[DB] Error inserting document: {e}")
            return None

    # --- Emails ---
    def insert_email(self, file_path, message_id, date, from_addr, to_addr,
                     cc_addr, subject, body_text, has_attachments=False):
        now = datetime.utcnow().isoformat()
        try:
            self.conn.execute(
                """INSERT OR REPLACE INTO emails
                   (file_path, message_id, date, from_addr, to_addr, cc_addr,
                    subject, body_text, has_attachments, parsed_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (file_path, message_id, date, from_addr, to_addr, cc_addr,
                 subject, body_text, 1 if has_attachments else 0, now)
            )
            self.conn.commit()
            return self.conn.execute(
                "SELECT id FROM emails WHERE file_path=?", (file_path,)
            ).fetchone()[0]
        except Exception as e:
            print(f"[DB] Error inserting email: {e}")
            return None

    # --- Entities ---
    def insert_entity(self, source_type, source_id, entity_type, entity_value, context=""):
        now = datetime.utcnow().isoformat()
        self.conn.execute(
            """INSERT INTO entities
               (source_type, source_id, entity_type, entity_value, context, found_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (source_type, source_id, entity_type, entity_value, context, now)
        )
        self.conn.commit()

    # --- Timeline ---
    def insert_event(self, event_date, event_type, title, description="",
                     source_type=None, source_id=None, tags=None):
        tags_json = json.dumps(tags) if tags else None
        self.conn.execute(
            """INSERT INTO timeline_events
               (event_date, event_type, title, description, source_type, source_id, tags)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (event_date, event_type, title, description, source_type, source_id, tags_json)
        )
        self.conn.commit()

    # --- Queries ---
    def search_documents(self, query: str, limit=50):
        return self.conn.execute(
            """SELECT id, file_name, file_type, source_dir, parsed_at,
                      substr(content_text, 1, 500) as snippet
               FROM documents
               WHERE content_text LIKE ? OR file_name LIKE ?
               ORDER BY parsed_at DESC LIMIT ?""",
            (f"%{query}%", f"%{query}%", limit)
        ).fetchall()

    def search_emails(self, query: str, limit=50):
        return self.conn.execute(
            """SELECT id, date, from_addr, to_addr, subject,
                      substr(body_text, 1, 500) as snippet
               FROM emails
               WHERE body_text LIKE ? OR subject LIKE ? OR from_addr LIKE ?
               ORDER BY date DESC LIMIT ?""",
            (f"%{query}%", f"%{query}%", f"%{query}%", limit)
        ).fetchall()

    def get_timeline(self, start_date=None, end_date=None, event_type=None, limit=200):
        sql = "SELECT * FROM timeline_events WHERE 1=1"
        params = []
        if start_date:
            sql += " AND event_date >= ?"
            params.append(start_date)
        if end_date:
            sql += " AND event_date <= ?"
            params.append(end_date)
        if event_type:
            sql += " AND event_type = ?"
            params.append(event_type)
        sql += " ORDER BY event_date ASC LIMIT ?"
        params.append(limit)
        return self.conn.execute(sql, params).fetchall()

    def get_entities(self, entity_type=None, limit=100):
        if entity_type:
            return self.conn.execute(
                "SELECT * FROM entities WHERE entity_type=? ORDER BY entity_value LIMIT ?",
                (entity_type, limit)
            ).fetchall()
        return self.conn.execute(
            "SELECT * FROM entities ORDER BY entity_type, entity_value LIMIT ?",
            (limit,)
        ).fetchall()

    def get_stats(self):
        docs = self.conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        emails = self.conn.execute("SELECT COUNT(*) FROM emails").fetchone()[0]
        entities = self.conn.execute("SELECT COUNT(*) FROM entities").fetchone()[0]
        events = self.conn.execute("SELECT COUNT(*) FROM timeline_events").fetchone()[0]
        return {"documents": docs, "emails": emails, "entities": entities, "events": events}
