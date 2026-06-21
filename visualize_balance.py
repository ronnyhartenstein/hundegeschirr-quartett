#!/usr/bin/env python3
"""Generates balance.html — a visual overview of card stat distribution per quality tier."""

import glob
import json
import yaml
from pathlib import Path

CARDS_DIR = Path(__file__).parent / "cards"
OUTPUT_FILE = Path(__file__).parent / "balance.html"

QUALITY_ORDER = ["Gewöhnlich", "Selten", "Episch", "Magisch", "Legendär"]
QUALITY_TARGET = {"Gewöhnlich": 23, "Selten": 26, "Episch": 29, "Magisch": 32, "Legendär": 34}
QUALITY_COLORS = {
    "Gewöhnlich": "#FFFFFF",
    "Selten": "#16a34a",
    "Episch": "#A335EE",
    "Magisch": "#0070DD",
    "Legendär": "#FF8000",
}
STATS = ["zugkraft", "schutz", "beweglichkeit", "instinkt", "knurren"]
STAT_LABELS = {"zugkraft": "Zugkraft", "schutz": "Schutz", "beweglichkeit": "Beweglichkeit", "instinkt": "Instinkt", "knurren": "Knurren"}


def parse_card(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    parts = text.split("---")
    if len(parts) < 3:
        raise ValueError(f"Invalid frontmatter in {path}")
    data = yaml.safe_load(parts[1])
    data["file"] = path.name
    return data


def load_cards() -> list[dict]:
    files = sorted(glob.glob(str(CARDS_DIR / "*.md")))
    return [parse_card(Path(f)) for f in files]


def compute_stats(cards: list[dict]) -> dict:
    by_quality = {q: [] for q in QUALITY_ORDER}
    for card in cards:
        q = card["qualitaet"]
        by_quality[q].append(card)

    result = {}
    for q, group in by_quality.items():
        result[q] = {}
        for stat in STATS:
            vals = [c[stat] for c in group]
            result[q][stat] = {
                "min": min(vals),
                "max": max(vals),
                "avg": sum(vals) / len(vals),
                "values": vals,
            }
    return result


def build_html(cards: list[dict], stats: dict) -> str:
    cards_json = json.dumps(cards, ensure_ascii=False)
    stats_json = json.dumps(stats, ensure_ascii=False)
    quality_order_json = json.dumps(QUALITY_ORDER)
    quality_colors_json = json.dumps(QUALITY_COLORS)
    quality_target_json = json.dumps(QUALITY_TARGET)
    stats_list_json = json.dumps(STATS)
    stat_labels_json = json.dumps(STAT_LABELS)

    return f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Hundegeschirr-Quartett – Balance-Analyse</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"></script>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: system-ui, sans-serif; background: #0f172a; color: #e2e8f0; padding: 2rem; }}
  h1 {{ font-size: 1.8rem; margin-bottom: 0.25rem; color: #f1f5f9; }}
  .subtitle {{ color: #64748b; margin-bottom: 2rem; font-size: 0.9rem; }}
  h2 {{ font-size: 1.2rem; margin: 2rem 0 1rem; color: #cbd5e1; border-bottom: 1px solid #1e293b; padding-bottom: 0.5rem; }}
  .card {{ background: #1e293b; border-radius: 0.75rem; padding: 1.5rem; margin-bottom: 2rem; }}
  .chart-wrap {{ position: relative; height: 380px; }}
  .chart-wrap-tall {{ position: relative; height: 480px; }}
  .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }}
  @media (max-width: 900px) {{ .grid-2 {{ grid-template-columns: 1fr; }} }}

  /* Table */
  table {{ width: 100%; border-collapse: collapse; font-size: 0.85rem; }}
  th {{ background: #0f172a; padding: 0.5rem 0.75rem; text-align: left; color: #94a3b8; font-weight: 600; position: sticky; top: 0; }}
  td {{ padding: 0.4rem 0.75rem; border-bottom: 1px solid #0f172a; }}
  tr:hover td {{ background: #263344; }}
  .badge {{ display: inline-block; padding: 0.15rem 0.5rem; border-radius: 999px; font-size: 0.75rem; font-weight: 600; color: #fff; }}
  .num {{ text-align: right; font-variant-numeric: tabular-nums; }}
  .ok {{ color: #4ade80; }}
  .err {{ color: #f87171; font-weight: 700; }}
  .table-wrap {{ max-height: 480px; overflow-y: auto; border-radius: 0.5rem; }}

  /* Principle & assessment sections */
  .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }}
  @media (max-width: 900px) {{ .info-grid {{ grid-template-columns: 1fr; }} }}
  .info-box {{ background: #0f172a; border-radius: 0.5rem; padding: 1.1rem 1.25rem; border-left: 3px solid #334155; }}
  .info-box h3 {{ font-size: 0.9rem; font-weight: 700; margin-bottom: 0.4rem; color: #e2e8f0; }}
  .info-box p {{ font-size: 0.82rem; color: #94a3b8; line-height: 1.65; }}
  .qual-pill {{ display: inline-flex; align-items: center; gap: 0.3rem; padding: 0.2rem 0.55rem; border-radius: 999px; font-size: 0.72rem; font-weight: 700; margin: 0.15rem 0.1rem; }}
  .section-intro {{ font-size: 0.85rem; color: #94a3b8; line-height: 1.7; margin-bottom: 1.25rem; border-left: 2px solid #1e293b; padding-left: 0.85rem; }}
  .section-intro strong {{ color: #cbd5e1; }}
  .hcard-grid {{ display: flex; flex-wrap: wrap; gap: 0.75rem; margin-top: 0.5rem; }}
  .hcard {{ background: #0f172a; border-radius: 0.5rem; padding: 0.85rem 1rem; flex: 1 1 270px; border-left: 3px solid #334155; }}
  .hcard-name {{ font-size: 0.82rem; font-weight: 700; margin-bottom: 0.2rem; color: #e2e8f0; }}
  .hcard-meta {{ font-size: 0.72rem; color: #64748b; margin-bottom: 0.35rem; }}
  .hcard-desc {{ font-size: 0.8rem; color: #94a3b8; line-height: 1.55; }}
  .stat-chip {{ display: inline-block; padding: 0.1rem 0.45rem; border-radius: 4px; font-size: 0.72rem; font-weight: 700; background: #1e293b; color: #e2e8f0; margin: 0 0.1rem; }}
  .upset-table {{ width: 100%; border-collapse: collapse; font-size: 0.83rem; margin-top: 0.75rem; }}
  .upset-table th {{ background: #0f172a; padding: 0.45rem 0.75rem; text-align: left; color: #94a3b8; font-weight: 600; }}
  .upset-table td {{ padding: 0.4rem 0.75rem; border-bottom: 1px solid #1e293b; color: #cbd5e1; }}
  .upset-table tr:hover td {{ background: #263344; }}
  .legend-table {{ width: 100%; border-collapse: collapse; font-size: 0.83rem; margin-top: 0.75rem; }}
  .legend-table th {{ background: #0f172a; padding: 0.45rem 0.75rem; text-align: left; color: #94a3b8; font-weight: 600; }}
  .legend-table td {{ padding: 0.4rem 0.75rem; border-bottom: 1px solid #1e293b; }}
  .legend-table tr:hover td {{ background: #263344; }}
  .insight-box {{ background: #0f172a; border-radius: 0.5rem; padding: 1rem 1.25rem; margin-top: 1rem; border: 1px solid #1e293b; }}
  .insight-box p {{ font-size: 0.83rem; color: #94a3b8; line-height: 1.7; margin: 0; }}
  .insight-box p + p {{ margin-top: 0.5rem; }}
  .sub-h2 {{ font-size: 1rem; margin: 1.5rem 0 0.5rem; color: #94a3b8; border: none; padding: 0; }}
</style>
</head>
<body>
<h1>Hundegeschirr-Quartett</h1>
<p class="subtitle">Balance-Analyse · {len(cards)} Karten · 5 Qualitätsstufen</p>

<h2>Spielprinzip &amp; Balancing</h2>
<div class="card">
  <div class="info-grid">
    <div class="info-box" style="border-color:#3b82f6">
      <h3>Fünf Spielwerte</h3>
      <p>Jede Karte hat fünf Werte (1–10, höher = besser). Der aktive Spieler wählt einen Wert – wer den höheren Wert hat, gewinnt alle Karten der Runde. Bei Gleichstand kommen beide Karten in die Mitte; derselbe Spieler wählt mit der nächsten Karte erneut, und wer dann gewinnt, bekommt alles.</p>
    </div>
    <div class="info-box" style="border-color:#f59e0b">
      <h3>Qualitätsstufen &amp; Gesamtwerte</h3>
      <p>Fünf Stufen mit festem Gesamtpunkte-Soll – der Wert wird <em>nicht</em> aufgedruckt, dient nur dem Balancing. Abstände von +3 pro Stufe; Legendär macht bewusst +4, damit sich diese Karten als echte Supertrümpfe anfühlen.</p>
      <div style="margin-top:0.65rem">
        <span class="qual-pill" style="background:#334155;color:#e2e8f0">Gewöhnlich · 23</span>
        <span class="qual-pill" style="background:#16a34a;color:#fff">Selten · 26</span>
        <span class="qual-pill" style="background:#A335EE;color:#fff">Episch · 29</span>
        <span class="qual-pill" style="background:#0070DD;color:#fff">Magisch · 32</span>
        <span class="qual-pill" style="background:#FF8000;color:#fff">Legendär · 34</span>
      </div>
    </div>
    <div class="info-box" style="border-color:#22c55e">
      <h3>Spezialisten schlagen höhere Stufen</h3>
      <p>Das zentrale Designziel: Auch eine Gewöhnliche Karte kann eine Magische schlagen – wenn der Spieler den richtigen Wert ausruft. Dafür hat jede Karte mindestens eine Stärke und mindestens eine Schwäche, unabhängig von der Qualitätsstufe.</p>
    </div>
    <div class="info-box" style="border-color:#FF8000">
      <h3>Legendäre Karten – Supertrümpfe mit Angriffspunkten</h3>
      <p>Jede Legendäre Karte hat mindestens einen Wert unter 7. Kein Supertrumpf dominiert alle fünf Kategorien gleichzeitig. Wer eine Legendäre Karte mit dem richtigen Wert herausfordert, kann sie trotzdem schlagen.</p>
    </div>
  </div>
</div>

<h2>1 · Kartenübersicht</h2>
<p class="section-intro">Alle {len(cards)} Karten mit ihren Rohwerten. Die Spalte <strong>Gesamt</strong> zeigt die Summe der fünf Spielwerte – grün wenn sie exakt dem Soll der Qualitätsstufe entspricht, rot bei Abweichungen. Das Soll wird nicht auf die Karte gedruckt.</p>
<div class="card">
  <div class="table-wrap">
    <table id="cardTable">
      <thead>
        <tr>
          <th>#</th>
          <th>Name</th>
          <th>Qualität</th>
          <th class="num">Zugkraft</th>
          <th class="num">Schutz</th>
          <th class="num">Beweglichkeit</th>
          <th class="num">Instinkt</th>
          <th class="num">Knurren</th>
          <th class="num">Gesamt</th>
          <th class="num">Soll</th>
        </tr>
      </thead>
      <tbody id="cardTableBody"></tbody>
    </table>
  </div>
</div>

<h2>2 · Durchschnittswerte je Qualitätsstufe</h2>
<p class="section-intro">Durchschnittliche Stat-Werte je Qualitätsstufe. Auffällig: <strong>Instinkt</strong> variiert am wenigsten zwischen den Stufen (Spanne Gewöhnlich→Legendär: ~0,9 Punkte) – Instinkt-Spezialisten aus niedrigen Stufen sind deshalb besonders konkurrenzfähig. <strong>Zugkraft</strong> bei Magisch liegt sogar über dem Legendär-Durchschnitt – bedingt durch die extremen 10er-Werte bei Mops und Chihuahua.</p>
<div class="card">
  <div class="chart-wrap"><canvas id="avgChart"></canvas></div>
</div>

<h2>3 · Wertebereich je Stat &amp; Qualitätsstufe</h2>
<p class="section-intro">Min, Durchschnitt und Max je Stat innerhalb einer Qualitätsstufe. Breite Balken zeigen hohe Streuung – hier verstecken sich die Spezialisten. Selbst innerhalb von Gewöhnlich gibt es Karten mit Wert 10 (Dackel: Instinkt) und Karten mit Wert 1 (Schäferhund: Zugkraft/Beweglichkeit). Diese Streuung ist absichtlich: Sie macht den Werteaufruf zur taktischen Entscheidung.</p>
<div class="card grid-2">
  <div class="chart-wrap"><canvas id="rangeZugkraft"></canvas></div>
  <div class="chart-wrap"><canvas id="rangeSchutz"></canvas></div>
  <div class="chart-wrap"><canvas id="rangeBeweglichkeit"></canvas></div>
  <div class="chart-wrap"><canvas id="rangeInstinkt"></canvas></div>
  <div class="chart-wrap"><canvas id="rangeKnurren"></canvas></div>
</div>

<h2>4 · Gesamtpunkte aller Karten (Ist vs. Soll)</h2>
<p class="section-intro">Jede Karte als farbige Säule, die gestrichelte Linie zeigt den Sollwert ihrer Qualitätsstufe. Alle Säulen sollten exakt auf der Linie landen – Abweichungen weisen auf Balancing-Fehler hin. Die Farbblöcke folgen den Qualitätsfarben: Weiß (Gewöhnlich), Grün (Selten), Lila (Episch), Blau (Magisch), Orange (Legendär).</p>
<div class="card">
  <div class="chart-wrap-tall"><canvas id="totalChart"></canvas></div>
</div>

<h2>5 · Einzelwerte gestapelt je Karte</h2>
<p class="section-intro">Jede Karte als gestapelter Balken – die fünf Farbsegmente zeigen die Verteilung der Punkte auf die einzelnen Stats. Gleichmäßig breite Segmente = ausgewogene Karte; ein dominierendes Segment = Spezialist. Karten mit einer sehr breiten Farbe (z.B. Knurren bei Mops oder Instinkt beim Dackel) sind die taktischen Joker des Decks.</p>
<div class="card">
  <div class="chart-wrap-tall"><canvas id="stackedChart"></canvas></div>
</div>

<h2>6 · Einschätzungen</h2>

<h2 class="sub-h2">Absurde Karten – bewusste Ausreißer</h2>
<p class="section-intro">Diese Karten haben extreme Stat-Kombinationen, die spielerisch für Überraschungen sorgen. Sie sind absichtlich so designed – jede hat ein klares Thema und eine klare Gegenspiel-Lücke.</p>
<div class="card">
  <div class="hcard-grid">
    <div class="hcard" style="border-color:#FFFFFF">
      <div class="hcard-name">Corgi – Flickengeschirr des Hofboten</div>
      <div class="hcard-meta">Gewöhnlich · #07</div>
      <div class="hcard-desc">
        <span class="stat-chip">K 8</span> <span class="stat-chip">Z 7</span> – aber <span class="stat-chip" style="color:#f87171">B 2</span>.
        Der kurzbeinige Hofbote kommt nirgendwo schnell hin, ist aber für seine Stufe überraschend bissig. Knurren 8 schlägt mehrere Magisch-Karten.
      </div>
    </div>
    <div class="hcard" style="border-color:#16a34a">
      <div class="hcard-name">Basset Hound – Schlappohr-Geschirr des Faulenzers</div>
      <div class="hcard-meta">Selten · #13</div>
      <div class="hcard-desc">
        <span class="stat-chip">I 9</span> <span class="stat-chip">S 7</span> – aber <span class="stat-chip" style="color:#f87171">B 1</span> (Minimum im gesamten Spiel).
        Er macht nichts schnell. Dafür erschnüffelt er alles. Gegenspiel: jeden Beweglichkeitswert über 1 gewinnt gegen ihn.
      </div>
    </div>
    <div class="hcard" style="border-color:#A335EE">
      <div class="hcard-name">Afghaner Windhund – Goldgeschirr des Aufschneiders</div>
      <div class="hcard-meta">Episch · #20</div>
      <div class="hcard-desc">
        <span class="stat-chip">Z 8</span> <span class="stat-chip">B 9</span> <span class="stat-chip">I 8</span> – aber <span class="stat-chip" style="color:#f87171">S 2</span> <span class="stat-chip" style="color:#f87171">K 2</span>.
        Läuft schnell weg, macht viel Wind, hält aber keinen Treffer aus und beißt nie.
      </div>
    </div>
    <div class="hcard" style="border-color:#0070DD">
      <div class="hcard-name">Mops – Plattenpanzer des Kriegers</div>
      <div class="hcard-meta">Magisch · #26</div>
      <div class="hcard-desc">
        <span class="stat-chip">Z 10</span> <span class="stat-chip">S 8</span> <span class="stat-chip">K 9</span> – aber <span class="stat-chip" style="color:#f87171">I 1</span> <span class="stat-chip" style="color:#f87171">B 4</span>.
        Unverhoffte Zugkraft 10 aus einem Mops. Findet keine Fährte, rennt nirgendwo hin – aber macht alles kurz und klein.
      </div>
    </div>
    <div class="hcard" style="border-color:#0070DD">
      <div class="hcard-name">Chihuahua – Drachengeschirr des Flammenläufers</div>
      <div class="hcard-meta">Magisch · #29</div>
      <div class="hcard-desc">
        <span class="stat-chip">Z 10</span> <span class="stat-chip">S 7</span> <span class="stat-chip">K 9</span> – aber <span class="stat-chip" style="color:#f87171">I 1</span> <span class="stat-chip" style="color:#f87171">B 5</span>.
        Zweite Magisch-Karte mit Zugkraft 10 – damit hat diese Stufe den höchsten Zugkraft-Durchschnitt aller Stufen.
      </div>
    </div>
    <div class="hcard" style="border-color:#FF8000">
      <div class="hcard-name">Komondor – Narrenschellen-Geschirr des Gauklers</div>
      <div class="hcard-meta">Legendär · #40</div>
      <div class="hcard-desc">
        <span class="stat-chip">K 10</span> <span class="stat-chip">B 10</span> <span class="stat-chip">I 10</span> – aber <span class="stat-chip" style="color:#f87171">Z 2</span> <span class="stat-chip" style="color:#f87171">S 2</span>.
        Höchstes Knurren im Spiel. Unantastbar in drei Stats. Ruft ein Gegner Zugkraft oder Schutz aus, verliert der Gaukler gegen nahezu jede Karte im Deck.
      </div>
    </div>
  </div>
</div>

<h2 class="sub-h2">Stufen-Überraschungen – Gewöhnlich schlägt Magisch &amp; Legendär</h2>
<p class="section-intro">Durch die breite Stat-Streuung innerhalb jeder Qualitätsstufe gibt es zahlreiche Konstellationen, in denen eine Gewöhnliche Karte eine Magische oder sogar Legendäre schlägt.</p>
<div class="card">
  <table class="upset-table">
    <thead>
      <tr>
        <th>Gewöhnliche Karte</th>
        <th>Wert</th>
        <th>Schlägt</th>
        <th>Wert (Gegner)</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Leichtes Geschirr des Läufers (Whippet)</td>
        <td><span class="stat-chip">B 8</span></td>
        <td>Plattenpanzer des Kriegers (Magisch, Mops)</td>
        <td><span class="stat-chip" style="color:#f87171">B 4</span></td>
      </tr>
      <tr>
        <td>Strapazierfähiges Geschirr des Wächters (Schäferhund)</td>
        <td><span class="stat-chip">S 8</span></td>
        <td>Schattengeschirr des Nachtschnüfflers (Magisch)</td>
        <td><span class="stat-chip" style="color:#f87171">S 3</span></td>
      </tr>
      <tr>
        <td>Strapazierfähiges Geschirr des Wächters (Schäferhund)</td>
        <td><span class="stat-chip">S 8</span></td>
        <td>Schicksalsgeschirr des Sehers (Legendär)</td>
        <td><span class="stat-chip" style="color:#f87171">S 7</span></td>
      </tr>
      <tr>
        <td>Einfaches Leder des Fährtenhundes (Dackel)</td>
        <td><span class="stat-chip">I 10</span></td>
        <td>Titanengeschirr des Urvaters (Legendär)</td>
        <td><span class="stat-chip" style="color:#f87171">I 3</span></td>
      </tr>
      <tr>
        <td>Einfaches Leder des Fährtenhundes (Dackel)</td>
        <td><span class="stat-chip">I 10</span></td>
        <td>Kriegsgeschirr des Schlachtkaisers (Legendär)</td>
        <td><span class="stat-chip" style="color:#f87171">I 1</span></td>
      </tr>
      <tr>
        <td>Einfaches Leder des Fährtenhundes (Dackel)</td>
        <td><span class="stat-chip">I 10</span></td>
        <td>Heilsgeschirr des Götterboten (Legendär)</td>
        <td><span class="stat-chip" style="color:#f87171">I 7</span></td>
      </tr>
      <tr>
        <td>Robustes Geschirr des Knechts (Mastiff)</td>
        <td><span class="stat-chip">K 9</span></td>
        <td>Runengeschirr des Beschwörers (Magisch, Pudel)</td>
        <td><span class="stat-chip" style="color:#f87171">K 4</span></td>
      </tr>
    </tbody>
  </table>
  <div class="insight-box">
    <p>Der <strong>Dackel</strong> (Gewöhnlich, Instinkt 10) schlägt in diesem Wert 5 von 8 Legendären Karten – darunter den Schlachtkaiser (Instinkt 1) und den Urvater (Instinkt 3). Kein anderer Wert zeigt so wenig Respekt vor Qualitätsstufen wie <strong>Instinkt</strong>.</p>
  </div>
</div>

<h2 class="sub-h2">Legendäre Karten – Stärken &amp; Angriffspunkte</h2>
<p class="section-intro">Jede Legendäre Karte hat mindestens einen Wert unter 7. Diese Schwächen sind bewusste Design-Entscheidungen: Sie schaffen Gegenspiel und verhindern, dass Legendäre Karten automatisch gewinnen.</p>
<div class="card">
  <table class="legend-table">
    <thead>
      <tr><th>#</th><th>Karte</th><th>Stärke</th><th>Angriffspunkt</th></tr>
    </thead>
    <tbody>
      <tr>
        <td>33</td><td>Schicksalsgeschirr des Sehers</td>
        <td><span class="stat-chip" style="color:#4ade80">I 10</span></td>
        <td><span class="stat-chip" style="color:#f87171">Z 5</span> <span class="stat-chip" style="color:#f87171">K 4</span></td>
      </tr>
      <tr>
        <td>34</td><td>Titanengeschirr des Urvaters</td>
        <td><span class="stat-chip" style="color:#4ade80">Z 10</span> <span class="stat-chip" style="color:#4ade80">K 8</span></td>
        <td><span class="stat-chip" style="color:#f87171">I 3</span> <span class="stat-chip" style="color:#f87171">B 5</span></td>
      </tr>
      <tr>
        <td>35</td><td>Heilsgeschirr des Götterboten</td>
        <td><span class="stat-chip" style="color:#4ade80">S 10</span></td>
        <td><span class="stat-chip" style="color:#f87171">Z 5</span> <span class="stat-chip" style="color:#f87171">K 5</span></td>
      </tr>
      <tr>
        <td>36</td><td>Geistergeschirr des Phantomläufers</td>
        <td><span class="stat-chip" style="color:#4ade80">B 10</span> <span class="stat-chip" style="color:#4ade80">I 10</span></td>
        <td><span class="stat-chip" style="color:#f87171">Z 4</span> <span class="stat-chip" style="color:#f87171">K 4</span></td>
      </tr>
      <tr>
        <td>37</td><td>Kronengeschirr des Hochkönigs</td>
        <td>Ausgeglichen (min. 5)</td>
        <td><span class="stat-chip" style="color:#fbbf24">I 5</span> – kein Spitzenwert, berechenbar</td>
      </tr>
      <tr>
        <td>38</td><td>Kriegsgeschirr des Schlachtkaisers</td>
        <td><span class="stat-chip" style="color:#4ade80">Z 10</span> <span class="stat-chip" style="color:#4ade80">K 9</span> <span class="stat-chip" style="color:#4ade80">S 9</span></td>
        <td><span class="stat-chip" style="color:#f87171">I 1</span> – leichteste Beute für Instinkt-Spezialisten</td>
      </tr>
      <tr>
        <td>39</td><td>Sterngeschirr des Sternenwanderers</td>
        <td><span class="stat-chip" style="color:#4ade80">B 9</span> <span class="stat-chip" style="color:#4ade80">I 8</span></td>
        <td><span class="stat-chip" style="color:#f87171">Z 6</span> <span class="stat-chip" style="color:#f87171">S 6</span></td>
      </tr>
      <tr>
        <td>40</td><td>Narrenschellen-Geschirr des Gauklers</td>
        <td><span class="stat-chip" style="color:#4ade80">K 10</span> <span class="stat-chip" style="color:#4ade80">B 10</span> <span class="stat-chip" style="color:#4ade80">I 10</span></td>
        <td><span class="stat-chip" style="color:#f87171">Z 2</span> <span class="stat-chip" style="color:#f87171">S 2</span> – verliert gegen fast jede Karte in diesen Werten</td>
      </tr>
    </tbody>
  </table>
</div>

<script>
const cards = {cards_json};
const statsByQuality = {stats_json};
const QUALITY_ORDER = {quality_order_json};
const QUALITY_COLORS = {quality_colors_json};
const QUALITY_TARGET = {quality_target_json};
const STATS = {stats_list_json};
const STAT_LABELS = {stat_labels_json};

// ── 1 · Table ────────────────────────────────────────────────────────────────
const tbody = document.getElementById('cardTableBody');
cards.forEach((c, i) => {{
  const total = c.zugkraft + c.schutz + c.beweglichkeit + c.instinkt + c.knurren;
  const target = QUALITY_TARGET[c.qualitaet];
  const ok = total === target;
  const color = QUALITY_COLORS[c.qualitaet];
  const textColor = color === '#FFFFFF' ? '#0f172a' : '#fff';
  tbody.insertAdjacentHTML('beforeend', `
    <tr>
      <td>${{String(i+1).padStart(2,'0')}}</td>
      <td>${{c.name}}</td>
      <td><span class="badge" style="background:${{color}};color:${{textColor}}">${{c.qualitaet}}</span></td>
      <td class="num">${{c.zugkraft}}</td>
      <td class="num">${{c.schutz}}</td>
      <td class="num">${{c.beweglichkeit}}</td>
      <td class="num">${{c.instinkt}}</td>
      <td class="num">${{c.knurren}}</td>
      <td class="num ${{ok?'ok':'err'}}">${{total}}</td>
      <td class="num" style="color:#64748b">${{target}}</td>
    </tr>`);
}});

// ── 2 · Avg grouped bar ──────────────────────────────────────────────────────
const statColors = ['#3b82f6','#22c55e','#f59e0b','#ec4899','#ef4444'];
const avgDatasets = STATS.map((stat, i) => ({{
  label: STAT_LABELS[stat],
  data: QUALITY_ORDER.map(q => statsByQuality[q][stat].avg),
  backgroundColor: statColors[i],
  borderRadius: 4,
}}));
new Chart(document.getElementById('avgChart'), {{
  type: 'bar',
  data: {{ labels: QUALITY_ORDER, datasets: avgDatasets }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    plugins: {{ legend: {{ labels: {{ color: '#cbd5e1' }} }} }},
    scales: {{
      x: {{ ticks: {{ color: '#94a3b8' }}, grid: {{ color: '#1e293b' }} }},
      y: {{ min: 0, max: 10, ticks: {{ color: '#94a3b8' }}, grid: {{ color: '#1e293b' }} }},
    }},
  }},
}});

// ── 3 · Range charts (one per stat) ─────────────────────────────────────────
STATS.forEach((stat, idx) => {{
  const canvasId = 'range' + stat.charAt(0).toUpperCase() + stat.slice(1);
  const avgs = QUALITY_ORDER.map(q => statsByQuality[q][stat].avg);
  const mins = QUALITY_ORDER.map(q => statsByQuality[q][stat].min);
  const maxs = QUALITY_ORDER.map(q => statsByQuality[q][stat].max);

  new Chart(document.getElementById(canvasId), {{
    type: 'bar',
    data: {{
      labels: QUALITY_ORDER,
      datasets: [
        {{
          label: 'Max',
          data: maxs,
          backgroundColor: statColors[idx] + '55',
          borderColor: statColors[idx],
          borderWidth: 1,
          borderRadius: 2,
        }},
        {{
          label: 'Ø',
          data: avgs,
          backgroundColor: statColors[idx] + 'cc',
          borderColor: statColors[idx],
          borderWidth: 1,
          borderRadius: 2,
          type: 'bar',
        }},
        {{
          label: 'Min',
          data: mins,
          backgroundColor: '#0f172a',
          borderColor: statColors[idx] + '88',
          borderWidth: 1,
          borderRadius: 2,
          type: 'bar',
        }},
      ],
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      plugins: {{
        title: {{ display: true, text: STAT_LABELS[stat], color: '#e2e8f0', font: {{ size: 14 }} }},
        legend: {{ labels: {{ color: '#94a3b8', boxWidth: 12 }} }},
      }},
      scales: {{
        x: {{ ticks: {{ color: '#94a3b8' }}, grid: {{ color: '#1e293b' }} }},
        y: {{ min: 0, max: 10, ticks: {{ color: '#94a3b8' }}, grid: {{ color: '#1e293b' }} }},
      }},
    }},
  }});
}});

// ── 4 · Total points per card ────────────────────────────────────────────────
const totalLabels = cards.map(c => c.nummer ? String(c.nummer).padStart(2,'0') : '');
const totalValues = cards.map(c => c.zugkraft + c.schutz + c.beweglichkeit + c.instinkt + c.knurren);
const totalColors = cards.map(c => QUALITY_COLORS[c.qualitaet]);
const totalTargets = cards.map(c => QUALITY_TARGET[c.qualitaet]);

// Annotation lines for each quality target
const annotationLines = Object.entries(QUALITY_TARGET).map(([q, t]) => ({{
  type: 'line',
  yMin: t, yMax: t,
  borderColor: QUALITY_COLORS[q] + '88',
  borderWidth: 1,
  borderDash: [4, 4],
  label: {{ content: q + ' (' + t + ')', display: true, position: 'start', color: QUALITY_COLORS[q], font: {{ size: 10 }} }},
}}));

new Chart(document.getElementById('totalChart'), {{
  type: 'bar',
  data: {{
    labels: totalLabels,
    datasets: [
      {{
        label: 'Gesamtwert',
        data: totalValues,
        backgroundColor: totalColors,
        borderRadius: 3,
      }},
      {{
        label: 'Soll',
        data: totalTargets,
        type: 'line',
        borderColor: '#ffffff33',
        borderWidth: 1,
        borderDash: [3, 3],
        pointRadius: 0,
        fill: false,
        tension: 0,
      }},
    ],
  }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    plugins: {{
      legend: {{ labels: {{ color: '#cbd5e1' }} }},
      tooltip: {{
        callbacks: {{
          title: (items) => cards[items[0].dataIndex].name,
          afterBody: (items) => {{
            const c = cards[items[0].dataIndex];
            return `Qualität: ${{c.qualitaet}}\\nSoll: ${{QUALITY_TARGET[c.qualitaet]}}`;
          }},
        }},
      }},
    }},
    scales: {{
      x: {{ ticks: {{ color: '#94a3b8', maxRotation: 0 }}, grid: {{ color: '#1e293b' }} }},
      y: {{ min: 14, max: 38, ticks: {{ color: '#94a3b8' }}, grid: {{ color: '#1e293b' }} }},
    }},
  }},
}});

// ── 5 · Stacked individual stats per card ────────────────────────────────────
const stackedDatasets = STATS.map((stat, i) => ({{
  label: STAT_LABELS[stat],
  data: cards.map(c => c[stat]),
  backgroundColor: statColors[i],
  borderWidth: 0,
}}));

new Chart(document.getElementById('stackedChart'), {{
  type: 'bar',
  data: {{ labels: totalLabels, datasets: stackedDatasets }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    plugins: {{
      legend: {{ labels: {{ color: '#cbd5e1' }} }},
      tooltip: {{
        callbacks: {{
          title: (items) => cards[items[0].dataIndex].name,
          afterTitle: (items) => {{
            const c = cards[items[0].dataIndex];
            return `${{c.qualitaet}} · Gesamt: ${{STATS.reduce((s, st) => s + c[st], 0)}}`;
          }},
        }},
      }},
    }},
    scales: {{
      x: {{ stacked: true, ticks: {{ color: '#94a3b8', maxRotation: 0 }}, grid: {{ color: '#1e293b' }} }},
      y: {{ stacked: true, min: 0, max: 38, ticks: {{ color: '#94a3b8' }}, grid: {{ color: '#1e293b' }} }},
    }},
  }},
}});
</script>
</body>
</html>
"""


def main():
    cards = load_cards()
    stats = compute_stats(cards)
    html = build_html(cards, stats)
    OUTPUT_FILE.write_text(html, encoding="utf-8")
    print(f"Generated: {OUTPUT_FILE}")
    print(f"Cards parsed: {len(cards)}")
    for q in QUALITY_ORDER:
        count = sum(1 for c in cards if c["qualitaet"] == q)
        wrong = [c for c in cards if c["qualitaet"] == q and
                 c["zugkraft"] + c["schutz"] + c["beweglichkeit"] + c["instinkt"] + c["knurren"] != QUALITY_TARGET[q]]
        status = f"✓" if not wrong else f"✗ {len(wrong)} falsch"
        print(f"  {q}: {count} Karten  [{status}]")


if __name__ == "__main__":
    main()
