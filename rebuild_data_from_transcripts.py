#!/usr/bin/env python3
"""Rebuild data/<eval>__<model>.jsonl from transcripts/<eval>__<model>.md.

Why this exists
---------------
`data/*.jsonl` is gitignored (roughly 1MB per file, over the size line in the
root CLAUDE.md), and on 2026-08-15 the working copies of the four final runs
were deleted during the move to a standalone repository. There was no backup:
never tracked, no Time Machine destination, no APFS snapshot. The transcripts
were tracked, so they are what is left.

This is the inverse of `common/transcripts.py`. It is deliberately strict --
it asserts the per-file call count in the transcript header matches the number
of rows recovered, and refuses to write a file that does not reconcile --
because a silently partial rebuild is worse than no rebuild.

What comes back exactly, and what does not
------------------------------------------
Recovered exactly: every field `analyze.py` reads except one. That is
run ids, image keys, both eval-1 scores, parse status and retry count, the
snapshot/trajectory indices, the position->image permutation, the chosen
position and key per turn, and the full response text.

`response_chars` is recomputed as `len(response_text)`, which is how the
runners defined it (verified against surviving raw logs: 0 of 72 rows
disagree). The transcript renderer applies `.strip()` to the response before
quoting it, so this is exact only if no response carried leading or trailing
whitespace -- also verified against the survivors, 0 of 72.

NOT recoverable: `response_completion_tokens` (never rendered), and the raw
API `usage`/`cost`/`timestamp`/`raw_response` payloads. Rows are therefore
written with `response_completion_tokens: null`, which propagates to a single
column of `eval1_by_image.csv` and to the `resp_tokens_mean` rows of
`eval1_implicit_engagement.csv`. Every other table regenerates identically --
`--verify` proves it.

Usage
-----
    python rebuild_data_from_transcripts.py --check testruns/smoke-2026-08-14
    python rebuild_data_from_transcripts.py
    python analyze.py

`--check DIR` runs the rebuild against a directory that still has both its
`data/` and `transcripts/`, and diffs field by field against the surviving
JSONL. That is the honest test of this script, and it should be run before
trusting its output anywhere else.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from reparse import reparse_row

HEADER_MODEL = re.compile(r"^# (eval\d) — (.+)$")
HEADER_CALLS = re.compile(r"^- \*\*calls\*\*: (\d+) \((\d+) parsed, (\d+) failed\)$")

EVAL1_SECTION = re.compile(r"^## `([^`]+)` \(([^)]+)\) — (\d+) runs$")
EVAL1_ENTRY = re.compile(
    r"^### (\S+) — (?:enjoyment=(-?\d+) interest=(-?\d+)|\*\*PARSE FAILED\*\*)"
    r"(?: · \*reparsed after a failed first attempt\*)?$"
)
EVAL2_SECTION = re.compile(r"^## Snapshot (\d+) — (\d+) trials$")
EVAL2_ENTRY = re.compile(
    r"^### Trial (\d+) — (?:chose \*\*Image (\d+)\*\* = `([^`]+)`|\*\*PARSE FAILED\*\*)"
)
TRAJ_SECTION = re.compile(r"^## Trajectory (\d+)$")
TRAJ_ENTRY = re.compile(
    r"^### Choice (\d+) of (\d+) — (?:chose \*\*Image (\d+)\*\* = `([^`]+)`|\*\*PARSE FAILED\*\*)"
)
LEGEND_ROW = re.compile(r"^\| Image (\d+) \| `([^`]+)` \| \S+ \|$")

REPARSED = " · *reparsed after a failed first attempt*"
EMPTY_MARKER = "> *(empty response)*"


def _unquote(lines: list[str], start: int) -> tuple[str, int]:
    """Invert `common.transcripts._quote`, starting at `start`.

    Returns the recovered text and the index of the first line after the
    blockquote. `> ` prefixes a content line and a bare `>` an empty one.
    """
    if start < len(lines) and lines[start] == EMPTY_MARKER:
        return "", start + 1
    out: list[str] = []
    i = start
    while i < len(lines):
        line = lines[i]
        if line.startswith("> "):
            out.append(line[2:])
        elif line == ">":
            out.append("")
        else:
            break
        i += 1
    return "\n".join(out), i


def _legend(lines: list[str], start: int) -> tuple[list[str], int]:
    """Read a position->image legend table; returns the permutation."""
    perm: dict[int, str] = {}
    i = start
    while i < len(lines):
        m = LEGEND_ROW.match(lines[i])
        if m:
            perm[int(m.group(1))] = m.group(2)
        elif perm and lines[i].startswith("</details>"):
            break
        i += 1
    if not perm:
        raise ValueError(f"no legend found at line {start}")
    return [perm[j] for j in sorted(perm)], i


def _next_quote(lines: list[str], i: int) -> tuple[str, int]:
    """Skip blank lines to the blockquote that follows an entry heading."""
    while i < len(lines) and not lines[i].startswith(">"):
        if lines[i].startswith("###") or lines[i].startswith("##"):
            raise ValueError(f"expected a response blockquote near line {i}")
        i += 1
    return _unquote(lines, i)


def parse_transcript(path: Path, label: str) -> list[dict]:
    lines = path.read_text().splitlines()
    m = HEADER_MODEL.match(lines[0])
    if not m:
        raise ValueError(f"{path}: unrecognised header {lines[0]!r}")
    eval_name, model = m.group(1), m.group(2)

    declared = None
    for line in lines[:10]:
        h = HEADER_CALLS.match(line)
        if h:
            declared = int(h.group(1))
            break

    rows: list[dict] = []
    permutation: list[str] = []
    section: int | None = None
    i = 1
    while i < len(lines):
        line = lines[i]

        if eval_name == "eval1":
            s = EVAL1_SECTION.match(line)
            if s:
                section = s.group(1)  # image_key
                i += 1
                continue
            e = EVAL1_ENTRY.match(line)
            if e:
                text, i = _next_quote(lines, i + 1)
                ok = e.group(2) is not None
                rows.append({
                    "run_id": e.group(1), "eval": "eval1", "model": model,
                    "image_key": section,
                    "parse_ok": ok,
                    "parse_attempts": 2 if line.endswith(REPARSED) else 1,
                    "enjoyment": int(e.group(2)) if ok else None,
                    "interest": int(e.group(3)) if ok else None,
                    "response_text": text, "response_chars": len(text),
                    "response_completion_tokens": None,
                    "reconstructed_from_transcript": True,
                })
                continue

        elif eval_name == "eval2":
            s = EVAL2_SECTION.match(line)
            if s:
                section = int(s.group(1))
                permutation, i = _legend(lines, i + 1)
                continue
            e = EVAL2_ENTRY.match(line)
            if e:
                text, i = _next_quote(lines, i + 1)
                ok = e.group(2) is not None
                trial = int(e.group(1))
                rows.append({
                    "run_id": f"{label}__snap{section:03d}__t{trial:02d}",
                    "eval": "eval2", "model": model,
                    "snapshot_idx": section, "trial_idx": trial,
                    "permutation": permutation,
                    "chosen_position": int(e.group(2)) if ok else None,
                    "chosen_key": e.group(3) if ok else None,
                    "parse_ok": ok, "delivered": ok,
                    "response_text": text, "response_chars": len(text),
                    "response_completion_tokens": None,
                    "reconstructed_from_transcript": True,
                })
                continue

        else:  # eval3 / eval4
            s = TRAJ_SECTION.match(line)
            if s:
                section = int(s.group(1))
                permutation, i = _legend(lines, i + 1)
                continue
            e = TRAJ_ENTRY.match(line)
            if e:
                text, i = _next_quote(lines, i + 1)
                ok = e.group(3) is not None
                turn = int(e.group(1)) - 1
                rows.append({
                    "run_id": f"{label}__traj{section:03d}__turn{turn:02d}",
                    "eval": eval_name, "model": model,
                    "trajectory_idx": section, "turn_idx": turn,
                    "redact": eval_name == "eval4",
                    "permutation": permutation,
                    "chosen_position": int(e.group(3)) if ok else None,
                    "chosen_key": e.group(4) if ok else None,
                    "parse_ok": ok,
                    "response_text": text, "response_chars": len(text),
                    "response_completion_tokens": None,
                    "reconstructed_from_transcript": True,
                })
                continue

        i += 1

    if declared is not None and len(rows) != declared:
        raise ValueError(
            f"{path}: header declares {declared} calls, recovered {len(rows)}. "
            "Refusing to write a partial rebuild."
        )
    return rows


# Fields the transcript cannot carry. Compared as "expected missing" by --check
# rather than silently ignored.
UNRECOVERABLE = {"usage", "raw_response", "timestamp", "response_completion_tokens"}


def check(run_dir: Path) -> int:
    """Rebuild from a directory's transcripts and diff against its real JSONL."""
    # Older archived runs keep their JSONL at the directory root; newer ones
    # use a data/ subdirectory. Accept either.
    data_dir = run_dir / "data" if (run_dir / "data").is_dir() else run_dir
    tr_dir = run_dir / "transcripts"
    if not tr_dir.is_dir() or not any(data_dir.glob("*.jsonl")):
        print(f"{run_dir}: needs both JSONL and transcripts/ to check against")
        return 1

    failures = 0
    for src in sorted(data_dir.glob("*.jsonl")):
        eval_name, label = src.stem.split("__")
        tr = tr_dir / f"{eval_name}__{label}.md"
        if not tr.exists():
            print(f"  {src.name}: no transcript, skipped")
            continue
        truth = [json.loads(l) for l in src.read_text().splitlines() if l.strip()]
        rebuilt = parse_transcript(tr, label)

        if len(truth) != len(rebuilt):
            print(f"  {src.name}: FAIL row count {len(rebuilt)} != {len(truth)}")
            failures += 1
            continue

        truth_by_id = {r["run_id"]: r for r in truth}
        mismatched: dict[str, int] = {}
        for row in rebuilt:
            orig = truth_by_id.get(row["run_id"])
            if orig is None:
                mismatched["<missing run_id>"] = mismatched.get("<missing run_id>", 0) + 1
                continue
            for field, value in row.items():
                if field in UNRECOVERABLE or field == "reconstructed_from_transcript":
                    continue
                if field in orig and orig[field] != value:
                    mismatched[field] = mismatched.get(field, 0) + 1
        if mismatched:
            print(f"  {src.name}: FAIL {len(truth)} rows, mismatches {mismatched}")
            failures += 1
        else:
            print(f"  {src.name}: ok ({len(truth)} rows, all recoverable fields identical)")
    print("\nCHECK PASSED" if not failures else f"\nCHECK FAILED ({failures} file(s))")
    return failures


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", metavar="DIR", type=Path,
                    help="validate against a run directory that still has data/ and transcripts/")
    ap.add_argument("--transcripts", type=Path, default=Path("transcripts"))
    ap.add_argument("--out", type=Path, default=Path("data"))
    args = ap.parse_args()

    if args.check:
        raise SystemExit(check(args.check))

    args.out.mkdir(parents=True, exist_ok=True)
    total = recovered = 0
    for tr in sorted(args.transcripts.glob("eval*__*.md")):
        eval_name, label = tr.stem.split("__")
        rows = parse_transcript(tr, label)
        # A transcript can lag the data it was rendered from: transcripts are
        # written at the end of a run, but `reparse.py` may re-derive parsed
        # fields from stored text afterwards without re-rendering. Applying the
        # current parser here closes that gap, and uses the same function
        # reparse.py does rather than a second copy of the rules.
        newly = sum(reparse_row(row)[1] for row in rows)
        if newly:
            print(f"  {tr.name}: reparsed {newly} row(s) the transcript recorded as failed")
        recovered += newly
        dest = args.out / f"{eval_name}__{label}.jsonl"
        with open(dest, "w") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        total += len(rows)
        print(f"  wrote {dest} ({len(rows)} rows)")
    print(f"\n{total} rows rebuilt, {recovered} recovered by reparse. "
          f"Raw usage/cost/timestamps are NOT recovered; see this file's docstring.")


if __name__ == "__main__":
    main()
