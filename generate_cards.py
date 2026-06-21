#!/usr/bin/env python3
"""
Generates card images for Hundegeschirr-Quartett using the OpenAI gpt-image-2 model.

Usage:
    python generate_cards.py                          # Generate all missing images
    python generate_cards.py --force                  # Regenerate all images
    python generate_cards.py cards/01-*.md            # Single card
    python generate_cards.py --quality high           # Image quality: low/medium/high
    python generate_cards.py --recompress             # Re-encode oversized output WebPs
    python generate_cards.py --print                  # Convert output/ WebPs to print/ JPGs

Requires:
    OPENAI_API_KEY environment variable
    pip install openai python-frontmatter Pillow
"""

import argparse
import base64
import datetime
import io
import os
import re
import sys
import time
from pathlib import Path

import frontmatter
from openai import OpenAI
from PIL import Image

CARDS_DIR = Path(__file__).parent / "cards"
OUTPUT_DIR = Path(__file__).parent / "output"
PRINT_DIR = Path(__file__).parent / "print"
MASTER_PROMPT_FILE = Path(__file__).parent / "master_prompt.md"
IMAGE_SIZE = "832x1424"  # 70 x 120 mm @ 300 DPI, beide Dimensionen durch 16 teilbar
MODEL = "gpt-image-2"
RATE_LIMIT_DELAY = 1.0  # seconds between API calls
WEBP_QUALITY = 25       # lossy WebP quality (0–100); 25 is plenty for low/medium API output
RECOMPRESS_THRESHOLD = 3 * 1024 * 1024  # bytes; images larger than this get recompressed

QUALITAETSFARBE_MAP = {
    "Gewöhnlich": "weiß-silberner Akzent",
    "Selten":     "smaragdgrüner Akzent",
    "Episch":     "violetter Akzent",
    "Magisch":    "blauer magischer Akzent",
    "Legendär":   "gold-orangefarbener magischer Akzent",
}


def _highest_stat_names(meta: dict) -> str:
    stats = {
        "Zugkraft":      int(meta.get("zugkraft", 0)),
        "Schutz":        int(meta.get("schutz", 0)),
        "Beweglichkeit": int(meta.get("beweglichkeit", 0)),
        "Instinkt":      int(meta.get("instinkt", 0)),
        "Knurren":       int(meta.get("knurren", 0)),
    }
    max_val = max(stats.values())
    winners = [name for name, val in stats.items() if val == max_val]
    return " und ".join(winners)


# Maps master_prompt.md placeholders to frontmatter fields / transformations.
# Each value is a callable (meta: dict) -> str.
PLACEHOLDER_MAP: dict[str, object] = {
    "[QUALITÄT]":             lambda m: str(m.get("qualitaet", "")),
    "[NAME]":                 lambda m: str(m.get("name", "")),
    "[HUNDERASSE]":           lambda m: str(m.get("hunderasse", "")),
    "[POSE]":                 lambda m: str(m.get("pose", "")),
    "[GESCHIRR_BESCHREIBUNG]": lambda m: str(m.get("geschirr_beschreibung", "")),
    "[QUALITÄTSFARBE]":       lambda m: QUALITAETSFARBE_MAP.get(str(m.get("qualitaet", "")), ""),
    "[HINTERGRUND]":          lambda m: str(m.get("hintergrund", "")),
    "[ZUGKRAFT]":             lambda m: str(m.get("zugkraft", "")),
    "[SCHUTZ]":               lambda m: str(m.get("schutz", "")),
    "[BEWEGLICHKEIT]":        lambda m: str(m.get("beweglichkeit", "")),
    "[INSTINKT]":             lambda m: str(m.get("instinkt", "")),
    "[KNURREN]":              lambda m: str(m.get("knurren", "")),
    "[HÖCHSTER_STAT]":        lambda m: _highest_stat_names(m),
}


def _ts() -> str:
    return datetime.datetime.now().strftime("%H:%M:%S")


