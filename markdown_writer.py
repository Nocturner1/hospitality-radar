"""
Ersatz für notion_writer.py – schreibt Ergebnisse als Markdown-Dateien ins Repo.

Ausgabe:
  weekly-reviews/YYYY-KWNN.md   – lesbarer Wochendigest
  data/YYYY-KWNN.json           – alle bewerteten Items (Rohdaten)
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

ScoredItem = dict[str, Any]
REPO_ROOT = Path(__file__).parent


def _decision_emoji(decision: str) -> str:
    return {"keep": "🟢", "watch": "🟡", "reject": "🔴"}.get(decision, "⚪")


def _category_label(cat: str) -> str:
    labels = {
        "distribution":       "Distribution",
        "revenue":            "Revenue",
        "guest_communication":"Gästekommunikation",
        "operations":         "Operations",
        "marketing":          "Marketing",
        "crm":                "CRM",
        "agent_booking":      "Agent Booking",
        "ai_platforms":       "AI Platforms",
        "other":              "Sonstiges",
    }
    return labels.get(cat, cat)


# ---------------------------------------------------------------------------
# Rohdaten als JSON speichern
# ---------------------------------------------------------------------------

def write_data_json(scored_items: list[ScoredItem], week_id: str) -> Path:
    """Speichert alle bewerteten Items als JSON in data/."""
    out_dir = REPO_ROOT / "data"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"{week_id}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(scored_items, f, ensure_ascii=False, indent=2)
    logger.info("Daten gespeichert: %s", out_path)
    return out_path


# ---------------------------------------------------------------------------
# Wochendigest als Markdown schreiben
# ---------------------------------------------------------------------------

def write_weekly_review(digest: dict, scored_items: list[ScoredItem], week_id: str, week_label: str) -> Path:
    """Schreibt den Digest als Markdown-Datei nach weekly-reviews/."""
    out_dir = REPO_ROOT / "weekly-reviews"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"{week_id}.md"

    keep_items  = [i for i in scored_items if i.get("decision") == "keep"]
    watch_items = [i for i in scored_items if i.get("decision") == "watch"]
    all_items   = [i for i in scored_items if i.get("decision") != "reject"]

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines: list[str] = []

    # Header
    lines += [
        f"# Hospitality AI Watch – {week_label}",
        "",
        f"> Generiert: {generated_at} · "
        f"**{len(keep_items)} Top-Meldungen** · "
        f"**{len(watch_items)} Watchlist** · "
        f"Rohdaten: [data/{week_id}.json](../data/{week_id}.json)",
        "",
        "---",
        "",
    ]

    # 1. Executive Summary
    lines += [
        "## 1. Executive Summary",
        "",
        digest.get("executive_summary", "_Kein Summary vorhanden._"),
        "",
        "---",
        "",
    ]

    # 2. Top-Meldungen
    lines += ["## 2. Top-Meldungen", ""]
    for story in digest.get("top_stories", []):
        lines += [
            f"### {story.get('title', '')}",
            "",
            f"**Was ist passiert?** {story.get('what_happened', '')}",
            "",
            f"**Warum relevant?** {story.get('why_relevant', '')}",
            "",
            f"**Testen / beobachten:** {story.get('action', '')}",
            "",
        ]
    if not digest.get("top_stories"):
        lines += ["_Keine Top-Meldungen diese Woche._", ""]
    lines += ["---", ""]

    # 3. Tools & Programme
    lines += ["## 3. Tools & Programme", ""]
    for tool in digest.get("tools", []):
        lines.append(f"- {tool}")
    if not digest.get("tools"):
        lines.append("_Keine neuen Tools diese Woche._")
    lines += ["", "---", ""]

    # 4. Agent Booking Watch
    lines += [
        "## 4. Agent Booking Watch",
        "",
        digest.get("agent_booking_watch") or "_Keine spezifischen Meldungen zu MCP/WebMCP/Suchagenten diese Woche._",
        "",
        "---",
        "",
    ]

    # 5. Was Hotels jetzt testen sollten
    lines += ["## 5. Was Hotels jetzt testen sollten", ""]
    for i, exp in enumerate(digest.get("experiments", []), 1):
        lines.append(f"{i}. {exp}")
    if not digest.get("experiments"):
        lines.append("_Keine Experimente diese Woche._")
    lines += ["", "---", ""]

    # 6. Watchlist
    lines += ["## 6. Watchlist", ""]
    for w in digest.get("watchlist", []):
        lines += [
            f"### {w.get('title', '')}",
            "",
            w.get("comment", ""),
            "",
        ]
    if not digest.get("watchlist"):
        lines += ["_Keine Watchlist-Einträge diese Woche._", ""]
    lines += ["---", ""]

    # 7. Rohdaten-Tabelle (alle keep + watch Items)
    lines += [
        "## 7. Alle bewerteten Meldungen",
        "",
        "| # | Entscheidung | Score | Titel | Quelle | Kategorie |",
        "|---|---|---|---|---|---|",
    ]
    for idx, item in enumerate(
        sorted(all_items, key=lambda x: x.get("score", 0), reverse=True), 1
    ):
        emoji    = _decision_emoji(item.get("decision", ""))
        score    = item.get("score", 0)
        title    = item.get("title", "").replace("|", "\\|")[:70]
        url      = item.get("url", "")
        source   = item.get("source", "")
        category = _category_label(item.get("category", ""))
        title_md = f"[{title}]({url})" if url else title
        lines.append(f"| {idx} | {emoji} {item.get('decision','')} | {score:.2f} | {title_md} | {source} | {category} |")

    lines += ["", "---", ""]
    lines.append(f"_Hospitality AI Radar · {week_id} · automatisch generiert_")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    logger.info("Review gespeichert: %s", out_path)
    return out_path


# ---------------------------------------------------------------------------
# Index-Seite aktualisieren
# ---------------------------------------------------------------------------

def update_index(week_id: str, week_label: str, digest: dict) -> Path:
    """Hängt den neuen Eintrag oben in weekly-reviews/README.md ein."""
    index_path = REPO_ROOT / "weekly-reviews" / "README.md"

    new_entry = (
        f"| [{week_label}]({week_id}.md) | "
        f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')} | "
        f"{digest.get('executive_summary', '')[:100]}… |"
    )

    if index_path.exists():
        existing = index_path.read_text(encoding="utf-8")
        # Eintrag nach der Tabellenüberschrift einfügen
        marker = "|---|---|---|"
        if marker in existing:
            existing = existing.replace(marker, f"{marker}\n{new_entry}", 1)
            index_path.write_text(existing, encoding="utf-8")
            return index_path

    # Neu anlegen
    content = "\n".join([
        "# Hospitality AI Watch – Alle Ausgaben",
        "",
        "| Woche | Datum | Zusammenfassung |",
        "|---|---|---|",
        new_entry,
        "",
    ])
    index_path.write_text(content, encoding="utf-8")
    logger.info("Index aktualisiert: %s", index_path)
    return index_path
