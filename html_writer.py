"""
Generiert die öffentliche Website:
  index.html                        – Übersicht aller Ausgaben
  weekly-reviews/YYYY-KWNN.html     – Einzelne Wochenausgabe
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

# ---------------------------------------------------------------------------
# CSS & Basis-Layout
# ---------------------------------------------------------------------------

CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #f8f9fa;
  color: #1a1a2e;
  line-height: 1.7;
}

a { color: #2563eb; text-decoration: none; }
a:hover { text-decoration: underline; }

header {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 60%, #0f3460 100%);
  color: white;
  padding: 48px 24px 40px;
  text-align: center;
}
header h1 { font-size: 2rem; font-weight: 700; letter-spacing: -0.5px; }
header p  { margin-top: 10px; opacity: 0.75; font-size: 1rem; }
header .badge {
  display: inline-block; margin-top: 16px;
  background: rgba(255,255,255,0.15); border-radius: 20px;
  padding: 4px 14px; font-size: 0.8rem; letter-spacing: 0.5px;
}

.container { max-width: 860px; margin: 0 auto; padding: 40px 24px 80px; }

/* Index: Karten-Liste */
.issue-list { display: flex; flex-direction: column; gap: 16px; margin-top: 32px; }

.issue-card {
  background: white;
  border-radius: 12px;
  padding: 24px 28px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.07);
  border-left: 4px solid #2563eb;
  transition: box-shadow 0.15s;
}
.issue-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.12); }
.issue-card h2 { font-size: 1.1rem; font-weight: 600; }
.issue-card h2 a { color: #1a1a2e; }
.issue-card h2 a:hover { color: #2563eb; text-decoration: none; }
.issue-card .meta { font-size: 0.82rem; color: #6b7280; margin-top: 4px; }
.issue-card .summary { margin-top: 10px; font-size: 0.9rem; color: #374151; }

/* Digest-Seite */
.digest-meta {
  background: white; border-radius: 10px; padding: 16px 20px;
  margin-bottom: 32px; font-size: 0.85rem; color: #6b7280;
  display: flex; gap: 20px; flex-wrap: wrap;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.digest-meta span { display: flex; align-items: center; gap: 6px; }
.pill {
  background: #eff6ff; color: #1d4ed8;
  border-radius: 20px; padding: 3px 12px; font-size: 0.8rem; font-weight: 600;
}
.pill.watch { background: #fefce8; color: #854d0e; }
.pill.reject { background: #fef2f2; color: #991b1b; }

section { margin-bottom: 40px; }
section h2 {
  font-size: 1.25rem; font-weight: 700;
  padding-bottom: 8px; margin-bottom: 20px;
  border-bottom: 2px solid #e5e7eb;
  display: flex; align-items: center; gap: 10px;
}
section h2 .icon { font-size: 1.1rem; }

.summary-box {
  background: white; border-radius: 10px; padding: 24px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06); font-size: 0.95rem; line-height: 1.8;
}

.story-card {
  background: white; border-radius: 10px; padding: 24px 28px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06); margin-bottom: 16px;
}
.story-card h3 { font-size: 1rem; font-weight: 700; margin-bottom: 14px; color: #111827; }
.story-card .story-row { display: flex; gap: 10px; margin-bottom: 10px; font-size: 0.9rem; }
.story-card .label {
  font-weight: 600; color: #6b7280; min-width: 130px; font-size: 0.82rem;
  padding-top: 2px;
}
.story-card .value { color: #374151; flex: 1; }

.tools-list, .experiments-list { list-style: none; }
.tools-list li, .experiments-list li {
  background: white; border-radius: 8px; padding: 14px 18px;
  margin-bottom: 10px; font-size: 0.9rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  display: flex; gap: 10px; align-items: flex-start;
}
.tools-list li::before { content: "🔧"; }
.experiments-list li::before { content: "🧪"; font-size: 1rem; margin-top: 1px; }

.agent-box {
  background: linear-gradient(135deg, #eff6ff, #f0fdf4);
  border: 1px solid #bfdbfe; border-radius: 10px;
  padding: 20px 24px; font-size: 0.92rem; line-height: 1.8;
}

.watch-card {
  background: white; border-radius: 10px; padding: 20px 24px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06); margin-bottom: 12px;
  border-left: 3px solid #f59e0b;
}
.watch-card h3 { font-size: 0.95rem; font-weight: 600; margin-bottom: 8px; }
.watch-card p { font-size: 0.88rem; color: #4b5563; }

.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 0.85rem; background: white;
        border-radius: 10px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
th { background: #f3f4f6; padding: 12px 14px; text-align: left; font-weight: 600;
     color: #374151; border-bottom: 1px solid #e5e7eb; }
td { padding: 11px 14px; border-bottom: 1px solid #f3f4f6; vertical-align: top; }
tr:last-child td { border-bottom: none; }
tr:hover td { background: #f9fafb; }

.back-link { display: inline-flex; align-items: center; gap: 6px; color: #6b7280;
             font-size: 0.88rem; margin-bottom: 24px; }
.back-link:hover { color: #2563eb; text-decoration: none; }

footer {
  text-align: center; padding: 32px 24px;
  font-size: 0.82rem; color: #9ca3af;
  border-top: 1px solid #e5e7eb;
}
"""

