"""ISS heatmap rendering utilities."""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
from typing import Any

import cv2
import numpy as np
from tqdm.auto import tqdm

from iss_nmr_toolkit.constants import DEFAULT_VIEWS


def normalize_heatmaps_joint(frame_heatmaps: list[np.ndarray]) -> np.ndarray:
    stacked = np.stack(
        [np.nan_to_num(h.astype(np.float32), nan=0.0, posinf=0.0, neginf=0.0) for h in frame_heatmaps],
        axis=0,
    )
    h_min = float(stacked.min())
    h_max = float(stacked.max())
    if h_max - h_min < 1e-8:
        return np.zeros_like(stacked, dtype=np.float32)
    return (stacked - h_min) / (h_max - h_min)


def emphasize_joint_topk(joint_heatmaps: np.ndarray, top_k_percent: float, background_ceiling: float = 0.35) -> np.ndarray:
    if top_k_percent <= 0:
        return joint_heatmaps

    flat = joint_heatmaps.reshape(-1)
    k_count = max(1, int(np.ceil(flat.size * top_k_percent / 100.0)))
    threshold = np.partition(flat, -k_count)[-k_count]
    if threshold <= 1e-8:
        return joint_heatmaps

    emphasized = np.empty_like(joint_heatmaps, dtype=np.float32)
    below = joint_heatmaps < threshold
    above = ~below
    emphasized[below] = background_ceiling * (joint_heatmaps[below] / threshold)
    if threshold >= 1.0 - 1e-8:
        emphasized[above] = 1.0
    else:
        emphasized[above] = background_ceiling + (1.0 - background_ceiling) * (
            (joint_heatmaps[above] - threshold) / (1.0 - threshold)
        )
    return np.clip(emphasized, 0.0, 1.0)


def overlay_heatmap(image: np.ndarray, heatmap: np.ndarray, alpha: float) -> np.ndarray:
    heatmap = np.clip(heatmap.astype(np.float32), 0.0, 1.0)
    color = cv2.applyColorMap(np.uint8(heatmap * 255), cv2.COLORMAP_JET)
    color = cv2.cvtColor(color, cv2.COLOR_BGR2RGB)
    if color.shape[:2] != image.shape[:2]:
        color = cv2.resize(color, (image.shape[1], image.shape[0]), interpolation=cv2.INTER_LINEAR)
    return cv2.addWeighted(image, 1.0 - alpha, color, alpha, 0)


def _open_writer(path: Path, frame_shape: tuple[int, ...], fps: int) -> cv2.VideoWriter:
    path.parent.mkdir(parents=True, exist_ok=True)
    height, width = frame_shape[:2]
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))
    if not writer.isOpened():
        raise RuntimeError(f"Failed to open video writer: {path}")
    return writer


def _transcode_h264(input_path: Path, output_path: Path) -> None:
    """Write a VS Code/browser-friendly H.264 MP4 when ffmpeg is available."""
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        if input_path != output_path:
            shutil.move(str(input_path), str(output_path))
        print("Warning: ffmpeg not found; ISS videos were saved with OpenCV mp4v.")
        return

    cmd = [
        ffmpeg,
        "-y",
        "-loglevel",
        "error",
        "-i",
        str(input_path),
        "-an",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(output_path),
    ]
    try:
        subprocess.run(cmd, check=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        if input_path != output_path:
            shutil.move(str(input_path), str(output_path))
        print(f"Warning: ffmpeg H.264 transcode failed ({exc}); saved OpenCV mp4v video instead.")
    else:
        if input_path != output_path and input_path.exists():
            input_path.unlink()


def render_iss_videos(
    observations: list[dict[str, Any]],
    heatmaps: dict[str, np.ndarray],
    output_dir: str | Path,
    *,
    views: dict[str, str] = DEFAULT_VIEWS,
    fps: int = 15,
    alpha: float = 0.6,
    top_k_percent: float = 0.0,
) -> None:
    output = Path(output_dir)
    writers: dict[str, cv2.VideoWriter] = {}
    raw_paths: dict[str, Path] = {}
    final_paths: dict[str, Path] = {}
    view_names = list(views.keys())

    for view_name, obs_key in views.items():
        final_path = output / f"{view_name}_iss.mp4"
        raw_path = output / f".{view_name}_iss.opencv.mp4"
        final_paths[view_name] = final_path
        raw_paths[view_name] = raw_path
        writers[view_name] = _open_writer(raw_path, observations[0][obs_key].shape, fps)

    try:
        for step, obs in enumerate(tqdm(observations, desc="Rendering ISS videos")):
            joint_heatmaps = normalize_heatmaps_joint([heatmaps[view_name][step] for view_name in view_names])
            joint_heatmaps = emphasize_joint_topk(joint_heatmaps, top_k_percent)

            for view_idx, (view_name, obs_key) in enumerate(views.items()):
                frame = overlay_heatmap(obs[obs_key], joint_heatmaps[view_idx], alpha)
                writers[view_name].write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
    finally:
        for writer in writers.values():
            writer.release()

    for view_name in view_names:
        _transcode_h264(raw_paths[view_name], final_paths[view_name])


def save_iss_snapshots(
    observations: list[dict[str, Any]],
    heatmaps: dict[str, np.ndarray],
    output_dir: str | Path,
    *,
    views: dict[str, str] = DEFAULT_VIEWS,
    steps: list[int] | None = None,
    alpha: float = 0.6,
    top_k_percent: float = 0.0,
) -> list[Path]:
    """Save representative ISS overlay images for each view."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    total_steps = len(observations)
    if steps is None:
        if total_steps <= 5:
            steps = list(range(total_steps))
        else:
            steps = sorted(set(int(round(x)) for x in np.linspace(0, total_steps - 1, 5)))
    steps = [step for step in steps if 0 <= step < total_steps]

    saved: list[Path] = []
    view_names = list(views.keys())
    for step in tqdm(steps, desc="Saving ISS snapshots"):
        joint_heatmaps = normalize_heatmaps_joint([heatmaps[view_name][step] for view_name in view_names])
        joint_heatmaps = emphasize_joint_topk(joint_heatmaps, top_k_percent)

        for view_idx, (view_name, obs_key) in enumerate(views.items()):
            frame = overlay_heatmap(observations[step][obs_key], joint_heatmaps[view_idx], alpha)
            path = output / f"step{step:04d}_{view_name}_iss.png"
            cv2.imwrite(str(path), cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
            saved.append(path)

    return saved
