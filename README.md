# Hundegeschirr-Quartett

Ein mittelalterliches Fantasy-Trumpfquartett mit Hundegeschirren. 40 Karten in fünf Qualitätsstufen – von gewöhnlichem Bauerngeschirr bis zum legendären Weltgeschirr. Bilder werden per KI generiert.

## Spielprinzip

Jede Karte hat fünf Werte (1–10, höher ist besser):

| Wert | Bedeutung |
|---|---|
| **Zugkraft** | Stärke, Traglast, körperliche Kraft |
| **Schutz** | Rüstung, Widerstandskraft, Standfestigkeit |
| **Beweglichkeit** | Geschwindigkeit, Ausweichen, Wendigkeit |
| **Instinkt** | Spurfinden, Wachsamkeit, Magie, Treue |
| **Knurren** | Kampfaggression, Einschüchterung, Bissigkeit |

Spieler wählen abwechselnd einen Wert – wer den höheren Wert hat, gewinnt beide Karten. Magische Karten sind im Schnitt stärker, haben aber Schwächen: ein gewöhnliches Läufergeschirr (Beweglichkeit 8) schlägt den magischen Plattenpanzer (Beweglichkeit 4).

### Qualitätsstufen

| Stufe | Gesamtwert | Farbe |
|---|---|---|
| Gewöhnlich | 23 | Weiß/Silber |
| Selten | 26 | Smaragdgrün |
| Episch | 29 | Violett |
| Magisch | 32 | Blau |
| Legendär | 34 | Orange/Gold |

## Voraussetzungen

```bash
pip install openai python-frontmatter Pillow
export OPENAI_API_KEY=sk-...
```

Oder per Docker (kein lokales Python nötig):

```bash
export OPENAI_API_KEY=sk-...
docker compose run generate-cards
```

## Bilder generieren

```bash
# Alle fehlenden Bilder generieren
python generate_cards.py

# Einzelne Karte
python generate_cards.py cards/01-schlichtes-geschirr-des-bauern.md

# Alle neu generieren (überschreibt bestehende mit Backup)
python generate_cards.py --force

# Bildqualität wählen (low/medium/high, Standard: medium)
python generate_cards.py --quality high

# Eine Karte pro Qualitätsstufe generieren (5 Karten, zum Testen)
python generate_cards.py --sample

# Mehrere Varianten pro Karte generieren
python generate_cards.py --variants 3 cards/01-schlichtes-geschirr-des-bauern.md

# Prompt anzeigen ohne API-Call
python generate_cards.py --dry-run cards/01-schlichtes-geschirr-des-bauern.md
```

## Druckdateien exportieren

```bash
# WebPs aus output/ als JPG nach print/ exportieren
python generate_cards.py --print

# Andere JPEG-Qualität (Standard: 95)
python generate_cards.py --print --print-quality 85
```

## Sonstige Befehle

```bash
# Große WebPs neu komprimieren (> 3 MB)
python generate_cards.py --recompress
```

## Dateistruktur

```
cards/                # 40 Karten-Dateien als Markdown mit YAML-Frontmatter
output/               # generierte WebP-Bilder (832×1424 px, ~300 DPI für 70×120 mm)
print/                # druckfertige JPGs
back/                 # Kartenrücken-Varianten
master_prompt.md      # Image-Prompt-Template mit Platzhaltern
karten.md             # Spieldesign, Balancing, vollständige Kartenliste
qualitaetsstufen.md   # Farben und Symbole je Qualitätsstufe
rueckseite.md         # Kartenrücken-Prompt und Varianten
generate_cards.py     # Bildgenerierungs-Script
visualize_balance.py  # Balancing-Visualisierung → balance.html
docker-compose.yml
```

## Neue Karte hinzufügen

1. Eintrag in `karten.md` ergänzen (Werte müssen dem Qualitäts-Gesamtwert entsprechen)
2. Datei `cards/NN-name-des-archetyps.md` anlegen (Frontmatter + `## Flavourtext` + `## Bildprompt`)
3. `python generate_cards.py cards/NN-name-des-archetyps.md`
