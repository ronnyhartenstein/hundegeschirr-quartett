#!/usr/bin/env python3
"""Generates balance.html — a visual overview of card stat distribution per quality tier."""

import glob
import json
import yaml
from pathlib import Path

CARDS_DIR = Path(__file__).parent / "cards"
OUTPUT_FILE = Path(__file__).parent / "balance.html"

QUALITY_ORDER = ["Gewöhnlich", "Selten", "Episch", "Magisch", "Legendär"]
QUALITY_TARGET = {"Gewöhnlich": 21, "Selten": 24, "Episch": 27, "Magisch": 30, "Legendär": 34}
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
</style>
</head>
<body>
<h1>Hundegeschirr-Quartett</h1>
<p class="subtitle">Balance-Analyse · {len(cards)} Karten · 5 Qualitätsstufen</p>

<h2>1 · Kartenübersicht</h2>
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
<div class="card">
  <div class="chart-wrap"><canvas id="avgChart"></canvas></div>
</div>

<h2>3 · Wertebereich je Stat &amp; Qualitätsstufe</h2>
<div class="card grid-2">
  <div class="chart-wrap"><canvas id="rangeZugkraft"></canvas></div>
  <div class="chart-wrap"><canvas id="rangeSchutz"></canvas></div>
  <div class="chart-wrap"><canvas id="rangeBeweglichkeit"></canvas></div>
  <div class="chart-wrap"><canvas id="rangeInstinkt"></canvas></div>
  <div class="chart-wrap"><canvas id="rangeKnurren"></canvas></div>
</div>

<h2>4 · Gesamtpunkte aller Karten (Ist vs. Soll)</h2>
<div class="card">
  <div class="chart-wrap-tall"><canvas id="totalChart"></canvas></div>
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
const totalValues = cards.map(c => c.zugkraft + c.schutz + c.beweglichkeit + c.instinkt);
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
