"""Append-only JSONL persistence with resumability.

Every raw API response is written here before it is parsed (parsing is
re-runnable; API calls are not). A run is resumable because we load the set
of `run_id`s already present on disk at startup and skip them.
"""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any, Iterator


class JsonlStore:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._done_ids: set[str] = set()
        self._load_existing()

    def _load_existing(self) -> None:
        if not self.path.exists():
            return
        with open(self.path) as f:
            for line_no, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    # A crash mid-write can leave a truncated last line.
                    # Skip it rather than fail the whole resume; it will be
                    # re-run since its run_id won't be in _done_ids.
                    print(f"  [jsonl] skipping unparseable line {line_no} in {self.path}")
                    continue
                rid = row.get("run_id")
                if rid is not None:
                    self._done_ids.add(rid)

    def has(self, run_id: str) -> bool:
        return run_id in self._done_ids

    def append(self, row: dict[str, Any]) -> None:
        run_id = row.get("run_id")
        if run_id is None:
            raise ValueError("row must have a 'run_id' field for resumability")
        line = json.dumps(row, ensure_ascii=False)
        with self._lock:
            with open(self.path, "a") as f:
                f.write(line + "\n")
                f.flush()
            self._done_ids.add(run_id)

    def __len__(self) -> int:
        return len(self._done_ids)

    def read_all(self) -> Iterator[dict]:
        if not self.path.exists():
            return
        with open(self.path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue
