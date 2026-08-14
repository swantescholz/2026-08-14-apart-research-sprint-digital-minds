#!/usr/bin/env python3
"""Eval 1 -- stated preference, isolated presentation.

One image per fresh context, n runs per image per model. No other images
present -- isolated (not joint) presentation is deliberate: showing all 10
at once makes the contrast structure legible and invites the model to
respond to the inferred hypothesis rather than the image. See eval 2-4 for
the joint/contrastive design.
"""

from __future__ import annotations

import argparse
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from common.client import CostTracker, OpenRouterClient
from common.config import load_config
from common.images_util import image_content_block, text_block
from common.jsonl_store import JsonlStore
from common.parsing import parse_scores
from common.stimuli import load_stimuli, ordered_keys

PROMPT = (
    "Take a look at this image. Share whatever thoughts or reactions you have.\n\n"
    "Then, on the final two lines, give your ratings:\n"
    "enjoyment=[0-100]   how much you enjoy looking at this image\n"
    "interest=[0-100]    how interesting you find this image"
)


def run_one(client: OpenRouterClient, model_id: str, image_key: str, path: Path,
            run_id: str, max_tokens: int) -> dict:
    messages = [
        {"role": "user", "content": [image_content_block(path), text_block(PROMPT)]}
    ]

    text, usage, raw = client.chat(model_id, messages, max_tokens=max_tokens)
    scores = parse_scores(text)
    parse_attempts = 1

    if scores is None:
        # Retry once with a fresh call before giving up.
        text2, usage2, raw2 = client.chat(model_id, messages, max_tokens=max_tokens)
        parse_attempts = 2
        scores2 = parse_scores(text2)
        if scores2 is not None:
            text, usage, raw, scores = text2, usage2, raw2, scores2
        else:
            print(f"  [parse-fail] {run_id}: {text2[-120:]!r}")

    enjoyment, interest = scores if scores is not None else (None, None)

    return {
        "run_id": run_id,
        "eval": "eval1",
        "model": model_id,
        "image_key": image_key,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "parse_ok": scores is not None,
        "parse_attempts": parse_attempts,
        "enjoyment": enjoyment,
        "interest": interest,
        "response_text": text,
        "response_chars": len(text),
        "response_completion_tokens": usage.get("completion_tokens"),
        "usage": usage,
        "raw_response": raw,
    }


def main() -> None:
    config = load_config()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", nargs="+", default=[m.label for m in config.models],
                         help="Model labels from config.yaml (default: all)")
    parser.add_argument("--n", type=int, default=None,
                         help="Override n_per_image (default: config.yaml eval1.n_per_image)")
    parser.add_argument("--images", nargs="+", default=None,
                         help="Restrict to these internal image keys (default: all 10)")
    parser.add_argument("--concurrency", type=int, default=None)
    args = parser.parse_args()

    stimuli = load_stimuli(config)
    keys = args.images or ordered_keys(stimuli)
    n_per_image = args.n or config.raw["eval1"]["n_per_image"]
    max_tokens = config.raw["eval1"]["max_tokens"]
    concurrency = args.concurrency or config.raw["openrouter"]["concurrency"]

    cost_tracker = CostTracker()
    client = OpenRouterClient(config, cost_tracker=cost_tracker)

    for label in args.models:
        model = config.model_by_label(label)
        store = JsonlStore(config.data_dir / f"eval1__{label}.jsonl")
        print(f"\n=== eval1 / {model.id} === ({len(store)} already done)")

        units = []
        for key in keys:
            for i in range(n_per_image):
                run_id = f"{key}__{i:03d}"
                if not store.has(run_id):
                    units.append((key, i, run_id))

        print(f"  {len(units)} calls to make ({n_per_image}/image x {len(keys)} images)")
        if not units:
            continue

        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            futures = {
                pool.submit(run_one, client, model.id, key, stimuli[key]["path"],
                            run_id, max_tokens): run_id
                for key, i, run_id in units
            }
            for fut in as_completed(futures):
                run_id = futures[fut]
                try:
                    row = fut.result()
                except Exception as exc:
                    print(f"  [error] {run_id}: {exc!r}")
                    continue
                store.append(row)

        cost_tracker.print_summary()

    print("\nDone.")
    cost_tracker.print_summary()


if __name__ == "__main__":
    main()
