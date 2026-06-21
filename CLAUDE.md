# Hundegeschirr-Quartett – Projektkontext für Claude

## Was ist das?

Ein mittelalterliches Fantasy-Trumpfquartett (Supertrumpf) mit Hundegeschirren als Karten. 40 Karten in 5 Qualitätsstufen, jede Karte hat 4 Spielwerte. Bilder werden per `gpt-image-2` generiert.

## Dateistruktur

```
cards/                    # 40 Karten-Dateien (01–40), je eine .md pro Karte
output/                   # generierte WebP-Bilder (von generate_cards.py)
print/                    # druckfertige JPGs (via --print Flag)
back/                     # Kartenrücken-Varianten
master_prompt.md          # Image-Prompt-Template mit [PLACEHOLDER]-Tokens
karten.md                 # Spieldesign, Balancing, vollständige Kartenliste mit Hunderassen
qualitaetsstufen.md       # Farben und Symbole je Qualitätsstufe
rueckseite.md             # Kartenrücken-Prompt und Varianten
platzhalter-beispiele.md  # Beispielwerte für die Prompt-Platzhalter
generate_cards.py         # Bildgenerierungs-Script (OpenAI gpt-image-2)
visualize_balance.py      # Balancing-Visualisierung → balance.html  ← GENERIERT, nie direkt editieren!
docker-compose.yml        # Docker-Setup für generate_cards.py
```

## Karten-Dateiformat

Jede Karte in `cards/` hat YAML-Frontmatter + zwei Markdown-Abschnitte:

```markdown
---
nummer: 01
name: Schlichtes Geschirr des Bauern
qualitaet: Gewöhnlich          # Gewöhnlich | Selten | Episch | Magisch | Legendär
zugkraft: 5
schutz: 4
beweglichkeit: 4
instinkt: 4
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
| Gewöhnlich | 23         |
| Selten     | 26         |
| Episch     | 29         |
| Magisch    | 32         |
| Legendär   | 34         |

Werte gehen von 1–10, höher ist besser. Jede Karte hat eine Stärke und Schwächen – auch gewöhnliche Karten können magische in einzelnen Werten schlagen.

## Placeholder-Mapping (master_prompt.md → Frontmatter)

| Placeholder          | Frontmatter-Feld       | Transformation              |
|----------------------|------------------------|-----------------------------|
| `[QUALITÄT]`         | `qualitaet`            | as-is (z. B. „Gewöhnlich")  |
| `[NAME]`             | `name`                 | as-is (vollständiger Name)  |
| `[HUNDERASSE]`       | `hunderasse`           | —                           |
| `[POSE]`             | `pose`                 | —                           |
| `[GESCHIRR_BESCHREIBUNG]` | `geschirr_beschreibung` | —                      |
| `[QUALITÄTSFARBE]`   | `qualitaet`            | via `QUALITAETSFARBE_MAP` im Script |
| `[HINTERGRUND]`      | `hintergrund`          | —                           |
| `[ZUGKRAFT]`         | `zugkraft`             | —                           |
| `[SCHUTZ]`           | `schutz`               | —                           |
| `[BEWEGLICHKEIT]`    | `beweglichkeit`        | —                           |
| `[INSTINKT]`         | `instinkt`             | —                           |
| `[KNURREN]`          | `knurren`              | —                           |
| `[FLAVOURTEXT]`      | `## Flavourtext`-Body  | aus Markdown-Abschnitt      |

## Hunderassen-Zuordnung (thematisch)

Jede Rasse erscheint genau einmal. Legendäre Karten haben ihre eigene Einzelrasse.

**Legendär (8 Karten):**
- **Tschechoslowakischer Wolfhund** – Seher
- **Tibetischer Mastiff** – Urvater
- **Leonberger** – Götterbote
- **Azawakh** – Phantomläufer
- **Neapolitanischer Mastiff** – Hochkönig
- **Kaukasischer Owtscharka** – Schlachtkaiser
- **Saarloos-Wolfhund** – Sternenwanderer
- **Komondor** – Gaukler *(absurd: B10/I10/K10 – höchstes Knurren im Spiel, aber Z2/S2)*

**Gewöhnlich (8 Karten):**
- **Berner Sennenhund** – Bauer
- **Mastiff** – Knecht
- **Dackel** – Fährtenhund
- **Windhund** – Bote
- **Deutscher Schäferhund** – Wächter
- **Whippet** – Läufer
- **Corgi** – Hofbote *(absurd: Knurren 8, Beweglichkeit 2)*
- **Border Collie** – Hirte

**Selten (8 Karten):**
- **Bernhardiner** – Reisender
- **Kelpie** – Späher
- **Bluthund** – Fährtenleser
- **Rottweiler** – Grenzer
- **Basset Hound** – Faulenzer *(absurd: Beweglichkeit 1 = Minimum im Spiel, Instinkt 9)*
- **Borzoi** – Bote (Schnallengeschirr)
- **Bulldogge** – Kriegshund
- **Dobermann** – Leibwächter

**Episch (8 Karten):**
- **Deutsche Dogge** – Ritter
- **Golden Retriever** – Paladin
- **Australian Shepherd** – Berittener
- **Afghaner Windhund** – Aufschneider *(absurd: Schutz 2, kein Biss – läuft weg)*
- **Jack Russell Terrier** – Fallensteller
- **Dalmatiner** – Kundschafter
- **Boxer** – Söldner
- **Schnauzer** – Wachhund

**Magisch (8 Karten):**
- **Pudel** – Beschwörer *(absurd: Zauberer-Pudel, Instinkt 10)*
- **Mops** – Krieger *(absurd: Zugkraft 10)*
- **Nackthund** – Nachtschnüffler
- **Samojede** – Lichtbringer
- **Chihuahua** – Flammenläufer *(absurd: Zugkraft 10)*
- **Husky** – Eiszahnläufer
- **Beagle** – Windjäger
- **Wolfsspitz** – Bergwächter

## Konventionen

- **Kartenlimit: 40 Karten – absolutes Drucklimit, nicht überschreiten**
- Jede Hunderasse erscheint genau einmal im Deck
- Neue Karten: Dateiname `NN-slug-des-namens.md`, Nummer zweistellig
- Gesamtwert der Spielwerte muss der Qualitätsstufe entsprechen (siehe Tabelle)
- **`karten.md` ist die kanonische Referenz für alle Kartenwerte** – bei Fragen zu Stats immer dort zuerst nachschauen; Änderungen dort auch in der jeweiligen Card-Datei nachführen
- Generierte Bilder (`output/`, `print/`) werden ins Repo eingecheckt
