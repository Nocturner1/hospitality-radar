---
layout: home
title: Hospitality AI Watch
---

Wöchentlicher Radar zu **AI & Automatisierung** in Tourismus und Hotellerie.  
Für Entscheider in Hotels, Hotelgruppen und Travel-Tech-Teams.

---

## Alle Ausgaben

| Woche | Themen |
|---|---|
{% for file in site.static_files %}{% if file.path contains 'weekly-reviews/' and file.extname == '.md' and file.name != 'README.md' %}| [{{ file.basename | replace: '2026-', 'KW ' | replace: 'KW KW', 'KW ' }}]({{ file.path | remove: '.md' }}) | – |
{% endif %}{% endfor %}

---

*Automatisch generiert jeden Montag · [GitHub](https://github.com/Nocturner1/hospitality-radar)*
