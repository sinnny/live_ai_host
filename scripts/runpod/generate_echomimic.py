#!/usr/bin/env python3
"""
Run EchoMimic v3 Flash on Stage 4 Tests 1-3.

Invoked on the pod after bootstrap_echomimic.sh completes. Shells out to the repo's
infer_flash.py (which accepts CLI args, unlike infer_preview.py). Pre-resamples the
24 kHz project audio to 16 kHz once for wav2vec2.

Tests:
  hero               → inputs/photos/hero.png + reference Korean wav
  variant_3q         → inputs/photos/variant_3q.png + reference Korean wav
  variant_speaking   → inputs/photos/variant_speaking.png + reference Korean wav

Usage:
  python generate_echomimic.py --tests hero                           # smoke test
  python generate_echomimic.py --tests variant_3q,variant_speaking
  python generate_echomimic.py --resolution 768                       # fallback if 1024 fails
  python generate_echomimic.py --video-length 49                      # OOM mitigation
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ECHOMIMIC_DIR = Path(os.environ.get("ECHOMIMIC_DIR", "/workspace/echomimic_v3"))

TESTS = {
    "hero": "hero.png",
    "variant_3q": "variant_3q.png",
    "variant_speaking": "variant_speaking.png",
    "test_2": "test_2.png",
}
AUDIO_SRC = PROJECT_ROOT / "inputs/audio/reference_korean_30s.wav"
OUT_ROOT = PROJECT_ROOT / "outputs/stage4_videos"

# Mirrors the plan's prompt for Test 1, applied uniformly across all 3 tests.
DEFAULT_PROMPT = (
    "A Korean woman in a relaxed pose, speaking naturally with minimal "
    "head movement. Don't blink too often. Preserve background integrity."
)

# Test B1 (Phase 0 v2 post-mortem #1 §8): EchoMimic v3 on stylized Daramzzi.
# Cartoon squirrel mascot, gentle natural motion. Lip-sync imprecision is on-brand
# per PRD §1.2 "obviously AI / failure-modes-as-style" — we want motion, not realism.
DARAMZZI_PROMPT = (
    "A cute cartoon squirrel mascot character with a beige apron and headset, "
    "speaking naturally with gentle head movement. Eyes mostly open and alert, "
    "rare blinks. Earnest, friendly expression. Preserve character design and background."
)


def ensure_audio_16k(src: Path) -> Path:
    """Resample input audio to 16 kHz mono once; cache result. wav2vec2 expects 16 kHz."""
    cache_dir = OUT_ROOT / "_audio_16k"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache = cache_dir / (src.stem + ".16k.wav")
    if cache.exists() and cache.stat().st_mtime > src.stat().st_mtime:
        return cache
    print(f"[audio] resampling {src} → 16 kHz mono → {cache}")
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error",
         "-i", str(src), "-ac", "1", "-ar", "16000", str(cache)],
        check=True,
    )
    return cache


def ensure_audio_enhanced(src: Path) -> Path:
    """16 kHz mono + 500ms leading silence anchor + EBU R128 loudness normalize (-16 LUFS,
    true-peak -3 dBFS). The leading silence gives wav2vec2 a "neutral mouth" prior so the
    first few output frames aren't garbage; loudnorm raises quiet TTS audio so the model
    actually opens the mouth. Cached separately from the raw 16k version."""
    cache_dir = OUT_ROOT / "_audio_16k"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache = cache_dir / (src.stem + ".16k.enh.wav")
    if cache.exists() and cache.stat().st_mtime > src.stat().st_mtime:
        return cache
    print(f"[audio] enhanced preprocess (500ms silence + loudnorm) {src} → {cache}")
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error",
         "-i", str(src),
         "-ac", "1", "-ar", "16000",
         "-af", "adelay=500,loudnorm=I=-16:TP=-3:LRA=11",
         str(cache)],
        check=True,
    )
    return cache


def default_video_length(resolution: int) -> int:
    # Repo docs: 113 fits 24 GB at 768. 1024 ≈ 1.78× tokens → drop margin even on A6000 48 GB.
    return 65 if resolution == 1024 else 81


def run_flash(test_name: str, image_path: Path, audio_path: Path,
              resolution: int, video_length: int, seed: int,
              prompt: str, negative_prompt: str,
              guidance_scale: float, audio_guidance_scale: float) -> dict:
    save_dir = OUT_ROOT / f"flash_{resolution}" / test_name
    save_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        str(ECHOMIMIC_DIR / ".venv/bin/python"), "infer_flash.py",
        "--image_path", str(image_path),
        "--audio_path", str(audio_path),
        "--save_path", str(save_dir),
        "--config_path", "config/config.yaml",
        "--model_name", str(ECHOMIMIC_DIR / "flash/Wan2.1-Fun-V1.1-1.3B-InP"),
        "--transformer_path", str(ECHOMIMIC_DIR / "flash/transformer/diffusion_pytorch_model.safetensors"),
        "--wav2vec_model_dir", str(ECHOMIMIC_DIR / "flash/chinese-wav2vec2-base"),
        "--num_inference_steps", "8",
        "--ckpt_idx", "50000",
        "--sampler_name", "Flow_Unipc",
        "--video_length", str(video_length),
        "--guidance_scale", str(guidance_scale),
        "--audio_guidance_scale", str(audio_guidance_scale),
        "--audio_scale", "1.0",
        "--neg_scale", "1.0",
        "--neg_steps", "0",
        "--seed", str(seed),
        "--weight_dtype", "bfloat16",
        "--sample_size", str(resolution), str(resolution),
        "--fps", "25",
        "--shift", "5.0",
        "--enable_teacache",
        "--teacache_threshold", "0.1",
        "--num_skip_start_steps", "5",
        "--riflex_k", "6",
        "--ulysses_degree", "1",
        "--ring_degree", "1",
        "--prompt", prompt,
        "--add_prompt", "",
        "--negative_prompt", negative_prompt,
    ]

    print(f"[{test_name}] running infer_flash.py (cwd={ECHOMIMIC_DIR})")
    print("    " + " ".join(cmd[:6]) + " ...")

    t0 = time.time()
    proc = subprocess.run(cmd, cwd=ECHOMIMIC_DIR)
    dt = time.time() - t0

    return {
        "test_name": test_name,
        "variant": "flash",
        "resolution": resolution,
        "video_length": video_length,
        "seed": seed,
        "image_path": str(image_path),
        "audio_path": str(audio_path),
        "save_dir": str(save_dir),
        "wall_seconds": round(dt, 1),
        "exit_code": proc.returncode,
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "guidance_scale": guidance_scale,
        "audio_guidance_scale": audio_guidance_scale,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--variant", choices=["flash", "preview"], default="flash")
    p.add_argument("--resolution", type=int, choices=[768, 1024], default=1024)
    p.add_argument("--tests", default="hero,variant_3q,variant_speaking",
                   help="comma-separated subset of: " + ",".join(TESTS) +
                        ". Ignored if --image-path and --audio-path are passed.")
    p.add_argument("--image-path", type=Path, default=None,
                   help="explicit input image (overrides --tests). Use for B1/Daramzzi.")
    p.add_argument("--audio-path", type=Path, default=None,
                   help="explicit input audio (overrides default reference_korean_30s.wav).")
    p.add_argument("--test-name", default=None,
                   help="output folder name when using --image-path. Default: image stem.")
    p.add_argument("--video-length", type=int, default=None,
                   help="sliding-window chunk size; default 65@1024, 81@768. Drop if OOM.")
    p.add_argument("--seed", type=int, default=43)
    p.add_argument("--prompt", default=None,
                   help="text prompt; default is photoreal-human DEFAULT_PROMPT, "
                        "or DARAMZZI_PROMPT when --image-path stem starts with 'daramzzi' or 'seed'.")
    p.add_argument("--negative-prompt", default="",
                   help="passed to infer_flash.py --negative_prompt; default empty (run_flash.sh default)")
    p.add_argument("--guidance-scale", type=float, default=6.0,
                   help="text CFG; run_flash.sh default 6.0. Lower (4.5-5.0) loosens prompt adherence.")
    p.add_argument("--audio-guidance-scale", type=float, default=3.0,
                   help="audio CFG — the lip-sync dial. Default 3.0. Higher (3.5-4.0) = tighter sync, more jitter.")
    p.add_argument("--audio-preprocessing", choices=["standard", "enhanced"], default="standard",
                   help="standard = resample 16kHz only; enhanced = +500ms leading silence anchor + EBU R128 loudnorm.")
    args = p.parse_args()

    if args.variant == "preview":
        sys.exit(
            "Preview variant is not wired through this script — gate on Flash quality first.\n"
            "If/when needed: edit echomimic_v3/config/config.yaml manually and run\n"
            "  cd $ECHOMIMIC_DIR && .venv/bin/python infer_preview.py\n"
            "Bootstrap has Preview weights ready at echomimic_v3/preview/."
        )

    if args.video_length is None:
        args.video_length = default_video_length(args.resolution)

    # Audio source: --audio-path override, else the legacy photoreal reference.
    audio_src = args.audio_path if args.audio_path else AUDIO_SRC
    if not audio_src.exists():
        sys.exit(f"Audio not found: {audio_src}")
    if args.audio_preprocessing == "enhanced":
        audio_path = ensure_audio_enhanced(audio_src)
    else:
        audio_path = ensure_audio_16k(audio_src)

    # Build the (test_name, image_path) work list. Two modes:
    #   --image-path  → single explicit run (Daramzzi / B1)
    #   --tests       → original photoreal sweep (legacy)
    if args.image_path:
        if not args.image_path.exists():
            sys.exit(f"Image not found: {args.image_path}")
        args.image_path = args.image_path.resolve()
        test_name = args.test_name or args.image_path.stem
        work = [(test_name, args.image_path)]
        stem_lower = args.image_path.stem.lower()
        prompt = args.prompt or (
            DARAMZZI_PROMPT if (stem_lower.startswith("daramzzi") or stem_lower.startswith("seed"))
            else DEFAULT_PROMPT
        )
    else:
        tests = [t.strip() for t in args.tests.split(",") if t.strip()]
        bad = [t for t in tests if t not in TESTS]
        if bad:
            sys.exit(f"Unknown test(s) {bad}. Available: {list(TESTS)}")
        work = [(t, PROJECT_ROOT / "inputs/photos" / TESTS[t]) for t in tests]
        prompt = args.prompt or DEFAULT_PROMPT

    print(f"\n=== EchoMimic v3 Flash · {args.resolution}x{args.resolution} · "
          f"vlen={args.video_length} · runs={[w[0] for w in work]} ===\n")

    results = []
    for test_name, image_path in work:
        if not image_path.exists():
            print(f"SKIP {test_name}: input image not found at {image_path}")
            results.append({"test_name": test_name, "error": "input image missing"})
            continue
        try:
            meta = run_flash(
                test_name=test_name,
                image_path=image_path,
                audio_path=audio_path,
                resolution=args.resolution,
                video_length=args.video_length,
                seed=args.seed,
                prompt=prompt,
                negative_prompt=args.negative_prompt,
                guidance_scale=args.guidance_scale,
                audio_guidance_scale=args.audio_guidance_scale,
            )
        except Exception as e:
            meta = {"test_name": test_name, "error": repr(e)}

        sidecar = OUT_ROOT / f"flash_{args.resolution}" / test_name / "_meta.json"
        sidecar.parent.mkdir(parents=True, exist_ok=True)
        sidecar.write_text(json.dumps(meta, indent=2))
        results.append(meta)
        print(f"--- {test_name}: exit={meta.get('exit_code')} time={meta.get('wall_seconds', 'n/a')}s ---\n")

    print("\n=== Summary ===")
    for r in results:
        name = r["test_name"]
        if "error" in r:
            print(f"  {name:20s}  ERROR: {r['error']}")
        else:
            print(f"  {name:20s}  exit={r['exit_code']}  time={r['wall_seconds']}s  "
                  f"→ {r['save_dir']}")


if __name__ == "__main__":
    main()
