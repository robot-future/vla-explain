"""Pi05 policy adapter.

OpenPI is imported lazily so that the rest of the toolkit remains importable
without model dependencies.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any


def _quiet_openpi_logs() -> None:
    os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
    os.environ.setdefault("JAX_PLATFORMS", "cuda")
    os.environ.setdefault("ABSL_MIN_LOG_LEVEL", "2")

    for name in ("absl", "jax", "jax._src.xla_bridge", "orbax", "datasets"):
        logging.getLogger(name).setLevel(logging.WARNING)


def _validate_checkpoint_dir(checkpoint_dir: str) -> Path:
    path = Path(checkpoint_dir).expanduser().resolve()
    params_dir = path / "params"
    metadata_file = params_dir / "_METADATA"
    assets_dir = path / "assets"

    if metadata_file.exists() and assets_dir.exists():
        return path

    nested = sorted(path.glob("**/params/_METADATA"))
    nested_hint = ""
    if nested:
        candidates = [str(metadata.parent.parent) for metadata in nested[:3]]
        nested_hint = "\nFound a nested complete checkpoint candidate:\n  " + "\n  ".join(candidates)

    raise FileNotFoundError(
        "Incomplete Pi05 X-ICM checkpoint.\n"
        f"Expected checkpoint root: {path}\n"
        f"Missing required Orbax metadata: {metadata_file}\n"
        f"Expected assets directory: {assets_dir}\n"
        "Download a complete checkpoint with:\n"
        "  rm -rf checkpoints/pi05_xicm\n"
        "  hf download HanxinZhang/pi05-xicm --local-dir checkpoints/pi05_xicm --force-download\n"
        "Then verify:\n"
        "  test -f checkpoints/pi05_xicm/params/_METADATA && echo \"orbax metadata ok\"\n"
        "  test -d checkpoints/pi05_xicm/assets && echo \"assets ok\""
        f"{nested_hint}"
    )


class Pi05PolicyAdapter:
    """Minimal adapter exposing ``batch_infer`` for the ISS core."""

    def __init__(
        self,
        checkpoint_dir: str,
        *,
        config_name: str = "pi05_xicm",
        cuda_visible_devices: str | None = None,
    ) -> None:
        if cuda_visible_devices is not None:
            os.environ["CUDA_VISIBLE_DEVICES"] = cuda_visible_devices
        _quiet_openpi_logs()

        try:
            from openpi.policies import policy_config
            from openpi.training import config as _config

            try:
                from absl import logging as absl_logging

                absl_logging.set_verbosity(absl_logging.WARNING)
            except Exception:
                pass
        except ModuleNotFoundError as exc:
            if exc.name == "openpi":
                raise ModuleNotFoundError(
                    "OpenPI is not installed in this environment. Run `bash install.sh` "
                    "from the repository root on the Linux/CUDA inference machine, then activate "
                    "`.venv_iss_nmr` before running this script."
                ) from exc
            raise

        checkpoint_path = _validate_checkpoint_dir(checkpoint_dir)
        config = _config.get_config(config_name)
        self.policy = policy_config.create_trained_policy(config, checkpoint_path)
        self._warned_no_batch = False

    def batch_infer(self, observations: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if hasattr(self.policy, "batch_infer"):
            return self.policy.batch_infer(observations)
        if not hasattr(self.policy, "infer"):
            raise AttributeError("OpenPI policy exposes neither batch_infer nor infer.")
        if not self._warned_no_batch:
            print("Warning: OpenPI policy has no batch_infer; falling back to sequential infer.")
            self._warned_no_batch = True
        return [self.policy.infer(obs) for obs in observations]
