"""Shared helpers for the public X-ICM command-line runners."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np
from omegaconf import DictConfig


def quiet_third_party_logs() -> None:
    logging.getLogger().setLevel(logging.WARNING)
    for name in ("absl", "jax", "jax._src.xla_bridge", "orbax", "datasets"):
        logging.getLogger(name).setLevel(logging.WARNING)


def parse_steps(value: Any) -> list[int] | None:
    if value is None:
        return None
    if isinstance(value, str):
        if not value.strip():
            return None
        return [int(part.strip()) for part in value.split(",") if part.strip()]
    return [int(step) for step in value]


def resolve_episode_dir(cfg: DictConfig) -> Path:
    if cfg.data.episode_dir is not None:
        return Path(str(cfg.data.episode_dir))
    return Path(str(cfg.data.root)) / str(cfg.data.task) / str(cfg.data.episode)


def resolve_prompt(cfg: DictConfig) -> str | None:
    if cfg.data.prompt is not None:
        return str(cfg.data.prompt)
    return None


def output_dir(cfg: DictConfig) -> Path:
    return Path(str(cfg.output.dir))


def iss_path(cfg: DictConfig) -> Path:
    return output_dir(cfg) / "iss" / "iss_heatmaps.npz"


def k_slug(k_pixels: int, k_percent: float) -> str:
    if k_pixels > 0:
        return f"{int(k_pixels)}px"
    return f"{float(k_percent):g}".replace(".", "p") + "pct"


def k_title(k_pixels: int, k_percent: float) -> str:
    if k_pixels > 0:
        return f"{int(k_pixels)} pixels"
    return f"{float(k_percent):g}%"


def nmr_paths(cfg: DictConfig) -> dict[str, Path]:
    slug = k_slug(int(cfg.nmr.k_pixels), float(cfg.nmr.k_percent))
    root = output_dir(cfg) / "nmr"
    return {
        "json": root / f"nmr@{slug}.json",
        "csv": root / f"nmr@{slug}.csv",
        "png": root / f"nmr@{slug}.png",
    }


def legacy_nmr_json_path(cfg: DictConfig) -> Path:
    return output_dir(cfg) / "nmr" / "nmr.json"


def visualization_dirs(cfg: DictConfig) -> tuple[Path, Path]:
    slug = k_slug(int(cfg.nmr.k_pixels), float(cfg.nmr.k_percent))
    root = output_dir(cfg)
    return root / f"iss_images_nmr@{slug}", root / f"iss_videos_nmr@{slug}"


def require_existing(path: Path, producer: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Missing {path}. Run `{producer}` first.")


def top_k_percent_for_visualization(cfg: DictConfig, heatmaps: dict[str, np.ndarray]) -> float:
    if cfg.viz.top_k_percent is not None:
        return float(cfg.viz.top_k_percent)
    k_pixels = int(cfg.nmr.k_pixels)
    if k_pixels > 0:
        num_pixels = sum(int(np.prod(heatmaps[view][0].shape)) for view in heatmaps)
        return 100.0 * min(k_pixels, num_pixels) / float(num_pixels)
    return float(cfg.nmr.k_percent)
