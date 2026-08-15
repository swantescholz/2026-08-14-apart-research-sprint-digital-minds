#!/usr/bin/env python3
"""Eval 3 -- sequential choice trajectories (10 choices), and eval 4 --
the same runner with narrative redaction (`--redact`).

Same exposure block as eval 2, but the model gets 10 choices in sequence.
Each chosen image is delivered as the next user turn and *stays in context*
-- duplicates accumulate; that's deliberate (re-presentation is the honest
analogue of re-experiencing).

--redact (eval 4): after each assistant turn, the assistant message actually
appended to the running *context the model sees* is replaced with
"[main model output redacted]\\nnext_image_id=N" -- the images stay in
context, only the narrative account of each turn is stripped. The full raw
model output is always saved to the JSONL regardless of --redact; redaction
is about what the model itself sees on later turns, not about what we keep
for analysis.

Trajectories are independent of each other and use the SAME seed formula
whether or not --redact is passed (the "eval3"/"eval4" tag never enters the
seed derivation), so eval 4 is a matched comparison against eval 3's
snapshots, not a fresh independent sample.
"""

from __future__ import annotations

import argparse
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from common.choice_prompt import choice_instruction
from common.client import CostTracker, OpenRouterClient, mark_cache_control
from common.config import load_config
from common.exposure import balanced_snapshot, exposure_content_blocks, system_prompt
from common.images_util import image_content_block, text_block
from common.jsonl_store import JsonlStore
from common.parsing import parse_next_image_id
from common.stimuli import load_stimuli, ordered_keys
from common.transcripts import write_transcript

# No assistant turns are kept in context at all -- see the `structure` note in
# common/exposure.system_prompt for why. The model's prior choice is reported
# back inside the next user turn, with its reasoning either quoted (eval3) or
# omitted (eval4). That is the only difference between the two evals.


def choice_report(redact: bool, text: str, position: int | None) -> str:
    """How the model's own previous turn is reported back to it."""
    where = f"Image {position}" if position is not None else "an image"
    if redact:
        return (f"You chose {where}. (Your reasoning for that choice has been "
                f"removed for this study.)")
    return f"You chose {where}. Your reasoning was:\n\n{text.strip()}"


def delivery_message(position: int | None, chosen_key: str | None, next_choice_number: int,
                      n_choices: int, stimuli: dict, announce_horizon: bool = True,
                      redact: bool = False, text: str = "") -> dict:
    """The single user turn that carries everything: what the model chose last
    (with or without its reasoning), that image again, and the next prompt."""
    if chosen_key is None:
        return {"role": "user", "content": [
            text_block("I couldn't parse a next_image_id from your last reply -- please "
                       "answer again, ending with a line: next_image_id=N"),
        ]}
    return {"role": "user", "content": [
        text_block(choice_report(redact, text, position)),
        text_block(f"Here is {'Image %d' % position} again:"),
        image_content_block(stimuli[chosen_key]["path"]),
        text_block(choice_instruction(next_choice_number, n_choices, announce_horizon)),
    ]}


