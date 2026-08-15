#!/usr/bin/env python3
"""Regenerate human-readable Markdown transcripts from the raw JSONL logs.

The eval runners write a transcript automatically at the end of each run, so
this is for logs that already exist, for re-rendering after a change to the
transcript format, and for rendering archived runs under testruns/.

    python make_transcripts.py                      # everything in data/
    python make_transcripts.py --evals eval3 eval4  # just those
    python make_transcripts.py --data-dir testruns/smoke-2026-08-14/data \
                               --out testruns/smoke-2026-08-14/transcripts
"""

from __future__ import annotations

import argparse
from pathlib import Path

from common.config import load_config
from common.jsonl_store import JsonlStore
from common.stimuli import load_stimuli
from common.transcripts import render

EVALS = ("eval1", "eval2", "eval3", "eval4")


def main() -> None:
    config = load_config()
    parser = argparse.ArgumentParser(description=__doc__,
                                      formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--evals", nargs="+", default=list(EVALS), choices=EVALS)
    parser.add_argument("--models", nargs="+", default=None,
                         help="Model labels (default: whatever is present in the data dir)")
    parser.add_argument("--data-dir", type=Path, default=None,
                         help="Read logs from here instead of config's data_dir")
    parser.add_argument("--out", type=Path, default=None,
                         help="Write transcripts here instead of ./transcripts")
    args = parser.parse_args()

    data_dir = args.data_dir or config.data_dir
    out_dir = args.out or (config.data_dir.parent / "transcripts")
    out_dir.mkdir(parents=True, exist_ok=True)
    stimuli = load_stimuli(config)

    written = 0
    for eval_name in args.evals:
        for src in sorted(data_dir.glob(f"{eval_name}__*.jsonl")):
            label = src.stem.removeprefix(f"{eval_name}__")
            if args.models and label not in args.models:
                continue
            rows = list(JsonlStore(src).read_all())
            if not rows:
                continue
            model = rows[0].get("model", label)
            dest = out_dir / f"{eval_name}__{label}.md"
            dest.write_text(render(eval_name, rows, stimuli, config, model))
            size_kb = dest.stat().st_size / 1024
            print(f"  wrote {dest}  ({len(rows)} calls, {size_kb:.0f} KB)")
            written += 1

    if not written:
        print(f"No logs found in {data_dir}")
    else:
        print(f"\n{written} transcript(s) in {out_dir}")


if __name__ == "__main__":
    main()
