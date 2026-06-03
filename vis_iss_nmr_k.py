"""Visualize ISS heatmaps using the same top-k threshold as NMR@k."""

from __future__ import annotations

import json

import hydra
from iss_nmr_toolkit.constants import DEFAULT_VIEWS, VIEW_NAMES
from iss_nmr_toolkit.io.artifacts import load_iss
from iss_nmr_toolkit.io.episode import load_episode_directory
from iss_nmr_toolkit.runner_utils import (
    iss_path,
    k_title,
    legacy_nmr_json_path,
    nmr_paths,
    parse_steps,
    quiet_third_party_logs,
    require_existing,
    resolve_episode_dir,
    resolve_prompt,
    top_k_percent_for_visualization,
    visualization_dirs,
)
from iss_nmr_toolkit.viz.heatmap import render_iss_videos, save_iss_snapshots
from iss_nmr_toolkit.viz.nmr import plot_nmr
from omegaconf import DictConfig


def load_nmr_payload(cfg: DictConfig) -> tuple[dict[str, object], str]:
    path = nmr_paths(cfg)["json"]
    if not path.exists() and legacy_nmr_json_path(cfg).exists():
        path = legacy_nmr_json_path(cfg)
    require_existing(path, "python compute_nmr_k.py")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f), str(path)


@hydra.main(version_base=None, config_path="configs", config_name="xicm_episode")
def main(cfg: DictConfig) -> None:
    quiet_third_party_logs()
    path = iss_path(cfg)
    try:
        require_existing(path, "python gen_iss_heatmap.py")
        nmr_payload, nmr_json = load_nmr_payload(cfg)
    except FileNotFoundError as exc:
        print(f"Error: {exc}")
        raise SystemExit(1) from exc

    episode_dir = resolve_episode_dir(cfg)
    observations = load_episode_directory(
        episode_dir,
        prompt=resolve_prompt(cfg),
        require_state=False,
    )
    heatmaps = load_iss(path, views=VIEW_NAMES)
    top_k_percent = top_k_percent_for_visualization(cfg, heatmaps)
    image_dir, video_dir = visualization_dirs(cfg)

    snapshot_paths = save_iss_snapshots(
        observations,
        heatmaps,
        image_dir,
        views=DEFAULT_VIEWS,
        steps=parse_steps(cfg.viz.snapshot_steps),
        alpha=float(cfg.viz.alpha),
        top_k_percent=top_k_percent,
    )
    if not bool(cfg.viz.skip_video):
        render_iss_videos(
            observations,
            heatmaps,
            video_dir,
            views=DEFAULT_VIEWS,
            fps=int(cfg.viz.fps),
            alpha=float(cfg.viz.alpha),
            top_k_percent=top_k_percent,
        )

    k = k_title(int(cfg.nmr.k_pixels), float(cfg.nmr.k_percent))
    nmr_png = plot_nmr(
        nmr_paths(cfg)["png"],
        nmr_payload,
        views=VIEW_NAMES,
        title=f"{cfg.data.task}/{cfg.data.episode} NMR@{k}",
        ylabel=f"NMR@{k}",
    )

    print(f"Loaded ISS heatmaps: {path}")
    print(f"Loaded NMR values: {nmr_json}")
    print(f"Visualized ISS top-k threshold: {top_k_percent:.6g}%")
    print(f"Saved ISS images: {image_dir} ({len(snapshot_paths)} files)")
    if not bool(cfg.viz.skip_video):
        print(f"Saved ISS videos: {video_dir}")
    print(f"Saved NMR plot: {nmr_png}")


if __name__ == "__main__":
    main()
