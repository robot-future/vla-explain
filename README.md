# Embodied Interpretability: Linking Causal Understanding to Generalization in Vision-Language-Action Models

Code for running ISS and NMR@k.

## Prepare

```bash
bash install.sh
source .venv_iss_nmr/bin/activate

hf download HanxinZhang/pi05-xicm \
  --local-dir checkpoints/pi05_xicm

unzip -q data/xicm_demo.zip -d data
```

## Run

```bash
CUDA_VISIBLE_DEVICES=0 python gen_iss_heatmap.py \
  data.root=data/xicm_demo \
  data.task=close_jar \
  data.episode=episode0 \
  policy.checkpoint_dir=checkpoints/pi05_xicm

python compute_nmr_k.py \
  data.root=data/xicm_demo \
  data.task=close_jar \
  data.episode=episode0

python vis_iss_nmr_k.py \
  data.root=data/xicm_demo \
  data.task=close_jar \
  data.episode=episode0
```

Default config:

```text
configs/xicm_episode.yaml
```

Outputs:

```text
outputs/${data.task}/${data.episode}
```

## Direct LeRobot XArm dataset ISS

`gen_iss_heatmap.py` can also read one episode directly from a LeRobot v3
dataset and run the LeRobot PyTorch pi0/pi0.5 checkpoint used by the XArm
deployment code. No PNG export or `states.npz` conversion is needed.

The prepared configuration is:

```text
configs/lerobot_xarm_episode.yaml
```

It maps the three views as follows:

```text
chest       -> observation.images.cam_chest
wrist_left  -> observation.images.cam_wrist_left
wrist_right -> observation.images.cam_wrist_right
state       -> observation.state
```

Run a quick pipeline check (`N=20` from the config):

```bash
cd vla-explain
source .venv_iss_nmr/bin/activate

CUDA_VISIBLE_DEVICES=0 python gen_iss_heatmap.py \
  --config-name lerobot_xarm_episode \
  policy.checkpoint_dir=/absolute/path/to/your/lerobot_pi05_checkpoint \
  data.episode_index=0
```

Run the paper setting after the quick check succeeds:

```bash
CUDA_VISIBLE_DEVICES=0 python gen_iss_heatmap.py \
  --config-name lerobot_xarm_episode \
  policy.checkpoint_dir=/absolute/path/to/your/lerobot_pi05_checkpoint \
  data.episode_index=0 \
  iss.n_masks=100
```

The direct runner writes the raw ISS arrays and immediately renders overlay
images/videos:

```text
outputs/bag1_pickup/episode_0/iss/iss_heatmaps.npz
outputs/bag1_pickup/episode_0/iss_images/*.png
outputs/bag1_pickup/episode_0/iss_videos/*.mp4
```

The Windows dataset path is already set to:

```text
C:\Users\26220\Desktop\Reconova\bag1_pickup_am629_cleaned
```

When running from WSL/Linux, override it with the mounted path, for example:

```bash
data.root=/mnt/c/Users/26220/Desktop/Reconova/bag1_pickup_am629_cleaned
```

Use the checkpoint actually trained on this dataset. The paper's
`HanxinZhang/pi05-xicm` checkpoint expects a different single-arm state/action
space and different camera semantics, so its ISS output is not a valid
explanation of the dual-arm XArm policy.
