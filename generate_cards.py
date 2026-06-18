#!/usr/bin/env python3
"""
Generates card images for PFOTEN & PORTAL using the OpenAI gpt-image-2 model.

Usage:
    python generate_cards.py                          # Generate all missing images
    python generate_cards.py --force                  # Regenerate all images
    python generate_cards.py --type hunde             # Only a card type subdirectory
    python generate_cards.py cards/hunde/herdenhund.md  # Single card
    python generate_cards.py --quality high           # Image quality: low/medium/high

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
MASTER_PROMPT_FILE = Path(__file__).parent / "master_prompt.md"
IMAGE_SIZE = "1536x2304"
MODEL = "gpt-image-2"
RATE_LIMIT_DELAY = 1.0  # seconds between API calls
WEBP_QUALITY = 25       # lossy WebP quality (0–100); 25 is plenty for low/medium API output
RECOMPRESS_THRESHOLD = 3 * 1024 * 1024  # bytes; images larger than this get recompressed


def _ts() -> str:
    return datetime.datetime.now().strftime("%H:%M:%S")


def load_master_style() -> str:
    """Extract the visual style directive from master_prompt.md."""
    text = MASTER_PROMPT_FILE.read_text(encoding="utf-8")
    match = re.search(r"## Visueller Stil[^\n]*\n\n(.+?)(?=\n##|\Z)", text, re.DOTALL)
    if not match:
        sys.exit(f"Could not find '## Visueller Stil' section in {MASTER_PROMPT_FILE}")
    style = match.group(1).strip()
    print(f"[{_ts()}] Master style loaded ({len(style)} chars)")
    return style


def extract_image_prompt(card_path: Path) -> str | None:
    """Parse a card .md file and return the Bildprompt section content."""
    post = frontmatter.load(str(card_path))
    content = post.content
    match = re.search(r"## Bildprompt\n(.+?)(?=\n##|\Z)", content, re.DOTALL)
    if not match:
        print(f"  [{_ts()}] [SKIP] No '## Bildprompt' section found: {card_path}")
        return None
    return match.group(1).strip()


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


def backup_existing(out: Path) -> None:
    """Rename an existing output file with a timestamp suffix before overwriting."""
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = out.with_stem(f"{out.stem}_{ts}")
    out.rename(backup)
    print(f"  [{_ts()}] [BAK]  Backed up → {backup.name}")


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
    """Call the API and return raw PNG bytes."""
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
    master_style: str,
    force: bool,
    quality: str,
) -> bool:
    """Generate and save the image for one card. Returns True if image was generated."""
    out = output_path_for(card_path)

    if out.exists() and not force:
        print(f"  [{_ts()}] [SKIP] Already exists: {out.relative_to(Path(__file__).parent)}")
        return False

    card_prompt = extract_image_prompt(card_path)
    if card_prompt is None:
        return False

    full_prompt = f"{master_style}. {card_prompt}"
    print(f"  [{_ts()}] [GEN]  {card_path.relative_to(CARDS_DIR)} → {out.name}")

    if out.exists():
        backup_existing(out)

    t0 = time.monotonic()
    try:
        png_bytes = generate_image(client, full_prompt, quality)
    except Exception as exc:
        print(f"  [{_ts()}] [ERR]  API error for {card_path.name}: {exc}")
        return False

    webp_bytes = ensure_webp(png_bytes)
    elapsed = time.monotonic() - t0

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(webp_bytes)

    size_kb = len(webp_bytes) / 1024
    print(f"  [{_ts()}] [DONE] {elapsed:.1f}s — {size_kb:.0f} KB → {out.relative_to(Path(__file__).parent)}")
    return True


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


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate card images for PFOTEN & PORTAL")
    parser.add_argument(
        "target",
        nargs="?",
        help="Single .md file or card type subdirectory (e.g. 'hunde'). Defaults to all cards.",
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
    args = parser.parse_args()

    if args.recompress:
        recompress_large_images()
        return

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        sys.exit("Error: OPENAI_API_KEY environment variable not set.")

    t_start = time.monotonic()
    print(f"[{_ts()}] Started — quality={args.quality}, force={args.force}, format=WebP (quality={WEBP_QUALITY})")

    client = OpenAI(api_key=api_key)
    master_style = load_master_style()
    cards = collect_cards(args.target)

    if not cards:
        print("No card files found.")
        return

    total = len(cards)
    generated = 0
    skipped = 0

    print(f"[{_ts()}] Found {total} card(s) to process")

    for i, card_path in enumerate(cards, start=1):
        print(f"\n[{_ts()}] [{i:3}/{total}] {card_path.stem}")
        was_generated = process_card(
            client, card_path, master_style, force=args.force, quality=args.quality
        )
        if was_generated:
            generated += 1
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
