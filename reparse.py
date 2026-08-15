#!/usr/bin/env python3
"""Re-derive the parsed fields in existing JSONL from the stored response text.

The raw API response is persisted before parsing precisely so that a parser
fix does not cost another API call. This applies the current parser to data
already on disk and rewrites the parsed columns in place.

Only parsed fields change (enjoyment/interest/chosen_position/chosen_key/
parse_ok). response_text, usage and raw_response are never touched.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from common.config import load_config
from common.parsing import parse_next_image_id, parse_scores


def reparse_row(row: dict) -> tuple[dict, bool]:
    text = row.get("response_text") or ""
    before = row.get("parse_ok")
    if row["eval"] == "eval1":
        scores = parse_scores(text)
        row["enjoyment"], row["interest"] = scores if scores else (None, None)
        row["parse_ok"] = scores is not None
    else:
        perm = row.get("permutation") or []
        pos = parse_next_image_id(text, range(1, len(perm) + 1))
        row["chosen_position"] = pos
        row["chosen_key"] = perm[pos - 1] if pos else None
        row["parse_ok"] = pos is not None
    return row, row["parse_ok"] != before


def main() -> None:
    config = load_config()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true", help="report changes, write nothing")
    args = ap.parse_args()

    total_changed = 0
    for path in sorted(config.data_dir.glob("eval*.jsonl")):
        rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
        changed = 0
        for row in rows:
            _, did = reparse_row(row)
            changed += did
        ok = sum(1 for r in rows if r["parse_ok"])
        flag = f"  {changed:+d} newly parsed" if changed else ""
        print(f"  {path.name:<26} {ok}/{len(rows)} parse_ok{flag}")
        if changed and not args.dry_run:
            shutil.copy(path, path.with_suffix(".jsonl.bak"))
            with open(path, "w") as f:
                for row in rows:
                    f.write(json.dumps(row, ensure_ascii=False) + "\n")
        total_changed += changed
    print(f"\n{total_changed} row(s) changed" + (" (dry run, nothing written)" if args.dry_run else ""))


if __name__ == "__main__":
    main()
