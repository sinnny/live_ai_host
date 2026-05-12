#!/usr/bin/env bash
# Launch ComfyUI on Mac MPS.
#
# Usage:
#   scripts/comfyui.sh                  # default: --force-fp16, MPS fallback enabled
#   scripts/comfyui.sh --listen         # bind to all interfaces (LAN access)
#   scripts/comfyui.sh --port 8189      # custom port
#   scripts/comfyui.sh --cpu            # CPU-only fallback if MPS misbehaves
#
# Stop with Ctrl+C in this terminal.

set -euo pipefail

PROJECT_ROOT="/Users/shinheehwang/Desktop/projects/00_live_ai_host"
COMFYUI_DIR="$PROJECT_ROOT/tools/ComfyUI"
PYTHON="$COMFYUI_DIR/.venv/bin/python"

if [ ! -x "$PYTHON" ]; then
  echo "Error: ComfyUI venv not found at $COMFYUI_DIR/.venv" >&2
  echo "Recreate it with:" >&2
  echo "  cd $COMFYUI_DIR && uv venv --python 3.11 && uv pip install -r requirements.txt" >&2
  exit 1
fi

cd "$COMFYUI_DIR"
PYTORCH_ENABLE_MPS_FALLBACK=1 exec "$PYTHON" main.py --force-fp16 "$@"