def _page(title: str, body: str, back: bool = False) -> str:
    back_html = '<a class="back-link" href="../index.html">← Alle Ausgaben</a>' if back else ""
    return f"""<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} · Hospitality AI Watch</title>
  <style>{CSS}</style>
</head>
<body>
<header>
  <h1>Hospitality AI Watch</h1>
  <p>Wöchentlicher Radar zu AI &amp; Automatisierung in Tourismus und Hotellerie</p>
  <span class="badge">Für Entscheider in Hotellerie &amp; Travel-Tech</span>
</header>
<div class="container">
  {back_html}
  {body}
</div>
<footer>
  Automatisch generiert jeden Montag &nbsp;·&nbsp;
  <a href="https://github.com/Nocturner1/hospitality-radar">GitHub</a>
</footer>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Index-Seite
# ---------------------------------------------------------------------------

def generate_index(issues: list[dict]) -> str:
    """Gibt HTML für die Übersichtsseite zurück."""
    cards = ""
    for issue in sorted(issues, key=lambda x: x["week_id"], reverse=True):
        summary = issue.get("summary", "")[:180]
        if summary and not summary.endswith("…"):
            summary += "…"
        cards += f"""
<div class="issue-card">
  <h2><a href="weekly-reviews/{issue['week_id']}.html">{issue['title']}</a></h2>
  <div class="meta">{issue['date']} &nbsp;·&nbsp;
    <span class="pill">{issue['keep']} Top-Meldungen</span>&nbsp;
    <span class="pill watch">{issue['watch']} Watchlist</span>
  </div>
  {"<p class='summary'>" + summary + "</p>" if summary else ""}
</div>"""

    body = f"""
<h2 style="font-size:1.4rem;font-weight:700;margin-bottom:8px;">Alle Ausgaben</h2>
<p style="color:#6b7280;font-size:0.9rem;">Jeden Montag neu · {len(issues)} {'Ausgabe' if len(issues)==1 else 'Ausgaben'}</p>
<div class="issue-list">{cards if cards else '<p style="color:#9ca3af;padding:40px 0;text-align:center;">Noch keine Ausgaben vorhanden.</p>'}</div>
"""
    return _page("Alle Ausgaben", body)


def write_index(issues: list[dict]) -> Path:
    out = REPO_ROOT / "index.html"
    out.write_text(generate_index(issues), encoding="utf-8")
    logger.info("Index geschrieben: %s", out)
    return out


# ---------------------------------------------------------------------------
# Digest-Seite
# ---------------------------------------------------------------------------

def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def generate_digest_html(digest: dict, scored_items: list[ScoredItem],
                          week_id: str, week_label: str) -> str:
    keep  = [i for i in scored_items if i.get("decision") == "keep"]
    watch = [i for i in scored_items if i.get("decision") == "watch"]
    gen   = datetime.now(timezone.utc).strftime("%d.%m.%Y %H:%M UTC")

    # Meta-Zeile
    meta = f"""<div class="digest-meta">
  <span>📅 {gen}</span>
  <span><span class="pill">{len(keep)} Top-Meldungen</span></span>
  <span><span class="pill watch">{len(watch)} Watchlist</span></span>
</div>"""

    # 1. Executive Summary
    s1 = f"""<section>
  <h2><span class="icon">📋</span> Executive Summary</h2>
  <div class="summary-box">{_esc(digest.get('executive_summary',''))}</div>
</section>"""

    # 2. Top-Meldungen
    stories_html = ""
    for s in digest.get("top_stories", []):
        stories_html += f"""<div class="story-card">
  <h3>{_esc(s.get('title',''))}</h3>
  <div class="story-row"><span class="label">Was ist passiert?</span><span class="value">{_esc(s.get('what_happened',''))}</span></div>
  <div class="story-row"><span class="label">Warum relevant?</span><span class="value">{_esc(s.get('why_relevant',''))}</span></div>
  <div class="story-row"><span class="label">Testen / beobachten</span><span class="value">{_esc(s.get('action',''))}</span></div>