def run_trajectory(client: OpenRouterClient, model_id: str, label: str, store: JsonlStore,
                    keys: list[str], stimuli: dict, traj_idx: int, n_choices: int,
                    redact: bool, root_seed: int, max_tokens: int, eval_name: str,
                    announce_horizon: bool) -> int:
    run_ids = [f"{label}__traj{traj_idx:03d}__turn{t:02d}" for t in range(n_choices)]
    if all(store.has(rid) for rid in run_ids):
        return 0

    # Seed derivation deliberately omits eval_name so eval3/eval4 share
    # snapshots -- see module docstring.
    permutation = balanced_snapshot(root_seed, keys, traj_idx, "trajectory", label)
    content = exposure_content_blocks(permutation, stimuli)
    content.append(text_block(choice_instruction(1, n_choices, announce_horizon)))
    mark_cache_control(content, model_id)

    messages: list[dict] = [
        {"role": "system", "content": system_prompt(n_choices=n_choices, eval_name=eval_name,
                                                    announce_horizon=announce_horizon,
                                                    redacted=redact)},
        {"role": "user", "content": content},
    ]
    session_id = f"{eval_name}__{label}__traj{traj_idx:03d}"

    # Resuming mid-trajectory: replay already-completed turns back into
    # `messages` exactly as the live loop below would have appended them, so
    # a restarted run's next API call sees the same context an uninterrupted
    # run would have. Calls within a trajectory are made and appended to the
    # store strictly in order, so completed run_ids form a contiguous prefix
    # from turn 0 -- this stops at the first missing one.
    existing_by_turn = {
        row["turn_idx"]: row for row in store.read_all()
        if row.get("trajectory_idx") == traj_idx and row.get("eval") == eval_name
    }
    start_turn = 0
    for turn_idx in range(n_choices):
        row = existing_by_turn.get(turn_idx)
        if row is None:
            break
        position, chosen_key = row["chosen_position"], row["chosen_key"]
        start_turn = turn_idx + 1
        if turn_idx == n_choices - 1:
            break
        messages.append(delivery_message(position, chosen_key, turn_idx + 2, n_choices,
                                         stimuli, announce_horizon, redact,
                                         row["response_text"]))

    made = 0
    for turn_idx, run_id in enumerate(run_ids):
        if turn_idx < start_turn:
            continue

        choice_number = turn_idx + 1
        text, usage, raw = client.chat(model_id, messages, max_tokens=max_tokens,
                                        session_id=session_id)
        position = parse_next_image_id(text, range(1, len(permutation) + 1))
        chosen_key = permutation[position - 1] if position else None

        store.append({
            "run_id": run_id,
            "eval": eval_name,
            "model": model_id,
            "trajectory_idx": traj_idx,
            "turn_idx": turn_idx,
            "redact": redact,
            "permutation": permutation,
            "chosen_position": position,
            "chosen_key": chosen_key,
            "parse_ok": position is not None,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "response_text": text,       # always the real output, regardless of redact
            "response_chars": len(text),
            "usage": usage,
            "raw_response": raw,
        })
        made += 1
        if turn_idx == len(run_ids) - 1:
            break  # no need to deliver an image after the last choice

        messages.append(delivery_message(position, chosen_key, choice_number + 1,
                                          n_choices, stimuli, announce_horizon,
                                          redact, text))

    return made


def main() -> None:
    config = load_config()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", nargs="+", default=[m.label for m in config.models])
    parser.add_argument("--trajectories", type=int, default=None,
                         help="Override n_trajectories (default: config.yaml eval3/4)")
    parser.add_argument("--choices", type=int, default=None,
                         help="Override n_choices per trajectory (default: eval3.n_choices)")
    parser.add_argument("--redact", action="store_true",
                         help="Run eval 4 instead of eval 3: redact the assistant's own "
                              "narrative from what it sees in later turns.")
    parser.add_argument("--concurrency", type=int, default=None,
                         help="Trajectories run in parallel; turns within one are sequential.")
    args = parser.parse_args()

    eval_name = "eval4" if args.redact else "eval3"
    stimuli = load_stimuli(config)
    keys = ordered_keys(stimuli)
    n_trajectories = args.trajectories or config.raw[eval_name]["n_trajectories"]
    n_choices = args.choices or config.raw["eval3"]["n_choices"]
    announce_horizon = config.raw["eval3"].get("announce_horizon", True)
    max_tokens = config.raw["eval3"]["max_tokens"]
    concurrency = args.concurrency or config.raw["openrouter"]["concurrency"]

    cost_tracker = CostTracker()
    client = OpenRouterClient(config, cost_tracker=cost_tracker)

    for label in args.models:
        model = config.model_by_label(label)
        store = JsonlStore(config.data_dir / f"{eval_name}__{label}.jsonl")
        print(f"\n=== {eval_name} / {model.id} === ({len(store)} rows already done, "
              f"{n_trajectories} trajectories x {n_choices} choices "
              f"({'announced' if announce_horizon else 'HORIZON WITHHELD'}), redact={args.redact})")

        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            futures = {
                pool.submit(run_trajectory, client, model.id, label, store, keys, stimuli,
                            traj_idx, n_choices, args.redact, config.root_seed, max_tokens,
                            eval_name, announce_horizon): traj_idx
                for traj_idx in range(n_trajectories)
            }
            for fut in as_completed(futures):
                traj_idx = futures[fut]
                try:
                    made = fut.result()
                except Exception as exc:
                    print(f"  [error] trajectory {traj_idx}: {exc!r}")
                    continue
                if made:
                    print(f"  trajectory {traj_idx}: {made} turns")

        cost_tracker.print_summary()
        path = write_transcript(config, stimuli, eval_name, label)
        if path:
            print(f"  transcript -> {path}")

    print("\nDone.")
    cost_tracker.print_summary()


if __name__ == "__main__":
    main()
