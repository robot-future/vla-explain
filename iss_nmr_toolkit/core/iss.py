"""Interventional Significance Score (ISS).

This module is extracted from ``web_page/final_iss.py`` and keeps the same
algorithmic choices: stitched multi-view RISE masks, Gaussian mixing, action
MSE divergence, fixed-denominator normalization, and temporal interpolation.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any, Dict

import cv2
import numpy as np
from tqdm.auto import tqdm

from iss_nmr_toolkit.constants import DEFAULT_VIEWS


Observation = Dict[str, Any]
Heatmaps = Dict[str, np.ndarray]


def parse_image(image: Any) -> np.ndarray:
    """Convert common tensor/image layouts to uint8 HWC RGB."""
    arr = np.asarray(image)
    if np.issubdtype(arr.dtype, np.floating):
        arr = 255.0 * arr
    if arr.ndim == 3 and arr.shape[0] == 3:
        arr = np.transpose(arr, (1, 2, 0))
    return np.clip(arr, 0, 255).astype(np.uint8)


def run_inference(policy: Any, observations: Sequence[Observation], batch_size: int, desc: str) -> list[dict[str, Any]]:
    """Run ``policy.batch_infer`` on a sequence of observations."""
    if not observations:
        raise ValueError("observations is empty")
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")

    results: list[dict[str, Any]] = []
    num_batches = math.ceil(len(observations) / batch_size)

    batch_iter = tqdm(range(num_batches), desc=desc) if desc else range(num_batches)
    for batch_idx in batch_iter:
        start = batch_idx * batch_size
        end = min((batch_idx + 1) * batch_size, len(observations))
        chunk = list(observations[start:end])
        actual_size = len(chunk)

        if actual_size < batch_size:
            chunk = chunk + [chunk[-1]] * (batch_size - actual_size)

        chunk_results = policy.batch_infer(chunk)
        results.extend(chunk_results[:actual_size])

    return results


def interpolate_heatmaps(
    sparse_heatmaps: Mapping[str, Mapping[int, np.ndarray]],
    total_steps: int,
    computed_indices: Sequence[int],
    height: int,
    width: int,
) -> Heatmaps:
    """Linearly interpolate sparsely computed ISS maps to all time steps."""
    if total_steps <= 0:
        raise ValueError("total_steps must be positive")
    if not computed_indices:
        raise ValueError("computed_indices is empty")

    full_heatmaps: Heatmaps = {}
    sorted_indices = sorted(int(i) for i in computed_indices)

    for view_name, sparse in sparse_heatmaps.items():
        sequence = np.zeros((total_steps, height, width), dtype=np.float32)
        for t in sorted_indices:
            sequence[t] = sparse[t]

        for left, right in zip(sorted_indices[:-1], sorted_indices[1:]):
            gap = right - left
            if gap <= 1:
                continue
            for offset in range(1, gap):
                ratio = offset / float(gap)
                sequence[left + offset] = (1.0 - ratio) * sequence[left] + ratio * sequence[right]

        if sorted_indices[0] > 0:
            sequence[: sorted_indices[0]] = sequence[sorted_indices[0]]
        if sorted_indices[-1] < total_steps - 1:
            sequence[sorted_indices[-1] + 1 :] = sequence[sorted_indices[-1]]

        full_heatmaps[view_name] = sequence

    return full_heatmaps


def _action_mse(pred_actions: np.ndarray, baseline_action: np.ndarray) -> np.ndarray:
    diff = pred_actions - baseline_action
    if diff.ndim == 1:
        return np.square(diff).astype(np.float32)
    axes = tuple(range(1, diff.ndim))
    return np.mean(np.square(diff), axis=axes).astype(np.float32)


def compute_iss(
    policy: Any,
    observations: Sequence[Observation],
    baseline_results: Sequence[Mapping[str, Any]] | None = None,
    *,
    views: Mapping[str, str] = DEFAULT_VIEWS,
    n_masks: int = 500,
    p_keep: float = 0.3,
    grid_size: tuple[int, int] = (7, 7),
    blur_sigma: float = 10.0,
    time_stride: int = 10,
    batch_size: int = 64,
    seed: int = 0,
    show_progress: bool = True,
) -> Heatmaps:
    """Compute ISS heatmaps for one recorded episode.

    Args:
        policy: Object exposing ``batch_infer(list[dict]) -> list[dict]``.
        observations: Recorded episode observations.
        baseline_results: Optional baseline policy outputs. If omitted, they
            are computed from ``observations``.
        views: Mapping from public view name to observation image key.
        n_masks: Number of RISE masks.
        p_keep: Bernoulli keep probability.
        grid_size: Coarse mask grid ``(height, width_per_view)``.
        blur_sigma: Gaussian blur sigma used for masked-out pixels.
        time_stride: Compute ISS every ``time_stride`` frames, then interpolate.
        batch_size: Policy inference batch size.
        seed: Random seed for mask sampling.
        show_progress: Whether to show tqdm progress bars.

    Returns:
        Dict mapping each view name to a ``(T, H, W)`` float32 ISS array.
    """
    if not observations:
        raise ValueError("observations is empty")
    if n_masks <= 0:
        raise ValueError("n_masks must be positive")
    if not (0.0 < p_keep < 1.0):
        raise ValueError("p_keep must be in (0, 1)")
    if grid_size[0] <= 0 or grid_size[1] <= 0:
        raise ValueError("grid_size entries must be positive")
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")

    view_names = list(views.keys())
    view_obs_keys = list(views.values())
    sample_key = view_obs_keys[0]
    sample_image = parse_image(observations[0][sample_key])
    height, width, _ = sample_image.shape
    total_steps = len(observations)
    rng = np.random.RandomState(seed)

    if baseline_results is None:
        baseline_results = run_inference(
            policy,
            observations,
            batch_size=batch_size,
            desc="Baseline inference" if show_progress else "",
        )
    if len(baseline_results) != total_steps:
        raise ValueError("baseline_results length must match observations length")

    stitched_grid_w = grid_size[1] * len(view_names)
    stitched_img_w = width * len(view_names)
    raw_masks = (rng.rand(n_masks, grid_size[0], stitched_grid_w) < p_keep).astype(np.float32)
    stitched_masks = np.empty((n_masks, height, stitched_img_w, 1), dtype=np.float32)
    for mask_idx in range(n_masks):
        stitched_masks[mask_idx, :, :, 0] = cv2.resize(
            raw_masks[mask_idx],
            (stitched_img_w, height),
            interpolation=cv2.INTER_LINEAR,
        )

    keep_masks: dict[str, np.ndarray] = {}
    drop_masks: dict[str, np.ndarray] = {}
    for view_idx, view_name in enumerate(view_names):
        start_w = view_idx * width
        end_w = (view_idx + 1) * width
        keep_masks[view_name] = stitched_masks[:, :, start_w:end_w, :]
        drop_masks[view_name] = 1.0 - keep_masks[view_name]

    computed_steps = list(range(0, total_steps, max(1, int(time_stride))))
    if total_steps - 1 not in computed_steps:
        computed_steps.append(total_steps - 1)

    sparse_heatmaps: dict[str, dict[int, np.ndarray]] = {view_name: {} for view_name in view_names}
    ksize = int(2 * round(3 * blur_sigma) + 1)
    step_iter = tqdm(computed_steps, desc="Computing ISS") if show_progress else computed_steps

    for step in step_iter:
        obs = observations[step]
        baseline_action = np.asarray(baseline_results[step]["actions"])
        static_context = {k: v for k, v in obs.items() if k not in view_obs_keys}

        original_images: dict[str, np.ndarray] = {}
        blurred_images: dict[str, np.ndarray] = {}
        for view_name, obs_key in views.items():
            img = parse_image(obs[obs_key]).astype(np.float32)
            original_images[view_name] = img
            blurred_images[view_name] = cv2.GaussianBlur(img, (ksize, ksize), blur_sigma)

        sparse_accum = {view_name: np.zeros((height, width), dtype=np.float32) for view_name in view_names}
        num_chunks = math.ceil(n_masks / batch_size)

        for chunk_idx in range(num_chunks):
            start = chunk_idx * batch_size
            end = min((chunk_idx + 1) * batch_size, n_masks)
            chunk_size = end - start
            batch_inputs: list[Observation] = []

            for mask_idx in range(start, end):
                item = static_context.copy()
                for view_name, obs_key in views.items():
                    keep = keep_masks[view_name][mask_idx]
                    original = original_images[view_name]
                    blurred = blurred_images[view_name]
                    masked = original * keep + blurred * (1.0 - keep)
                    item[obs_key] = np.clip(masked, 0, 255).astype(np.uint8)
                batch_inputs.append(item)

            if chunk_size < batch_size:
                batch_inputs = batch_inputs + [batch_inputs[-1]] * (batch_size - chunk_size)

            batch_results = policy.batch_infer(batch_inputs)[:chunk_size]
            pred_actions = np.stack([np.asarray(r["actions"]) for r in batch_results], axis=0)
            divergence = _action_mse(pred_actions, baseline_action)

            for view_name in view_names:
                dropped = drop_masks[view_name][start:end]
                weighted = divergence[:, None, None, None] * dropped
                sparse_accum[view_name] += np.sum(weighted, axis=0).squeeze()

        for view_name in view_names:
            sparse_heatmaps[view_name][step] = sparse_accum[view_name] / (n_masks * (1.0 - p_keep))

    return interpolate_heatmaps(sparse_heatmaps, total_steps, computed_steps, height, width)
