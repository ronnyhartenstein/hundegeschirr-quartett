# Hundegeschirr-Quartett – Projektkontext für Claude

## Was ist das?

Ein mittelalterliches Fantasy-Trumpfquartett (Supertrumpf) mit Hundegeschirren als Karten. 40 Karten in 5 Qualitätsstufen, jede Karte hat 4 Spielwerte. Bilder werden per `gpt-image-2` generiert.

## Dateistruktur

```
cards/           # 40 Karten-Dateien (01–40), je eine .md pro Karte
output/          # generierte WebP-Bilder (von generate_cards.py)
print/           # druckfertige JPGs (via --print Flag)
master_prompt.md # Image-Prompt-Template mit [PLACEHOLDER]-Tokens
karten.md        # Spieldesign, Balancing, vollständige Kartenliste mit Hunderassen
qualitaetsstufen.md  # Farben und Symbole je Qualitätsstufe
platzhalter-beispiele.md  # Beispielwerte für die Prompt-Platzhalter
generate_cards.py  # Bildgenerierungs-Script (OpenAI gpt-image-2)
docker-compose.yml # Docker-Setup für generate_cards.py
```

## Karten-Dateiformat

Jede Karte in `cards/` hat YAML-Frontmatter + zwei Markdown-Abschnitte:

```markdown
---
nummer: 01
name: Schlichtes Geschirr des Bauern
qualitaet: Gewöhnlich          # Gewöhnlich | Selten | Episch | Magisch | Legendär
qualitaetsfarbe: weiß-silberner Akzent
zugkraft: 44
schutz: 44
beweglichkeit: 40
instinkt: 42
hunderasse: Berner Sennenhund
pose: steht ruhig auf einem Feldweg vor einem Bauerndorf
hintergrund: mittelalterliches Dorf am Waldrand
geschirr_beschreibung: robustes braunes Leder mit einfachen Eisenschnallen
---

## Flavourtext

Ein kurzer Satz mit Würze zur Karte.

## Bildprompt

Szenenspezifische Bildbeschreibung für gpt-image-2 (ergänzt das master_prompt.md Template).
```

## Spielwerte und Balancing

| Qualität   | Gesamtwert |
|------------|------------|
| Gewöhnlich | 17         |
| Selten     | 20         |
| Episch     | 23         |
| Magisch    | 26         |
| Legendär   | 30         |

Werte gehen von 1–10, höher ist besser. Jede Karte hat eine Stärke und Schwächen – auch gewöhnliche Karten können magische in einzelnen Werten schlagen.

## Placeholder-Mapping (master_prompt.md → Frontmatter)

| Placeholder          | Frontmatter-Feld       | Transformation              |
|----------------------|------------------------|-----------------------------|
| `[QUALITÄT]`         | `qualitaet`            | as-is (z. B. „Gewöhnlich")  |
| `[NAME]`             | `name`                 | as-is (vollständiger Name)  |
| `[HUNDERASSE]`       | `hunderasse`           | —                           |
| `[POSE]`             | `pose`                 | —                           |
| `[GESCHIRR_BESCHREIBUNG]` | `geschirr_beschreibung` | —                      |
| `[QUALITÄTSFARBE]`   | `qualitaetsfarbe`      | —                           |
| `[HINTERGRUND]`      | `hintergrund`          | —                           |
| `[ZUGKRAFT]`         | `zugkraft`             | —                           |
| `[SCHUTZ]`           | `schutz`               | —                           |
| `[BEWEGLICHKEIT]`    | `beweglichkeit`        | —                           |
| `[INSTINKT]`         | `instinkt`             | —                           |
| `[FLAVOURTEXT]`      | `## Flavourtext`-Body  | aus Markdown-Abschnitt      |

## Hunderassen-Zuordnung (thematisch)

- **Tschechoslowakischer Wolfhund** – Seher (Legendär)
- **Tibetischer Mastiff** – Urvater (Legendär)
- **Leonberger** – Götterbote (Legendär)
- **Azawakh** – Phantomläufer (Legendär)
- **Neapolitanischer Mastiff** – Hochkönig (Legendär)
- **Kaukasischer Owtscharka** – Schlachtkaiser (Legendär)
- **Saarloos-Wolfhund** – Sternenwanderer (Legendär)
- **Kangal** – Weltenwanderer (Legendär)
- **Berner Sennenhund** – Bauer, Reisender, Paladin, Lichtbringer, Bergwächter
- **Mastiff** – Knecht, Packtier, Kriegshund, Söldner, Krieger, Flammenläufer
- **Windhund** – Bote, Läufer, Späher, Berittener, Kundschafter, Windjäger
- **Schwarzer Windhund** – Schattenschnüffler
- **Deutscher Schäferhund** – Wächter, Grenzer, Leibwächter, Wachhund
- **Irischer Wolfshund** – Jäger, Ritter, Adliger, Beschwörer
- **Dackel** – Fährtenhund, Fallensteller
- **Bluthund** – Fährtenleser
- **Border Collie** – Hirte
- **Deutsche Dogge** – Flammenläufer
- **Husky** – Eiszahnläufer

## Konventionen

- Neue Karten: Dateiname `NN-slug-des-namens.md`, Nummer zweistellig
- Gesamtwert der Spielwerte muss der Qualitätsstufe entsprechen (siehe Tabelle)
- `karten.md` ist die kanonische Referenz für alle Karten – Änderungen dort auch in der Card-Datei nachführen
- Generierte Bilder (`output/`, `print/`) werden ins Repo eingecheckt
