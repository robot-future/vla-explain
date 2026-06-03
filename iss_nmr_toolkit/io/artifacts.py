"""Save and load ISS/NMR artifacts."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import numpy as np

from iss_nmr_toolkit.constants import VIEW_NAMES


def save_iss_npz(path: str | Path, heatmaps: dict[str, np.ndarray], meta: dict[str, Any] | None = None) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {view: heatmaps[view].astype(np.float32) for view in heatmaps}
    payload["meta_json"] = np.asarray(json.dumps(meta or {}, indent=2))
    np.savez_compressed(output, **payload)
    return output


def load_iss(path: str | Path, *, views: tuple[str, ...] = VIEW_NAMES) -> dict[str, np.ndarray]:
    path = Path(path)
    if path.suffix == ".npz":
        data = np.load(path, allow_pickle=True)
        return {view: np.asarray(data[view], dtype=np.float32) for view in views}

    data = np.load(path, allow_pickle=True)
    if isinstance(data, np.ndarray) and data.shape == ():
        data = data.item()
    if not isinstance(data, dict) or "heatmaps" not in data:
        raise ValueError(f"Invalid ISS artifact: {path}")
    return {view: np.asarray(data["heatmaps"][view], dtype=np.float32) for view in views}


def save_nmr_json(path: str | Path, nmr_payload: dict[str, Any]) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)

    serializable: dict[str, Any] = {}
    for key, value in nmr_payload.items():
        if isinstance(value, np.ndarray):
            serializable[key] = value.tolist()
        elif isinstance(value, dict):
            serializable[key] = {
                sub_key: sub_value.tolist() if isinstance(sub_value, np.ndarray) else sub_value
                for sub_key, sub_value in value.items()
            }
        else:
            serializable[key] = value

    with output.open("w", encoding="utf-8") as f:
        json.dump(serializable, f, indent=2)
    return output


def save_nmr_csv(path: str | Path, nmr_payload: dict[str, Any], *, views: tuple[str, ...] = VIEW_NAMES) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)

    scores = np.asarray(nmr_payload["scores"], dtype=np.float32)
    per_view = nmr_payload["per_view_scores"]
    coverage = nmr_payload.get("coverage_scores")
    per_view_coverage = nmr_payload.get("per_view_coverage_scores")
    with output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if coverage is None or per_view_coverage is None:
            writer.writerow(["step", "nmr", *[f"nmr_{view}" for view in views]])
        else:
            writer.writerow(
                [
                    "step",
                    "nmr",
                    *[f"nmr_{view}" for view in views],
                    "coverage_green_blue",
                    *[f"coverage_green_blue_{view}" for view in views],
                ]
            )
        for step, score in enumerate(scores):
            row = [step, float(score), *[float(per_view[view][step]) for view in views]]
            if coverage is not None and per_view_coverage is not None:
                row.extend(
                    [
                        float(coverage[step]),
                        *[float(per_view_coverage[view][step]) for view in views],
                    ]
                )
            writer.writerow(row)
    return output
