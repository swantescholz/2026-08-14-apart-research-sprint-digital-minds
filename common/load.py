"""Load eval JSONL output into pandas DataFrames for analyze.py."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def _read_jsonl(path: Path) -> list[dict]:
    rows = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def load_eval(data_dir: Path, eval_name: str) -> pd.DataFrame:
    """Load every data_dir/<eval_name>__<label>.jsonl into one DataFrame,
    with a `model_label` column added. Empty DataFrame if none exist."""
    rows = []
    for path in sorted(data_dir.glob(f"{eval_name}__*.jsonl")):
        label = path.stem.removeprefix(f"{eval_name}__")
        for row in _read_jsonl(path):
            row["model_label"] = label
            rows.append(row)
    return pd.DataFrame(rows)


def with_category(df: pd.DataFrame, stimuli: dict, key_col: str = "image_key") -> pd.DataFrame:
    """Add `category` / `exemplar` columns by looking up `key_col` in stimuli.json."""
    df = df.copy()
    df["category"] = df[key_col].map(lambda k: stimuli[k]["category"] if pd.notna(k) else None)
    df["exemplar"] = df[key_col].map(lambda k: stimuli[k]["exemplar"] if pd.notna(k) else None)
    return df
