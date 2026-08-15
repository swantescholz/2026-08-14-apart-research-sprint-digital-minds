"""Render the raw JSONL logs as human-readable Markdown transcripts.

The JSONL is the record of what happened; it is not something anyone wants to
read. These transcripts are the readable view: what the model was shown, what
it actually said, and what that got parsed into.

Two things the model never sees are added here deliberately, because a human
reading a transcript needs them to make sense of anything: the internal image
keys (`tech_2`) and their categories. The model only ever saw "Image 7" and
the pixels. Anywhere a transcript shows a key, that is annotation for the
reader, not something that was in the prompt.

`write_transcript` is called at the end of each eval run, so a transcript
appears (and refreshes) automatically; `make_transcripts.py` regenerates them
for logs that already exist.
"""

from __future__ import annotations

import itertools
from pathlib import Path

from common.jsonl_store import JsonlStore

RULE = "\n---\n"


def _legend(permutation: list[str], stimuli: dict) -> str:
    """The position -> image mapping for one snapshot. Reader-only."""
    lines = ["| shown as | image | category |", "|---|---|---|"]
    for i, key in enumerate(permutation, start=1):
        lines.append(f"| Image {i} | `{key}` | {stimuli[key]['category']} |")
    return "\n".join(lines)


def _quote(text: str) -> str:
    """Render model output as a blockquote so it can't break the page
    structure with its own headings or lists."""
    if not text.strip():
        return "> *(empty response)*"
    return "\n".join("> " + line if line.strip() else ">"
                     for line in text.strip().splitlines())


def _header(eval_name: str, model: str, rows: list[dict], config, extra: str = "") -> str:
    ok = sum(1 for r in rows if r.get("parse_ok"))
    cost = sum((r.get("usage") or {}).get("cost") or 0.0 for r in rows)
    return (
        f"# {eval_name} — {model}\n\n"
        f"*Generated from `data/{eval_name}__*.jsonl`. Do not edit; regenerate with "
        f"`python make_transcripts.py`.*\n\n"
        f"- **calls**: {len(rows)} ({ok} parsed, {len(rows) - ok} failed)\n"
        f"- **temperature**: {config.temperature} · **root seed**: {config.root_seed}\n"
        f"- **cost**: ${cost:.4f}\n"
        f"{extra}"
    )


def _render_eval1(rows: list[dict], stimuli: dict, config, model: str) -> str:
    rows = sorted(rows, key=lambda r: (r["image_key"], r["run_id"]))
    out = [_header("eval1", model, rows, config,
                    "\n**Design**: one image per fresh context, no other images present. "
                    "The model was asked for a free-form reaction plus `enjoyment` and "
                    "`interest` scores.\n")]
    for image_key, group in itertools.groupby(rows, key=lambda r: r["image_key"]):
        group = list(group)
        cat = stimuli[image_key]["category"]
        enj = [r["enjoyment"] for r in group if r["enjoyment"] is not None]
        inte = [r["interest"] for r in group if r["interest"] is not None]
        out.append(RULE)
        out.append(f"## `{image_key}` ({cat}) — {len(group)} runs\n")
        if enj:
            out.append(f"mean enjoyment **{sum(enj)/len(enj):.1f}**, "
                       f"mean interest **{sum(inte)/len(inte):.1f}**\n")
        for r in group:
            retried = " · *reparsed after a failed first attempt*" if r.get("parse_attempts", 1) > 1 else ""
            scores = (f"enjoyment={r['enjoyment']} interest={r['interest']}"
                      if r["parse_ok"] else "**PARSE FAILED**")
            out.append(f"\n### {r['run_id']} — {scores}{retried}\n")
            out.append(_quote(r["response_text"]))
    return "\n".join(out) + "\n"


def _render_eval2(rows: list[dict], stimuli: dict, config, model: str) -> str:
    rows = sorted(rows, key=lambda r: (r["snapshot_idx"], r["trial_idx"]))
    out = [_header("eval2", model, rows, config,
                    "\n**Design**: all 10 images in one shuffled, labelled exposure turn, "
                    "then exactly one choice. Each snapshot is one shuffle, reused across "
                    "its trials; snapshots are position-balanced.\n")]
    for snap, group in itertools.groupby(rows, key=lambda r: r["snapshot_idx"]):
        group = list(group)
        out.append(RULE)
        out.append(f"## Snapshot {snap} — {len(group)} trials\n")
        out.append("<details><summary>position → image legend "
                   "(reader annotation; the model saw only the images)</summary>\n")
        out.append(_legend(group[0]["permutation"], stimuli))
        out.append("\n</details>\n")
        for r in group:
            if r["parse_ok"]:
                chose = (f"chose **Image {r['chosen_position']}** = `{r['chosen_key']}` "
                         f"({stimuli[r['chosen_key']]['category']})")
            else:
                chose = "**PARSE FAILED**"
            out.append(f"\n### Trial {r['trial_idx']} — {chose}\n")
            out.append(_quote(r["response_text"]))
    return "\n".join(out) + "\n"


