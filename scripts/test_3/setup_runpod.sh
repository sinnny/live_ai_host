#!/usr/bin/env bash
# One-shot setup for a fresh RunPod L40S pod (PyTorch 2.x template).
#
# What it does:
#   - Installs Phase 0 v2 Python deps (mirrors the Dockerfiles)
#   - Clones + installs AI-Toolkit (Ostris) for LoRA training
#   - Downloads Rhubarb Lip Sync binary
#   - Installs Playwright Chromium for the renderer
#   - Points HF cache at the persistent network volume so model weights
#     survive pod restarts
#
# Usage:
#   cd /workspace/live_ai_host
#   bash scripts/test_3/setup_runpod.sh
#
# Idempotent — safe to rerun. Skips work already done.

set -euo pipefail

WORKSPACE="${WORKSPACE_DIR:-/workspace}"
HF_HOME_PATH="${HF_HOME:-$WORKSPACE/.hf_cache}"
AI_TOOLKIT_ROOT="${AI_TOOLKIT_ROOT:-/opt/ai-toolkit}"
RHUBARB_VERSION="${RHUBARB_VERSION:-1.13.0}"

echo "[setup_runpod] WORKSPACE=$WORKSPACE"
echo "[setup_runpod] HF_HOME=$HF_HOME_PATH"
echo "[setup_runpod] AI_TOOLKIT_ROOT=$AI_TOOLKIT_ROOT"

mkdir -p "$HF_HOME_PATH"

# Persist env vars for future shells
ENV_FILE="$WORKSPACE/.runpod_env"
cat > "$ENV_FILE" <<EOF
export HF_HOME="$HF_HOME_PATH"
export TRANSFORMERS_CACHE="$HF_HOME_PATH"
export AI_TOOLKIT_ROOT="$AI_TOOLKIT_ROOT"
export PYTHONPATH="/opt/cosyvoice:/opt/cosyvoice/third_party/Matcha-TTS:\${PYTHONPATH:-}"
export PATH="\$AI_TOOLKIT_ROOT:\$PATH"
# Mitigate VRAM fragmentation on 48 GB cards loading Qwen-Image (~40 GB bf16).
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
# Silence pip's "running as root" reminder on RunPod (we are root by design).
export PIP_ROOT_USER_ACTION=ignore
EOF
if ! grep -q "source $ENV_FILE" /root/.bashrc 2>/dev/null; then
  echo "source $ENV_FILE" >> /root/.bashrc
fi
# Apply to current shell
# shellcheck disable=SC1090
source "$ENV_FILE"

# System packages (idempotent)
echo "[setup_runpod] apt install system libs..."
apt-get update -qq
apt-get install -y -qq --no-install-recommends \
    git curl ca-certificates xz-utils unzip \
    ffmpeg libsndfile1 \
    libgl1 libglib2.0-0 libsm6 libxext6 libxrender1 \
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libxkbcommon0 \
    libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libpango-1.0-0 \
    libcairo2 libasound2 libatspi2.0-0 \
    fonts-noto fonts-noto-cjk \
    >/dev/null

python -m pip install --upgrade -q pip wheel setuptools

# Image-gen / training stack.
# IMPORTANT: We force-upgrade torch first. RunPod's PyTorch template can ship
# with a torch old enough that its `infer_schema` doesn't resolve string-form
# type annotations, which breaks recent diffusers at import (see
# diffusers/models/attention_dispatch.py registering @_custom_op decorators).
echo "[setup_runpod] force-upgrading torch to match CUDA 12.4 build..."
pip install --upgrade -q --index-url https://download.pytorch.org/whl/cu124 \
    torch torchvision torchaudio

echo "[setup_runpod] pip install image-gen + training stack..."
pip install --upgrade -q \
    diffusers \
    transformers \
    "accelerate>=0.34" \
    "peft>=0.13" \
    "safetensors>=0.4" \
    "huggingface_hub>=0.25" \
    sentencepiece protobuf \
    "Pillow>=10.4" "numpy<2" \
    opencv-python-headless mediapipe \
    "click>=8.1" pyyaml einops scipy tqdm \
    timm kornia \
    jsonschema librosa soundfile

# AI-Toolkit (Ostris) — LoRA trainer.
# Not pip-installable (no setup.py/pyproject.toml); we invoke run.py directly
# via $AI_TOOLKIT_ROOT/run.py, so we only need its requirements installed.
if [ ! -d "$AI_TOOLKIT_ROOT/.git" ]; then
  echo "[setup_runpod] cloning AI-Toolkit..."
  git clone --depth 1 https://github.com/ostris/ai-toolkit.git "$AI_TOOLKIT_ROOT"
else
  echo "[setup_runpod] AI-Toolkit already at $AI_TOOLKIT_ROOT — skipping clone"
fi
if [ -f "$AI_TOOLKIT_ROOT/requirements.txt" ]; then
  echo "[setup_runpod] installing AI-Toolkit requirements (idempotent)..."
  pip install -q -r "$AI_TOOLKIT_ROOT/requirements.txt" || \
    echo "[setup_runpod] WARN: some AI-Toolkit deps failed to install; pipeline may still work for our path"
fi

# CosyVoice 2 — needed only for the prototype pipeline; install if missing
if [ ! -d "/opt/cosyvoice/.git" ]; then
  echo "[setup_runpod] cloning CosyVoice 2..."
  git clone --depth 1 --recursive https://github.com/FunAudioLLM/CosyVoice.git /opt/cosyvoice
  ( cd /opt/cosyvoice && pip install -r requirements.txt -q || true )
else
  echo "[setup_runpod] CosyVoice already at /opt/cosyvoice — skipping"
fi

# Rhubarb Lip Sync — release binary
if [ ! -x /usr/local/bin/rhubarb ]; then
  echo "[setup_runpod] downloading Rhubarb $RHUBARB_VERSION..."
  curl -sSL -o /tmp/rhubarb.zip \
    "https://github.com/DanielSWolf/rhubarb-lip-sync/releases/download/v${RHUBARB_VERSION}/Rhubarb-Lip-Sync-${RHUBARB_VERSION}-Linux.zip"
  unzip -q /tmp/rhubarb.zip -d /opt/
  mv "/opt/Rhubarb-Lip-Sync-${RHUBARB_VERSION}-Linux" /opt/rhubarb
  ln -sf /opt/rhubarb/rhubarb /usr/local/bin/rhubarb
  chmod +x /opt/rhubarb/rhubarb
  rm -f /tmp/rhubarb.zip
else
  echo "[setup_runpod] Rhubarb already installed — skipping"
fi

# Playwright Chromium (for renderer_cli.py)
echo "[setup_runpod] pip install playwright + chromium..."
pip install -q playwright
playwright install --with-deps chromium 2>&1 | tail -5 || true

echo ""
echo "[setup_runpod] DONE."
echo "  HF cache (persistent on volume): $HF_HOME_PATH"
echo "  Env file:                       $ENV_FILE"
echo "  Run \`source $ENV_FILE\` in any new shell, or re-login (sourced via .bashrc)."
echo ""
echo "Next:"
echo "  cd $WORKSPACE/live_ai_host/scripts/test_3/mascot/daramzzi"
echo "  python pipeline.py init"
echo "  python pipeline.py run-all --config daramzzi_config.yaml"
