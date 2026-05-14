"""Stage 5.2 — Seed generation (founder approval gate).

Generates the canonical "neutral pose, mouth closed, tail relaxed, ears up"
sprite at 1024x1024. Idempotent: skips if `seed.png` exists unless `force=True`.

The actual approval gate (visual review by founder) lives outside the pipeline.
This module just produces the image; the checklist tracks approval state.
"""

from __future__ import annotations

from pathlib import Path

from .config import Config
from .prompts import load_prompts
from .qwen_pipe import generate, get_pipeline


def run(cfg: Config, *, new_seed: int | None = None, force: bool = False) -> dict:
    out_dir = cfg.stage_dir("02_seed")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "seed.png"

    if out_path.exists() and not force and new_seed is None:
        return {"output": str(out_path), "skipped": True}

    book = load_prompts(cfg.stage_dir("01_brief") / "prompts.json")
    seed_value = new_seed if new_seed is not None else cfg.seed

    pipe = get_pipeline(cfg.base_model)
    qwen = book.qwen_image_settings
    img = generate(
        pipe,
        positive=book.seed_prompt.positive,
        negative=book.seed_prompt.negative,
        seed=seed_value,
        width=int(qwen.get("width", cfg.canvas.sprite_size)),
        height=int(qwen.get("height", cfg.canvas.sprite_size)),
        steps=int(qwen.get("num_inference_steps", 50)),
        guidance=float(qwen.get("guidance_scale", 7.5)),
    )

    # Versioned save so retried seeds are preserved for comparison.
    versioned = out_dir / f"seed_attempt_{seed_value}.png"
    img.save(versioned, format="PNG")
    img.save(out_path, format="PNG")

    return {
        "output": str(out_path),
        "attempt": str(versioned),
        "seed": seed_value,
    }