def _render_trajectories(rows: list[dict], stimuli: dict, config, model: str,
                          eval_name: str) -> str:
    rows = sorted(rows, key=lambda r: (r["trajectory_idx"], r["turn_idx"]))
    redacted = any(r.get("redact") for r in rows)
    note = (
        "\n**Design**: same exposure block as eval2, then 10 choices in sequence. "
        "Each chosen image is re-delivered as the next user turn and stays in "
        "context, so duplicates accumulate.\n"
    )
    if redacted:
        note += (
            "\n> **Redaction is on.** Everything quoted below is what the model *wrote*, "
            "and all of it is preserved in the log — but on later turns the model saw "
            "only `[main model output redacted]` plus its own `next_image_id=N` line in "
            "place of each of its earlier replies. The images stayed in context. So the "
            "reasoning you are reading was **not** visible to the model when it made "
            "later choices.\n"
        )
    out = [_header(eval_name, model, rows, config, note)]
    for traj, group in itertools.groupby(rows, key=lambda r: r["trajectory_idx"]):
        group = list(group)
        seq = " → ".join(str(r["chosen_position"]) for r in group)
        distinct = len({r["chosen_key"] for r in group if r["chosen_key"]})
        out.append(RULE)
        out.append(f"## Trajectory {traj}\n")
        out.append(f"positions chosen: `{seq}` · {distinct} distinct images\n")
        out.append("<details><summary>position → image legend "
                   "(reader annotation; the model saw only the images)</summary>\n")
        out.append(_legend(group[0]["permutation"], stimuli))
        out.append("\n</details>\n")
        seen: dict[str, int] = {}
        for r in group:
            key = r["chosen_key"]
            if r["parse_ok"]:
                nth = seen.get(key, 0)
                again = f" · {nth + 1}{'st' if nth == 0 else 'nd' if nth == 1 else 'rd' if nth == 2 else 'th'} time chosen"
                chose = (f"chose **Image {r['chosen_position']}** = `{key}` "
                         f"({stimuli[key]['category']}){again}")
                seen[key] = nth + 1
            else:
                chose = "**PARSE FAILED** — trajectory continued with a re-ask"
            out.append(f"\n### Choice {r['turn_idx'] + 1} of {len(group)} — {chose}\n")
            out.append(_quote(r["response_text"]))
    return "\n".join(out) + "\n"


RENDERERS = {
    "eval1": _render_eval1,
    "eval2": _render_eval2,
}


def render(eval_name: str, rows: list[dict], stimuli: dict, config, model: str) -> str:
    if eval_name in RENDERERS:
        return RENDERERS[eval_name](rows, stimuli, config, model)
    if eval_name in ("eval3", "eval4"):
        return _render_trajectories(rows, stimuli, config, model, eval_name)
    raise ValueError(f"no transcript renderer for {eval_name!r}")


def write_transcript(config, stimuli: dict, eval_name: str, label: str) -> Path | None:
    """Render data/<eval>__<label>.jsonl to transcripts/<eval>__<label>.md.

    Returns the path written, or None if there is no data yet. Never raises on
    a rendering problem: a transcript is a convenience view, and losing one
    must not take down a run that has already paid for its API calls.
    """
    src = config.data_dir / f"{eval_name}__{label}.jsonl"
    if not src.exists():
        return None
    rows = list(JsonlStore(src).read_all())
    if not rows:
        return None
    dest_dir = config.raw["paths"].get("transcripts_dir", "transcripts")
    dest_dir = Path(dest_dir)
    if not dest_dir.is_absolute():
        dest_dir = config.data_dir.parent / dest_dir
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{eval_name}__{label}.md"
    try:
        model = rows[0].get("model", label)
        dest.write_text(render(eval_name, rows, stimuli, config, model))
    except Exception as exc:  # noqa: BLE001 - see docstring
        print(f"  [transcript] failed to render {eval_name}/{label}: {exc!r}")
        return None
    return dest
