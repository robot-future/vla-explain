#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

VENV_DIR="${VENV_DIR:-.venv_iss_nmr}"
VENV_FALLBACK_DIR="${VENV_FALLBACK_DIR:-$HOME/.venvs/vla-explain-iss-nmr}"
PYTHON_VERSION="${PYTHON_VERSION:-3.11}"
RECREATE="${RECREATE:-0}"
if [[ -z "${INSTALL_OPENPI+x}" ]]; then
  if [[ "$(uname -s)" == "Darwin" ]]; then
    INSTALL_OPENPI=0
  else
    INSTALL_OPENPI=1
  fi
fi
SKIP_GIT_LFS_SMUDGE="${SKIP_GIT_LFS_SMUDGE:-1}"
OPENPI_REPO="${OPENPI_REPO:-https://github.com/Hanxin-Zhang/openp_xicm.git}"
OPENPI_REF="${OPENPI_REF:-55ac37700a523b5bbc9a3c1b45ab3afbe71c85bc}"
OPENPI_DIR="${OPENPI_DIR:-.deps/openpi}"

archive_invalid_venv() {
  local target="$1"
  if [[ ! -e "$target" ]]; then
    return 0
  fi
  local stale_dir="${target}_stale_$(date +%s)"
  echo "Warning: $target exists but does not look like a valid virtual environment."
  echo "Moving it to $stale_dir"
  if ! mv "$target" "$stale_dir"; then
    echo "Warning: failed to move $target; trying to remove it."
    rm -rf "$target" || true
  fi
}

create_venv() {
  local target="$1"
  if uv venv --python "$PYTHON_VERSION" "$target"; then
    return 0
  fi

  echo "Warning: uv venv failed for $target; trying python -m venv --copies."
  local python_bin
  python_bin="$(uv python find "$PYTHON_VERSION" 2>/dev/null || true)"
  if [[ -z "$python_bin" ]]; then
    python_bin="$(command -v python3 || true)"
  fi
  if [[ -z "$python_bin" ]]; then
    return 1
  fi
  "$python_bin" -m venv --copies "$target"
}

ensure_venv() {
  if [[ -x "$VENV_DIR/bin/python" ]] && ! "$VENV_DIR/bin/python" -c "import sys" >/dev/null 2>&1; then
    archive_invalid_venv "$VENV_DIR"
  fi

  if [[ ! -x "$VENV_DIR/bin/python" ]]; then
    archive_invalid_venv "$VENV_DIR"
    if create_venv "$VENV_DIR"; then
      return 0
    fi

    if [[ "$VENV_DIR" != "$VENV_FALLBACK_DIR" ]]; then
      echo "Warning: could not create a virtual environment under this repository."
      echo "Falling back to: $VENV_FALLBACK_DIR"
      VENV_DIR="$VENV_FALLBACK_DIR"
      if [[ -x "$VENV_DIR/bin/python" ]] && "$VENV_DIR/bin/python" -c "import sys" >/dev/null 2>&1; then
        return 0
      fi
      archive_invalid_venv "$VENV_DIR"
      create_venv "$VENV_DIR"
      return
    fi
    return 1
  fi
}

if ! command -v uv >/dev/null 2>&1; then
  echo "Error: uv is required. Install it first: https://docs.astral.sh/uv/"
  exit 1
fi

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "Warning: ffmpeg was not found. ISS videos will fall back to OpenCV mp4v,"
  echo "which may not preview correctly in VS Code. Install ffmpeg for H.264 MP4 output."
fi

if [[ -e "$VENV_DIR" && "$RECREATE" == "1" ]]; then
  if ! rm -rf "$VENV_DIR"; then
    STALE_DIR="${VENV_DIR}_stale_$(date +%s)"
    echo "Warning: failed to remove $VENV_DIR; moving it to $STALE_DIR"
    mv "$VENV_DIR" "$STALE_DIR"
  fi
fi

ensure_venv

uv pip install --python "$VENV_DIR/bin/python" -e .

if [[ "$INSTALL_OPENPI" == "1" ]]; then
  if [[ "$(uname -s)" == "Darwin" ]]; then
    echo "Error: OpenPI inference dependencies are configured for Linux/CUDA."
    echo "Run this install on the Linux GPU machine used for Pi05 inference."
    echo "For toolkit-only checks on macOS, run: INSTALL_OPENPI=0 bash install.sh"
    exit 1
  fi
  if ! command -v git >/dev/null 2>&1; then
    echo "Error: git is required to download the X-ICM OpenPI fork."
    exit 1
  fi
  if [[ "$SKIP_GIT_LFS_SMUDGE" == "1" ]]; then
    echo "Skipping Git LFS smudge during OpenPI dependency install."
    echo "This avoids downloading unused LeRobot test artifacts."
    uv cache clean lerobot >/dev/null 2>&1 || true
    export GIT_LFS_SKIP_SMUDGE=1
  fi

  if [[ ! -d "$OPENPI_DIR/.git" ]]; then
    rm -rf "$OPENPI_DIR"
    mkdir -p "$(dirname "$OPENPI_DIR")"
    git init "$OPENPI_DIR"
    git -C "$OPENPI_DIR" remote add origin "$OPENPI_REPO"
  fi
  git -C "$OPENPI_DIR" fetch --depth 1 origin "$OPENPI_REF"
  git -C "$OPENPI_DIR" checkout --detach "$OPENPI_REF"

  uv pip install --python "$VENV_DIR/bin/python" -e "$OPENPI_DIR/packages/openpi-client"
  uv pip install --python "$VENV_DIR/bin/python" -e "$OPENPI_DIR"
  uv pip install --python "$VENV_DIR/bin/python" \
    "jax[cuda12]==0.5.3" \
    "jaxlib==0.5.3" \
    "flax==0.10.2" \
    "orbax-checkpoint==0.11.13" \
    "chex==0.1.89" \
    "optax==0.2.4" \
    "pytest==8.3.5" \
    "safetensors==0.5.3" \
    "pydantic==2.11.5" \
    "pynvml==12.0.0" \
    "gcsfs==2025.3.0"
  CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}" "$VENV_DIR/bin/python" - <<'PY'
import jax
import jaxlib
from openpi.policies import policy_config
from openpi.training import config as openpi_config

openpi_config.get_config("pi05_xicm")
print(f"JAX {jax.__version__}, jaxlib {jaxlib.__version__}")
print("OpenPI Pi05 import check passed.")
PY
fi

cat <<EOF

Environment ready: $VENV_DIR

Activate it with:
  source $VENV_DIR/bin/activate

Download the Pi05 X-ICM checkpoint:
  hf download HanxinZhang/pi05-xicm --local-dir checkpoints/pi05_xicm

Check the checkpoint:
  test -f checkpoints/pi05_xicm/params/_METADATA && echo "orbax metadata ok"
  test -d checkpoints/pi05_xicm/assets && echo "assets ok"

Run one prepared X-ICM episode in three steps:
  python gen_iss_heatmap.py data.root=data/xicm_demo data.task=close_jar data.episode=episode0 policy.checkpoint_dir=checkpoints/pi05_xicm
  python compute_nmr_k.py data.root=data/xicm_demo data.task=close_jar data.episode=episode0
  python vis_iss_nmr_k.py data.root=data/xicm_demo data.task=close_jar data.episode=episode0

If you only want the lightweight toolkit without OpenPI:
  INSTALL_OPENPI=0 bash install.sh

EOF
