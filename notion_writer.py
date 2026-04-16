"""
Notion-Integration:
  - Schreibt bewertete Items in die Rohdatenbank
  - Erstellt die wöchentliche Review-Seite mit Blöcken
"""

from __future__ import annotations

import logging
import os
from typing import Any

from notion_client import Client

logger = logging.getLogger(__name__)

ScoredItem = dict[str, Any]


def _rich_text(text: str) -> list[dict]:
    """Hilfsfunktion: Notion rich_text Objekt."""
    return [{"type": "text", "text": {"content": str(text)[:2000]}}]


def write_item_to_db(notion: Client, db_id: str, item: ScoredItem, week_id: str) -> str | None:
    """Legt einen Datenbankeintrag an. Gibt die neue Page-ID zurück."""
    try:
        page = notion.pages.create(
            parent={"database_id": db_id},
            properties={
                "Name": {
                    "title": _rich_text(item.get("title", "Kein Titel"))
                },
                "URL": {
                    "url": item.get("url") or None
                },
                "Source": {
                    "select": {"name": item.get("source", "Unbekannt")[:100]}
                },
                "Published": {
                    "date": {"start": item["published_at"][:10]} if item.get("published_at") else None
                },
                "Week ID": {
                    "rich_text": _rich_text(week_id)
                },
                "Category": {
                    "select": {"name": item.get("category", "other")}
                },
                "Relevance Hospitality": {
                    "number": item.get("relevance_hospitality")
                },
                "Novelty": {
                    "number": item.get("novelty")
                },
                "Testability 90d": {
                    "number": item.get("testability_90d")
                },
                "Strategic Impact 24m": {
                    "number": item.get("strategic_impact_24m")
                },
                "Score": {
                    "number": item.get("score")
                },
                "Decision": {
                    "select": {"name": item.get("decision", "reject")}
                },
                "Summary DE": {
                    "rich_text": _rich_text(item.get("summary_de", ""))
                },
                "Why It Matters DE": {
                    "rich_text": _rich_text(item.get("why_it_matters_de", ""))
                },
                "Action Hint DE": {
                    "rich_text": _rich_text(item.get("action_hint_de", ""))
                },
                "Reviewed": {
                    "checkbox": False
                },
            },
        )
        return page["id"]
    except Exception as exc:
        logger.error("Notion DB Fehler [%s]: %s", item.get("title", "?")[:50], exc)
        return None


def write_all_items(items: list[ScoredItem], week_id: str) -> None:
    """Schreibt alle Items in die Notion-Datenbank."""
    notion = Client(auth=os.environ["NOTION_API_KEY"])
    db_id = os.environ["NOTION_DATABASE_ID"]

    logger.info("Schreibe %d Items in Notion-Datenbank …", len(items))
    for i, item in enumerate(items, 1):
        page_id = write_item_to_db(notion, db_id, item, week_id)
        status = "OK" if page_id else "FEHLER"
        logger.info("  [%d/%d] %s – %s", i, len(items), item.get("title", "")[:50], status)


# ---------------------------------------------------------------------------
# Review-Seite erstellen
# ---------------------------------------------------------------------------

def _heading2(text: str) -> dict:
    return {
        "object": "block",
        "type": "heading_2",
        "heading_2": {"rich_text": _rich_text(text)},
    }


def _heading3(text: str) -> dict:
    return {
        "object": "block",
        "type": "heading_3",
        "heading_3": {"rich_text": _rich_text(text)},
    }


def _paragraph(text: str) -> dict:
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {"rich_text": _rich_text(text)},
    }


def _bulleted(text: str) -> dict:
    return {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {"rich_text": _rich_text(text)},
    }


def _divider() -> dict:
    return {"object": "block", "type": "divider", "divider": {}}


def create_review_page(digest: dict, week_id: str, week_label: str) -> str | None:
    """
    Erstellt eine neue Notion-Seite unter dem Reviews-Parent.
    `digest` ist das strukturierte Dict aus digest.py.
    Gibt die Page-ID zurück.
    """
    notion = Client(auth=os.environ["NOTION_API_KEY"])
    parent_id = os.environ["NOTION_REVIEWS_PAGE_ID"]

    title = f"Hospitality AI Watch – {week_label}"

    try:
        page = notion.pages.create(
            parent={"page_id": parent_id},
            properties={
                "title": {"title": _rich_text(title)}
            },
        )
        page_id = page["id"]
    except Exception as exc:
        logger.error("Review-Seite anlegen fehlgeschlagen: %s", exc)
        return None

    # Blöcke zusammenbauen
    blocks: list[dict] = []

    # 1. Executive Summary
    blocks.append(_heading2("1. Executive Summary"))
    blocks.append(_paragraph(digest.get("executive_summary", "")))
    blocks.append(_divider())

    # 2. Top-Meldungen
    blocks.append(_heading2("2. Top-Meldungen"))
    for story in digest.get("top_stories", []):
        blocks.append(_heading3(story.get("title", "")))
        blocks.append(_bulleted(f"Was ist passiert? {story.get('what_happened', '')}"))
        blocks.append(_bulleted(f"Warum relevant? {story.get('why_relevant', '')}"))
        blocks.append(_bulleted(f"Was testen/beobachten? {story.get('action', '')}"))
    blocks.append(_divider())

    # 3. Tools & Programme
    blocks.append(_heading2("3. Tools & Programme"))
    for tool in digest.get("tools", []):
        blocks.append(_bulleted(tool))
    blocks.append(_divider())

    # 4. Agent Booking Watch
    blocks.append(_heading2("4. Agent Booking Watch"))
    blocks.append(_paragraph(digest.get("agent_booking_watch", "")))
    blocks.append(_divider())

    # 5. Was Hotels jetzt testen sollten
    blocks.append(_heading2("5. Was Hotels jetzt testen sollten"))
    for experiment in digest.get("experiments", []):
        blocks.append(_bulleted(experiment))
    blocks.append(_divider())

    # 6. Watchlist
    blocks.append(_heading2("6. Watchlist"))
    for watch_item in digest.get("watchlist", []):
        blocks.append(_heading3(watch_item.get("title", "")))
        blocks.append(_paragraph(watch_item.get("comment", "")))
    blocks.append(_divider())

    # 7. Rohdaten-Verweis
    blocks.append(_heading2("7. Rohdaten"))
    blocks.append(_paragraph(f"Woche: {week_id} – Alle Einträge in der Datenbank 'AI Hospitality Radar Items' filtern."))

    # Blöcke in Chunks von 100 anhängen (Notion-Limit)
    try:
        for i in range(0, len(blocks), 100):
            notion.blocks.children.append(
                block_id=page_id,
                children=blocks[i : i + 100],
            )
        logger.info("Review-Seite erstellt: %s (ID: %s)", title, page_id)
        return page_id
    except Exception as exc:
        logger.error("Blöcke anhängen fehlgeschlagen: %s", exc)
        return page_id  # Seite existiert trotzdem
