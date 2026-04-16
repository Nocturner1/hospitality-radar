"""
RSS-Feeds abrufen und auf den Zeitraum der letzten N Tage filtern.
Gibt eine flache Liste von Rohartikeln zurück.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Any

import feedparser
import requests
from dateutil import parser as dateparser

from config import Source, LOOKBACK_DAYS

logger = logging.getLogger(__name__)

# Artikel-Schema (alle Keys sind immer vorhanden, ggf. leer)
RawItem = dict[str, Any]


def _parse_date(entry: Any) -> datetime | None:
    """Versucht, ein Datum aus einem feedparser-Entry zu lesen."""
    for attr in ("published", "updated", "created"):
        raw = getattr(entry, attr, None)
        if raw:
            try:
                return dateparser.parse(raw).astimezone(timezone.utc)
            except Exception:
                continue
    # feedparser kann das Datum auch als struct_time liefern
    for attr in ("published_parsed", "updated_parsed"):
        t = getattr(entry, attr, None)
        if t:
            try:
                return datetime(*t[:6], tzinfo=timezone.utc)
            except Exception:
                continue
    return None


def fetch_source(source: Source, cutoff: datetime) -> list[RawItem]:
    """Lädt einen einzelnen RSS-Feed und gibt Artikel nach `cutoff` zurück."""
    items: list[RawItem] = []
    try:
        # Timeout & User-Agent, damit Feeds nicht blockieren
        resp = requests.get(
            source.rss_url,
            timeout=15,
            headers={"User-Agent": "HospitalityRadarBot/1.0"},
        )
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)
    except Exception as exc:
        logger.warning("Feed-Fehler [%s]: %s", source.name, exc)
        return items

    for entry in feed.entries:
        pub_date = _parse_date(entry)
        if pub_date and pub_date < cutoff:
            continue  # zu alt

        # Kurzbeschreibung: summary bevorzugen, sonst content
        description = getattr(entry, "summary", "") or ""
        if not description:
            content = getattr(entry, "content", [])
            if content:
                description = content[0].get("value", "")
        # HTML-Tags grob entfernen (kein BeautifulSoup nötig)
        import re
        description = re.sub(r"<[^>]+>", " ", description).strip()
        description = re.sub(r"\s+", " ", description)[:600]  # auf 600 Zeichen kürzen

        items.append(
            {
                "title": getattr(entry, "title", "").strip(),
                "url": getattr(entry, "link", "").strip(),
                "source": source.name,
                "tier": source.tier,
                "published_at": pub_date.isoformat() if pub_date else "",
                "description": description,
            }
        )

    logger.info("  [%s] %d Artikel (Tier %s)", source.name, len(items), source.tier)
    return items


def fetch_all(sources: list[Source], lookback_days: int = LOOKBACK_DAYS) -> list[RawItem]:
    """Alle Quellen abfragen und Ergebnisse zusammenführen."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)
    logger.info("Lade Feeds (Cutoff: %s) …", cutoff.strftime("%Y-%m-%d"))
    all_items: list[RawItem] = []
    for source in sources:
        all_items.extend(fetch_source(source, cutoff))
    logger.info("Gesamt Rohfunde: %d", len(all_items))
    return all_items
