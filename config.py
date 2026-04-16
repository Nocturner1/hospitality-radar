"""
Konfiguration: Quellen, Schwellwerte, Gewichtungen.
Tier A = Kernquellen (laufen jede Woche)
Tier B = Ergänzungsquellen (niedriger gewichtet)
Tier C = Optional / nur Beobachtung
"""

from dataclasses import dataclass


@dataclass
class Source:
    name: str
    rss_url: str
    tier: str  # "A", "B", "C"


# ---------------------------------------------------------------------------
# Quellenliste
# ---------------------------------------------------------------------------
SOURCES: list[Source] = [
    # --- Tier A: Kernquellen ------------------------------------------------
    Source(
        "PhocusWire",
        "https://www.phocuswire.com/rss",
        "A",
    ),
    Source(
        "Hospitality Net",
        "https://www.hospitalitynet.org/rss/all.xml",
        "A",
    ),
    Source(
        "Skift",
        "https://skift.com/feed/",
        "A",
    ),
    Source(
        "Travel Weekly",
        "https://www.travelweekly.com/rss",
        "A",
    ),
    Source(
        "Hotel Dive",
        "https://www.hoteldive.com/feeds/news.rss",
        "A",
    ),
    Source(
        "Hotel Management",
        "https://www.hotelmanagement.net/rss.xml",
        "A",
    ),
    Source(
        "Chrome Developers",
        "https://developer.chrome.com/feeds/blog.xml",
        "A",
    ),
    Source(
        "Google Cloud Blog",
        "https://cloudblog.withgoogle.com/rss/",
        "A",
    ),
    Source(
        "Google – The Keyword",
        "https://blog.google/rss/",
        "A",
    ),
    Source(
        "OpenAI Blog",
        "https://openai.com/blog/rss/",
        "A",
    ),
    Source(
        "Anthropic News",
        "https://www.anthropic.com/news/rss",
        "A",
    ),
    Source(
        "Hotel Tech Report",
        "https://hoteltechreport.com/news/rss",
        "A",
    ),
    Source(
        "MCP – GitHub Releases",
        "https://github.com/modelcontextprotocol/specification/releases.atom",
        "A",
    ),
    # --- Tier B: Ergänzungsquellen ------------------------------------------
    Source(
        "Web in Travel",
        "https://www.webintravel.com/feed/",
        "B",
    ),
    Source(
        "Mews Blog",
        "https://www.mews.com/en/blog/rss",
        "B",
    ),
    Source(
        "SiteMinder Blog",
        "https://www.siteminder.com/r/feed/",
        "B",
    ),
    Source(
        "Cloudbeds Blog",
        "https://www.cloudbeds.com/articles/feed/",
        "B",
    ),
    Source(
        "Amadeus Hospitality",
        "https://hospitality.amadeus.com/feed/",
        "B",
    ),
    Source(
        "Sabre Insights",
        "https://www.sabre.com/insights/feed/",
        "B",
    ),
    Source(
        "Canary Technologies Blog",
        "https://www.canarytechnologies.com/blog/rss",
        "B",
    ),
    Source(
        "Revinate Blog",
        "https://www.revinate.com/blog/feed/",
        "B",
    ),
    Source(
        "Asksuite Blog",
        "https://asksuite.com/blog/feed/",
        "B",
    ),
    # --- Tier C: Optional / später ------------------------------------------
    Source(
        "Lighthouse Blog",
        "https://www.lighthouse.com/blog/feed/",
        "C",
    ),
    Source(
        "Actabl Blog",
        "https://www.actabl.com/blog/feed/",
        "C",
    ),
]

# ---------------------------------------------------------------------------
# Scoring-Logik
# ---------------------------------------------------------------------------
SCORE_WEIGHTS = {
    "relevance_hospitality": 0.35,
    "novelty": 0.20,
    "testability_90d": 0.25,
    "strategic_impact_24m": 0.20,
}

THRESHOLD_KEEP = 4.0    # >= 4.0  → Hauptnewsletter
THRESHOLD_WATCH = 3.2   # 3.2–3.9 → Watchlist
# < 3.2 → reject

# ---------------------------------------------------------------------------
# Pipeline-Limits
# ---------------------------------------------------------------------------
MAX_RAW_ITEMS = 50       # Maximal so viele Rohfunde pro Lauf
MAX_TOP_STORIES = 8      # Maximal so viele Hauptmeldungen
MAX_WATCHLIST = 5        # Maximal so viele Watchlist-Einträge
LOOKBACK_DAYS = 7        # Nur Artikel der letzten N Tage

# ---------------------------------------------------------------------------
# Claude-Modelle
# ---------------------------------------------------------------------------
SCORE_MODEL = "claude-3-5-haiku-20241022"     # Günstig, für Massen-Scoring
DIGEST_MODEL = "claude-3-5-sonnet-20241022"  # Besser, für den Wochendigest
