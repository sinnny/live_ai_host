#!/usr/bin/env bash
# Download Phase 0 weights for ComfyUI (~18 GB total).
#
# Files:
#   Flux dev fp8 e4m3fn   ~12 GB  → models/diffusion_models/
#   T5XXL fp8             ~5  GB  → models/text_encoders/
#   CLIP-L                ~250MB  → models/text_encoders/
#   Flux VAE              ~335MB  → models/vae/
#   PuLID-Flux v0.9.1     ~1.2GB  → models/pulid/
#
# Auto-downloaded by ComfyUI on first workflow run (NOT here):
#   EVA-CLIP, InsightFace antelopev2, facexlib parsing models
#
# Idempotent: huggingface-cli skips files already present.
# Resumable: partial downloads resume on re-run.
#
# Usage:
#   ./dev download-weights
#   (or) scripts/download_weights.sh

set -euo pipefail

PROJECT_ROOT="/Users/shinheehwang/Desktop/projects/00_live_ai_host"
COMFYUI_DIR="$PROJECT_ROOT/tools/ComfyUI"
COMFYUI_MODELS="$COMFYUI_DIR/models"
HF="$COMFYUI_DIR/.venv/bin/hf"

if [ ! -x "$HF" ]; then
  echo "Error: 'hf' (new HuggingFace CLI) not found at $HF" >&2
  echo "Note: 'huggingface-cli' was renamed to 'hf' in huggingface_hub 1.x. Install/upgrade with:" >&2
  echo "  cd $COMFYUI_DIR && uv pip install --python .venv/bin/python --upgrade huggingface_hub" >&2
  exit 1
fi

mkdir -p \
  "$COMFYUI_MODELS/diffusion_models" \
  "$COMFYUI_MODELS/text_encoders" \
  "$COMFYUI_MODELS/vae" \
  "$COMFYUI_MODELS/pulid"

echo "==> [1/5] Flux dev fp8 e4m3fn (~12 GB) → diffusion_models/"
"$HF" download Kijai/flux-fp8 flux1-dev-fp8-e4m3fn.safetensors \
  --local-dir "$COMFYUI_MODELS/diffusion_models"

echo ""
echo "==> [2/5] T5XXL fp8 text encoder (~5 GB) → text_encoders/"
"$HF" download comfyanonymous/flux_text_encoders t5xxl_fp8_e4m3fn.safetensors \
  --local-dir "$COMFYUI_MODELS/text_encoders"

echo ""
echo "==> [3/5] CLIP-L text encoder (~250 MB) → text_encoders/"
"$HF" download comfyanonymous/flux_text_encoders clip_l.safetensors \
  --local-dir "$COMFYUI_MODELS/text_encoders"

echo ""
echo "==> [4/5] Flux VAE bf16 (~335 MB) → vae/"
"$HF" download Kijai/flux-fp8 flux-vae-bf16.safetensors \
  --local-dir "$COMFYUI_MODELS/vae"

echo ""
echo "==> [5/5] PuLID-Flux v0.9.1 (~1.2 GB) → pulid/"
"$HF" download guozinan/PuLID pulid_flux_v0.9.1.safetensors \
  --local-dir "$COMFYUI_MODELS/pulid"

echo ""
echo "============================================================"
echo "Phase 0 weights downloaded. Summary:"
echo "============================================================"
ls -lh "$COMFYUI_MODELS/diffusion_models/" "$COMFYUI_MODELS/text_encoders/" "$COMFYUI_MODELS/vae/" "$COMFYUI_MODELS/pulid/" 2>/dev/null \
  | grep -vE "^total|^d|\.cache" || true
echo ""
echo "Auto-downloaded on first workflow run (no action needed now):"
echo "  - EVA-CLIP-L-14-336        → models/clip/"
echo "  - InsightFace antelopev2   → models/insightface/models/antelopev2/"
echo "  - facexlib parsing models  → models/facexlib/"
