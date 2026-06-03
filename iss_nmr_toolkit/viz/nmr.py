"""NMR plotting utilities."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from iss_nmr_toolkit.constants import VIEW_NAMES


def plot_nmr(
    path: str | Path,
    nmr_payload: dict[str, object],
    *,
    views: tuple[str, ...] = VIEW_NAMES,
    title: str = "NMR@k",
    ylabel: str = "NMR@k",
) -> Path:
    """Plot trajectory-level and per-view NMR curves.

    Matplotlib is imported lazily so that plotting remains optional.
    """
    import matplotlib.pyplot as plt

    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)

    scores = np.asarray(nmr_payload["scores"], dtype=np.float32)
    per_view = nmr_payload["per_view_scores"]
    x = np.arange(len(scores))

    plt.figure(figsize=(10, 4.8))
    plt.plot(x, scores, color="#111111", linewidth=2.4, label="all views")
    for view, color in zip(views, ("#2f80ed", "#27ae60", "#f2994a")):
        plt.plot(x, per_view[view], color=color, linewidth=1.2, alpha=0.55, label=view)

    mean_score = float(np.nanmean(scores))
    plt.axhline(mean_score, color="#d62728", linestyle="--", linewidth=1.4, label=f"mean={mean_score:.4f}")
    plt.ylim(-0.02, 1.02)
    plt.xlabel("Step")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(alpha=0.25)
    plt.legend(loc="best")
    plt.tight_layout()
    plt.savefig(output, dpi=180)
    plt.close()
    return output
