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
# Shared CSS
# ---------------------------------------------------------------------------

FONTS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900'
    '&family=Playfair+Display:ital,wght@0,700;0,800;1,700&display=swap" rel="stylesheet">'
)

CSS = """
:root{
  --bg:#09090f;--surface:#0f1117;--surface2:#161923;
  --border:rgba(255,255,255,0.06);--border2:rgba(255,255,255,0.12);
  --text:#e8eaf0;--muted:#6b7280;--subtle:#374151;
  --accent:#c9a84c;--accent2:#e8c96d;
  --blue:#3b82f6;--indigo:#818cf8;--teal:#14b8a6;
}
*{box-sizing:border-box;margin:0;padding:0;}
html{scroll-behavior:smooth;}
body{font-family:'Inter',sans-serif;background:var(--bg);color:var(--text);min-height:100vh;line-height:1.65;-webkit-font-smoothing:antialiased;}
a{color:inherit;text-decoration:none;}

/* NAV */
nav{position:sticky;top:0;z-index:100;background:rgba(9,9,15,0.92);backdrop-filter:blur(20px);border-bottom:1px solid var(--border);padding:0 40px;display:flex;align-items:center;justify-content:space-between;height:52px;}
.nav-left{display:flex;align-items:center;gap:12px;}
.nav-logo{font-size:0.78rem;font-weight:700;letter-spacing:2.5px;text-transform:uppercase;color:var(--text);}
.nav-sep{width:1px;height:16px;background:var(--border2);}
.nav-edition{font-size:0.72rem;color:var(--muted);letter-spacing:0.5px;}
.nav-live{display:flex;align-items:center;gap:6px;font-size:0.65rem;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;color:var(--accent);}
.nav-live-dot{width:5px;height:5px;border-radius:50%;background:var(--accent);animation:blink 2.5s ease-in-out infinite;}
@keyframes blink{0%,100%{opacity:1;}50%{opacity:0.2;}}

/* MASTHEAD */
.masthead{border-bottom:1px solid var(--border);padding:56px 40px 48px;max-width:1120px;margin:0 auto;display:grid;grid-template-columns:1fr 200px;gap:60px;align-items:end;}
.masthead-kicker{font-size:0.68rem;font-weight:600;letter-spacing:3px;text-transform:uppercase;color:var(--accent);margin-bottom:20px;}
.masthead h1{font-family:'Playfair Display',serif;font-size:clamp(2.8rem,5vw,4.2rem);font-weight:800;line-height:1.05;letter-spacing:-1.5px;color:var(--text);}
.masthead h1 i{font-style:italic;color:var(--accent);}
.masthead-desc{margin-top:20px;font-size:0.92rem;color:var(--muted);line-height:1.7;max-width:520px;font-weight:400;}
.masthead-meta{margin-top:32px;display:flex;align-items:center;gap:28px;}
.meta-item{text-align:left;}
.meta-num{font-size:1.6rem;font-weight:800;color:var(--text);line-height:1;font-variant-numeric:tabular-nums;}
.meta-label{font-size:0.62rem;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;color:var(--muted);margin-top:3px;}
.meta-div{width:1px;height:36px;background:var(--border2);}
.kw-block{text-align:right;}
.kw-num{font-family:'Playfair Display',serif;font-size:5rem;font-weight:800;line-height:1;color:var(--accent);letter-spacing:-3px;}
.kw-label{font-size:0.6rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:var(--muted);margin-top:4px;}

/* SECTION RULE */
.section-rule{max-width:1120px;margin:40px auto 28px;padding:0 40px;display:flex;align-items:center;gap:0;}
.section-rule-label{font-size:0.6rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:var(--muted);padding-right:20px;white-space:nowrap;}
.section-rule-line{flex:1;height:1px;background:var(--border);}
.section-rule-accent{flex:0 0 40px;height:1px;background:var(--accent);}

/* STORY GRID */
.story-grid{max-width:1120px;margin:0 auto 2px;padding:0 40px;display:grid;grid-template-columns:1.4fr 1fr;gap:1px;background:var(--border);border:1px solid var(--border);border-radius:4px;overflow:hidden;}
.story-card{background:var(--surface);padding:32px 36px;transition:background 0.15s;cursor:pointer;}
.story-card:hover{background:var(--surface2);}
.story-card.lead{padding:40px 44px;}
.story-right{display:grid;grid-template-rows:1fr 1fr;gap:1px;background:var(--border);}

.card-tag{font-size:0.58rem;font-weight:700;letter-spacing:2.5px;text-transform:uppercase;margin-bottom:14px;}
.tag-agent{color:#818cf8;}.tag-ai{color:#38bdf8;}.tag-dist{color:#34d399;}
.tag-revenue{color:var(--accent2);}.tag-guest{color:#f472b6;}
.tag-industry{color:var(--muted);}.tag-ops{color:#fb923c;}.tag-mkt{color:#c084fc;}.tag-crm{color:#f472b6;}.tag-other{color:var(--muted);}

.card-source{font-size:0.65rem;font-weight:500;letter-spacing:1px;text-transform:uppercase;color:var(--muted);margin-bottom:10px;}
.card-headline{font-family:'Playfair Display',serif;font-size:1.2rem;font-weight:700;line-height:1.35;color:var(--text);margin-bottom:12px;}
.story-card.lead .card-headline{font-size:1.55rem;}
.card-deck{font-size:0.83rem;color:#9ca3af;line-height:1.65;}
.card-rule{height:1px;background:var(--border);margin:18px 0;}
.card-action{font-size:0.75rem;color:var(--accent);font-weight:500;letter-spacing:0.3px;}
.card-action::before{content:'→  ';}

/* STORY ROW (3-col) */
.story-row{max-width:1120px;margin:1px auto 0;padding:0 40px;display:grid;grid-template-columns:repeat(3,1fr);gap:1px;background:var(--border);border:1px solid var(--border);border-top:none;border-radius:0 0 4px 4px;overflow:hidden;}
.story-row .story-card{padding:24px 28px;}
.story-row .card-headline{font-size:0.95rem;}

/* BODY LAYOUT */
.body-grid{max-width:1120px;margin:0 auto;padding:0 40px 80px;display:grid;grid-template-columns:1fr 280px;gap:40px;}

/* SUMMARY */
.block-label{font-size:0.58rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:var(--muted);padding-bottom:12px;margin-bottom:16px;border-bottom:1px solid var(--border);}
.summary-para{font-size:0.97rem;line-height:1.85;color:#d1d5db;font-weight:400;}
.summary-para strong{color:var(--text);font-weight:600;}
.summary-block{margin-bottom:40px;}

/* TOOLS */
.tools-block{margin-bottom:40px;}
.tool-row{display:flex;gap:16px;padding:14px 0;border-bottom:1px solid var(--border);font-size:0.84rem;color:#9ca3af;align-items:flex-start;}
.tool-row:first-of-type{border-top:1px solid var(--border);}
.tool-index{font-size:0.65rem;font-weight:700;color:var(--accent);min-width:18px;padding-top:2px;letter-spacing:0.5px;}

/* SIDEBAR */
.sidebar{padding-top:40px;}
.sidebar-block{margin-bottom:36px;}
.agent-block{border:1px solid rgba(129,140,248,0.2);border-radius:4px;padding:24px;background:rgba(129,140,248,0.04);margin-bottom:36px;}
.agent-label{font-size:0.58rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:#818cf8;padding-bottom:12px;margin-bottom:14px;border-bottom:1px solid rgba(129,140,248,0.15);}
.agent-text{font-size:0.82rem;line-height:1.75;color:#9ca3af;}

.exp-row{display:flex;gap:12px;padding:12px 0;border-bottom:1px solid var(--border);font-size:0.82rem;color:#9ca3af;line-height:1.55;}
.exp-row:first-of-type{border-top:1px solid var(--border);}
.exp-n{font-size:0.72rem;font-weight:700;color:var(--accent);min-width:16px;padding-top:1px;}

.watch-row{padding:14px 0 14px 14px;border-bottom:1px solid var(--border);border-left:1px solid var(--accent);}
.watch-row:first-of-type{border-top:1px solid var(--border);}
.watch-title{font-size:0.82rem;font-weight:600;color:var(--text);margin-bottom:5px;}
.watch-text{font-size:0.75rem;color:var(--muted);line-height:1.55;}

/* ARCHIVE */
.archive-wrap{max-width:1120px;margin:0 auto 80px;padding:0 40px;}
.archive-row{display:flex;align-items:center;gap:24px;padding:20px 0;border-bottom:1px solid var(--border);cursor:pointer;transition:opacity 0.15s;}
.archive-row:first-of-type{border-top:1px solid var(--border);}
.archive-row:hover{opacity:0.75;}
.archive-kw{font-family:'Playfair Display',serif;font-size:1.4rem;font-weight:700;color:var(--accent);min-width:52px;letter-spacing:-0.5px;}
.archive-body{flex:1;}
.archive-title{font-size:0.9rem;font-weight:600;color:var(--text);margin-bottom:4px;}
.archive-summary{font-size:0.78rem;color:var(--muted);line-height:1.5;}
.archive-pills{display:flex;gap:8px;margin-top:8px;}
.pill{font-size:0.62rem;font-weight:600;letter-spacing:0.5px;padding:2px 8px;border-radius:2px;}
.pill-k{background:rgba(52,211,153,0.1);color:#34d399;border:1px solid rgba(52,211,153,0.2);}
.pill-w{background:rgba(201,168,76,0.1);color:var(--accent);border:1px solid rgba(201,168,76,0.2);}
.archive-arrow{color:var(--muted);font-size:0.9rem;}

/* INDEX MASTHEAD */
.index-masthead{border-bottom:1px solid var(--border);padding:64px 40px 56px;max-width:1120px;margin:0 auto;}
.index-masthead h1{font-family:'Playfair Display',serif;font-size:clamp(2.4rem,4vw,3.6rem);font-weight:800;line-height:1.1;letter-spacing:-1.5px;color:var(--text);margin-bottom:16px;}
.index-masthead h1 i{font-style:italic;color:var(--accent);}
.index-masthead p{font-size:0.94rem;color:var(--muted);line-height:1.7;max-width:560px;}

/* FOOTER */
footer{border-top:1px solid var(--border);padding:28px 40px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;}
.footer-brand{font-size:0.65rem;font-weight:700;letter-spacing:2.5px;text-transform:uppercase;color:var(--muted);}
.footer-links{display:flex;gap:20px;}
.footer-links a{font-size:0.72rem;color:var(--muted);}
.footer-links a:hover{color:var(--text);}

@media(max-width:768px){
  nav,.masthead,.section-rule,.story-grid,.story-row,.body-grid,.archive-wrap,.index-masthead,footer{padding-left:20px;padding-right:20px;}
  .masthead{grid-template-columns:1fr;gap:24px;}
  .story-grid,.story-row{grid-template-columns:1fr;}
  .story-right{grid-template-rows:unset;}
  .body-grid{grid-template-columns:1fr;}
}
"""

