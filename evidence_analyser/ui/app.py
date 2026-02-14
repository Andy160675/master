"""
Sovereign Evidence Analyser — Gradio UI
Local browser interface. Runs on 127.0.0.1 only.
"""
import gradio as gr
import json
from pathlib import Path

from ..config import APP_TITLE, APP_HOST, APP_PORT, DEFAULT_SOURCES
from ..db.store import EvidenceStore
from ..parsers.email_parser import scan_email_directory
from ..parsers.document_parser import scan_document_directory
from ..engine.pattern_engine import extract_entities, detect_patterns
from ..engine.timeline import build_timeline_from_emails, build_timeline_from_documents


def create_app(store: EvidenceStore) -> gr.Blocks:
    with gr.Blocks(title=APP_TITLE) as app:
        gr.Markdown(f"# {APP_TITLE}")
        gr.Markdown("**100% offline** — all data stays on this machine. No cloud. No API calls.")

        with gr.Tab("Dashboard"):
            stats_display = gr.JSON(label="Evidence Statistics")
            refresh_btn = gr.Button("Refresh Stats", variant="primary")

            def get_stats():
                return store.get_stats()

            refresh_btn.click(fn=get_stats, outputs=stats_display)
            app.load(fn=get_stats, outputs=stats_display)

        with gr.Tab("Ingest"):
            gr.Markdown("### Import Evidence Sources")
            gr.Markdown("Scan directories to parse emails and documents into the local database.")

            with gr.Row():
                email_dir = gr.Textbox(
                    label="Email Directory (.eml files)",
                    value=DEFAULT_SOURCES.get("emails", ""),
                )
                email_btn = gr.Button("Ingest Emails", variant="primary")

            with gr.Row():
                doc_dir = gr.Textbox(
                    label="Document Directory (PDF/DOCX/TXT)",
                    value=DEFAULT_SOURCES.get("evidence_annexes", ""),
                )
                doc_btn = gr.Button("Ingest Documents", variant="primary")

            ingest_log = gr.Textbox(label="Ingest Log", lines=10, interactive=False)

            def ingest_emails(directory):
                if not directory or not Path(directory).exists():
                    return "Directory not found."
                emails = scan_email_directory(directory)
                count = 0
                for em in emails:
                    eid = store.insert_email(**em)
                    if eid:
                        entities = extract_entities(
                            (em.get("subject", "") + " " + em.get("body_text", "")),
                            "email", eid
                        )
                        for ent in entities:
                            store.insert_entity(**ent)
                        count += 1
                build_timeline_from_emails(store)
                return f"Ingested {count} emails. Entities extracted. Timeline updated."

            def ingest_documents(directory):
                if not directory or not Path(directory).exists():
                    return "Directory not found."
                docs = scan_document_directory(directory)
                count = 0
                for doc in docs:
                    did = store.insert_document(**doc)
                    if did:
                        entities = extract_entities(
                            doc.get("content_text", ""),
                            "document", did
                        )
                        for ent in entities:
                            store.insert_entity(**ent)
                        count += 1
                build_timeline_from_documents(store)
                return f"Ingested {count} documents. Entities extracted. Timeline updated."

            email_btn.click(fn=ingest_emails, inputs=email_dir, outputs=ingest_log)
            doc_btn.click(fn=ingest_documents, inputs=doc_dir, outputs=ingest_log)

        with gr.Tab("Search"):
            gr.Markdown("### Search Evidence")
            search_input = gr.Textbox(label="Search query", placeholder="e.g. coercive control, EDF, DSAR...")
            search_btn = gr.Button("Search", variant="primary")

            with gr.Row():
                doc_results = gr.Dataframe(
                    headers=["ID", "File", "Type", "Snippet"],
                    label="Documents",
                )
                email_results = gr.Dataframe(
                    headers=["ID", "Date", "From", "Subject", "Snippet"],
                    label="Emails",
                )

            def do_search(query):
                if not query:
                    return [], []
                docs = store.search_documents(query)
                emails = store.search_emails(query)
                doc_rows = [[r["id"], r["file_name"], r["file_type"], r["snippet"][:150]] for r in docs]
                email_rows = [[r["id"], r["date"], r["from_addr"], r["subject"], r["snippet"][:150]] for r in emails]
                return doc_rows, email_rows

            search_btn.click(fn=do_search, inputs=search_input, outputs=[doc_results, email_results])

        with gr.Tab("Timeline"):
            gr.Markdown("### Chronological Event Timeline")
            with gr.Row():
                tl_start = gr.Textbox(label="Start date (YYYY-MM-DD)", value="2019-01-01")
                tl_end = gr.Textbox(label="End date (YYYY-MM-DD)", value="2026-12-31")
                tl_type = gr.Dropdown(
                    label="Event type",
                    choices=["all", "email", "court", "financial", "incident", "communication", "document"],
                    value="all",
                )
            tl_btn = gr.Button("Load Timeline", variant="primary")
            timeline_table = gr.Dataframe(
                headers=["Date", "Type", "Title", "Description"],
                label="Events",
            )

            def load_timeline(start, end, etype):
                etype = None if etype == "all" else etype
                events = store.get_timeline(start or None, end or None, etype)
                return [[e["event_date"], e["event_type"], e["title"], e["description"]] for e in events]

            tl_btn.click(fn=load_timeline, inputs=[tl_start, tl_end, tl_type], outputs=timeline_table)

        with gr.Tab("Entities"):
            gr.Markdown("### Extracted Entities")
            ent_type = gr.Dropdown(
                label="Entity type",
                choices=["all", "organisation", "keyword", "date", "email_address", "financial_amount", "person"],
                value="all",
            )
            ent_btn = gr.Button("Load Entities", variant="primary")
            entity_table = gr.Dataframe(
                headers=["Type", "Value", "Context"],
                label="Entities",
            )

            def load_entities(etype):
                etype = None if etype == "all" else etype
                ents = store.get_entities(etype)
                return [[e["entity_type"], e["entity_value"], (e["context"] or "")[:150]] for e in ents]

            ent_btn.click(fn=load_entities, inputs=ent_type, outputs=entity_table)

        with gr.Tab("Patterns"):
            gr.Markdown("### Detected Patterns")
            gr.Markdown("Cross-document behavioural patterns, recurring themes, and communication clusters.")
            pattern_btn = gr.Button("Detect Patterns", variant="primary")
            pattern_table = gr.Dataframe(
                headers=["Pattern", "Description", "Confidence"],
                label="Patterns",
            )

            def run_patterns():
                patterns = detect_patterns(store)
                return [[p["pattern_name"], p["description"], f"{p['confidence']:.0%}"] for p in patterns]

            pattern_btn.click(fn=run_patterns, outputs=pattern_table)

    return app


def launch(store: EvidenceStore):
    app = create_app(store)
    app.launch(server_name=APP_HOST, server_port=APP_PORT, share=False, theme=gr.themes.Soft())