def load_master_template() -> str:
    """Load master_prompt.md as a raw template string."""
    text = MASTER_PROMPT_FILE.read_text(encoding="utf-8").strip()
    print(f"[{_ts()}] Master template loaded ({len(text)} chars)")
    return text


def fill_template(template: str, meta: dict) -> str:
    """Replace all [PLACEHOLDER] tokens in *template* with values from *meta*."""
    result = template
    for placeholder, getter in PLACEHOLDER_MAP.items():
        result = result.replace(placeholder, getter(meta))
    return result


def extract_section(content: str, heading: str) -> str | None:
    """Return the text under a '## heading' in a card's body, or None."""
    match = re.search(rf"## {re.escape(heading)}\n(.+?)(?=\n##|\Z)", content, re.DOTALL)
    return match.group(1).strip() if match else None


def build_prompt(template: str, card_path: Path) -> str | None:
    """
    Build the full image generation prompt for one card.

    1. Fill master_prompt.md template with frontmatter values.
    2. Replace [FLAVOURTEXT] with the card's ## Flavourtext section.
    3. Append the card's ## Bildprompt section as additional scene detail.
    """
    post = frontmatter.load(str(card_path))
    content = post.content

    filled = fill_template(template, post.metadata)

    flavourtext = extract_section(content, "Flavourtext")
    if flavourtext:
        filled = filled.replace("[FLAVOURTEXT]", flavourtext)
    else:
        print(f"  [{_ts()}] [WARN] No '## Flavourtext' section found: {card_path.name}")

    remaining = re.findall(r"\[[A-ZÄÖÜ_]+\]", filled)
    if remaining:
        print(f"  [{_ts()}] [WARN] Unfilled placeholders in {card_path.name}: {remaining}")

    bildprompt = extract_section(content, "Bildprompt")
    if bildprompt:
        filled += f"\n\nZusätzliche Szenendetails: {bildprompt}"
    else:
        print(f"  [{_ts()}] [WARN] No '## Bildprompt' section found: {card_path.name}")

    return filled


def output_path_for(card_path: Path) -> Path:
    """Determine where the output WebP should be saved."""
    relative = card_path.relative_to(CARDS_DIR)
    return OUTPUT_DIR / relative.parent / (card_path.stem + ".webp")


def ensure_webp(image_bytes: bytes) -> bytes:
    """Re-encode image bytes as lossy WebP via Pillow at WEBP_QUALITY."""
    img = Image.open(io.BytesIO(image_bytes))
    buf = io.BytesIO()
    img.save(buf, format="WEBP", quality=WEBP_QUALITY, method=6)
    return buf.getvalue()


def _next_backup_num(out: Path) -> int:
    """Return the next free integer suffix for backup files of *out*."""
    nums = []
    for p in out.parent.glob(f"{out.stem}_*{out.suffix}"):
        tail = p.stem[len(out.stem) + 1:]
        if tail.isdigit():
            nums.append(int(tail))
    return max(nums, default=0) + 1


def migrate_ts_backups(out: Path) -> None:
    """Rename old timestamp-style backups (stem_YYYYMMDD_HHMMSS) to stem_N."""
    for p in sorted(out.parent.glob(f"{out.stem}_*{out.suffix}")):
        tail = p.stem[len(out.stem) + 1:]
        if re.fullmatch(r"\d{8}_\d{6}", tail):
            n = _next_backup_num(out)
            new_path = p.with_stem(f"{out.stem}_{n}")
            p.rename(new_path)
            print(f"  [{_ts()}] [MIG]  {p.name} → {new_path.name}")


def backup_existing(out: Path) -> None:
    """Rename an existing output file with the next available integer suffix."""
    n = _next_backup_num(out)
    backup = out.with_stem(f"{out.stem}_{n}")
    out.rename(backup)
    print(f"  [{_ts()}] [BAK]  Backed up → {backup.name}")


