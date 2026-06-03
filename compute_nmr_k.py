"""Compute NMR@k from saved ISS heatmaps and prepared masks."""

from __future__ import annotations

import json

import hydra
from iss_nmr_toolkit.constants import VIEW_NAMES
from iss_nmr_toolkit.core.nmr import compute_nmr
from iss_nmr_toolkit.io.artifacts import load_iss, save_nmr_csv, save_nmr_json
from iss_nmr_toolkit.io.episode import load_masks
from iss_nmr_toolkit.runner_utils import (
    iss_path,
    k_title,
    nmr_paths,
    output_dir,
    quiet_third_party_logs,
    require_existing,
    resolve_episode_dir,
)
from omegaconf import DictConfig, OmegaConf


@hydra.main(version_base=None, config_path="configs", config_name="xicm_episode")
def main(cfg: DictConfig) -> None:
    quiet_third_party_logs()
    path = iss_path(cfg)
    try:
        require_existing(path, "python gen_iss_heatmap.py")
    except FileNotFoundError as exc:
        print(f"Error: {exc}")
        raise SystemExit(1) from exc

    episode_dir = resolve_episode_dir(cfg)
    heatmaps = load_iss(path, views=VIEW_NAMES)
    masks = load_masks(episode_dir, views=VIEW_NAMES)
    payload = compute_nmr(
        heatmaps,
        masks,
        views=VIEW_NAMES,
        k_pixels=int(cfg.nmr.k_pixels),
        k_percent=float(cfg.nmr.k_percent),
        normalize=str(cfg.nmr.normalize),
    )
    payload["episode_dir"] = str(episode_dir.resolve())
    payload["iss_path"] = str(path.resolve())
    payload["config"] = OmegaConf.to_container(cfg, resolve=True)

    paths = nmr_paths(cfg)
    json_path = save_nmr_json(paths["json"], payload)
    csv_path = save_nmr_csv(paths["csv"], payload, views=VIEW_NAMES)
    summary = {
        "mean_nmr": payload["mean_score"],
        "mean_coverage": payload["mean_coverage"],
        "nmr_json": str(json_path),
        "nmr_csv": str(csv_path),
        "iss_heatmaps": str(path),
        "config": OmegaConf.to_container(cfg, resolve=True),
    }
    output_dir(cfg).mkdir(parents=True, exist_ok=True)
    with (output_dir(cfg) / "nmr_summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"NMR@{k_title(int(cfg.nmr.k_pixels), float(cfg.nmr.k_percent))}: {payload['mean_score']:.6f}")
    print(f"Top-k green+blue coverage: {payload['mean_coverage']:.6f}")
    print(f"Saved NMR JSON: {json_path}")
    print(f"Saved NMR CSV: {csv_path}")


if __name__ == "__main__":
    main()
