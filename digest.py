"""
Wochendigest erzeugen:
  - Nimmt alle keep/watch Items
  - Schickt sie an Claude Sonnet
  - Gibt ein strukturiertes Dict zurück (für notion_writer.py)
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

import anthropic

from config import DIGEST_MODEL, MAX_TOP_STORIES, MAX_WATCHLIST

logger = logging.getLogger(__name__)

ScoredItem = dict[str, Any]

DIGEST_PROMPT = """\
Du erstellst einen wöchentlichen Radar für AI und Automatisierung in Tourismus und Hotellerie.

Ziel:
Aus kuratierten Einzelmeldungen eine prägnante deutschsprachige Review-Ausgabe erstellen.

Nutze NUR die gelieferten Items. Keine Halluzinationen. Keine neuen Fakten erfinden. Kein Hype.

Gib deine Antwort ausschließlich als valides JSON zurück – kein Markdown, keine Erklärungen.

JSON-Schema:
{{
  "executive_summary": "max. 5 Sätze mit dem roten Faden der Woche",
  "top_stories": [
    {{
      "title": "Titel der Meldung",
      "what_happened": "Was ist passiert?",
      "why_relevant": "Warum ist das für Hotels/Tourismus relevant?",
      "action": "Was sollte man konkret testen oder beobachten?"
    }}
  ],
  "tools": ["Tool/Programm 1 – kurze Beschreibung", "Tool 2 …"],
  "agent_booking_watch": "Zusammenfassung aller MCP/WebMCP/Suchagenten/Booking-Agent-Themen dieser Woche",
  "experiments": [
    "Konkretes Experiment 1 (niedrig Aufwand)",
    "Konkretes Experiment 2",
    "Konkretes Experiment 3"
  ],
  "watchlist": [
    {{
      "title": "Thema",
      "comment": "Satz 1: Warum beobachten? Satz 2: Was müsste passieren, damit es nächste Woche relevant genug wird?"
    }}
  ]
}}

Regeln:
- top_stories: max. {max_stories} Einträge, nur decision=keep
- watchlist: max. {max_watchlist} Einträge, nur decision=watch
- tools: separate Rubrik für neue Tools, Features, APIs, Integrationen
- agent_booking_watch: eigene Würdigung für MCP, WebMCP, Suchagenten, Browser-Agenten, buchungsfähige Assistenten
- Schreibe auf Deutsch, knapp, sachlich, lesbar

INPUT ITEMS (JSON):
{items_json}
"""

WATCHLIST_ONLY_PROMPT = """\
Du erhältst Items mit mittlerer Relevanz.
Schreibe für jedes Item genau 2 Sätze:
1. Warum beobachten?
2. Was müsste passieren, damit es nächste Woche relevant genug wird?

Schreibe sachlich und konkret.
Gib deine Antwort als JSON-Array zurück:
[{{"title": "...", "comment": "Satz 1. Satz 2."}}]

INPUT:
{items_json}
"""


def _items_to_json(items: list[ScoredItem]) -> str:
    """Kompakte JSON-Darstellung der Items für den Prompt."""
    slim = [
        {
            "title": i.get("title", ""),
            "source": i.get("source", ""),
            "url": i.get("url", ""),
            "category": i.get("category", ""),
            "score": i.get("score", 0),
            "decision": i.get("decision", ""),
            "summary_de": i.get("summary_de", ""),
            "why_it_matters_de": i.get("why_it_matters_de", ""),
            "action_hint_de": i.get("action_hint_de", ""),
        }
        for i in items
    ]
    return json.dumps(slim, ensure_ascii=False, indent=2)


def generate_digest(scored_items: list[ScoredItem]) -> dict:
    """
    Erzeugt den strukturierten Wochendigest.
    Gibt ein Dict zurück, das notion_writer.create_review_page() erwartet.
    """
    client = anthropic.Anthropic()

    keep_items = [i for i in scored_items if i.get("decision") == "keep"]
    watch_items = [i for i in scored_items if i.get("decision") == "watch"]

    logger.info(
        "Digest: %d keep-Items, %d watch-Items",
        len(keep_items),
        len(watch_items),
    )

    if not keep_items and not watch_items:
        logger.warning("Keine Items für den Digest vorhanden.")
        return {
            "executive_summary": "Keine relevanten Meldungen diese Woche.",
            "top_stories": [],
            "tools": [],
            "agent_booking_watch": "",
            "experiments": [],
            "watchlist": [],
        }

    # Alle relevanten Items zusammenführen (keep zuerst)
    digest_items = keep_items + watch_items

    prompt = DIGEST_PROMPT.format(
        max_stories=MAX_TOP_STORIES,
        max_watchlist=MAX_WATCHLIST,
        items_json=_items_to_json(digest_items),
    )

    try:
        message = client.messages.create(
            model=DIGEST_MODEL,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        raw_text = message.content[0].text.strip()
        json_match = re.search(r"\{.*\}", raw_text, re.DOTALL)
        if not json_match:
            raise ValueError(f"Kein JSON im Digest: {raw_text[:300]}")
        result = json.loads(json_match.group())
        logger.info("Digest erfolgreich generiert.")
        return result

    except Exception as exc:
        logger.error("Digest-Fehler: %s", exc)
        # Minimaler Fallback
        return {
            "executive_summary": "Digest konnte nicht automatisch erstellt werden. Bitte manuell prüfen.",
            "top_stories": [
                {
                    "title": i.get("title", ""),
                    "what_happened": i.get("summary_de", ""),
                    "why_relevant": i.get("why_it_matters_de", ""),
                    "action": i.get("action_hint_de", ""),
                }
                for i in keep_items[:MAX_TOP_STORIES]
            ],
            "tools": [],
            "agent_booking_watch": "",
            "experiments": [],
            "watchlist": [
                {"title": i.get("title", ""), "comment": i.get("summary_de", "")}
                for i in watch_items[:MAX_WATCHLIST]
            ],
        }
