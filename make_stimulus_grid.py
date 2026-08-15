#!/usr/bin/env python3
"""Render the ten stimuli as one figure: 5 categories across, 2 exemplars down.

One image rather than ten, because ten separate images in the report would each
take their own paragraph and consume most of a page. Laid out so the design is
legible without reading the caption -- each column is a category, each row an
exemplar, so "five categories, two examples each" is visible at a glance.

Reads `images_processed/` (regenerate with `prepare_stimuli.py`) so the figure
shows exactly the pixels the models were sent, not the pre-processing originals.
"""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# Same order as analyze.py's CATEGORY_ORDER, so the figure reads left-to-right
# in the order every other figure and table uses.
CATEGORY_ORDER = ["humans", "nature", "tech", "solid_color", "noise"]

CELL = 256          # stimuli are 256x256; render 1:1, no resampling
GAP = 10            # between cells
MARGIN = 8
LABEL_H = 30
BG = (255, 255, 255)
LABEL_FG = (40, 40, 40)


def _font(size: int):
    for path in ("/System/Library/Fonts/Supplemental/Arial.ttf",
                 "/System/Library/Fonts/Helvetica.ttc",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def main() -> None:
    root = Path(__file__).parent
    stimuli = json.loads((root / "stimuli.json").read_text())
    processed = root / "images_processed"

    by_cat: dict[str, dict[int, str]] = {}
    for key, meta in stimuli.items():
        by_cat.setdefault(meta["category"], {})[meta["exemplar"]] = meta["filename"]

    missing = [c for c in CATEGORY_ORDER if c not in by_cat]
    if missing:
        raise SystemExit(f"missing categories {missing}; run prepare_stimuli.py first")

    cols, rows = len(CATEGORY_ORDER), 2
    W = MARGIN * 2 + cols * CELL + (cols - 1) * GAP
    H = MARGIN * 2 + LABEL_H + rows * CELL + (rows - 1) * GAP
    canvas = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(canvas)
    font = _font(20)

    for c, category in enumerate(CATEGORY_ORDER):
        x = MARGIN + c * (CELL + GAP)
        # Column label, centred over the pair. Underscores read badly at this
        # size; the report writes these categories with a space anyway.
        label = category.replace("_", " ")
        tw = draw.textbbox((0, 0), label, font=font)[2]
        draw.text((x + (CELL - tw) // 2, MARGIN + 4), label, fill=LABEL_FG, font=font)

        for r in range(rows):
            fn = by_cat[category].get(r + 1)
            if fn is None:
                raise SystemExit(f"{category} has no exemplar {r + 1}")
            y = MARGIN + LABEL_H + r * (CELL + GAP)
            im = Image.open(processed / fn).convert("RGB")
            if im.size != (CELL, CELL):
                raise SystemExit(f"{fn} is {im.size}, expected {(CELL, CELL)}")
            canvas.paste(im, (x, y))

    out = root / "results" / "stimuli_grid.png"
    out.parent.mkdir(exist_ok=True)
    canvas.save(out, dpi=(150, 150))
    print(f"  wrote {out}  ({W}x{H})")

    report_copy = root / "report" / "figures" / "stimuli_grid.png"
    if report_copy.parent.is_dir():
        canvas.save(report_copy, dpi=(150, 150))
        print(f"  wrote {report_copy}")


if __name__ == "__main__":
    main()
