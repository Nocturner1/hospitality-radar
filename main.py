"""
Hospitality AI Radar – Hauptpipeline

Ablauf:
  1. Feeds laden (Tier A, B, optional C)
  2. Bereinigen & deduplizieren
  3. Jedes Item via Claude Haiku bewerten
  4. Ausgabe schreiben (Markdown ins Repo ODER Notion)
  5. Wochendigest via Claude Sonnet generieren
  6. Review-Seite schreiben

Starten:
  python main.py                      # Markdown-Ausgabe (Standard)
  python main.py --output notion      # In Notion schreiben
  python main.py --dry-run            # Nur lokal, nichts schreiben
  python main.py --tier-c             # Auch Tier-C-Quellen
  python main.py --week KW16          # Manuelle Woche
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

from config import SOURCES
from fetch import fetch_all
from dedup import deduplicate
from score import score_all
from digest import generate_digest

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def current_week_id() -> tuple[str, str]:
    now = datetime.now(timezone.utc)
    iso_year, iso_week, _ = now.isocalendar()
    return f"{iso_year}-KW{iso_week:02d}", f"KW {iso_week:02d}"


def save_debug_json(data: list | dict, filename: str) -> None:
    out_path = Path(__file__).parent / "debug" / filename
    out_path.parent.mkdir(exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info("Debug: %s", out_path)


def git_commit_and_push(week_id: str) -> None:
    """Committed neue Markdown/JSON-Dateien und pusht ins Repo."""
    try:
        repo = Path(__file__).parent
        subprocess.run(["git", "add",
                        f"weekly-reviews/{week_id}.md",
                        "weekly-reviews/README.md",
                        f"data/{week_id}.json"],
                       cwd=repo, check=True)
        subprocess.run(["git", "commit", "-m",
                        f"radar: {week_id} – automatischer Wochendigest"],
                       cwd=repo, check=True)
        subprocess.run(["git", "push"], cwd=repo, check=True)
        logger.info("Git: Änderungen gepusht.")
    except subprocess.CalledProcessError as exc:
        logger.warning("Git-Push fehlgeschlagen (manuell pushen): %s", exc)


def run(
    dry_run: bool = False,
    output: str = "github",
    include_tier_c: bool = False,
    week_override: str | None = None,
    git_push: bool = False,
) -> None:
    # Woche bestimmen
    if week_override:
        now = datetime.now(timezone.utc)
        week_id = f"{now.year}-{week_override}"
        week_label = week_override.replace("KW", "KW ")
    else:
        week_id, week_label = current_week_id()

    logger.info("=" * 60)
    logger.info("Hospitality AI Radar – %s  [output=%s]", week_id, output)
    logger.info("=" * 60)

    # Quellen
    allowed = {"A", "B", "C"} if include_tier_c else {"A", "B"}
    sources = [s for s in SOURCES if s.tier in allowed]
    logger.info("Quellen: %d (Tier %s)", len(sources), "/".join(sorted(allowed)))

    # 1. Fetch
    raw_items = fetch_all(sources)
    if not raw_items:
        logger.warning("Keine Artikel gefunden. Abbruch.")
        return
    save_debug_json(raw_items, f"{week_id}_01_raw.json")

    # 2. Deduplizieren
    clean_items = deduplicate(raw_items)
    logger.info("Nach Deduplizierung: %d (vorher %d)", len(clean_items), len(raw_items))
    save_debug_json(clean_items, f"{week_id}_02_clean.json")

    # 3. Scoring
    logger.info("Scoring (%d Items) …", len(clean_items))
    scored_items = score_all(clean_items)
    save_debug_json(scored_items, f"{week_id}_03_scored.json")

    keep   = sum(1 for i in scored_items if i["decision"] == "keep")
    watch  = sum(1 for i in scored_items if i["decision"] == "watch")
    reject = sum(1 for i in scored_items if i["decision"] == "reject")
    logger.info("keep=%d  watch=%d  reject=%d", keep, watch, reject)

    # 4. Digest
    logger.info("Generiere Wochendigest …")
    digest = generate_digest(scored_items)
    save_debug_json(digest, f"{week_id}_04_digest.json")

    # 5. Ausgabe
    if dry_run:
        logger.info("[DRY RUN] Kein Schreiben. Digest-Vorschau:")
        print(json.dumps(digest, ensure_ascii=False, indent=2))
        return

    if output == "github":
        from markdown_writer import write_data_json, write_weekly_review, update_index
        write_data_json(scored_items, week_id)
        write_weekly_review(digest, scored_items, week_id, week_label)
        update_index(week_id, week_label, digest)
        logger.info("Markdown-Dateien geschrieben.")
        if git_push:
            git_commit_and_push(week_id)

    elif output == "notion":
        _check_env(["NOTION_API_KEY", "NOTION_DATABASE_ID", "NOTION_REVIEWS_PAGE_ID"])
        from notion_writer import write_all_items, create_review_page
        write_all_items(scored_items, week_id)
        create_review_page(digest, week_id, week_label)

    else:
        logger.error("Unbekannter output-Modus: %s", output)
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("Fertig: %s", week_id)
    logger.info("=" * 60)


def _check_env(keys: list[str]) -> None:
    missing = [k for k in keys if not os.environ.get(k)]
    if missing:
        logger.error("Fehlende Umgebungsvariablen: %s", ", ".join(missing))
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Hospitality AI Radar")
    parser.add_argument("--dry-run", action="store_true",
                        help="Nichts schreiben, nur lokale Debug-Dateien")
    parser.add_argument("--output", choices=["github", "notion"], default="github",
                        help="Ausgabeziel (Standard: github)")
    parser.add_argument("--tier-c", action="store_true",
                        help="Tier-C-Quellen einschließen")
    parser.add_argument("--week", type=str, default=None,
                        help="Manuelle Woche, z. B. KW16")
    parser.add_argument("--push", action="store_true",
                        help="Nach dem Schreiben automatisch git push")
    args = parser.parse_args()

    _check_env(["OPENAI_API_KEY"])
    run(
        dry_run=args.dry_run,
        output=args.output,
        include_tier_c=args.tier_c,
        week_override=args.week,
        git_push=args.push,
    )
