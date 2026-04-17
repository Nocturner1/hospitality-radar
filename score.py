"""
Einzelbewertung jedes Artikels via Claude Haiku.
Gibt pro Item ein erweitertes Dict mit Scoring-Feldern zurück.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from openai import OpenAI

from config import (
    SCORE_MODEL,
    SCORE_WEIGHTS,
    THRESHOLD_KEEP,
    THRESHOLD_WATCH,
)

logger = logging.getLogger(__name__)

RawItem = dict[str, Any]
ScoredItem = dict[str, Any]

SCORING_PROMPT = """\
Du bewertest News, Releases und Fachbeiträge für einen wöchentlichen deutschsprachigen Radar zu AI und Automatisierung in Tourismus und Hotellerie.

Zielgruppe: Entscheider in Hotellerie und Tourismus – von Einzelhotels bis Hotelgruppen.

Denke beim Bewerten weit: Ein Artikel muss keinen expliziten Hotelbezug haben, um relevant zu sein.
Auch folgende Themen sind für Hotels strategisch wichtig:
- Airline-Insolvenzen und Marktveränderungen (beeinflussen Nachfrage und Distribution)
- AI-Plattform-News von Google, OpenAI, Anthropic, Microsoft (prägen die Tools von morgen)
- Agentic AI, MCP, Browser-Agenten, AI-Suche (verändern wie Gäste buchen und recherchieren)
- Partnerships zwischen Technologiekonzernen und Hospitality (z.B. Google + Hotelkette)
- Corporate Travel Trends (betreffen MICE und B2B-Segment direkt)
- Neue Modelle, APIs, Features die Hotels in 12–24 Monaten nutzen werden

Sei großzügig bei der Bewertung. Im Zweifel lieber watch als reject.
Nur echte Werbebotschaften ohne Informationswert (z.B. reine Produktanzeigen) ablehnen.

Gib ausschließlich valides JSON zurück – kein Markdown, keine Erklärungen.

Felder:
- relevance_hospitality (1-5): Wie relevant für Hotel-/Tourismusentscheider? Großzügig bewerten.
- novelty (1-5): Wie neu oder überraschend ist das?
- testability_90d (1-5): Kann ein Hotel das in 90 Tagen konkret testen oder beobachten?
- strategic_impact_24m (1-5): Wie groß ist die strategische Bedeutung in 24 Monaten?
- category (one of: distribution, revenue, guest_communication, operations, marketing, crm, agent_booking, ai_platforms, industry_news, other)
- keep_decision (keep, watch, reject)
- short_summary_de (max. 2 Sätze, sachlich)
- why_it_matters_de (max. 2 Sätze – auch indirekter Bezug zur Hotellerie ist gültig)
- action_hint_de (max. 1 Satz – was sollte ein Hotelmanager jetzt tun oder beobachten?)

Entscheidungsregeln:
- keep: relevance_hospitality >= 3 ODER strategic_impact_24m >= 4
- watch: relevance_hospitality >= 2 ODER novelty >= 3
- reject: nur reine Werbung, lokale Randnachrichten ohne strategischen Wert, Duplikate
- Schreibe nüchtern, konkret, ohne Hype. Keine erfundenen Fakten.

INPUT:
Titel: {title}
Quelle: {source}
Datum: {published_at}
URL: {url}
Beschreibung: {description}
"""


def _calculate_score(result: dict) -> float:
    """Berechnet den Gesamtscore aus den vier Einzelwerten."""
    return round(
        result.get("relevance_hospitality", 0) * SCORE_WEIGHTS["relevance_hospitality"]
        + result.get("novelty", 0) * SCORE_WEIGHTS["novelty"]
        + result.get("testability_90d", 0) * SCORE_WEIGHTS["testability_90d"]
        + result.get("strategic_impact_24m", 0) * SCORE_WEIGHTS["strategic_impact_24m"],
        2,
    )


def _decision_from_score(score: float, llm_decision: str) -> str:
    """
    Kombination aus LLM-Entscheidung und Score-Schwellwerten.
    Score hat Vorrang bei Konflikten.
    """
    if score >= THRESHOLD_KEEP:
        return "keep"
    if score >= THRESHOLD_WATCH:
        return "watch"
    return "reject"


def score_item(client: OpenAI, item: RawItem) -> ScoredItem:
    """Bewertet ein einzelnes Item via OpenAI und gibt ein erweitertes Dict zurück."""
    prompt = SCORING_PROMPT.format(
        title=item.get("title", ""),
        source=item.get("source", ""),
        published_at=item.get("published_at", ""),
        url=item.get("url", ""),
        description=item.get("description", ""),
    )
    try:
        message = client.chat.completions.create(
            model=SCORE_MODEL,
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}],
        )
        raw_text = message.choices[0].message.content.strip()

        # JSON aus der Antwort extrahieren (falls doch Markdown dabei)
        json_match = re.search(r"\{.*\}", raw_text, re.DOTALL)
        if not json_match:
            raise ValueError(f"Kein JSON gefunden: {raw_text[:200]}")
        result = json.loads(json_match.group())

    except Exception as exc:
        logger.error("Scoring-Fehler [%s]: %s", item.get("title", "?")[:60], exc, exc_info=True)
        # Fallback: reject
        result = {
            "relevance_hospitality": 1,
            "novelty": 1,
            "testability_90d": 1,
            "strategic_impact_24m": 1,
            "category": "other",
            "keep_decision": "reject",
            "short_summary_de": "",
            "why_it_matters_de": "",
            "action_hint_de": "",
        }

    score = _calculate_score(result)
    decision = _decision_from_score(score, result.get("keep_decision", "reject"))

    return {
        **item,
        "relevance_hospitality": result.get("relevance_hospitality", 1),
        "novelty": result.get("novelty", 1),
        "testability_90d": result.get("testability_90d", 1),
        "strategic_impact_24m": result.get("strategic_impact_24m", 1),
        "score": score,
        "category": result.get("category", "other"),
        "decision": decision,
        "summary_de": result.get("short_summary_de", ""),
        "why_it_matters_de": result.get("why_it_matters_de", ""),
        "action_hint_de": result.get("action_hint_de", ""),
    }


def score_all(items: list[RawItem]) -> list[ScoredItem]:
    """Bewertet alle Items und gibt die vollständige Liste zurück."""
    client = OpenAI()  # liest OPENAI_API_KEY aus Env
    scored: list[ScoredItem] = []
    for i, item in enumerate(items, 1):
        logger.info("  Scoring %d/%d: %s", i, len(items), item.get("title", "")[:60])
        scored.append(score_item(client, item))
    return scored
