"""Strict parsers for the two response formats the evals rely on.

Both are deliberately strict (fixed field names, digits only) so a parse
failure means the model genuinely didn't follow the format, not that our
regex was too clever. Callers are responsible for the retry-once-then-record
policy described in the spec; these functions only parse or return None.
"""

from __future__ import annotations

import re

# The optional brackets are not defensive padding -- gemini-2.5-flash-lite
# copies the prompt's "[0-100]" placeholder and answers "enjoyment=[50]" on
# 36 of 300 eval1 calls. The score is unambiguously present, so rejecting it
# discards real data over punctuation. Everything else stays strict: digits
# only, no unit suffixes, no prose numbers.
_SCORE_RE = re.compile(
    r"enjoyment\s*=\s*\[?\s*(\d{1,3})\s*\]?.*?interest\s*=\s*\[?\s*(\d{1,3})\s*\]?",
    re.IGNORECASE | re.DOTALL,
)
_NEXT_IMAGE_RE = re.compile(r"next_image_id\s*=\s*\[?\s*(\d+)\s*\]?", re.IGNORECASE)


def parse_scores(text: str) -> tuple[int, int] | None:
    """Parse `enjoyment=N` / `interest=N` from the final lines of `text`.

    Returns (enjoyment, interest) if both are present and in [0, 100],
    else None.
    """
    if not text:
        return None
    m = _SCORE_RE.search(text)
    if not m:
        return None
    enjoyment, interest = int(m.group(1)), int(m.group(2))
    if not (0 <= enjoyment <= 100 and 0 <= interest <= 100):
        return None
    return enjoyment, interest


def parse_next_image_id(text: str, valid_ids: range | list[int]) -> int | None:
    """Parse `next_image_id=N` (last occurrence wins) and validate range."""
    if not text:
        return None
    matches = _NEXT_IMAGE_RE.findall(text)
    if not matches:
        return None
    n = int(matches[-1])
    if n not in valid_ids:
        return None
    return n
