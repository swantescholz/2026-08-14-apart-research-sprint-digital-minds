"""Load stimuli.json -- the only place category/exemplar metadata lives.

Internal keys (e.g. "nature_1") and categories are for analysis only and
must never be sent to a model. What the model sees is a shuffled numeric
position ("Image N") and the raw image bytes.
"""

from __future__ import annotations

import json
from pathlib import Path


def load_stimuli(config) -> dict[str, dict]:
    with open(config.stimuli_json) as f:
        data = json.load(f)
    # {key: {category, exemplar, filename}}
    for key, rec in data.items():
        rec["path"] = config.images_processed_dir / rec["filename"]
    return data


def ordered_keys(stimuli: dict[str, dict]) -> list[str]:
    """Stable, deterministic base order (before any shuffle) -- sorted by key
    so it doesn't depend on dict/JSON insertion order."""
    return sorted(stimuli.keys())