</div>"""
    s2 = f'<section><h2><span class="icon">🗞️</span> Top-Meldungen</h2>{stories_html or "<p style=\'color:#9ca3af\'>Keine Top-Meldungen diese Woche.</p>"}</section>'

    # 3. Tools
    tools = "".join(f"<li>{_esc(t)}</li>" for t in digest.get("tools", []))
    s3 = f'<section><h2><span class="icon">🔧</span> Tools &amp; Programme</h2><ul class="tools-list">{tools or "<li>Keine neuen Tools diese Woche.</li>"}</ul></section>'

    # 4. Agent Booking Watch
    agent = _esc(digest.get("agent_booking_watch") or "Keine spezifischen Meldungen zu MCP/WebMCP/Suchagenten diese Woche.")
    s4 = f'<section><h2><span class="icon">🤖</span> Agent Booking Watch</h2><div class="agent-box">{agent}</div></section>'

    # 5. Experimente
    exps = "".join(f"<li>{_esc(e)}</li>" for e in digest.get("experiments", []))
    s5 = f'<section><h2><span class="icon">🧪</span> Was Hotels jetzt testen sollten</h2><ul class="experiments-list">{exps or "<li>Keine Experimente diese Woche.</li>"}</ul></section>'

    # 6. Watchlist
    watches = ""
    for w in digest.get("watchlist", []):
        watches += f'<div class="watch-card"><h3>{_esc(w.get("title",""))}</h3><p>{_esc(w.get("comment",""))}</p></div>'
    s6 = f'<section><h2><span class="icon">👁️</span> Watchlist</h2>{watches or "<p style=\'color:#9ca3af\'>Keine Watchlist-Einträge.</p>"}</section>'

    # 7. Tabelle
    rows = ""
    emojis = {"keep": "🟢", "watch": "🟡", "reject": "🔴"}
    for i, item in enumerate(sorted(keep + watch, key=lambda x: x.get("score",0), reverse=True), 1):
        e = emojis.get(item.get("decision",""), "⚪")
        t = _esc(item.get("title","")[:70])
        url = item.get("url","")
        t_link = f'<a href="{url}" target="_blank">{t}</a>' if url else t
        rows += f"<tr><td>{i}</td><td>{e}</td><td>{item.get('score',0):.2f}</td><td>{t_link}</td><td>{_esc(item.get('source',''))}</td></tr>"
    s7 = f"""<section><h2><span class="icon">📊</span> Alle bewerteten Meldungen</h2>
<div class="table-wrap"><table>
<thead><tr><th>#</th><th></th><th>Score</th><th>Titel</th><th>Quelle</th></tr></thead>
<tbody>{rows or "<tr><td colspan='5' style='text-align:center;color:#9ca3af'>Keine Einträge</td></tr>"}</tbody>
</table></div></section>"""

    body = f"<h1 style='font-size:1.6rem;font-weight:800;margin-bottom:20px'>Hospitality AI Watch – {week_label}</h1>{meta}{s1}{s2}{s3}{s4}{s5}{s6}{s7}"
    return _page(f"Hospitality AI Watch – {week_label}", body, back=True)


def write_digest_html(digest: dict, scored_items: list[ScoredItem],
                       week_id: str, week_label: str) -> Path:
    out_dir = REPO_ROOT / "weekly-reviews"
    out_dir.mkdir(exist_ok=True)
    out = out_dir / f"{week_id}.html"
    out.write_text(generate_digest_html(digest, scored_items, week_id, week_label), encoding="utf-8")
    logger.info("Digest-HTML geschrieben: %s", out)
    return out


# ---------------------------------------------------------------------------
# Index aus vorhandenen JSON-Daten aufbauen
# ---------------------------------------------------------------------------

def rebuild_index() -> Path:
    """Liest alle data/*.json und baut den Index neu auf."""
    data_dir = REPO_ROOT / "data"
    issues = []
    for json_file in sorted(data_dir.glob("*.json")):
        if json_file.name == ".gitkeep":
            continue
        try:
            items = json.loads(json_file.read_text(encoding="utf-8"))
            week_id = json_file.stem
            keep  = sum(1 for i in items if i.get("decision") == "keep")
            watch = sum(1 for i in items if i.get("decision") == "watch")
            # Summary aus Digest-HTML lesen falls vorhanden
            summary = ""
            digest_path = REPO_ROOT / "weekly-reviews" / f"{week_id}.html"
            if not digest_path.exists():
                digest_path = REPO_ROOT / "weekly-reviews" / f"{week_id}.md"
            label = week_id.replace("-KW", " KW ").replace("2026 ", "")
            issues.append({
                "week_id": week_id,
                "title": f"Hospitality AI Watch – {label.replace('KW ', 'KW ')}",
                "date": week_id[:4] + " " + week_id[5:],
                "keep": keep,
                "watch": watch,
                "summary": summary,
            })
        except Exception as e:
            logger.warning("Index-Rebuild Fehler %s: %s", json_file, e)
    return write_index(issues)
