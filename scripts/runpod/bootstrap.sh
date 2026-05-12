#!/usr/bin/env bash
# RunPod bootstrap — sets up ComfyUI + PuLID-Flux + downloads weights, then launches ComfyUI.
#
# Run this once per pod session after `git clone`-ing the project.
# Idempotent: safe to re-run if interrupted (clones are conditional, downloads resume).
#
# Assumes pod template: generic PyTorch with CUDA (e.g., runpod/pytorch:2.4.0-py3.11-cuda12.4)
# After this script: ComfyUI is running on http://127.0.0.1:8188 in background.
# Next: python scripts/runpod/generate.py
#
# Estimated time: ~10-15 min, dominated by HF weight downloads (~17 GB).

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
COMFYUI_DIR="${COMFYUI_DIR:-/workspace/ComfyUI}"
COMFYUI_REPO="https://github.com/comfyanonymous/ComfyUI"
PULID_REPO="https://github.com/lldacing/ComfyUI_PuLID_Flux_ll"

echo "============================================================"
echo "PROJECT_ROOT: $PROJECT_ROOT"
echo "COMFYUI_DIR:  $COMFYUI_DIR"
echo "============================================================"

# ----- 1. GPU sanity check -----
echo ""
echo "==> [1/9] GPU sanity check"
if command -v nvidia-smi &> /dev/null; then
  nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv
else
  echo "WARNING: nvidia-smi not found — is this a GPU pod?" >&2
fi

# ----- 2. Install uv (10-100x faster than pip) -----
echo ""
echo "==> [2/9] Install uv"
if ! command -v uv &> /dev/null; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi
uv --version

# ----- 3. Clone ComfyUI -----
echo ""
echo "==> [3/9] Clone ComfyUI"
if [ ! -d "$COMFYUI_DIR" ]; then
  git clone "$COMFYUI_REPO" "$COMFYUI_DIR"
else
  echo "  ComfyUI already cloned at $COMFYUI_DIR (skipping clone)"
fi

# ----- 4. Set up ComfyUI venv + deps -----
echo ""
echo "==> [4/9] ComfyUI venv + requirements"
cd "$COMFYUI_DIR"
if [ ! -d ".venv" ]; then
  uv venv --python 3.11 .venv
fi
uv pip install --python .venv/bin/python -r requirements.txt

# ComfyUI's requirements.txt has unpinned torch, which pulls the latest from PyPI default
# index (currently cu130 wheels). RunPod's RTX A6000 driver supports CUDA 12.4, so we
# force-reinstall torch with cu124 wheels to match. Without this, ComfyUI crashes at the
# first sampling step with "Trying to convert Float8_e4m3fn to the MPS backend" or
# "NVIDIA driver too old" — see 2026-05-12 pod session notes.
echo "  forcing torch cu124 wheels (override PyPI default cu130 for driver compat)..."
uv pip install --python .venv/bin/python --reinstall \
  --index-url https://download.pytorch.org/whl/cu124 \
  torch torchvision torchaudio

# ----- 5. Clone + patch PuLID-Flux node -----
echo ""
echo "==> [5/9] Clone + patch PuLID-Flux node"
PULID_DIR="$COMFYUI_DIR/custom_nodes/ComfyUI_PuLID_Flux_ll"
if [ ! -d "$PULID_DIR" ]; then
  git clone "$PULID_REPO" "$PULID_DIR"
fi

# Apply PR #95 patch (timestep_zero_index kwarg fix for ComfyUI v0.21+)
HOOK_FILE="$PULID_DIR/PulidFluxHook.py"
if grep -q "swallow new ComfyUI kwargs" "$HOOK_FILE"; then
  echo "  PR #95 patch already applied"
else
  python3 <<PYEOF
