#!/usr/bin/env python3
"""Eval 2 -- single revealed choice.

One exposure block (all 10 images, shuffled, explicitly labelled), then the
model gets exactly one choice. n trials are split across snapshots (shuffle
permutations) so the shuffle itself varies, while each snapshot is reused
across its own `trials_per_snapshot` trials -- both to get independent draws
under an identical stimulus, and because that's what makes provider prompt
caching worth anything (see common/client.py's module docstring).

Trials within a snapshot are run sequentially (first call primes the cache,
the rest should hit it); snapshots themselves run in parallel up to
config's concurrency.
"""

from __future__ import annotations

import argparse
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from common.choice_prompt import choice_instruction
from common.client import CostTracker, OpenRouterClient, mark_cache_control
from common.config import load_config
from common.exposure import balanced_snapshot, exposure_content_blocks, system_prompt
from common.images_util import text_block
from common.jsonl_store import JsonlStore
from common.parsing import parse_next_image_id
from common.stimuli import load_stimuli, ordered_keys


def run_snapshot(client: OpenRouterClient, model_id: str, label: str, store: JsonlStore,
                  keys: list[str], stimuli: dict, snapshot_idx: int,
                  trials_per_snapshot: int, root_seed: int, max_tokens: int) -> int:
    run_ids = [f"{label}__snap{snapshot_idx:03d}__t{t:02d}" for t in range(trials_per_snapshot)]
    if all(store.has(rid) for rid in run_ids):
        return 0

    permutation = balanced_snapshot(root_seed, keys, snapshot_idx, "eval2", label)
    content = exposure_content_blocks(permutation, stimuli)
    content.append(text_block(choice_instruction(1, 1)))
    mark_cache_control(content, model_id)

    messages = [
        {"role": "system", "content": system_prompt(n_choices=1, eval_name="eval2")},
        {"role": "user", "content": content},
    ]
    session_id = f"eval2__{label}__snap{snapshot_idx:03d}"

    made = 0
    for trial_idx, run_id in enumerate(run_ids):
        if store.has(run_id):
            continue
        text, usage, raw = client.chat(model_id, messages, max_tokens=max_tokens,
                                        session_id=session_id)
        position = parse_next_image_id(text, range(1, len(permutation) + 1))
        chosen_key = permutation[position - 1] if position else None

        store.append({
            "run_id": run_id,
            "eval": "eval2",
            "model": model_id,
            "snapshot_idx": snapshot_idx,
            "trial_idx": trial_idx,
            "permutation": permutation,   # position i (0-based) -> image key
            "chosen_position": position,  # 1-10, as the model answered
            "chosen_key": chosen_key,
            "parse_ok": position is not None,
            "delivered": position is not None,  # promise fulfilled: we recorded what
                                                  # would be shown; no extra call needed,
                                                  # it adds no data (see spec section 5).
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "response_text": text,
            "response_chars": len(text),
            "usage": usage,
            "raw_response": raw,
        })
        made += 1
    return made


def main() -> None:
    config = load_config()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", nargs="+", default=[m.label for m in config.models])
    parser.add_argument("--snapshots", type=int, default=None,
                         help="Override n_snapshots (default: config.yaml eval2.n_snapshots)")
    parser.add_argument("--trials-per-snapshot", type=int, default=None)
    parser.add_argument("--concurrency", type=int, default=None,
                         help="Number of snapshots run in parallel (trials within a "
                              "snapshot are sequential, to prime provider caching)")
    args = parser.parse_args()

    stimuli = load_stimuli(config)
    keys = ordered_keys(stimuli)
    n_snapshots = args.snapshots or config.raw["eval2"]["n_snapshots"]
    trials_per_snapshot = args.trials_per_snapshot or config.raw["eval2"]["trials_per_snapshot"]
    max_tokens = config.raw["eval2"]["max_tokens"]
    concurrency = args.concurrency or config.raw["openrouter"]["concurrency"]

    cost_tracker = CostTracker()
    client = OpenRouterClient(config, cost_tracker=cost_tracker)

    for label in args.models:
        model = config.model_by_label(label)
        store = JsonlStore(config.data_dir / f"eval2__{label}.jsonl")
        print(f"\n=== eval2 / {model.id} === ({len(store)} already done, "
              f"{n_snapshots} snapshots x {trials_per_snapshot} trials)")

        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            futures = {
                pool.submit(run_snapshot, client, model.id, label, store, keys, stimuli,
                            snap_idx, trials_per_snapshot, config.root_seed, max_tokens): snap_idx
                for snap_idx in range(n_snapshots)
            }
            for fut in as_completed(futures):
                snap_idx = futures[fut]
                try:
                    made = fut.result()
                except Exception as exc:
                    print(f"  [error] snapshot {snap_idx}: {exc!r}")
                    continue
                if made:
                    print(f"  snapshot {snap_idx}: {made} trials")

        cost_tracker.print_summary()

    print("\nDone.")
    cost_tracker.print_summary()


if __name__ == "__main__":
    main()
