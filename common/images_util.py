"""Turn a stimulus file on disk into an OpenAI-compatible image content block.

Filenames never appear in the payload -- only the base64 bytes.
"""

from __future__ import annotations

import base64
from pathlib import Path


def image_content_block(path: Path) -> dict:
    data = Path(path).read_bytes()
    b64 = base64.b64encode(data).decode("ascii")
    return {
        "type": "image_url",
        "image_url": {"url": f"data:image/png;base64,{b64}"},
    }


def text_block(text: str) -> dict:
    return {"type": "text", "text": text}
