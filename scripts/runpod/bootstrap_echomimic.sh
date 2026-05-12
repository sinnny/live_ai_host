#!/usr/bin/env bash
# RunPod bootstrap — sets up EchoMimic v3 (Flash + Preview weights) for Stage 4 Tests 1-3.
#
# Run once per pod session after `git clone`-ing this repo.
# Idempotent: safe to re-run if interrupted (clones are conditional, hf/modelscope resume).
#
# Assumes pod template: generic PyTorch with CUDA (e.g., runpod/pytorch:2.4.0-py3.11-cuda12.4)
# Container disk: 50 GB minimum (env + Wan2.1 base + EchoMimic v3 flash+preview + buffer).
#
# After this script: venv ready, weights in place at echomimic_v3/{flash,preview}/.
# Next: python scripts/runpod/generate_echomimic.py --variant flash --tests hero
#
# Estimated time: ~10-15 min, dominated by HF/ModelScope weight downloads (~7-10 GB).

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ECHOMIMIC_DIR="${ECHOMIMIC_DIR:-/workspace/echomimic_v3}"
ECHOMIMIC_REPO="https://github.com/antgroup/echomimic_v3"

echo "============================================================"
echo "PROJECT_ROOT:  $PROJECT_ROOT"
echo "ECHOMIMIC_DIR: $ECHOMIMIC_DIR"
echo "============================================================"

# ----- 1. GPU sanity check -----
echo ""
echo "==> [1/8] GPU sanity check"
if command -v nvidia-smi &> /dev/null; then
  nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv
else
  echo "WARNING: nvidia-smi not found — is this a GPU pod?" >&2
fi

# ----- 2. Install uv -----
echo ""
echo "==> [2/8] Install uv"
if ! command -v uv &> /dev/null; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi
uv --version

# ----- 3. Clone EchoMimic v3 -----
echo ""
echo "==> [3/8] Clone EchoMimic v3"
if [ ! -d "$ECHOMIMIC_DIR" ]; then
  git clone "$ECHOMIMIC_REPO" "$ECHOMIMIC_DIR"
else
  echo "  EchoMimic v3 already cloned at $ECHOMIMIC_DIR (skipping clone)"
fi

# ----- 4. Set up venv + deps -----
# Repo recommends Python 3.10 explicitly. Force cu124 torch wheels after requirements.txt
# to match RunPod's typical driver (lesson from PuLID bootstrap — default cu130 wheels
# fail at the first sampling step).
echo ""
echo "==> [4/8] venv (python 3.10) + requirements"
cd "$ECHOMIMIC_DIR"
if [ ! -d ".venv" ]; then
  uv venv --python 3.10 .venv
fi
uv pip install --python .venv/bin/python -r requirements.txt

echo "  forcing torch cu124 wheels (override PyPI default for driver compat)..."
uv pip install --python .venv/bin/python --reinstall \
  --index-url https://download.pytorch.org/whl/cu124 \
  torch torchvision torchaudio

# chinese-wav2vec2-base lives only on ModelScope per the repo README.
uv pip install --python .venv/bin/python modelscope huggingface_hub

# ----- 5. Download shared base model (Wan2.1-Fun) once -----
echo ""
echo "==> [5/8] Download Wan2.1-Fun-V1.1-1.3B-InP (shared base)"
HF="$ECHOMIMIC_DIR/.venv/bin/hf"
mkdir -p "$ECHOMIMIC_DIR/shared"

if [ ! -f "$ECHOMIMIC_DIR/shared/Wan2.1-Fun-V1.1-1.3B-InP/.done" ]; then
  "$HF" download alibaba-pai/Wan2.1-Fun-V1.1-1.3B-InP \
    --local-dir "$ECHOMIMIC_DIR/shared/Wan2.1-Fun-V1.1-1.3B-InP"
  touch "$ECHOMIMIC_DIR/shared/Wan2.1-Fun-V1.1-1.3B-InP/.done"
else
  echo "  Wan2.1-Fun already downloaded (skip)"
fi

# ----- 6. Flash variant: chinese-wav2vec2 + flash transformer -----
echo ""
echo "==> [6/8] EchoMimic v3 Flash weights"
mkdir -p "$ECHOMIMIC_DIR/flash/transformer"

# chinese-wav2vec2-base — ModelScope only
if [ ! -f "$ECHOMIMIC_DIR/flash/chinese-wav2vec2-base/.done" ]; then
  echo "  [flash 1/3] chinese-wav2vec2-base (ModelScope, ~360 MB)"
  "$ECHOMIMIC_DIR/.venv/bin/modelscope" download \
    --model "TencentGameMate/chinese-wav2vec2-base" \
    --local_dir "$ECHOMIMIC_DIR/flash/chinese-wav2vec2-base"
  touch "$ECHOMIMIC_DIR/flash/chinese-wav2vec2-base/.done"
