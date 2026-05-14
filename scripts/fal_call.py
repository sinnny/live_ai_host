"""Stage 4 paid talking-head tests on fal.ai (Tests 4-6).

Tests 4-6 run an input image + reference_korean_30s.wav against three paid models:
    aurora      Test 4  paid-commodity        fal-ai/creatify/aurora
    omnihuman   Test 5  paid-premium-emo      fal-ai/bytedance/omnihuman/v1.5
    kling       Test 6  paid-premium-cinema   fal-ai/kling-video/ai-avatar/v2/pro

Variants (input image):
    hero       inputs/photos/hero.png       (default — 3/4-ish broadcast headshot)
    test_2     inputs/photos/test_2.png     (clean direct-front studio headshot)

Usage:
    uv run python scripts/fal_call.py aurora                       # run Test 4 on hero
    uv run python scripts/fal_call.py aurora --variant test_2      # run Test 4 on test_2
    uv run python scripts/fal_call.py aurora --dry-run             # print cost + args only
    uv run python scripts/fal_call.py aurora --force               # re-run even if output exists

Output: outputs/stage4_videos/<model_dir>/<variant>/{<variant>_output.mp4,_meta.json}
"""

from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import json
import os
import sys
import time
import wave
from pathlib import Path

import fal_client
import requests
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
AUDIO_PATH = PROJECT_ROOT / "inputs" / "audio" / "reference_korean_30s.wav"
OUT_ROOT = PROJECT_ROOT / "outputs" / "stage4_videos"

VARIANTS: dict[str, Path] = {
    "hero": PROJECT_ROOT / "inputs" / "photos" / "hero.png",
    "test_2": PROJECT_ROOT / "inputs" / "photos" / "test_2.png",
}

MODELS: dict[str, dict] = {
    "aurora": {
        "test_num": 4,
        "tier": "paid-commodity",
        "slug": "fal-ai/creatify/aurora",
        "out_dir": "aurora_720p",
        "fixed_args": {"resolution": "720p"},
        "price_per_sec_usd": 0.14,
    },
    "omnihuman": {
        "test_num": 5,
        "tier": "paid-premium-emotional",
        "slug": "fal-ai/bytedance/omnihuman/v1.5",
        "out_dir": "omnihuman_v1_5",
        "fixed_args": {"resolution": "720p"},
        "price_per_sec_usd": 0.16,
    },
    "kling": {
        "test_num": 6,
        "tier": "paid-premium-cinematic",
        "slug": "fal-ai/kling-video/ai-avatar/v2/pro",
        "out_dir": "kling_avatar_v2_pro",
        "fixed_args": {},
        "price_per_sec_usd": 0.115,
    },
}


