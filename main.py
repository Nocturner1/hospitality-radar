"""
Hospitality AI Radar – Hauptpipeline

Ablauf:
  1. Feeds laden (Tier A, B, optional C)
  2. Bereinigen & deduplizieren
  3. Jedes Item via Claude Haiku bewerten
  4. Bewertete Items in Notion-Datenbank schreiben
  5. Wochendigest via Claude Sonnet generieren
  6. Review-Seite in Notion anlegen

Starten:
  python main.py

Optionale Flags:
  --dry-run     Kein Schreiben nach Notion, alles nur in der Konsole
  --tier-c      Auch Tier-C-Quellen einschließen
  --week KW16   Manuell eine Woche angeben (sonst: aktuelle ISO-Woche)
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

# .env laden (lokal im Projektverzeichnis)
load_dotenv(Path(__file__).parent / ".env")

from config import SOURCES
from fetch import fetch_all
from dedup import deduplicate
from score import score_all
from notion_writer import write_all_items, create_review_page
from digest import generate_digest

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def current_week_id() -> tuple[str, str]:
    """Gibt (week_id, week_label) zurück, z. B. ('2026-KW16', 'KW 16')."""
    now = datetime.now(timezone.utc)
    iso_year, iso_week, _ = now.isocalendar()
    week_id = f"{iso_year}-KW{iso_week:02d}"
    week_label = f"KW {iso_week:02d}"
    return week_id, week_label


def save_debug_json(data: list | dict, filename: str) -> None:
    """Speichert Zwischenergebnisse als JSON-Datei (für Debugging)."""
    out_path = Path(__file__).parent / "debug" / filename
    out_path.parent.mkdir(exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info("Debug-Datei gespeichert: %s", out_path)


def run(dry_run: bool = False, include_tier_c: bool = False, week_override: str | None = None) -> None:
    # --- Woche bestimmen ---
    if week_override:
        week_id = f"{datetime.now(timezone.utc).year}-{week_override}"
        week_label = week_override.replace("KW", "KW ")
    else:
        week_id, week_label = current_week_id()

    logger.info("=" * 60)
    logger.info("Hospitality AI Radar – %s", week_id)
    logger.info("=" * 60)

    # --- 1. Quellen filtern ---
    allowed_tiers = {"A", "B", "C"} if include_tier_c else {"A", "B"}
    sources = [s for s in SOURCES if s.tier in allowed_tiers]
    logger.info("Quellen: %d (%s)", len(sources), ", ".join(sorted(allowed_tiers)))

    # --- 2. Feeds laden ---
    raw_items = fetch_all(sources)
    if not raw_items:
        logger.warning("Keine Artikel gefunden. Abbruch.")
        return
    save_debug_json(raw_items, f"{week_id}_01_raw.json")

    # --- 3. Bereinigen & deduplizieren ---
    clean_items = deduplicate(raw_items)
    logger.info("Nach Deduplizierung: %d Items (vorher %d)", len(clean_items), len(raw_items))
    save_debug_json(clean_items, f"{week_id}_02_clean.json")

    # --- 4. Scoring ---
    logger.info("Starte Scoring (%d Items) …", len(clean_items))
    scored_items = score_all(clean_items)
    save_debug_json(scored_items, f"{week_id}_03_scored.json")

    keep = sum(1 for i in scored_items if i["decision"] == "keep")
    watch = sum(1 for i in scored_items if i["decision"] == "watch")
    reject = sum(1 for i in scored_items if i["decision"] == "reject")
    logger.info("Ergebnis: %d keep | %d watch | %d reject", keep, watch, reject)

    # --- 5. Notion Rohdatenbank ---
    if dry_run:
        logger.info("[DRY RUN] Kein Schreiben nach Notion.")
    else:
        _check_env(["NOTION_API_KEY", "NOTION_DATABASE_ID", "NOTION_REVIEWS_PAGE_ID"])
        write_all_items(scored_items, week_id)

    # --- 6. Digest erzeugen ---
    logger.info("Generiere Wochendigest …")
    digest = generate_digest(scored_items)
    save_debug_json(digest, f"{week_id}_04_digest.json")

    # --- 7. Review-Seite in Notion ---
    if dry_run:
        logger.info("[DRY RUN] Digest-Vorschau:\n%s", json.dumps(digest, ensure_ascii=False, indent=2))
    else:
        page_id = create_review_page(digest, week_id, week_label)
        if page_id:
            logger.info("Review-Seite erstellt: %s", page_id)
        else:
            logger.error("Review-Seite konnte nicht erstellt werden.")

    logger.info("=" * 60)
    logger.info("Pipeline abgeschlossen: %s", week_id)
    logger.info("=" * 60)


def _check_env(keys: list[str]) -> None:
    missing = [k for k in keys if not os.environ.get(k)]
    if missing:
        logger.error("Fehlende Umgebungsvariablen: %s", ", ".join(missing))
        logger.error("Bitte .env-Datei prüfen (Vorlage: .env.example)")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Hospitality AI Radar – Wochenpipeline")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Kein Schreiben nach Notion, nur lokale Debug-Dateien",
    )
    parser.add_argument(
        "--tier-c",
        action="store_true",
        help="Auch Tier-C-Quellen (optional) einschließen",
    )
    parser.add_argument(
        "--week",
        type=str,
        default=None,
        help="Manuelle Wochen-ID, z. B. KW16",
    )
    args = parser.parse_args()

    # Prüfe API-Key (immer nötig für Scoring)
    _check_env(["ANTHROPIC_API_KEY"])

    run(
        dry_run=args.dry_run,
        include_tier_c=args.tier_c,
        week_override=args.week,
    )