else
  echo "  [flash 1/3] chinese-wav2vec2-base already downloaded (skip)"
fi

# Flash transformer + config — flat under echomimicv3-flash-pro/ in the repo,
# our local target dir is flash/transformer/ (matches infer_flash.py's --transformer_path).
FLASH_TX="$ECHOMIMIC_DIR/flash/transformer/diffusion_pytorch_model.safetensors"
FLASH_CFG="$ECHOMIMIC_DIR/flash/transformer/config.json"
if [ ! -f "$FLASH_TX" ] || [ ! -f "$FLASH_CFG" ]; then
  echo "  [flash 2/3] EchoMimic v3 Flash transformer (~3.73 GB) + config"
  "$HF" download BadToBest/EchoMimicV3 \
    --include "echomimicv3-flash-pro/*" \
    --local-dir "$ECHOMIMIC_DIR/flash/.hf_cache"
  mv "$ECHOMIMIC_DIR/flash/.hf_cache/echomimicv3-flash-pro/diffusion_pytorch_model.safetensors" "$FLASH_TX"
  mv "$ECHOMIMIC_DIR/flash/.hf_cache/echomimicv3-flash-pro/config.json" "$FLASH_CFG"
  rm -rf "$ECHOMIMIC_DIR/flash/.hf_cache"
else
  echo "  [flash 2/3] Flash transformer + config already downloaded (skip)"
fi

# Link the shared Wan2.1-Fun base into flash/
echo "  [flash 3/3] link Wan2.1-Fun base into flash/"
ln -sfn "$ECHOMIMIC_DIR/shared/Wan2.1-Fun-V1.1-1.3B-InP" \
        "$ECHOMIMIC_DIR/flash/Wan2.1-Fun-V1.1-1.3B-InP"

# ----- 7. Preview variant: wav2vec2-base-960h + preview transformer -----
# Downloaded eagerly so the optional A/B re-run on hero doesn't need a second pod session.
echo ""
echo "==> [7/8] EchoMimic v3 Preview weights (for optional A/B)"
mkdir -p "$ECHOMIMIC_DIR/preview/transformer"

if [ ! -f "$ECHOMIMIC_DIR/preview/wav2vec2-base-960h/.done" ]; then
  echo "  [preview 1/3] wav2vec2-base-960h (~360 MB)"
  "$HF" download facebook/wav2vec2-base-960h \
    --local-dir "$ECHOMIMIC_DIR/preview/wav2vec2-base-960h"
  touch "$ECHOMIMIC_DIR/preview/wav2vec2-base-960h/.done"
else
  echo "  [preview 1/3] wav2vec2-base-960h already downloaded (skip)"
fi

PREVIEW_TX="$ECHOMIMIC_DIR/preview/transformer/diffusion_pytorch_model.safetensors"
PREVIEW_CFG="$ECHOMIMIC_DIR/preview/transformer/config.json"
if [ ! -f "$PREVIEW_TX" ] || [ ! -f "$PREVIEW_CFG" ]; then
  echo "  [preview 2/3] EchoMimic v3 Preview transformer (~3.41 GB) + config"
  "$HF" download BadToBest/EchoMimicV3 \
    --include "transformer/*" \
    --local-dir "$ECHOMIMIC_DIR/preview"
  # hf download with --include preserves the transformer/ subdir, which matches our target.
else
  echo "  [preview 2/3] Preview transformer + config already downloaded (skip)"
fi

echo "  [preview 3/3] link Wan2.1-Fun base into preview/"
ln -sfn "$ECHOMIMIC_DIR/shared/Wan2.1-Fun-V1.1-1.3B-InP" \
        "$ECHOMIMIC_DIR/preview/Wan2.1-Fun-V1.1-1.3B-InP"

# ----- 8. Link project inputs into echomimic_v3 dir -----
# generate_echomimic.py reads from these absolute paths, but linking keeps the relative
# story clean for anyone poking around the pod.
echo ""
echo "==> [8/8] Link project inputs"
ln -sfn "$PROJECT_ROOT/inputs" "$ECHOMIMIC_DIR/project_inputs"
mkdir -p "$PROJECT_ROOT/outputs/stage4_videos"
ls -la "$ECHOMIMIC_DIR/" | head -20

echo ""
echo "============================================================"
echo "Bootstrap complete."
echo "============================================================"
echo "  EchoMimic v3:  $ECHOMIMIC_DIR"
echo "  Flash weights: $ECHOMIMIC_DIR/flash/"
echo "  Preview weights: $ECHOMIMIC_DIR/preview/"
echo "  Project inputs linked at: $ECHOMIMIC_DIR/project_inputs"
echo ""
echo "Next: python $PROJECT_ROOT/scripts/runpod/generate_echomimic.py \\"
echo "        --variant flash --resolution 1024 --tests hero"
echo "============================================================"