import re
src = open("$HOOK_FILE").read()
old = "    attn_mask: Tensor = None,\n) -> Tensor:"
new = "    attn_mask: Tensor = None,\n    **kwargs,  # swallow new ComfyUI kwargs (e.g. timestep_zero_index added in v0.21) — upstream PR #95\n) -> Tensor:"
if old not in src:
    raise SystemExit("PR #95 patch target string not found — node version may have changed")
open("$HOOK_FILE", "w").write(src.replace(old, new, 1))
print("  PR #95 patch applied")
PYEOF
fi

# Install PuLID requirements + facenet-pytorch (commented out in their requirements.txt)
uv pip install --python .venv/bin/python -r "$PULID_DIR/requirements.txt"
uv pip install --python .venv/bin/python --no-deps facenet-pytorch

# ----- 6. Download weights from HF (~17 GB; resumable) -----
echo ""
echo "==> [6/9] Download weights from HuggingFace"
mkdir -p "$COMFYUI_DIR/models"/{diffusion_models,text_encoders,vae,pulid}
HF="$COMFYUI_DIR/.venv/bin/hf"

echo "  [1/5] Flux dev fp8 e4m3fn (~12 GB) → diffusion_models/"
"$HF" download Kijai/flux-fp8 flux1-dev-fp8-e4m3fn.safetensors \
  --local-dir "$COMFYUI_DIR/models/diffusion_models"

echo "  [2/5] T5XXL fp8 text encoder (~5 GB) → text_encoders/"
"$HF" download comfyanonymous/flux_text_encoders t5xxl_fp8_e4m3fn.safetensors \
  --local-dir "$COMFYUI_DIR/models/text_encoders"

echo "  [3/5] CLIP-L text encoder (~250 MB) → text_encoders/"
"$HF" download comfyanonymous/flux_text_encoders clip_l.safetensors \
  --local-dir "$COMFYUI_DIR/models/text_encoders"

echo "  [4/5] Flux VAE bf16 (~335 MB) → vae/"
"$HF" download Kijai/flux-fp8 flux-vae-bf16.safetensors \
  --local-dir "$COMFYUI_DIR/models/vae"

echo "  [5/5] PuLID-Flux v0.9.1 (~1.2 GB) → pulid/"
"$HF" download guozinan/PuLID pulid_flux_v0.9.1.safetensors \
  --local-dir "$COMFYUI_DIR/models/pulid"

# ----- 7. Symlink project inputs into ComfyUI's input/ -----
echo ""
echo "==> [7/9] Link project inputs into ComfyUI"
mkdir -p "$COMFYUI_DIR/input"
ln -sfn "$PROJECT_ROOT/inputs/photos" "$COMFYUI_DIR/input/project_photos"
ln -sfn "$PROJECT_ROOT/inputs/audio" "$COMFYUI_DIR/input/project_audio"
ls -la "$COMFYUI_DIR/input/" | head -10

# ----- 8. Launch ComfyUI in background (no GUI; we use HTTP API) -----
echo ""
echo "==> [8/9] Launch ComfyUI (background, HTTP API on :8188)"
mkdir -p "$PROJECT_ROOT/logs"
LOG="$PROJECT_ROOT/logs/comfyui_pod.log"

# Kill any existing ComfyUI on this port
pkill -f "ComfyUI/main.py" 2>/dev/null || true
sleep 1

cd "$COMFYUI_DIR"
nohup .venv/bin/python main.py --listen --port 8188 > "$LOG" 2>&1 &
COMFYUI_PID=$!
echo "  ComfyUI launched (PID $COMFYUI_PID), logging to $LOG"

# ----- 9. Wait for API readiness -----
echo ""
echo "==> [9/9] Wait for ComfyUI API to be ready (max 60s)"
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
echo "Bootstrap complete."
echo "============================================================"
echo "  ComfyUI:  http://127.0.0.1:8188 (PID $COMFYUI_PID)"
echo "  Log:      $LOG"
echo ""
echo "Next: python scripts/runpod/generate.py"
echo ""
echo "To stop ComfyUI later: pkill -f 'ComfyUI/main.py'"
echo "============================================================"
