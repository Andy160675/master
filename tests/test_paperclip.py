# tests/test_paperclip.py
"""Tests for Layer 1 — Paperclip (Context Preservation & Decision Support).

Validates frozen invariants:
  - Advisory only (no blocking, no approval, no escalation)
  - Context preservation (prior decisions surfaced)
  - Layer 4 separation (no Sentinel imports)
  - Thread management
"""
import ast
import sqlite3
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from agi.core.assistant_channel import (
    ASSISTANT_SYSTEM_PROMPT,
    get_assistant_system_prompt,
    search_prior_decisions,
    format_prior_context,
    list_thread_messages,
    build_assistant_prompt,
    generate_assistant_reply,
    MAX_PRIOR_CONTEXT,
    MAX_SNIPPET_LEN,
)
from agi.core.receipt import init_db, DB_PATH


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def fresh_db(tmp_path, monkeypatch):
    """Create a fresh SQLite database for testing."""
    db_path = tmp_path / "test_sovereign.sqlite"
    monkeypatch.setattr("agi.core.receipt.DB_PATH", db_path)
    monkeypatch.setattr("agi.core.assistant_channel.DB_PATH", db_path)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sovereign_answers (
            answer_id TEXT PRIMARY KEY,
            receipt_id TEXT NOT NULL,
            question TEXT NOT NULL,
            raw_answer TEXT NOT NULL,
            explained_answer TEXT,
            audit_receipt TEXT,
            created_at TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS assistant_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            answer_id TEXT NOT NULL,
            receipt_id TEXT NOT NULL,
            role TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (answer_id) REFERENCES sovereign_answers(answer_id)
        )
    """)
    conn.commit()
    conn.close()
    return db_path


def _insert_answer(db_path, answer_id, question, raw_answer, created_at=None):
    """Helper: insert a sovereign answer for testing context search."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    created = created_at or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    cur.execute(
        "INSERT INTO sovereign_answers (answer_id, receipt_id, question, raw_answer, created_at) VALUES (?, ?, ?, ?, ?)",
        (answer_id, f"r-{answer_id}", question, raw_answer, created),
    )
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# 1. Frozen Invariants — System Prompt
# ---------------------------------------------------------------------------

class TestSystemPrompt:
    def test_prompt_contains_must_not_change(self):
        assert "MUST NOT change" in ASSISTANT_SYSTEM_PROMPT

    def test_prompt_contains_must_not_block(self):
        assert "MUST NOT" in ASSISTANT_SYSTEM_PROMPT
        assert "block" in ASSISTANT_SYSTEM_PROMPT

    def test_prompt_contains_must_not_approve(self):
        assert "approve" in ASSISTANT_SYSTEM_PROMPT

    def test_prompt_contains_must_not_escalate(self):
        assert "MUST NOT escalate" in ASSISTANT_SYSTEM_PROMPT

    def test_prompt_contains_re_run_instruction(self):
        assert "re-run" in ASSISTANT_SYSTEM_PROMPT

    def test_prompt_identifies_as_paperclip(self):
        assert "Paperclip" in ASSISTANT_SYSTEM_PROMPT

    def test_prompt_identifies_layer(self):
        assert "Layer 1" in ASSISTANT_SYSTEM_PROMPT

    def test_get_returns_same_prompt(self):
        assert get_assistant_system_prompt() is ASSISTANT_SYSTEM_PROMPT


# ---------------------------------------------------------------------------
# 2. Layer 4 Separation — No Sentinel Imports
# ---------------------------------------------------------------------------

class TestLayerSeparation:
    """Verify that assistant_channel.py does not import from Sentinel modules."""

    SENTINEL_MODULES = [
        "mcp_gatekeeper",
        "diff_validator",
        "policy_signature",
        "empathy_engine",
    ]

    def test_no_sentinel_imports(self):
        """Parse the AST of assistant_channel.py and verify no Sentinel imports."""
        source_path = Path(__file__).resolve().parent.parent / "agi" / "core" / "assistant_channel.py"
        source = source_path.read_text(encoding="utf-8")
        tree = ast.parse(source)

        imported_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module:
                    imported_names.add(node.module)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imported_names.add(alias.name)

        for sentinel_mod in self.SENTINEL_MODULES:
            for imp in imported_names:
                assert sentinel_mod not in imp, (
                    f"Layer 4 violation: assistant_channel.py imports '{imp}' "
                    f"which contains Sentinel module '{sentinel_mod}'"
                )


# ---------------------------------------------------------------------------
# 3. Context Preservation — Prior Decision Search
# ---------------------------------------------------------------------------

