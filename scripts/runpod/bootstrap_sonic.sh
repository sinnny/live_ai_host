#!/usr/bin/env bash
# RunPod bootstrap — Sonic (Portrait Animation, image+audio → video).
# Tencent Cloud OSS model. License: CC BY-NC-SA 4.0 (non-commercial; Phase 0 OK).
#
# Use case: realtime-ish OSS lip sync on cartoon/stylized characters
# (daramzzi). Their gallery includes anime/sculpture/portrait inputs.
#
# Run once per pod session after `git clone`-ing this repo.
# Idempotent: safe to re-run.
#
# Pod template: runpod/pytorch:2.4.0-py3.11-cuda12.4-devel-ubuntu22.04
# Disk: 50 GB Volume + 30 GB Container should be enough.
#
# After this script: venv ready, weights in place at /workspace/Sonic/checkpoints/.
# Next: ./dev sonic run

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SONIC_DIR="${SONIC_DIR:-/workspace/Sonic}"
SONIC_REPO="https://github.com/jixiaozhong/Sonic"

echo "============================================================"
echo "PROJECT_ROOT: $PROJECT_ROOT"
echo "SONIC_DIR:    $SONIC_DIR"
echo "============================================================"

# ----- 1. GPU sanity + system deps -----
echo ""
echo "==> [1/7] GPU sanity check + system deps (ffmpeg, git-lfs)"
if command -v nvidia-smi &> /dev/null; then
  nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv
else
  echo "WARNING: nvidia-smi not found — is this a GPU pod?" >&2
fi
# ffmpeg needed for audio re-encoding and final video assembly
if ! command -v ffmpeg &> /dev/null; then
  echo "  installing ffmpeg via apt..."
  apt-get update -qq && apt-get install -y -qq ffmpeg
fi
ffmpeg -version | head -1

# ----- 2. Install uv -----
echo ""
echo "==> [2/7] Install uv"
if ! command -v uv &> /dev/null; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi
uv --version

# ----- 3. Clone Sonic -----
echo ""
echo "==> [3/7] Clone Sonic"
if [ ! -d "$SONIC_DIR" ]; then
  git clone "$SONIC_REPO" "$SONIC_DIR"
else
  echo "  Sonic already cloned at $SONIC_DIR — pulling latest"
  cd "$SONIC_DIR" && git pull && cd - > /dev/null
fi

# ----- 4. venv + requirements + cu124 torch override -----
echo ""
echo "==> [4/7] venv (python 3.10) + requirements"
cd "$SONIC_DIR"
if [ ! -d ".venv" ]; then
  uv venv --python 3.10 .venv
fi
uv pip install --python .venv/bin/python -r requirements.txt

# Force cu124 torch (same lesson from PuLID/Kontext: RunPod driver compat)
echo "  forcing torch cu124 wheels (override default for driver compat)..."
uv pip install --python .venv/bin/python --reinstall \
  --index-url https://download.pytorch.org/whl/cu124 \
  torch torchvision torchaudio

# huggingface_hub CLI for weight downloads
uv pip install --python .venv/bin/python "huggingface_hub[cli]"

# ----- 5. Download weights (~13 GB total, resumable) -----
echo ""
echo "==> [5/7] Download weights from HuggingFace"
mkdir -p "$SONIC_DIR/checkpoints"
HF="$SONIC_DIR/.venv/bin/hf"

echo "  [1/3] Sonic core weights (~few GB) → checkpoints/"
"$HF" download LeonJoe13/Sonic --local-dir "$SONIC_DIR/checkpoints"

echo "  [2/3] Stable Video Diffusion img2vid-xt (~10 GB) → checkpoints/stable-video-diffusion-img2vid-xt/"
"$HF" download stabilityai/stable-video-diffusion-img2vid-xt \
  --local-dir "$SONIC_DIR/checkpoints/stable-video-diffusion-img2vid-xt"

echo "  [3/3] Whisper-tiny (~150 MB) → checkpoints/whisper-tiny/"
"$HF" download openai/whisper-tiny --local-dir "$SONIC_DIR/checkpoints/whisper-tiny"

# ----- 6. Symlink our inputs -----
echo ""
echo "==> [6/7] Link project inputs into Sonic input dir"
mkdir -p "$SONIC_DIR/inputs"
ln -sfn "$PROJECT_ROOT/docs/report/assets/images/daramzzi_seed.png" "$SONIC_DIR/inputs/daramzzi_seed.png"
ln -sfn "$PROJECT_ROOT/inputs/audio/daramzzi_voice_b1.wav" "$SONIC_DIR/inputs/daramzzi_voice_b1.wav"
ls -la "$SONIC_DIR/inputs/"

# ----- 7. Quick install verification -----
echo ""
echo "==> [7/7] Verify Sonic can import (no run yet)"
cd "$SONIC_DIR"
.venv/bin/python -c "import torch; print(f'torch: {torch.__version__} | cuda: {torch.cuda.is_available()} | device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"NONE\"}')"

echo ""
echo "============================================================"
echo "Sonic bootstrap complete."
echo "============================================================"
echo "  Repo:         $SONIC_DIR"
echo "  Inputs:       $SONIC_DIR/inputs/{daramzzi_seed.png,daramzzi_voice_b1.wav}"
echo "  Outputs:      will write to $SONIC_DIR/outputs/"
echo ""
echo "Next: ./dev sonic run"
echo "============================================================"
