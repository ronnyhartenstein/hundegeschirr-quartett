# Hundegeschirr-Quartett

Ein mittelalterliches Fantasy-Trumpfquartett mit Hundegeschirren. 32 Karten in vier Qualitätsstufen – von gewöhnlichem Bauerngeschirr bis zum epischen Drachengeschirr. Bilder werden per KI generiert.

## Spielprinzip

Jede Karte hat vier Werte (1–100, höher ist besser):

| Wert | Bedeutung |
|---|---|
| **Zugkraft** | Stärke, Traglast, körperliche Kraft |
| **Schutz** | Rüstung, Widerstandskraft, Standfestigkeit |
| **Beweglichkeit** | Geschwindigkeit, Ausweichen, Wendigkeit |
| **Instinkt** | Spurfinden, Wachsamkeit, Magie, Treue |

Spieler wählen abwechselnd einen Wert – wer den höheren Wert hat, gewinnt beide Karten. Epische Karten sind im Schnitt stärker, haben aber Schwächen: ein gewöhnliches Läufergeschirr (Beweglichkeit 84) schlägt den epischen Plattenpanzer (Beweglichkeit 40).

### Qualitätsstufen

| Stufe | Gesamtwert | Farbe |
|---|---|---|
| Gewöhnlich | 170 | Weiß/Silber |
| Magisch | 200 | Smaragdgrün |
| Selten | 230 | Blau |
| Episch | 260 | Violett |

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
cards/           # 32 Karten-Dateien als Markdown mit YAML-Frontmatter
output/          # generierte WebP-Bilder (nicht im Repo)
print/           # druckfertige JPGs (nicht im Repo)
master_prompt.md # Image-Prompt-Template mit Platzhaltern
karten.md        # Spieldesign, Balancing, vollständige Kartenliste
generate_cards.py
docker-compose.yml
```

## Neue Karte hinzufügen

1. Eintrag in `karten.md` ergänzen (Werte müssen dem Qualitäts-Gesamtwert entsprechen)
2. Datei `cards/NN-name-des-archetyps.md` anlegen (Frontmatter + `## Flavourtext` + `## Bildprompt`)
3. `python generate_cards.py cards/NN-name-des-archetyps.md`