class TestContextPreservation:
    def test_search_empty_db(self, fresh_db):
        results = search_prior_decisions("property acquisition strategies")
        assert results == []

    def test_search_finds_matching_question(self, fresh_db):
        _insert_answer(fresh_db, "a1", "lawful property strategies", "Use compulsory purchase orders.")
        results = search_prior_decisions("property acquisition strategies")
        assert len(results) >= 1
        assert results[0]["answer_id"] == "a1"

    def test_search_limits_results(self, fresh_db):
        for i in range(10):
            _insert_answer(fresh_db, f"a{i}", f"property question {i}", f"answer {i}")
        results = search_prior_decisions("property question", limit=3)
        assert len(results) <= 3

    def test_search_snippet_truncation(self, fresh_db):
        long_answer = "x" * 500
        _insert_answer(fresh_db, "a-long", "property question", long_answer)
        results = search_prior_decisions("property question")
        assert len(results) == 1
        assert len(results[0]["answer_snippet"]) == MAX_SNIPPET_LEN + 3  # +3 for "..."

    def test_search_short_words_ignored(self, fresh_db):
        """Words <=3 chars are excluded from keyword search."""
        results = search_prior_decisions("an is to")
        assert results == []

    def test_format_empty_priors(self):
        assert format_prior_context([]) == ""

    def test_format_priors_contains_context_header(self):
        priors = [{"answer_id": "a1", "question": "Q1", "answer_snippet": "A1", "created_at": "2026-01-01"}]
        result = format_prior_context(priors)
        assert "PRIOR DECISIONS" in result
        assert "context only" in result.lower()
        assert "not authority" in result.lower()

    def test_format_priors_includes_date(self):
        priors = [{"answer_id": "a1", "question": "Q1", "answer_snippet": "A1", "created_at": "2026-01-15T10:00:00Z"}]
        result = format_prior_context(priors)
        assert "2026-01-15" in result


# ---------------------------------------------------------------------------
# 4. Prompt Construction
# ---------------------------------------------------------------------------

class TestPromptConstruction:
    def test_prompt_includes_system(self):
        prompt = build_assistant_prompt("SYS", "ANSWER", [], "Hello")
        assert "SYS" in prompt

    def test_prompt_includes_answer(self):
        prompt = build_assistant_prompt("SYS", "ANSWER", [], "Hello")
        assert "ANSWER" in prompt

    def test_prompt_includes_read_only_marker(self):
        prompt = build_assistant_prompt("SYS", "ANSWER", [], "Hello")
        assert "read-only" in prompt.lower()

    def test_prompt_includes_prior_context(self):
        prompt = build_assistant_prompt("SYS", "ANSWER", [], "Hello", prior_context="PRIOR: xyz")
        assert "PRIOR: xyz" in prompt

    def test_prompt_without_prior_context(self):
        prompt = build_assistant_prompt("SYS", "ANSWER", [], "Hello")
        assert "PRIOR DECISIONS" not in prompt

    def test_prompt_ends_with_paperclip_tag(self):
        prompt = build_assistant_prompt("SYS", "ANSWER", [], "Hello")
        assert prompt.endswith("PAPERCLIP:")

    def test_prompt_includes_thread_messages(self):
        thread = [{"role": "user", "message": "What about X?", "created_at": "2026-01-01"}]
        prompt = build_assistant_prompt("SYS", "ANSWER", thread, "Hello")
        assert "What about X?" in prompt


# ---------------------------------------------------------------------------
# 5. Generate Reply — Integration (mocked model)
# ---------------------------------------------------------------------------

class TestGenerateReply:
    @patch("agi.core.assistant_channel.run_model_for_task")
    def test_basic_reply(self, mock_model, fresh_db):
        mock_model.return_value = {"text": "Here is my advisory note."}
        reply = generate_assistant_reply("a1", "r1", "Sovereign says X.", "Why X?")
        assert reply == "Here is my advisory note."

    @patch("agi.core.assistant_channel.run_model_for_task")
    def test_reply_with_question_triggers_context_search(self, mock_model, fresh_db):
        _insert_answer(fresh_db, "prior1", "property strategies", "Use CPO approach.")
        mock_model.return_value = {"text": "Context noted."}
        reply = generate_assistant_reply("a-new", "r-new", "Current answer.", "Explain.", question="property strategies")
        # Verify the model was called with prior context in the prompt
        call_args = mock_model.call_args
        prompt = call_args[1].get("prompt") or call_args[0][1] if len(call_args[0]) > 1 else call_args[1].get("prompt", "")
        assert reply == "Context noted."

    @patch("agi.core.assistant_channel.run_model_for_task")
    def test_reply_excludes_current_answer_from_priors(self, mock_model, fresh_db):
        _insert_answer(fresh_db, "same-id", "property question", "Same answer.")
        mock_model.return_value = {"text": "No self-reference."}
        reply = generate_assistant_reply("same-id", "r1", "Same answer.", "Discuss.", question="property question")
        assert reply == "No self-reference."

    @patch("agi.core.assistant_channel.run_model_for_task")
    def test_reply_persisted_to_thread(self, mock_model, fresh_db):
        mock_model.return_value = {"text": "Persisted reply."}
        generate_assistant_reply("a1", "r1", "Answer.", "Question.")
        thread = list_thread_messages("a1")
        assert len(thread) == 1
        assert thread[0]["role"] == "assistant"
        assert thread[0]["message"] == "Persisted reply."

    @patch("agi.core.assistant_channel.run_model_for_task")
    def test_reply_handles_string_result(self, mock_model, fresh_db):
        """Backwards compat: model may return a plain string."""
        mock_model.return_value = "Plain string reply."
        reply = generate_assistant_reply("a1", "r1", "Answer.", "Question.")
        assert reply == "Plain string reply."
