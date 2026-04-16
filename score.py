"""
Einzelbewertung jedes Artikels via Claude Haiku.
Gibt pro Item ein erweitertes Dict mit Scoring-Feldern zurück.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

import anthropic

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

Zielgruppe:
Entscheider in Hotellerie und Tourismus.

Bewerte ausschließlich aus Sicht von realem Nutzen für Hotels, Hotelgruppen, touristische Betriebe, Destinationsorganisationen und Travel-Tech-nahe Teams.

Bevorzuge Themen aus diesen Bereichen:
- Direktbuchung
- Gästekommunikation
- CRM / Personalisierung
- Revenue / Distribution
- Marketing Automation
- interne Prozessautomatisierung
- Contact Center / Reservation / Front Office
- Agentic AI
- MCP / WebMCP / AI-Agenten im Buchungskontext
- neue relevante Tools, Programme, APIs, Produktfeatures und Partnerschaften

Bewerte das folgende Item und gib ausschließlich valides JSON zurück – kein Markdown, keine Erklärungen.

Felder:
- relevance_hospitality (1-5)
- novelty (1-5)
- testability_90d (1-5)
- strategic_impact_24m (1-5)
- category (one of: distribution, revenue, guest_communication, operations, marketing, crm, agent_booking, ai_platforms, other)
- keep_decision (keep, watch, reject)
- short_summary_de (max. 2 Sätze)
- why_it_matters_de (max. 2 Sätze)
- action_hint_de (max. 1 Satz, konkret und handlungsorientiert)

Regeln:
- Keine generischen AI-News ohne klaren Hotel-/Tourismusbezug in keep einstufen.
- Themen rund um MCP, WebMCP, Suchagenten, Browser-Agenten und buchungsfähige Assistenten besonders sorgfältig prüfen.
- Wenn ein Thema eher strategisch als sofort testbar ist, darf es trotzdem keep sein, wenn die langfristige Relevanz hoch ist.
- Schreibe nüchtern, konkret und ohne Hype.

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


def score_item(client: anthropic.Anthropic, item: RawItem) -> ScoredItem:
    """Bewertet ein einzelnes Item via Claude und gibt ein erweitertes Dict zurück."""
    prompt = SCORING_PROMPT.format(
        title=item.get("title", ""),
        source=item.get("source", ""),
        published_at=item.get("published_at", ""),
        url=item.get("url", ""),
        description=item.get("description", ""),
    )
    try:
        message = client.messages.create(
            model=SCORE_MODEL,
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}],
        )
        raw_text = message.content[0].text.strip()

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
    client = anthropic.Anthropic()  # liest ANTHROPIC_API_KEY aus Env
    scored: list[ScoredItem] = []
    for i, item in enumerate(items, 1):
        logger.info("  Scoring %d/%d: %s", i, len(items), item.get("title", "")[:60])
        scored.append(score_item(client, item))
    return scored
