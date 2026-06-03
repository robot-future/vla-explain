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
