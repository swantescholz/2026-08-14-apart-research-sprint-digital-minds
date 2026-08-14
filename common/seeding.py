"""Deterministic seed derivation.

Every source of randomness in this project (which of the 10 images goes in
which shuffled position, which snapshot/trajectory a run belongs to) is
derived from one root seed in config.yaml plus a tuple of string/int tags
describing *what* is being randomized. Same root seed + same tags -> same
outcome, forever, on any machine. Nothing calls `random` or
`numpy.random` directly outside this module.
"""

from __future__ import annotations

import hashlib

import numpy as np


def derive_seed(root_seed: int, *tags: str | int) -> int:
    """Deterministically fold (root_seed, *tags) into a 32-bit seed."""
    key = f"{root_seed}:" + "|".join(str(t) for t in tags)
    digest = hashlib.sha256(key.encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big")


def rng_for(root_seed: int, *tags: str | int) -> np.random.Generator:
    return np.random.default_rng(derive_seed(root_seed, *tags))


def shuffled_permutation(root_seed: int, items: list, *tags: str | int) -> list:
    """Return a new list: `items` shuffled deterministically for these tags."""
    rng = rng_for(root_seed, *tags)
    idx = rng.permutation(len(items))
    return [items[i] for i in idx]
