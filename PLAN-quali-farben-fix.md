# Plan: qualitaetsfarbe per Mapping-Tabelle im Script ermitteln

## Context

Aktuell steht in jeder Karten-Datei (`cards/*.md`) das Feld `qualitaetsfarbe` im YAML-Frontmatter – z. B. `qualitaetsfarbe: weiß-silberner Akzent`. Da die Farbe eindeutig aus dem `qualitaet`-Feld ableitbar ist, soll der Wert künftig vom Script über eine zentrale Mapping-Tabelle ermittelt werden. Das entfernt Redundanz und verhindert Inkonsistenzen bei neuen Karten.

## Kanonisches Mapping

| qualitaet  | Farbe       | Mapping-Wert für Prompt              |
|------------|-------------|--------------------------------------|
| Gewöhnlich | Weiß        | weiß-silberner Akzent                |
| Selten     | Grün        | smaragdgrüner Akzent                 |
| Episch     | Blau        | blauer Akzent                        |
| Magisch    | Violett     | violetter magischer Akzent           |
| Legendär   | Orange      | gold-orangefarbener magischer Akzent |

Nur Magisch und Legendär tragen „magischer" im Akzent-Namen.

## Änderungen

### 1. `generate_cards.py` — Mapping-Tabelle + Lambda anpassen

**Neue Konstante** (nach den Imports, vor `PLACEHOLDER_MAP`):
```python
QUALITAETSFARBE_MAP = {
    "Gewöhnlich": "weiß-silberner Akzent",
    "Selten":     "smaragdgrüner Akzent",
    "Episch":     "blauer Akzent",
    "Magisch":    "violetter magischer Akzent",
    "Legendär":   "gold-orangefarbener magischer Akzent",
}
```

**Lambda in `PLACEHOLDER_MAP` ändern** (Zeile ~50):
```python
# vorher:
"[QUALITÄTSFARBE]": lambda m: str(m.get("qualitaetsfarbe", "")),
# nachher:
"[QUALITÄTSFARBE]": lambda m: QUALITAETSFARBE_MAP.get(str(m.get("qualitaet", "")), ""),
```

### 2. `qualitaetsfarbe`-Feld aus allen Karten-Dateien entfernen

Das Feld `qualitaetsfarbe:` aus dem YAML-Frontmatter aller 40 `cards/*.md` löschen.

### 3. `qualitaetsstufen.md` — Farb-Inkonsistenz korrigieren

Episch und Magisch waren vertauscht. Korrekt:
- Episch (Rare): Blau (#0070DD) / Blauer Schimmer
- Magisch (Epic): Violett (#A335EE) / Violetter Schimmer

## Verifikation

1. `python generate_cards.py cards/01-*.md --dry-run` o.ä. – prüfen dass `[QUALITÄTSFARBE]` korrekt substituiert wird
2. Sicherstellen dass Karten ohne `qualitaetsfarbe`-Frontmatter korrekt funktionieren