def convert_to_print(jpg_quality: int = 95) -> None:
    """Convert all WebP files in output/ to high-quality JPG in print/."""
    images = sorted(OUTPUT_DIR.rglob("*.webp"))
    if not images:
        print("No WebP files found in output/.")
        return

    converted = 0
    for webp_path in images:
        relative = webp_path.relative_to(OUTPUT_DIR)
        jpg_path = PRINT_DIR / relative.parent / (webp_path.stem + ".jpg")
        jpg_path.parent.mkdir(parents=True, exist_ok=True)

        img = Image.open(webp_path).convert("RGB")
        img.save(jpg_path, format="JPEG", quality=jpg_quality, subsampling=0)

        size_kb = jpg_path.stat().st_size / 1024
        print(f"  [{_ts()}] [PRINT] {relative} → {jpg_path.relative_to(PRINT_DIR.parent)} ({size_kb:.0f} KB)")
        converted += 1

    print(f"\n[{_ts()}] Converted {converted} image(s) to {PRINT_DIR}/")


def recompress_large_images() -> None:
    """Re-encode all output WebP files above RECOMPRESS_THRESHOLD via Pillow."""
    images = sorted(OUTPUT_DIR.rglob("*.webp"))
    if not images:
        print("No WebP files found in output/.")
        return

    recompressed = 0
    skipped = 0
    for img_path in images:
        size = img_path.stat().st_size
        if size <= RECOMPRESS_THRESHOLD:
            print(f"  [{_ts()}] [SKIP] {img_path.relative_to(OUTPUT_DIR)} — {size / 1024:.0f} KB")
            skipped += 1
            continue

        webp_bytes = ensure_webp(img_path.read_bytes())
        img_path.write_bytes(webp_bytes)
        new_size = len(webp_bytes)
        print(
            f"  [{_ts()}] [RECOMPRESS] {img_path.relative_to(OUTPUT_DIR)}: "
            f"{size / 1024:.0f} KB → {new_size / 1024:.0f} KB"
        )
        recompressed += 1

    print(f"\n[{_ts()}] Recompressed: {recompressed}, Skipped: {skipped}")


def generate_image(client: OpenAI, prompt: str, quality: str) -> bytes:
    """Call the API and return WebP bytes."""
    response = client.images.generate(
        model=MODEL,
        prompt=prompt,
        size=IMAGE_SIZE,
        quality=quality,
        output_format="webp",
        n=1,
    )
    return base64.b64decode(response.data[0].b64_json)


def process_card(
    client: OpenAI,
    card_path: Path,
    master_template: str,
    force: bool,
    quality: str,
    variants: int = 1,
) -> int:
    """Generate and save image(s) for one card. Returns number of images generated."""
    out = output_path_for(card_path)

    migrate_ts_backups(out)

    if out.exists() and not force and variants == 1:
        print(f"  [{_ts()}] [SKIP] Already exists: {out.relative_to(Path(__file__).parent)}")
        return 0

    prompt = build_prompt(master_template, card_path)
    if prompt is None:
        return 0

    generated = 0
    for v in range(variants):
        variant_label = f" (variant {v + 1}/{variants})" if variants > 1 else ""
        print(f"  [{_ts()}] [GEN]  {card_path.relative_to(CARDS_DIR)} → {out.name}{variant_label}")

        if out.exists():
            backup_existing(out)

        out.parent.mkdir(parents=True, exist_ok=True)

        t0 = time.monotonic()
        try:
            image_bytes = generate_image(client, prompt, quality)
        except Exception as exc:
            print(f"  [{_ts()}] [ERR]  API error for {card_path.name}: {exc}")
            break

        webp_bytes = ensure_webp(image_bytes)
        elapsed = time.monotonic() - t0
        out.write_bytes(webp_bytes)
        generated += 1

        size_kb = len(webp_bytes) / 1024
        print(f"  [{_ts()}] [DONE] {elapsed:.1f}s — {size_kb:.0f} KB → {out.relative_to(Path(__file__).parent)}")

        if v < variants - 1:
            time.sleep(RATE_LIMIT_DELAY)

    return generated


