#!/usr/bin/env bash
# RunPod bootstrap — Flux Kontext Dev (identity-preserving image edit).
# Mirrors bootstrap.sh but swaps PuLID for Kontext.
#
# Run once per pod session after `git clone`-ing the project.
# Idempotent: safe to re-run.
#
# Pod template: generic PyTorch with CUDA (e.g. runpod/pytorch:2.4.0-py3.11-cuda12.4)
# After this script: ComfyUI is running on http://127.0.0.1:8188 in background.
# Next: python scripts/runpod/generate_kontext.py
#
# Estimated time: ~10-15 min, dominated by HF weight downloads (~17 GB).
# Disk: 30 GB container disk is enough.

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
COMFYUI_DIR="${COMFYUI_DIR:-/workspace/ComfyUI}"
COMFYUI_REPO="https://github.com/comfyanonymous/ComfyUI"

echo "============================================================"
echo "PROJECT_ROOT: $PROJECT_ROOT"
echo "COMFYUI_DIR:  $COMFYUI_DIR"
echo "Mode:         Flux Kontext Dev (image edit)"
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

# ----- 3. Clone ComfyUI -----
echo ""
echo "==> [3/8] Clone ComfyUI"
if [ ! -d "$COMFYUI_DIR" ]; then
  git clone "$COMFYUI_REPO" "$COMFYUI_DIR"
else
  echo "  ComfyUI already cloned at $COMFYUI_DIR — pulling latest"
  cd "$COMFYUI_DIR" && git pull && cd - > /dev/null
fi

# ----- 4. Set up ComfyUI venv + deps -----
echo ""
echo "==> [4/8] ComfyUI venv + requirements"
cd "$COMFYUI_DIR"
if [ ! -d ".venv" ]; then
  uv venv --python 3.11 .venv
fi
uv pip install --python .venv/bin/python -r requirements.txt

# Force cu124 torch wheels for RunPod A6000/L40S driver compat (same as PuLID bootstrap)
echo "  forcing torch cu124 wheels (override PyPI default for driver compat)..."
uv pip install --python .venv/bin/python --reinstall \
  --index-url https://download.pytorch.org/whl/cu124 \
  torch torchvision torchaudio

# ----- 5. Download Kontext weights (~17 GB; resumable) -----
echo ""
echo "==> [5/8] Download Flux Kontext Dev weights from HuggingFace"
mkdir -p "$COMFYUI_DIR/models"/{diffusion_models,text_encoders,vae}
HF="$COMFYUI_DIR/.venv/bin/hf"

echo "  [1/4] Flux Kontext Dev fp8 scaled (~12 GB) → diffusion_models/"
"$HF" download Comfy-Org/flux1-kontext-dev_ComfyUI \
  split_files/diffusion_models/flux1-dev-kontext_fp8_scaled.safetensors \
  --local-dir "$COMFYUI_DIR/models"
# The Comfy-Org repo nests files under split_files/; flatten the layout so the
# UNETLoader can find them at models/diffusion_models/flux1-dev-kontext_fp8_scaled.safetensors
if [ -f "$COMFYUI_DIR/models/split_files/diffusion_models/flux1-dev-kontext_fp8_scaled.safetensors" ]; then
  mv -n "$COMFYUI_DIR/models/split_files/diffusion_models/flux1-dev-kontext_fp8_scaled.safetensors" \
    "$COMFYUI_DIR/models/diffusion_models/"
  rm -rf "$COMFYUI_DIR/models/split_files"
fi

echo "  [2/4] T5XXL fp8 text encoder (~5 GB) → text_encoders/"
"$HF" download comfyanonymous/flux_text_encoders t5xxl_fp8_e4m3fn.safetensors \
  --local-dir "$COMFYUI_DIR/models/text_encoders"

echo "  [3/4] CLIP-L text encoder (~250 MB) → text_encoders/"
"$HF" download comfyanonymous/flux_text_encoders clip_l.safetensors \
  --local-dir "$COMFYUI_DIR/models/text_encoders"

echo "  [4/4] Flux VAE (ae.safetensors, ~335 MB) → vae/"
"$HF" download Comfy-Org/flux1-kontext-dev_ComfyUI \
  split_files/vae/ae.safetensors \
  --local-dir "$COMFYUI_DIR/models"
if [ -f "$COMFYUI_DIR/models/split_files/vae/ae.safetensors" ]; then
  mv -n "$COMFYUI_DIR/models/split_files/vae/ae.safetensors" \
    "$COMFYUI_DIR/models/vae/"
  rm -rf "$COMFYUI_DIR/models/split_files"
fi

# ----- 6. Symlink project inputs into ComfyUI's input/ -----
echo ""
echo "==> [6/8] Link project inputs into ComfyUI"
mkdir -p "$COMFYUI_DIR/input"
ln -sfn "$PROJECT_ROOT/inputs/photos" "$COMFYUI_DIR/input/project_photos"
ls -la "$COMFYUI_DIR/input/" | head -10

# ----- 7. Launch ComfyUI in background (HTTP API on :8188) -----
echo ""
echo "==> [7/8] Launch ComfyUI (background, HTTP API on :8188)"
mkdir -p "$PROJECT_ROOT/logs"
LOG="$PROJECT_ROOT/logs/comfyui_kontext_pod.log"

# Kill any existing ComfyUI on this port
pkill -f "ComfyUI/main.py" 2>/dev/null || true
sleep 1

cd "$COMFYUI_DIR"
nohup .venv/bin/python main.py --listen --port 8188 > "$LOG" 2>&1 &
COMFYUI_PID=$!
echo "  ComfyUI launched (PID $COMFYUI_PID), logging to $LOG"

# ----- 8. Wait for API readiness -----
echo ""
echo "==> [8/8] Wait for ComfyUI API to be ready (max 60s)"
for i in $(seq 1 60); do
  if curl -sf http://127.0.0.1:8188/system_stats > /dev/null 2>&1; then
    echo "  API ready after ${i}s"
    break
  fi
  if ! kill -0 "$COMFYUI_PID" 2>/dev/null; then
    echo "  ERROR: ComfyUI process died. Last 30 lines of log:" >&2
    tail -30 "$LOG" >&2
    exit 1
  fi
  sleep 1
done

if ! curl -sf http://127.0.0.1:8188/system_stats > /dev/null 2>&1; then
  echo "  ERROR: ComfyUI did not become ready within 60s" >&2
  tail -30 "$LOG" >&2
  exit 1
fi

echo ""
echo "============================================================"
echo "Kontext bootstrap complete."
echo "============================================================"
echo "  ComfyUI:  http://127.0.0.1:8188 (PID $COMFYUI_PID)"
echo "  Log:      $LOG"
echo ""
echo "Next:"
echo "  python scripts/runpod/generate_kontext.py --limit 1   # smoke test (1 image)"
echo "  python scripts/runpod/generate_kontext.py             # full run (25 images)"
echo ""
echo "To stop ComfyUI: pkill -f 'ComfyUI/main.py'"
echo "============================================================"
