"""Load config.yaml and resolve paths relative to the project root."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Model:
    id: str
    label: str


@dataclass(frozen=True)
class Config:
    raw: dict
    root_seed: int
    temperature: float
    models: list[Model]
    image_size: int
    images_source_dir: Path
    images_processed_dir: Path
    stimuli_json: Path
    data_dir: Path
    results_dir: Path

    def model_by_label(self, label: str) -> Model:
        for m in self.models:
            if m.label == label:
                return m
        raise KeyError(f"No model with label {label!r} in config.yaml. "
                        f"Known labels: {[m.label for m in self.models]}")


def load_config(path: Path | None = None) -> Config:
    path = path or (PROJECT_ROOT / "config.yaml")
    with open(path) as f:
        raw = yaml.safe_load(f)

    paths = raw["paths"]

    def resolve(key: str) -> Path:
        p = Path(paths[key])
        return p if p.is_absolute() else PROJECT_ROOT / p

    models = [Model(id=m["id"], label=m["label"]) for m in raw["models"]]

    return Config(
        raw=raw,
        root_seed=int(raw["seed"]),
        temperature=float(raw["temperature"]),
        models=models,
        image_size=int(raw.get("image_size", 512)),
        images_source_dir=resolve("images_source_dir"),
        images_processed_dir=resolve("images_processed_dir"),
        stimuli_json=resolve("stimuli_json"),
        data_dir=resolve("data_dir"),
        results_dir=resolve("results_dir"),
    )