def wav_duration_seconds(path: Path) -> float:
    with contextlib.closing(wave.open(str(path), "rb")) as w:
        return w.getnframes() / w.getframerate()


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def run_one(model_key: str, variant: str, *, dry_run: bool, force: bool) -> None:
    if model_key not in MODELS:
        sys.exit(f"unknown model '{model_key}'. choices: {', '.join(MODELS)}")
    if variant not in VARIANTS:
        sys.exit(f"unknown variant '{variant}'. choices: {', '.join(VARIANTS)}")
    cfg = MODELS[model_key]
    image_path = VARIANTS[variant]

    if not image_path.exists():
        sys.exit(f"missing input: {image_path}")
    if not AUDIO_PATH.exists():
        sys.exit(f"missing input: {AUDIO_PATH}")

    audio_seconds = wav_duration_seconds(AUDIO_PATH)
    est_cost_usd = audio_seconds * cfg["price_per_sec_usd"]

    out_dir = OUT_ROOT / cfg["out_dir"] / variant
    out_video = out_dir / f"{variant}_output.mp4"
    out_meta = out_dir / "_meta.json"

    print(f"=== Test {cfg['test_num']}: {model_key} ({cfg['tier']}) [variant={variant}] ===")
    print(f"  slug:           {cfg['slug']}")
    print(f"  image:          {image_path}")
    print(f"  audio:          {AUDIO_PATH}  ({audio_seconds:.2f}s)")
    print(f"  fixed_args:     {cfg['fixed_args']}")
    print(f"  output:         {out_video}")
    print(f"  est cost:       ${est_cost_usd:.2f}  (@ ${cfg['price_per_sec_usd']}/sec)")

    if out_video.exists() and not force:
        print(f"  SKIP: {out_video} already exists. Pass --force to re-run.")
        return

    if dry_run:
        print("  DRY RUN — exiting before fal call.")
        return

    out_dir.mkdir(parents=True, exist_ok=True)

    load_dotenv(PROJECT_ROOT / ".env")
    if not os.environ.get("FAL_KEY"):
        sys.exit("FAL_KEY not set. Add it to .env at project root.")

    print("  uploading image + audio to fal...")
    image_url = fal_client.upload_file(str(image_path))
    audio_url = fal_client.upload_file(str(AUDIO_PATH))

    arguments = {"image_url": image_url, "audio_url": audio_url, **cfg["fixed_args"]}

    started_iso = now_iso()
    t0 = time.monotonic()
    print(f"  submitting to {cfg['slug']}...")
    result = fal_client.subscribe(
        cfg["slug"],
        arguments=arguments,
        with_logs=True,
        on_queue_update=lambda update: _print_queue_update(update),
    )
    wall_seconds = time.monotonic() - t0
    completed_iso = now_iso()
    print(f"  done in {wall_seconds:.1f}s wall.")

    video_url = result["video"]["url"]
    print(f"  downloading {video_url} -> {out_video}")
    video_bytes = requests.get(video_url, timeout=300).content
    out_video.write_bytes(video_bytes)

    billed_seconds = result.get("duration")
    billed_usd = (
        billed_seconds * cfg["price_per_sec_usd"]
        if isinstance(billed_seconds, (int, float))
        else None
    )

    meta = {
        "test_num": cfg["test_num"],
        "tier": cfg["tier"],
        "model_key": model_key,
        "variant": variant,
        "fal_slug": cfg["slug"],
        "image_path": str(image_path.relative_to(PROJECT_ROOT)),
        "audio_path": str(AUDIO_PATH.relative_to(PROJECT_ROOT)),
        "audio_duration_sec": round(audio_seconds, 3),
        "requested_args": cfg["fixed_args"],
        "fal_response_duration_sec": billed_seconds,
        "wall_seconds": round(wall_seconds, 1),
        "video_url": video_url,
        "video_bytes": len(video_bytes),
        "est_cost_usd": round(est_cost_usd, 4),
        "billed_cost_usd": round(billed_usd, 4) if billed_usd is not None else None,
        "price_per_sec_usd": cfg["price_per_sec_usd"],
        "generation_started_iso": started_iso,
        "generation_completed_iso": completed_iso,
    }
    out_meta.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n")
    print(f"  meta:           {out_meta}")
    if billed_usd is not None:
        print(f"  billed:         ${billed_usd:.2f}  ({billed_seconds}s @ ${cfg['price_per_sec_usd']}/sec)")


def _print_queue_update(update) -> None:
    name = type(update).__name__
    if name == "InProgress":
        for log in (getattr(update, "logs", None) or []):
            msg = log.get("message") if isinstance(log, dict) else str(log)
            if msg:
                print(f"    [{name}] {msg}")
    else:
        print(f"    [{name}]")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("model", choices=list(MODELS), help="which model to run")
    p.add_argument("--variant", choices=list(VARIANTS), default="hero",
                   help="input image variant (default: hero)")
    p.add_argument("--dry-run", action="store_true", help="print plan + cost, don't submit")
    p.add_argument("--force", action="store_true", help="re-run even if output exists")
    args = p.parse_args()
    run_one(args.model, args.variant, dry_run=args.dry_run, force=args.force)


if __name__ == "__main__":
    main()
