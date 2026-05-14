"""Stage 5.5 — Layered sprite batch generation (24 sprites with LoRA).

Generates all 24 sprites with the Daramzzi LoRA loaded. Idempotent: skips any
sprite whose PNG already exists. Supports targeted regeneration via
`only` (list of "layer/state" strings).
"""

from __future__ import annotations

from pathlib import Path

from .config import Config
from .prompts import load_prompts
from .qwen_pipe import generate, get_pipeline


MAX_RETRIES_PER_SPRITE = 3  # FSD §5.5
TOTAL_RETRY_BUDGET = 12     # FSD §5.5


def run(
    cfg: Config,
    *,
    only: list[str] | None = None,
    force: bool = False,
) -> dict:
    book = load_prompts(cfg.stage_dir("01_brief") / "prompts.json")
    lora_path = cfg.stage_dir("04_lora_train") / "checkpoints" / "final.safetensors"
    if not lora_path.exists():
        raise FileNotFoundError(
            f"LoRA checkpoint missing at {lora_path}. Run stage `lora-train` first."
        )

    pipe = get_pipeline(cfg.base_model, lora_safetensors=lora_path)
    qwen = book.qwen_image_settings

    out_root = cfg.stage_dir("05_raw_sprites")
    out_root.mkdir(parents=True, exist_ok=True)

    only_set = set(only) if only else None
    written: list[str] = []

    for sp in book.all_sprites():
        key = f"{sp.layer}/{sp.state}"
        if only_set is not None and key not in only_set:
            continue

        layer_dir = out_root / sp.layer
        layer_dir.mkdir(parents=True, exist_ok=True)
        target = layer_dir / f"{sp.state}.png"

        if target.exists() and not force:
            written.append(str(target))
            continue

        img = generate(
            pipe,
            positive=sp.positive,
            negative=sp.negative,
            seed=cfg.seed + sp.index,
            width=int(qwen.get("width", cfg.canvas.sprite_size)),
            height=int(qwen.get("height", cfg.canvas.sprite_size)),
            steps=int(qwen.get("num_inference_steps", 50)),
            guidance=float(qwen.get("guidance_scale", 7.5)),
        )
        img.save(target, format="PNG")
        written.append(str(target))

    return {
        "output_dir": str(out_root),
        "sprite_count": len(written),
        "sprites": written,
    }
