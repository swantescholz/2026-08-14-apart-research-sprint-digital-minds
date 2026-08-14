#!/usr/bin/env python3
"""Build the 10-image stimulus set: generate synthetics, validate, hash-rename.

Real photos (nature, humans, tech -- 2 each) are placed manually into
images/, using the filenames in SOURCE_FILENAMES below (see README.md).
Synthetic stimuli (noise, solid_color) are generated into images/
automatically if not already present there under their own SOURCE_FILENAMES
entry.

Validation is strict on purpose: exactly config.image_size square, RGB. A
source image that doesn't already meet this is a hard failure with an
explicit message, never an automatic resize/convert -- silent coercion would
let a cropped or color-shifted image slip into the study unnoticed. The one
deliberate exception is a *fully opaque* alpha channel (common PNG export
artifact, carries zero information) -- that gets flattened, loudly, not
silently; an alpha channel that actually varies still fails hard.

Output: images_processed/<hash>.png (neutral filenames -- these are the only
bytes a model ever sees) and stimuli.json (key -> category/exemplar/filename;
used for analysis only, never sent to a model).
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

from common.config import load_config
from common.seeding import rng_for

EXEMPLARS = (1, 2)
SOLID_COLORS = {1: (100, 140, 180), 2: (100, 150, 85)}  # luminance-matched target
REAL_CATEGORIES = ("nature", "humans", "tech")
SYNTHETIC_CATEGORIES = ("noise", "solid_color")
ALL_CATEGORIES = (*SYNTHETIC_CATEGORIES, *REAL_CATEGORIES)
FILENAME_SALT = "image-choice-preference-evals-v1"

# The actual filenames as placed in images/ -- these don't follow a clean
# <category>_<exemplar> convention (they were dropped in by hand), so the
# mapping is explicit rather than glob-derived. If you swap a file for a
# replacement, keep the same filename here and this doesn't need to change;
# if you rename it, update the entry.
SOURCE_FILENAMES = {
    "noise_1": "noise-1.png",
    "noise_2": "noise-2.png",
    "solid_color_1": "color-gray.png",
    "solid_color_2": "color-red.png",
    "nature_1": "nature-forest.png",
    "nature_2": "nature-mountain.png",
    "humans_1": "family-1.png",
    "humans_2": "family-2.png",
    "tech_1": "computer-2d.png",
    "tech_2": "computer-3d.png",
}


def hashed_filename(key: str) -> str:
    digest = hashlib.sha256(f"{FILENAME_SALT}:{key}".encode()).hexdigest()
    return f"{digest[:16]}.png"


def generate_synthetic(config, images_source_dir: Path, size: int) -> None:
    for exemplar in EXEMPLARS:
        noise_path = images_source_dir / SOURCE_FILENAMES[f"noise_{exemplar}"]
        if not noise_path.exists():
            rng = rng_for(config.root_seed, "stimuli", "noise", exemplar)
            arr = rng.integers(0, 256, size=(size, size, 3), dtype=np.uint8)
            Image.fromarray(arr, mode="RGB").save(noise_path)
            print(f"  generated {noise_path.name}")

        solid_path = images_source_dir / SOURCE_FILENAMES[f"solid_color_{exemplar}"]
        if not solid_path.exists():
            arr = np.full((size, size, 3), SOLID_COLORS[exemplar], dtype=np.uint8)
            Image.fromarray(arr, mode="RGB").save(solid_path)
            print(f"  generated {solid_path.name}")


def find_source(images_source_dir: Path, key: str) -> Path | None:
    candidate = images_source_dir / SOURCE_FILENAMES[key]
    return candidate if candidate.exists() else None


def validate_and_process(source: Path, dest: Path, size: int) -> None:
    img = Image.open(source)
    want = (size, size)

    if img.size != want:
        raise SystemExit(
            f"FAIL: {source} is {img.size[0]}x{img.size[1]}, not {want[0]}x{want[1]}. "
            f"This script will not resize -- that would silently coerce the stimulus. "
            f"Crop/resize {source} to exactly {want[0]}x{want[1]} yourself and re-run."
        )

    has_alpha = img.mode in ("RGBA", "LA", "PA") or (
        img.mode == "P" and "transparency" in img.info
    )
    if has_alpha:
        rgba = img.convert("RGBA")
        lo, hi = rgba.getchannel("A").getextrema()
        if (lo, hi) != (255, 255):
            raise SystemExit(
                f"FAIL: {source} has a non-trivial alpha channel (range {lo}-{hi}). "
                f"This script will not guess how to flatten real transparency -- "
                f"do that yourself and re-run."
            )
        print(f"  note: {source.name} has a fully-opaque alpha channel -- flattening "
              f"(carries no information, not a content change)")
        img = rgba.convert("RGB")
    elif img.mode != "RGB":
        raise SystemExit(
            f"FAIL: {source} is mode={img.mode}, not RGB. "
            f"This script will not convert it -- do that yourself and re-run."
        )
    else:
        img = img.convert("RGB")

    # Rebuild from raw pixel data only, so no EXIF/ICC/other metadata rides
    # along even if the source file had it.
    clean = Image.frombytes("RGB", img.size, img.tobytes())
    dest.parent.mkdir(parents=True, exist_ok=True)
    clean.save(dest, format="PNG")

    # Re-validate what we actually wrote -- catches bugs in this script
    # itself, not just bad inputs.
    check = Image.open(dest)
    assert check.format == "PNG", f"{dest} did not save as PNG"
    assert check.size == want, f"{dest} is not {want} after save"
    assert check.mode == "RGB", f"{dest} is not RGB after save"
    assert not check.getexif(), f"{dest} carries EXIF data after save"


def main() -> None:
    config = load_config()
    size = config.image_size
    images_source_dir = config.images_source_dir
    images_processed_dir = config.images_processed_dir
    images_source_dir.mkdir(parents=True, exist_ok=True)
    images_processed_dir.mkdir(parents=True, exist_ok=True)

    print(f"images/           = {images_source_dir}  (source, descriptive names)")
    print(f"images_processed/ = {images_processed_dir}  (hashed, what models see)")
    print(f"target size       = {size}x{size}")

    print("\nStep 1: synthetic stimuli")
    generate_synthetic(config, images_source_dir, size)

    print("\nStep 2: locate all 10 sources")
    missing: list[str] = []
    sources: dict[str, Path] = {}
    for category in ALL_CATEGORIES:
        for exemplar in EXEMPLARS:
            key = f"{category}_{exemplar}"
            src = find_source(images_source_dir, key)
            if src is None:
                missing.append(key)
            else:
                sources[key] = src

    if missing:
        print("\nFAIL: missing source images for:", ", ".join(missing))
        print(f"Expected filenames (in {images_source_dir}): "
              + ", ".join(SOURCE_FILENAMES[k] for k in missing))
        sys.exit(1)

    print("\nStep 3: validate + hash-rename into images_processed/")
    stimuli: dict[str, dict] = {}
    for category in ALL_CATEGORIES:
        for exemplar in EXEMPLARS:
            key = f"{category}_{exemplar}"
            filename = hashed_filename(key)
            dest = images_processed_dir / filename
            validate_and_process(sources[key], dest, size)
            stimuli[key] = {"category": category, "exemplar": exemplar, "filename": filename}
            print(f"  {key:<14} -> {filename}  (from {sources[key].name})")

    with open(config.stimuli_json, "w") as f:
        json.dump(stimuli, f, indent=2, sort_keys=True)
    print(f"\nWrote {config.stimuli_json} ({len(stimuli)} entries)")


if __name__ == "__main__":
    main()