# Category → display tag + CSS class
CAT_MAP = {
    "agent_booking":      ("Agent Booking",        "tag-agent"),
    "ai_platforms":       ("AI Platforms",          "tag-ai"),
    "distribution":       ("Distribution",          "tag-dist"),
    "revenue":            ("Revenue Management",    "tag-revenue"),
    "guest_communication":("Guest Communication",   "tag-guest"),
    "operations":         ("Operations",            "tag-ops"),
    "marketing":          ("Marketing",             "tag-mkt"),
    "crm":                ("CRM",                   "tag-crm"),
    "industry_news":      ("Industry News",         "tag-industry"),
    "other":              ("Sonstiges",             "tag-other"),
}


def _esc(s: str) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _tag_html(cat: str) -> str:
    label, css = CAT_MAP.get(cat, ("Sonstiges", "tag-other"))
    return f'<div class="card-tag {css}">{label}</div>'


def _page(title: str, nav_edition: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{_esc(title)} · Hospitality AI Watch</title>
  {FONTS}
  <style>{CSS}</style>
</head>
<body>
<nav>
  <div class="nav-left">
    <span class="nav-logo"><a href="../index.html" style="color:inherit;">Hospitality AI Watch</a></span>
    <span class="nav-sep"></span>
    <span class="nav-edition">{_esc(nav_edition)}</span>
  </div>
  <div class="nav-live"><span class="nav-live-dot"></span> Wöchentlich</div>
</nav>
{body}
<footer>
  <span class="footer-brand">Hospitality AI Watch</span>
  <div class="footer-links">
    <a href="#">Automatisch generiert &middot; jeden Montag</a>
    <a href="https://github.com/Nocturner1/hospitality-radar">GitHub</a>
  </div>
</footer>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Digest page
# ---------------------------------------------------------------------------

def _section_rule(label: str) -> str:
    return f"""<div class="section-rule">
  <div class="section-rule-accent"></div>
  <span class="section-rule-label">&nbsp;&nbsp;{label}</span>
  <div class="section-rule-line"></div>
</div>"""


def _story_card(story: dict, lead: bool = False) -> str:
    cls = "story-card lead" if lead else "story-card"
    action = story.get("action", "")
    action_html = f'<div class="card-rule"></div><div class="card-action">{_esc(action)}</div>' if action else ""
    return f"""<div class="{cls}">
  <div class="card-source">{_esc(story.get('source', ''))}</div>
  {_tag_html(story.get('category', 'other'))}
  <div class="card-headline">{_esc(story.get('title', ''))}</div>
  <div class="card-deck">{_esc(story.get('what_happened', ''))}</div>
  {action_html}
</div>"""


def generate_digest_html(digest: dict, scored_items: list[ScoredItem],
                          week_id: str, week_label: str) -> str:
    keep  = [i for i in scored_items if i.get("decision") == "keep"]
    watch = [i for i in scored_items if i.get("decision") == "watch"]
    year  = week_id[:4]
    kw_short = week_label.replace("KW ", "").strip()

    # Enrich stories with category + source from scored_items
    title_map = {i.get("title", "").lower(): i for i in scored_items}
    stories = digest.get("top_stories", [])
    for s in stories:
        key = s.get("title", "").lower()
        matched = title_map.get(key)
        if not s.get("category") and matched:
            s["category"] = matched.get("category", "other")
        if not s.get("source") and matched:
            s["source"] = matched.get("source", "")

    # ── MASTHEAD ──────────────────────────────────────────────────────────────
    masthead = f"""<div class="masthead">
  <div>
    <div class="masthead-kicker">Wöchentlicher Radar &middot; AI &amp; Automatisierung</div>
    <h1>Hospitality<br><i>AI Watch</i></h1>
    <p class="masthead-desc">Kuratierte Meldungen zu künstlicher Intelligenz, Buchungstechnologie und strategischen Entwicklungen für Entscheider in Hotels, Hotelgruppen und Travel-Tech-Teams.</p>
    <div class="masthead-meta">
      <div class="meta-item">
        <div class="meta-num">{len(keep)}</div>
        <div class="meta-label">Top-Meldungen</div>
      </div>
      <div class="meta-div"></div>
      <div class="meta-item">
        <div class="meta-num">{len(watch)}</div>
        <div class="meta-label">Watchlist</div>
      </div>
      <div class="meta-div"></div>
      <div class="meta-item">
        <div class="meta-num">{len(keep)+len(watch)}</div>
        <div class="meta-label">Gesamt</div>
      </div>
    </div>
  </div>
  <div class="kw-block">
    <div class="kw-num">{kw_short}</div>
    <div class="kw-label">Ausgabe &middot; {year}</div>
  </div>
</div>"""

    # ── EXECUTIVE SUMMARY ────────────────────────────────────────────────────
    summary_html = ""
    exec_sum = digest.get("executive_summary", "")
    if exec_sum:
        summary_html = _section_rule("Executive Summary")
        summary_html += f"""<div style="max-width:1120px;margin:0 auto;padding:0 40px 40px;">
  <p class="summary-para">{_esc(exec_sum)}</p>
</div>"""

    # ── TOP STORIES ───────────────────────────────────────────────────────────
    stories_html = ""
    if stories:
        stories_html = _section_rule("Top-Meldungen")
        lead = stories[0]
        second_pair = stories[1:3]
        rest = stories[3:6]

        # Lead + right column (2 stacked)
        right_col = "".join(_story_card(s) for s in second_pair)
        stories_html += f"""<div class="story-grid">
  {_story_card(lead, lead=True)}
  <div class="story-right">{right_col}</div>
</div>"""

        # Three-column row
        if rest:
            row_cards = "".join(_story_card(s) for s in rest)
            stories_html += f'<div class="story-row">{row_cards}</div>'

    # ── TOOLS ────────────────────────────────────────────────────────────────
    tools = digest.get("tools", [])
    tools_rows = ""
    for i, t in enumerate(tools, 1):
        tools_rows += f'<div class="tool-row"><span class="tool-index">{i:02d}</span><span>{_esc(t)}</span></div>'
    tools_block = f"""<div class="tools-block">
  <div class="block-label">Tools &amp; Programme</div>
  {tools_rows or '<div class="tool-row"><span class="tool-index">—</span><span>Keine neuen Tools diese Woche.</span></div>'}
</div>"""

    # ── AGENT WATCH ───────────────────────────────────────────────────────────
    agent_text = digest.get("agent_booking_watch") or "Keine spezifischen Meldungen zum Thema Buchungsautomatisierung diese Woche."
    agent_block = f"""<div class="agent-block">
  <div class="agent-label">Agent Booking Watch</div>
  <p class="agent-text">{_esc(agent_text)}</p>
</div>"""

    # ── EXPERIMENTS ───────────────────────────────────────────────────────────
    exps = digest.get("experiments", [])
    exp_rows = "".join(
        f'<div class="exp-row"><span class="exp-n">{i:02d}</span><span>{_esc(e)}</span></div>'
        for i, e in enumerate(exps, 1)
    )
    exp_block = f"""<div class="sidebar-block">
  <div class="block-label">Hotels testen jetzt</div>
  {exp_rows or '<div class="exp-row"><span class="exp-n">—</span><span>Keine Experimente diese Woche.</span></div>'}
</div>"""

    # ── WATCHLIST ─────────────────────────────────────────────────────────────
    watchlist = digest.get("watchlist", [])
    watch_rows = ""
    for w in watchlist:
        watch_rows += f"""<div class="watch-row">
  <div class="watch-title">{_esc(w.get('title', ''))}</div>
  <div class="watch-text">{_esc(w.get('comment', ''))}</div>
</div>"""
    watch_block = f"""<div class="sidebar-block" style="margin-top:32px;">
  <div class="block-label">Watchlist</div>
  {watch_rows or '<div class="watch-row"><div class="watch-text">Keine Watchlist-Einträge.</div></div>'}
</div>"""

    # ── BODY GRID ─────────────────────────────────────────────────────────────
    body_section = _section_rule("Analyse &amp; Kontext")
    body_section += f"""<div class="body-grid">
  <div>{tools_block}</div>
  <div class="sidebar">{agent_block}{exp_block}{watch_block}</div>
</div>"""

    body = masthead + summary_html + stories_html + body_section
    return _page(f"Hospitality AI Watch – {week_label}", f"{week_label} · {year}", body)


def write_digest_html(digest: dict, scored_items: list[ScoredItem],
                       week_id: str, week_label: str) -> Path:
    out_dir = REPO_ROOT / "weekly-reviews"
    out_dir.mkdir(exist_ok=True)
    out = out_dir / f"{week_id}.html"
    html = generate_digest_html(digest, scored_items, week_id, week_label)
    # Fix nav link on sub-pages (already correct: ../index.html)
    out.write_text(html, encoding="utf-8")
    logger.info("Digest-HTML: %s", out)
    return out


# ---------------------------------------------------------------------------
# Index page
# ---------------------------------------------------------------------------

def generate_index(issues: list[dict]) -> str:
    archive_rows = ""
    for issue in sorted(issues, key=lambda x: x["week_id"], reverse=True):
        kw_num = issue["week_id"].split("KW")[-1].lstrip("0") or "0"
        year   = issue["week_id"][:4]
        summary = issue.get("summary", "")
        summary_html = f'<div class="archive-summary">{_esc(summary[:180])}{"…" if len(summary)>180 else ""}</div>' if summary else ""
        archive_rows += f"""<a class="archive-row" href="weekly-reviews/{issue['week_id']}.html">
  <div class="archive-kw">{kw_num}</div>
  <div class="archive-body">
    <div class="archive-title">Hospitality AI Watch &middot; KW {kw_num} &middot; {year}</div>
    {summary_html}
    <div class="archive-pills">
      <span class="pill pill-k">{issue['keep']} Top-Meldungen</span>
      <span class="pill pill-w">{issue['watch']} Watchlist</span>
    </div>
  </div>
  <div class="archive-arrow">→</div>
</a>"""

    masthead = f"""<div class="index-masthead">
  <div class="masthead-kicker" style="font-size:0.68rem;font-weight:600;letter-spacing:3px;text-transform:uppercase;color:var(--accent);margin-bottom:20px;">Wöchentlicher Radar &middot; AI &amp; Automatisierung</div>
  <h1>AI &amp; Automatisierung<br>in der <i>Hotellerie</i></h1>
  <p>Kuratierte Meldungen zu künstlicher Intelligenz, Buchungstechnologie und strategischen Entwicklungen – für Entscheider in Hotels, Hotelgruppen und Travel-Tech-Teams.</p>
</div>"""

    archive_section = _section_rule("Alle Ausgaben")
    archive_section += f"""<div class="archive-wrap">
  {archive_rows if archive_rows else '<p style="color:var(--muted);padding:40px 0;">Noch keine Ausgaben vorhanden – der erste Radar erscheint am nächsten Montag.</p>'}
</div>"""

    return masthead + archive_section


def write_index(issues: list[dict]) -> Path:
    body = generate_index(issues)
    # On index, nav link points to itself – fix relative path
    page = _page("Hospitality AI Watch", "", body)
    page = page.replace('href="../index.html"', 'href="index.html"')
    out = REPO_ROOT / "index.html"
    out.write_text(page, encoding="utf-8")
    logger.info("Index: %s", out)
    return out


# ---------------------------------------------------------------------------
# Rebuild index from data/*.json
# ---------------------------------------------------------------------------

def rebuild_index() -> Path:
    data_dir = REPO_ROOT / "data"
    issues = []
    for json_file in sorted(data_dir.glob("*.json")):
        if json_file.stem == ".gitkeep":
            continue
        try:
            items = json.loads(json_file.read_text(encoding="utf-8"))
            week_id = json_file.stem
            keep  = sum(1 for i in items if i.get("decision") == "keep")
            watch = sum(1 for i in items if i.get("decision") == "watch")
            top = sorted(
                [i for i in items if i.get("decision") == "keep"],
                key=lambda x: x.get("score", 0), reverse=True
            )
            summary = " · ".join(i.get("title", "") for i in top[:3])
            issues.append({"week_id": week_id, "keep": keep, "watch": watch, "summary": summary})
        except Exception as e:
            logger.warning("Index-Fehler %s: %s", json_file, e)
    return write_index(issues)