def collect_cards(target: str | None) -> list[Path]:
    """Return a sorted list of card .md files to process."""
    if target and target.endswith(".md"):
        p = Path(target).resolve()
        if not p.exists():
            sys.exit(f"File not found: {target}")
        return [p]

    search_root = CARDS_DIR / target if target else CARDS_DIR
    if not search_root.exists():
        sys.exit(f"Directory not found: {search_root}")

    return sorted(search_root.rglob("*.md"))


def sample_one_per_quality(cards: list[Path]) -> list[Path]:
    """Return one card per quality level (in canonical order)."""
    order = ["Gewöhnlich", "Selten", "Episch", "Magisch", "Legendär"]
    by_quality: dict[str, Path] = {}
    for card_path in cards:
        post = frontmatter.load(str(card_path))
        q = str(post.metadata.get("qualitaet", ""))
        if q and q not in by_quality:
            by_quality[q] = card_path
    return [by_quality[q] for q in order if q in by_quality]


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate card images for Hundegeschirr-Quartett")
    parser.add_argument(
        "target",
        nargs="?",
        help="Single .md file or subdirectory. Defaults to all cards.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate images even if they already exist.",
    )
    parser.add_argument(
        "--quality",
        choices=["low", "medium", "high"],
        default="medium",
        help="Image quality passed to the OpenAI API (default: medium).",
    )
    parser.add_argument(
        "--recompress",
        action="store_true",
        help=f"Re-encode existing output WebP files larger than {RECOMPRESS_THRESHOLD // 1024 // 1024} MB via Pillow.",
    )
    parser.add_argument(
        "--print",
        dest="to_print",
        action="store_true",
        help="Convert all WebP files in output/ to high-quality JPG in print/.",
    )
    parser.add_argument(
        "--print-quality",
        type=int,
        default=95,
        metavar="Q",
        help="JPEG quality for --print (1–95, default: 95).",
    )
    parser.add_argument(
        "--variants",
        type=int,
        default=1,
        metavar="N",
        help="Number of image variants to generate per card (default: 1).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the prompt for each card without calling the API.",
    )
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Generate one card per quality level (5 cards total) — useful for test runs.",
    )
    args = parser.parse_args()

    if args.recompress:
        recompress_large_images()
        return

    if args.to_print:
        convert_to_print(jpg_quality=args.print_quality)
        return

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key and not args.dry_run:
        sys.exit("Error: OPENAI_API_KEY environment variable not set.")

    t_start = time.monotonic()
    print(f"[{_ts()}] Started — quality={args.quality}, force={args.force}, variants={args.variants}, format=WebP (quality={WEBP_QUALITY})")

    master_template = load_master_template()
    cards = collect_cards(args.target)

    if args.sample:
        cards = sample_one_per_quality(cards)
        print(f"[{_ts()}] --sample: selected {len(cards)} card(s), one per quality level")

    if not cards:
        print("No card files found.")
        return

    total = len(cards)
    generated = 0
    skipped = 0

    print(f"[{_ts()}] Found {total} card(s) to process")

    if args.dry_run:
        for card_path in cards:
            print(f"\n{'─' * 60}")
            print(f"Card: {card_path.name}")
            print(f"{'─' * 60}")
            prompt = build_prompt(master_template, card_path)
            print(prompt)
        return

    client = OpenAI(api_key=api_key)

    for i, card_path in enumerate(cards, start=1):
        print(f"\n[{_ts()}] [{i:3}/{total}] {card_path.stem}")
        count = process_card(
            client, card_path, master_template,
            force=args.force, quality=args.quality, variants=args.variants,
        )
        if count > 0:
            generated += count
            if i < total:
                time.sleep(RATE_LIMIT_DELAY)
        else:
            skipped += 1

    elapsed_total = time.monotonic() - t_start
    print(
        f"\n[{_ts()}] Done in {elapsed_total:.1f}s — "
        f"Generated: {generated}, Skipped: {skipped}, Total: {total}"
    )


if __name__ == "__main__":
    main()
