"""
Bereinigung und Deduplizierung der Rohfunde:
  1. Leere Einträge entfernen
  2. Exakte URL-Duplikate entfernen (UTM-Parameter werden vorher gestripped)
  3. Near-Duplicate-Titel (Levenshtein ≥ 85 %) zusammenführen
  4. Auf MAX_RAW_ITEMS begrenzen (Tier-A zuerst)
"""

from __future__ import annotations

import re
from typing import Any

from config import MAX_RAW_ITEMS

RawItem = dict[str, Any]


def _strip_utm(url: str) -> str:
    """Entfernt UTM- und andere Tracking-Parameter aus einer URL."""
    url = re.sub(r"[?&](utm_[^&=]+=?[^&]*)", "", url)
    url = re.sub(r"[?&](ref|source|medium|campaign)=[^&]*", "", url)
    url = url.rstrip("?&")
    return url


def _simple_similarity(a: str, b: str) -> float:
    """
    Schnelle Zeichenübereinstimmung (kein difflib wegen Performance).
    Gibt 0.0–1.0 zurück.
    """
    a, b = a.lower().strip(), b.lower().strip()
    if a == b:
        return 1.0
    shorter, longer = (a, b) if len(a) <= len(b) else (b, a)
    if not longer:
        return 0.0
    # Sliding-window gemeinsame Zeichen (Bigrams)
    def bigrams(s: str) -> set[str]:
        return {s[i : i + 2] for i in range(len(s) - 1)}

    bg_a, bg_b = bigrams(shorter), bigrams(longer)
    if not bg_a or not bg_b:
        return 0.0
    overlap = len(bg_a & bg_b)
    return 2.0 * overlap / (len(bg_a) + len(bg_b))


def deduplicate(items: list[RawItem]) -> list[RawItem]:
    """Gibt eine bereinigte, deduplizierte Liste zurück."""
    # 1. Leere Einträge raus
    items = [i for i in items if i.get("title") and i.get("url")]

    # 2. UTM-Parameter aus URL entfernen + URL-Deduplizierung
    seen_urls: set[str] = set()
    cleaned: list[RawItem] = []
    for item in items:
        clean_url = _strip_utm(item["url"])
        item["url"] = clean_url
        if clean_url not in seen_urls:
            seen_urls.add(clean_url)
            cleaned.append(item)
    items = cleaned

    # 3. Near-Duplicate-Titel (Schwellwert 85 %) – behalte den ersten (Tier A bevorzugt)
    # Sortiere Tier A zuerst, damit bei Kollision immer die hochwertigere Quelle bleibt
    tier_order = {"A": 0, "B": 1, "C": 2}
    items.sort(key=lambda x: tier_order.get(x.get("tier", "C"), 9))

    deduped: list[RawItem] = []
    kept_titles: list[str] = []
    for item in items:
        title = item["title"]
        is_dup = any(_simple_similarity(title, kept) >= 0.85 for kept in kept_titles)
        if not is_dup:
            deduped.append(item)
            kept_titles.append(title)

    # 4. Auf MAX_RAW_ITEMS begrenzen (Tier A first – Sortierung noch aktiv)
    deduped = deduped[:MAX_RAW_ITEMS]

    return deduped
