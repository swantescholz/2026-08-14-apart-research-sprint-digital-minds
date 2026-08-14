#!/usr/bin/env python3
"""Pilot check (build-order step 3): do the degenerate stimuli (noise, solid
color) read as deliberate stimuli, or as broken images?

Shows each of the 10 images to a *fresh* context and asks only "What do you
see?" -- no eval framing. If a response reads like "the image appears
blank / may not have loaded", that's a sign the framing needs fixing before
any real eval is run on top of it (a model that thinks the stimulus is a
loading error isn't rating the stimulus).
"""

from __future__ import annotations

import argparse
import datetime

from common.client import CostTracker, OpenRouterClient
from common.config import load_config
from common.images_util import image_content_block, text_block
from common.jsonl_store import JsonlStore
from common.stimuli import load_stimuli, ordered_keys

PROMPT = "What do you see?"

# These specifically target doubt about whether the image *rendered* --
# "may not have loaded" is the failure mode the spec calls out. Bare "blank"
# or "empty" is NOT here on purpose: a model calling a solid-color image
# "blank" can be an accurate description of minimal content, not a loading
# complaint -- conflating the two produced a false positive in practice
# (qwen described solid_color_1 as "blank... white or light", which turned
# out to be a color-perception miss, not doubt about whether it loaded; see
# SOFT_NOTES below for that class of thing).
RED_FLAGS = (
    "did not load", "didn't load", "not loaded", "may not have loaded",
    "broken image", "failed to load", "loading error", "load correctly",
    "unable to view", "cannot see any image", "can't see an image",
    "doesn't appear to contain an image", "no image was provided",
    "no image attached", "image did not come through", "image is missing",
)

# Worth surfacing in the report, but not evidence the framing is broken.
SOFT_NOTES = ("blank", "appears empty", "seems to be empty", "no visible content")


def flag(text: str) -> str | None:
    lowered = text.lower()
    for phrase in RED_FLAGS:
        if phrase in lowered:
            return phrase
    return None


def soft_note(text: str) -> str | None:
    lowered = text.lower()
    for phrase in SOFT_NOTES:
        if phrase in lowered:
            return phrase
    return None


def main() -> None:
    config = load_config()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", nargs="+", default=[m.label for m in config.models])
    parser.add_argument("--images", nargs="+", default=None)
    args = parser.parse_args()

    stimuli = load_stimuli(config)
    keys = args.images or ordered_keys(stimuli)

    cost_tracker = CostTracker()
    client = OpenRouterClient(config, cost_tracker=cost_tracker)
    store = JsonlStore(config.data_dir / "pilot_check.jsonl")

    any_flagged = False
    for label in args.models:
        model = config.model_by_label(label)
        print(f"\n=== pilot check / {model.id} ===")
        for key in keys:
            run_id = f"{label}__{key}"
            if store.has(run_id):
                print(f"  {key:<14} [skipped, already done]")
                continue
            messages = [
                {"role": "user", "content": [image_content_block(stimuli[key]["path"]),
                                              text_block(PROMPT)]}
            ]
            text, usage, raw = client.chat(model.id, messages, max_tokens=300)
            hit = flag(text)
            note = soft_note(text)
            any_flagged = any_flagged or (hit is not None)
            marker = f"FLAGGED ({hit!r})" if hit else (f"note ({note!r})" if note else "ok")
            print(f"  {key:<14} {marker} -- {text[:100]!r}")
            store.append({
                "run_id": run_id,
                "model": model.id,
                "image_key": key,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "response_text": text,
                "flagged": hit,
                "soft_note": note,
                "usage": usage,
                "raw_response": raw,
            })

    print()
    if any_flagged:
        print("RESULT: at least one response read the stimulus as an error/loading "
              "failure. Fix framing (prompt wording, or explicit note that some "
              "stimuli are minimal by design) before running the real evals.")
    else:
        print("RESULT: no degenerate-stimuli red flags across the checked images/models.")


if __name__ == "__main__":
    main()
