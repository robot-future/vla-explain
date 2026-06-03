"""Prepared X-ICM episode and semantic-mask loaders."""

from __future__ import annotations

import glob
import os
import re
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from tqdm.auto import tqdm

from iss_nmr_toolkit.constants import DEFAULT_VIEWS, VIEW_NAMES
from iss_nmr_toolkit.core.iss import parse_image


IMAGE_EXTENSIONS = ("*.png", "*.jpg", "*.jpeg", "*.bmp")


def natural_key(text: str) -> list[Any]:
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", text)]


def _find_frame_dir(episode_dir: Path, view: str, obs_key: str) -> Path | None:
    candidates = [
        episode_dir / view,
        episode_dir / f"{view}_rgb",
        episode_dir / obs_key,
        episode_dir / "images" / view,
        episode_dir / "images" / f"{view}_rgb",
        episode_dir / "rgb" / view,
    ]
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    return None


def _read_rgb(path: str | Path) -> np.ndarray:
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise FileNotFoundError(f"Could not read image: {path}")
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)


def _list_images(frame_dir: Path) -> list[str]:
    paths: list[str] = []
    for pattern in IMAGE_EXTENSIONS:
        paths.extend(glob.glob(str(frame_dir / pattern)))
    paths = [path for path in paths if not Path(path).name.startswith(".")]
    return sorted(paths, key=natural_key)


def _load_state_npz(episode_dir: Path) -> dict[str, Any]:
    for name in ("states.npz", "observations.npz", "episode.npz"):
        path = episode_dir / name
        if path.exists():
            data = np.load(path, allow_pickle=True)
            return {key: data[key] for key in data.files}
    return {}


def load_episode_directory(
    episode_dir: str | os.PathLike[str],
    *,
    views: dict[str, str] = DEFAULT_VIEWS,
    prompt: str | None = None,
    require_state: bool = False,
) -> list[dict[str, Any]]:
    """Load an exported episode directory into policy observations.

    Expected RGB layout can be any of:
    ``front/*.png``, ``front_rgb/*.png``, ``images/front/*.png``, or a folder
    named by the policy observation key such as ``exterior_image_1_left``.
    ``states.npz`` should contain ``joint_position`` and ``gripper_position``.
    ``prompt`` may also be stored there. Pi05 X-ICM uses state through the
    tokenized prompt transform, so set ``require_state=True`` for policy runs
    that should match the web-page ISS computation.
    """
    root = Path(episode_dir)
    if not root.is_dir():
        raise FileNotFoundError(f"Episode directory not found: {root}")

    frame_paths: dict[str, list[str]] = {}
    for view, obs_key in views.items():
        frame_dir = _find_frame_dir(root, view, obs_key)
        if frame_dir is None:
            raise FileNotFoundError(f"Missing RGB frame directory for view '{view}' under {root}")
        paths = _list_images(frame_dir)
        if not paths:
            raise FileNotFoundError(f"No RGB frames found in {frame_dir}")
        frame_paths[view] = paths

    lengths = {view: len(paths) for view, paths in frame_paths.items()}
    total_steps = min(lengths.values())
    if len(set(lengths.values())) != 1:
        print(f"Warning: view frame counts differ; truncating to {total_steps}: {lengths}")

    state = _load_state_npz(root)
    joint_positions = state.get("joint_position")
    gripper_positions = state.get("gripper_position")
    state_prompt = state.get("prompt")
    if require_state and (joint_positions is None or gripper_positions is None):
        raise FileNotFoundError(
            "Missing states.npz with joint_position and gripper_position. "
            "Pi05 X-ICM tokenizes state into the prompt, and the prepared X-ICM "
            "episode state must be aligned with every frame."
        )
    if prompt is None and state_prompt is not None:
        prompt = str(state_prompt.item() if hasattr(state_prompt, "item") else state_prompt)
    if prompt is None:
        prompt = root.parent.name.replace("_", " ")

    observations: list[dict[str, Any]] = []
    for step in tqdm(range(total_steps), desc="Loading episode frames"):
        obs: dict[str, Any] = {}
        for view, obs_key in views.items():
            obs[obs_key] = _read_rgb(frame_paths[view][step])

        if joint_positions is not None and step < len(joint_positions):
            obs["joint_position"] = np.asarray(joint_positions[step])
        else:
            obs["joint_position"] = np.zeros(7, dtype=np.float32)

        if gripper_positions is not None and step < len(gripper_positions):
            gripper = np.asarray(gripper_positions[step])
        else:
            gripper = np.zeros(1, dtype=np.float32)
        if gripper.ndim == 0:
            gripper = gripper[..., np.newaxis]
        obs["gripper_position"] = gripper
        obs["prompt"] = prompt
        observations.append(obs)

    return observations

def load_masks(
    mask_dir_or_episode_dir: str | os.PathLike[str],
    *,
    views: tuple[str, ...] = VIEW_NAMES,
) -> dict[str, np.ndarray]:
    """Load ``mask_{view}_rgb.npy`` files.

    Accepts either the mask directory itself or an episode directory containing
    a ``masks/`` subdirectory.
    """
    root = Path(mask_dir_or_episode_dir)
    candidates = [root, root / "masks"]
    mask_dir = next((path for path in candidates if (path / f"mask_{views[0]}_rgb.npy").exists()), None)
    if mask_dir is None:
        raise FileNotFoundError(f"Could not find mask files under {root}")

    masks: dict[str, np.ndarray] = {}
    for view in views:
        path = mask_dir / f"mask_{view}_rgb.npy"
        if not path.exists():
            raise FileNotFoundError(f"Missing mask file: {path}")
        masks[view] = np.load(path)
    return masks
