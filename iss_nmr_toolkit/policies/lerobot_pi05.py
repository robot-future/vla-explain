"""Adapter from a LeRobot pi0/pi0.5 checkpoint to the ISS batch API."""

from __future__ import annotations

import inspect
import random
from pathlib import Path
from typing import Any

import numpy as np
import torch


def _image_to_chw_float(image: Any) -> np.ndarray:
    if hasattr(image, "detach"):
        image = image.detach().cpu().numpy()
    array = np.asarray(image)
    if array.ndim != 3:
        raise ValueError(f"Expected a 3-D image, got {array.shape}")
    if array.shape[-1] in (1, 3, 4):
        array = np.moveaxis(array, -1, 0)
    if array.dtype == np.uint8:
        array = array.astype(np.float32) / 255.0
    else:
        array = array.astype(np.float32, copy=False)
        if array.size and float(array.max()) > 1.5:
            array = array / 255.0
    return np.ascontiguousarray(array)


class LeRobotPi05PolicyAdapter:
    """Expose deterministic ``batch_infer`` for a LeRobot pi0/pi0.5 policy.

    ISS compares full action chunks. A fixed flow-matching noise tensor is
    repeated for every item, ensuring that baseline/masked action differences
    come from the visual intervention rather than stochastic action sampling.
    """

    def __init__(
        self,
        checkpoint_dir: str,
        *,
        device: str = "cuda",
        use_half: bool = False,
        seed: int = 0,
        deterministic: bool = True,
    ) -> None:
        from lerobot.configs.policies import PreTrainedConfig
        from lerobot.policies.factory import get_policy_class, make_pre_post_processors

        self.checkpoint_dir = Path(checkpoint_dir).expanduser().resolve()
        if not self.checkpoint_dir.exists():
            raise FileNotFoundError(f"Policy checkpoint not found: {self.checkpoint_dir}")
        if device.startswith("cuda") and not torch.cuda.is_available():
            raise RuntimeError("CUDA was requested but torch.cuda.is_available() is false.")

        self.device = torch.device(device)
        self.use_half = bool(use_half)
        self.seed = int(seed)
        self.deterministic = bool(deterministic)
        self._set_determinism()

        config = PreTrainedConfig.from_pretrained(str(self.checkpoint_dir))
        config.device = str(self.device)
        config.pretrained_path = str(self.checkpoint_dir)
        policy_cls = get_policy_class(config.type)
        self.policy = policy_cls.from_pretrained(
            pretrained_name_or_path=str(self.checkpoint_dir), config=config
        ).to(self.device)
        self.policy.eval()
        if self.use_half:
            self.policy = self.policy.half()

        self.preprocessor, self.postprocessor = make_pre_post_processors(
            policy_cfg=config,
            pretrained_path=str(self.checkpoint_dir),
            preprocessor_overrides={"device_processor": {"device": str(self.device)}},
            postprocessor_overrides={"device_processor": {"device": str(self.device)}},
        )
        self.image_keys = tuple(getattr(config, "image_features", ()))
        self.state_key = "observation.state"

        if not hasattr(self.policy, "predict_action_chunk"):
            raise AttributeError(
                "This LeRobot policy has no predict_action_chunk(); ISS must bypass "
                "the rollout action queue to compare complete action chunks."
            )

    def _set_determinism(self) -> None:
        random.seed(self.seed)
        np.random.seed(self.seed)
        torch.manual_seed(self.seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(self.seed)
        if self.deterministic:
            torch.use_deterministic_algorithms(True)
            if hasattr(torch.backends, "cudnn"):
                torch.backends.cudnn.benchmark = False
                torch.backends.cudnn.deterministic = True
                torch.backends.cudnn.allow_tf32 = False
            if hasattr(torch.backends, "cuda") and hasattr(torch.backends.cuda, "matmul"):
                torch.backends.cuda.matmul.allow_tf32 = False

    def _fixed_noise(self, batch_size: int, batch: dict[str, Any]) -> torch.Tensor:
        config = self.policy.config
        chunk_size = int(config.chunk_size)
        max_action_dim = int(config.max_action_dim)
        generator = torch.Generator(device=self.device)
        generator.manual_seed(self.seed)
        single = torch.randn(
            (1, chunk_size, max_action_dim),
            generator=generator,
            device=self.device,
            dtype=torch.float32,
        )
        return single.repeat(batch_size, 1, 1)

    def _make_batch(self, observations: list[dict[str, Any]]) -> dict[str, Any]:
        if not observations:
            raise ValueError("observations is empty")
        batch: dict[str, Any] = {}
        for key in self.image_keys:
            try:
                values = [_image_to_chw_float(obs[key]) for obs in observations]
            except KeyError as exc:
                raise KeyError(
                    f"Policy expects image key {key!r}, but it is absent from the ISS observation."
                ) from exc
            tensor = torch.from_numpy(np.stack(values)).to(self.device)
            if self.use_half:
                tensor = tensor.half()
            batch[key] = tensor

        states = np.stack(
            [np.asarray(obs[self.state_key], dtype=np.float32) for obs in observations]
        )
        state_tensor = torch.from_numpy(states).to(self.device)
        if self.use_half:
            state_tensor = state_tensor.half()
        batch[self.state_key] = state_tensor
        batch["task"] = [str(obs.get("task", "")) for obs in observations]
        return self.preprocessor(batch)

    def batch_infer(self, observations: list[dict[str, Any]]) -> list[dict[str, Any]]:
        batch = self._make_batch(observations)
        noise = self._fixed_noise(len(observations), batch)

        # Current LeRobot forwards extra kwargs from predict_action_chunk to
        # model.sample_actions(noise=...). Check explicitly so older versions
        # fail rather than silently producing stochastic, invalid ISS values.
        signature = inspect.signature(self.policy.model.sample_actions)
        if "noise" not in signature.parameters:
            raise RuntimeError(
                "Installed LeRobot does not expose sample_actions(noise=...). "
                "Upgrade LeRobot or use a compatible pi0/pi0.5 implementation."
            )

        with torch.inference_mode():
            actions = self.policy.predict_action_chunk(batch, noise=noise)
            actions = self.postprocessor(actions)

        if isinstance(actions, dict):
            actions = actions.get("action", actions.get("actions"))
        if actions is None:
            raise RuntimeError("Policy postprocessor did not return actions.")
        if isinstance(actions, torch.Tensor):
            actions = actions.detach().float().cpu().numpy()
        else:
            actions = np.asarray(actions)
        if actions.shape[0] != len(observations):
            raise RuntimeError(
                f"Policy returned batch size {actions.shape[0]}, expected {len(observations)}."
            )
        return [{"actions": actions[index]} for index in range(len(observations))]
