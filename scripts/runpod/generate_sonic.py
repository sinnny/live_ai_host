#!/usr/bin/env python3
"""Run Sonic inference on daramzzi seed + Korean voice.

Sonic's demo.py CLI:
    python3 demo.py <image> <audio> <output>

This wrapper:
- locates Sonic install at /workspace/Sonic
- runs demo.py with our daramzzi inputs
- writes output to project's outputs/ dir
- writes sidecar metadata (wall time, exit code, command)

Run inside the pod after bootstrap_sonic.sh:
    python scripts/runpod/generate_sonic.py
"""

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SONIC_DIR = Path(os.environ.get("SONIC_DIR", "/workspace/Sonic"))
DEFAULT_IMAGE = SONIC_DIR / "inputs" / "daramzzi_seed.png"
DEFAULT_AUDIO = SONIC_DIR / "inputs" / "daramzzi_voice_b1.wav"
OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "sonic_test"


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--image", default=str(DEFAULT_IMAGE), help="Input image path")
    ap.add_argument("--audio", default=str(DEFAULT_AUDIO), help="Input audio path")
    ap.add_argument("--output", default=None, help="Output video path (default: outputs/sonic_test/daramzzi_sonic.mp4)")
    args = ap.parse_args()

    image = Path(args.image)
    audio = Path(args.audio)
    if not image.exists():
        sys.exit(f"missing image: {image}")
    if not audio.exists():
        sys.exit(f"missing audio: {audio}")

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    output = Path(args.output) if args.output else OUTPUT_ROOT / "daramzzi_sonic.mp4"
    output.parent.mkdir(parents=True, exist_ok=True)

    demo = SONIC_DIR / "demo.py"
    if not demo.exists():
        sys.exit(f"Sonic demo.py not found at {demo}. Run bootstrap_sonic.sh first.")

    cmd = [
        str(SONIC_DIR / ".venv" / "bin" / "python"),
        str(demo),
        str(image),
        str(audio),
        str(output),
    ]

    print(f"=== Sonic run ===")
    print(f"  image:  {image}")
    print(f"  audio:  {audio}  ({audio.stat().st_size / 1024:.1f} KB)")
    print(f"  output: {output}")
    print(f"  cmd:    {' '.join(cmd)}")

    started_iso = now_iso()
    t0 = time.monotonic()

    proc = subprocess.run(cmd, cwd=str(SONIC_DIR))
    wall_seconds = time.monotonic() - t0
    completed_iso = now_iso()

    meta = {
        "image_path": str(image),
        "audio_path": str(audio),
        "output_path": str(output),
        "wall_seconds": round(wall_seconds, 1),
        "exit_code": proc.returncode,
        "started_iso": started_iso,
        "completed_iso": completed_iso,
        "cmd": cmd,
    }
    (output.parent / "_meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n")

    print(f"")
    print(f"=== done ===")
    print(f"  exit code:    {proc.returncode}")
    print(f"  wall:         {wall_seconds:.1f}s ({wall_seconds/60:.1f}min)")
    print(f"  output exists: {output.exists()}")
    if output.exists():
        print(f"  output size:  {output.stat().st_size / 1024 / 1024:.1f} MB")
    print(f"  meta:         {output.parent / '_meta.json'}")
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
