"""Nuisance Mass Ratio (NMR) from ISS heatmaps and semantic masks."""

from __future__ import annotations

from collections.abc import Mapping

import cv2
import numpy as np

from iss_nmr_toolkit.constants import VIEW_NAMES


def normalize_array(arr: np.ndarray) -> np.ndarray:
    arr = np.nan_to_num(arr.astype(np.float32), nan=0.0, posinf=0.0, neginf=0.0)
    mn = float(arr.min())
    mx = float(arr.max())
    if mx - mn < 1e-8:
        return np.zeros_like(arr, dtype=np.float32)
    return (arr - mn) / (mx - mn)


def normalize_step_heatmaps(step_maps: list[np.ndarray], mode: str) -> list[np.ndarray]:
    if mode == "none":
        return [np.nan_to_num(h.astype(np.float32), nan=0.0, posinf=0.0, neginf=0.0) for h in step_maps]
    if mode == "per_view":
        return [normalize_array(h) for h in step_maps]
    if mode != "joint":
        raise ValueError("normalize must be one of: joint, per_view, none")

    stacked = np.stack(step_maps, axis=0)
    normalized = normalize_array(stacked)
    return [normalized[i] for i in range(normalized.shape[0])]


def resize_mask(mask: np.ndarray, target_hw: tuple[int, int]) -> np.ndarray:
    target_h, target_w = target_hw
    if mask.shape == (target_h, target_w):
        return mask
    return cv2.resize(mask.astype(np.uint8), (target_w, target_h), interpolation=cv2.INTER_NEAREST)


def mask_frame_for_step(mask_seq: np.ndarray, step: int, total_steps: int) -> np.ndarray:
    if len(mask_seq) == total_steps:
        return mask_seq[step]
    if total_steps <= 1:
        return mask_seq[0]
    mask_idx = int(round(step * (len(mask_seq) - 1) / float(total_steps - 1)))
    return mask_seq[mask_idx]


def topk_count(num_pixels: int, k_pixels: int = 0, k_percent: float = 10.0) -> int:
    if k_pixels > 0:
        return min(num_pixels, max(1, int(k_pixels)))
    return min(num_pixels, max(1, int(np.ceil(num_pixels * k_percent / 100.0))))


def compute_nmr(
    heatmaps: Mapping[str, np.ndarray],
    masks: Mapping[str, np.ndarray],
    *,
    views: tuple[str, ...] = VIEW_NAMES,
    k_pixels: int = 0,
    k_percent: float = 10.0,
    normalize: str = "joint",
) -> dict[str, object]:
    """Compute web-page NMR@k from ISS heatmaps and semantic masks.

    This matches ``web_page/final_nmr.py``:
    ``NMR@k = 1 - fraction(ISS top-k pixels inside green+blue masks)``.
    Semantic masks use ``0=background/nuisance`` and ``>0=valid object/robot``.
    Lower NMR is better.
    """
    lengths = [heatmaps[view].shape[0] for view in views]
    if len(set(lengths)) != 1:
        raise ValueError(f"ISS heatmap lengths differ by view: {dict(zip(views, lengths))}")

    total_steps = lengths[0]
    nmr_scores = np.zeros(total_steps, dtype=np.float32)
    coverage_scores = np.zeros(total_steps, dtype=np.float32)
    per_view_nmr = {view: np.zeros(total_steps, dtype=np.float32) for view in views}
    per_view_coverage = {view: np.zeros(total_steps, dtype=np.float32) for view in views}

    for step in range(total_steps):
        step_maps = normalize_step_heatmaps([heatmaps[view][step] for view in views], normalize)
        flat_iss_parts: list[np.ndarray] = []
        flat_valid_parts: list[np.ndarray] = []
        view_slices: dict[str, slice] = {}
        offset = 0

        for view, heatmap in zip(views, step_maps):
            height, width = heatmap.shape
            mask = mask_frame_for_step(np.asarray(masks[view]), step, total_steps)
            mask = resize_mask(mask, (height, width))
            valid = mask > 0

            flat_iss = heatmap.reshape(-1)
            flat_valid = valid.reshape(-1)
            flat_iss_parts.append(flat_iss)
            flat_valid_parts.append(flat_valid)
            view_slices[view] = slice(offset, offset + flat_iss.size)
            offset += flat_iss.size

        flat_iss = np.concatenate(flat_iss_parts, axis=0)
        flat_valid = np.concatenate(flat_valid_parts, axis=0)
        k = topk_count(flat_iss.size, k_pixels=k_pixels, k_percent=k_percent)

        if k >= flat_iss.size:
            top_idx = np.arange(flat_iss.size)
        else:
            top_idx = np.argpartition(flat_iss, -k)[-k:]

        coverage = float(np.mean(flat_valid[top_idx]))
        coverage_scores[step] = coverage
        nmr_scores[step] = 1.0 - coverage

        for view in views:
            view_idx = top_idx[(top_idx >= view_slices[view].start) & (top_idx < view_slices[view].stop)]
            if len(view_idx) == 0:
                per_view_coverage[view][step] = np.nan
                per_view_nmr[view][step] = np.nan
            else:
                view_coverage = float(np.mean(flat_valid[view_idx]))
                per_view_coverage[view][step] = view_coverage
                per_view_nmr[view][step] = 1.0 - view_coverage

    return {
        "scores": nmr_scores,
        "per_view_scores": per_view_nmr,
        "coverage_scores": coverage_scores,
        "per_view_coverage_scores": per_view_coverage,
        "mean_score": float(np.nanmean(nmr_scores)),
        "mean_coverage": float(np.nanmean(coverage_scores)),
        "k_percent": float(k_percent),
        "k_pixels": int(k_pixels),
        "normalize": normalize,
        "definition": "nmr@k = 1 - fraction(ISS top-k pixels inside green+blue mask); lower is better",
    }
