# Hospitality AI Radar – Setup-Anleitung

## Voraussetzungen
- Python 3.11+
- Anthropic API Key (für Scoring & Digest)
- Notion Integration Token + Datenbank-IDs

---

## 1. Python-Abhängigkeiten installieren

```bash
cd hospitality-radar
pip install -r requirements.txt
```

---

## 2. Notion vorbereiten

### Schritt 1 – Integration anlegen
1. Gehe zu https://www.notion.so/my-integrations
2. „+ New integration" → Name: „Hospitality Radar Bot"
3. Capabilities: Read + Write content, No user info
4. Kopiere den **Internal Integration Token** (= `NOTION_API_KEY`)

### Schritt 2 – Datenbank anlegen (`AI Hospitality Radar Items`)
Erstelle eine neue **Full-page Database** in Notion mit folgenden Properties:

| Property | Typ |
|---|---|
| Name | Title |
| URL | URL |
| Source | Select |
| Published | Date |
| Week ID | Text |
| Category | Select |
| Relevance Hospitality | Number |
| Novelty | Number |
| Testability 90d | Number |
| Strategic Impact 24m | Number |
| Score | Number |
| Decision | Select (keep / watch / reject) |
| Summary DE | Text |
| Why It Matters DE | Text |
| Action Hint DE | Text |
| Reviewed | Checkbox |
| Notes | Text |

Dann: Teile die Datenbank mit deiner Integration (Share → Invite → Hospitality Radar Bot).

**Datenbank-ID kopieren:** Die ID steht in der URL:
`https://www.notion.so/{workspace}/{DATABASE_ID}?v=...`

### Schritt 3 – Weekly Reviews Seite anlegen
1. Erstelle eine neue Seite „Weekly Reviews"
2. Teile sie mit der Integration
3. **Page-ID kopieren** (aus der URL wie oben)

---

## 3. Umgebungsvariablen konfigurieren

```bash
cp .env.example .env
```

Datei `.env` ausfüllen:
```
ANTHROPIC_API_KEY=sk-ant-...
NOTION_API_KEY=secret_...
NOTION_DATABASE_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
NOTION_REVIEWS_PAGE_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

---

## 4. Ersten Testlauf starten

```bash
# Trockenlauf: kein Schreiben nach Notion, nur lokale Debug-Dateien
python main.py --dry-run

# Echter Lauf
python main.py

# Mit Tier-C-Quellen (optional)
python main.py --tier-c

# Bestimmte Woche manuell angeben
python main.py --week KW16
```

Debug-Dateien landen unter `debug/`:
- `2026-KW16_01_raw.json` – alle Rohfunde
- `2026-KW16_02_clean.json` – nach Deduplizierung
- `2026-KW16_03_scored.json` – mit AI-Scoring
- `2026-KW16_04_digest.json` – fertiger Digest

---

## 5. Wöchentliche Automatisierung

### Windows Task Scheduler
1. Öffne Task Scheduler → „Create Basic Task"
2. Trigger: Wöchentlich, Montag 06:30
3. Action: `python C:\Users\domin\Downloads\hospitality-radar\main.py`
4. Working Directory setzen

### Alternativ: Make.com Webhook
- HTTP-Modul in Make → POST auf einen lokalen Ngrok-Tunnel, der main.py aufruft
- Oder: Direkt als Python-Skript in einem Make Custom Function Modul (falls verfügbar)

---

## 6. RSS-Feed-URLs prüfen

Einige Feeds könnten sich geändert haben oder kein RSS anbieten.
Prüfe nach dem ersten Dry-Run die Debug-Datei `_01_raw.json`:
- Quellen mit 0 Artikeln → URL in `config.py` anpassen
- Bekannte Probleme:
  - **Anthropic**: kein offizieller RSS – ggf. `https://www.anthropic.com/news` als HTML-Scraping
  - **OpenAI**: RSS-URL gelegentlich geändert – ggf. https://openai.com/news/rss prüfen

---

## 7. Schwellwerte anpassen (nach 2 Wochen)

In `config.py`:
```python
THRESHOLD_KEEP = 4.0   # >= 4.0 → Hauptnewsletter
THRESHOLD_WATCH = 3.2  # 3.2–3.9 → Watchlist
```

Wenn zu wenig in den Newsletter kommt → THRESHOLD_KEEP auf 3.8 senken.
Wenn zu viel durchkommt → auf 4.2 erhöhen.

---

## Dateiübersicht

| Datei | Funktion |
|---|---|
| `main.py` | Pipeline-Orchestrierung |
| `config.py` | Quellen, Schwellwerte, Modelle |
| `fetch.py` | RSS-Feeds laden & filtern |
| `dedup.py` | Bereinigung & Deduplizierung |
| `score.py` | AI-Scoring via Claude Haiku |
| `digest.py` | Wochendigest via Claude Sonnet |
| `notion_writer.py` | Notion API (DB + Review-Seite) |
| `.env` | API-Keys (nicht ins Git!) |
| `debug/` | Lokale JSON-Zwischenstände |
