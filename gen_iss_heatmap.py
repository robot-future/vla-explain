"""Generate ISS heatmaps from an exported X-ICM or native LeRobot episode."""

from __future__ import annotations

import json

import hydra
from iss_nmr_toolkit.core.iss import compute_iss
from iss_nmr_toolkit.io.artifacts import save_iss_npz
from iss_nmr_toolkit.io.episode import load_episode_directory, load_lerobot_episode
from iss_nmr_toolkit.policies.lerobot_pi05 import LeRobotPi05PolicyAdapter
from iss_nmr_toolkit.policies.pi05 import Pi05PolicyAdapter
from iss_nmr_toolkit.runner_utils import (
    iss_path,
    output_dir,
    quiet_third_party_logs,
    resolve_episode_dir,
    resolve_prompt,
    resolve_views,
)
from iss_nmr_toolkit.viz.heatmap import render_iss_videos, save_iss_snapshots
from omegaconf import DictConfig, OmegaConf


@hydra.main(version_base=None, config_path="configs", config_name="xicm_episode")
def main(cfg: DictConfig) -> None:
    quiet_third_party_logs()
    views = resolve_views(cfg)
    data_source = str(cfg.data.get("source", "directory"))
    episode_dir = resolve_episode_dir(cfg) if data_source == "directory" else None
    out_dir = output_dir(cfg)
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        if data_source == "lerobot":
            observations = load_lerobot_episode(
                cfg.data.root,
                repo_id=str(cfg.data.repo_id),
                episode_index=int(cfg.data.episode_index),
                views=views,
                prompt=resolve_prompt(cfg),
                require_state=bool(cfg.data.require_state),
                state_key=str(cfg.data.get("state_key", "observation.state")),
            )
        else:
            observations = load_episode_directory(
                episode_dir,
                views=views,
                prompt=resolve_prompt(cfg),
                require_state=bool(cfg.data.require_state),
            )
    except FileNotFoundError as exc:
        print(f"Error: {exc}")
        if data_source == "directory":
            print(
                "The prepared episode must include states.npz in the episode directory, "
                "with joint_position and gripper_position arrays aligned to the RGB frames."
            )
        else:
            print(
                "Check data.root, data.repo_id, data.episode_index, and whether the "
                "LeRobot environment can decode this dataset's videos."
            )
        raise SystemExit(1) from exc

    policy_backend = str(cfg.policy.get("backend", "openpi"))
    if policy_backend == "lerobot":
        policy = LeRobotPi05PolicyAdapter(
            cfg.policy.checkpoint_dir,
            device=str(cfg.policy.get("device", "cuda")),
            use_half=bool(cfg.policy.get("use_half", False)),
            seed=int(cfg.policy.get("seed", cfg.iss.seed)),
            deterministic=bool(cfg.policy.get("deterministic", True)),
        )
    else:
        policy = Pi05PolicyAdapter(
            cfg.policy.checkpoint_dir,
            config_name=cfg.policy.config_name,
            cuda_visible_devices=cfg.policy.cuda_visible_devices,
        )
    heatmaps = compute_iss(
        policy,
        observations,
        views=views,
        n_masks=int(cfg.iss.n_masks),
        p_keep=float(cfg.iss.p_keep),
        grid_size=(int(cfg.iss.grid_size[0]), int(cfg.iss.grid_size[1])),
        blur_sigma=float(cfg.iss.blur_sigma),
        time_stride=int(cfg.iss.time_stride),
        batch_size=int(cfg.iss.batch_size),
        seed=int(cfg.iss.seed),
    )

    path = save_iss_npz(
        iss_path(cfg),
        heatmaps,
        meta={
            "episode_dir": str(episode_dir.resolve()) if episode_dir is not None else None,
            "dataset_root": str(cfg.data.root),
            "episode_index": int(cfg.data.get("episode_index", -1)),
            "policy": policy_backend,
            "config_name": str(cfg.policy.get("config_name", "")),
            "n_masks": int(cfg.iss.n_masks),
            "p_keep": float(cfg.iss.p_keep),
            "grid_size": [int(cfg.iss.grid_size[0]), int(cfg.iss.grid_size[1])],
            "blur_sigma": float(cfg.iss.blur_sigma),
            "time_stride": int(cfg.iss.time_stride),
            "seed": int(cfg.iss.seed),
            "views": views,
            "config": OmegaConf.to_container(cfg, resolve=True),
        },
    )
    summary = {
        "iss_heatmaps": str(path),
        "episode_dir": str(episode_dir) if episode_dir is not None else None,
        "config": OmegaConf.to_container(cfg, resolve=True),
    }
    with (out_dir / "iss_summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    if bool(cfg.viz.get("render_after_iss", False)):
        image_dir = out_dir / "iss_images"
        video_dir = out_dir / "iss_videos"
        save_iss_snapshots(
            observations,
            heatmaps,
            image_dir,
            views=views,
            steps=None,
            alpha=float(cfg.viz.alpha),
            top_k_percent=float(cfg.viz.get("top_k_percent") or 0.0),
        )
        if not bool(cfg.viz.skip_video):
            render_iss_videos(
                observations,
                heatmaps,
                video_dir,
                views=views,
                fps=int(cfg.viz.fps),
                alpha=float(cfg.viz.alpha),
                top_k_percent=float(cfg.viz.get("top_k_percent") or 0.0),
            )
        print(f"Saved ISS overlay images: {image_dir}")
        if not bool(cfg.viz.skip_video):
            print(f"Saved ISS overlay videos: {video_dir}")

    print(f"Saved ISS heatmaps: {path}")


if __name__ == "__main__":
    main()
