"""Stage 5.5 — Layered sprite batch generation.

Two-pass generation:
  - Pass 1: expression layer (10 sprites) WITH the trained Daramzzi LoRA so
    the full-character sprites read as Daramzzi specifically.
  - Pass 2: mouth/tail/ears layers (14 sprites) WITHOUT the LoRA — base
    Qwen-Image only. The LoRA's training distribution is full-character-only,
    which makes it override "ISOLATED mouth on white background" prompts and
    produce full characters. Base Qwen-Image respects the isolation prompts
    cleanly. Style coherence comes from the prompts themselves (chestnut fur,
    cream highlights, 3D rendered mascot aesthetic), not from the LoRA.

Idempotent: skips any sprite whose PNG already exists. Supports targeted
regeneration via `only` (list of "layer/state" strings).
"""

from __future__ import annotations

from pathlib import Path

from .config import Config
from .prompts import load_prompts
from .qwen_pipe import generate, get_pipeline


MAX_RETRIES_PER_SPRITE = 3  # FSD §5.5
TOTAL_RETRY_BUDGET = 12     # FSD §5.5

# Layers that should be generated with the Daramzzi LoRA loaded.
# All other layers (mouth, tail, ears) use base Qwen-Image only — see
# module docstring for the why.
LORA_LAYERS = {"expression"}


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

    qwen = book.qwen_image_settings
    out_root = cfg.stage_dir("05_raw_sprites")
    out_root.mkdir(parents=True, exist_ok=True)

    only_set = set(only) if only else None
    written: list[str] = []

    # Bucket the requested sprites by whether they need the LoRA.
    expression_sprites = []
    overlay_sprites = []
    for sp in book.all_sprites():
        key = f"{sp.layer}/{sp.state}"
        if only_set is not None and key not in only_set:
            continue
        target = out_root / sp.layer / f"{sp.state}.png"
        if target.exists() and not force:
            written.append(str(target))
            continue
        if sp.layer in LORA_LAYERS:
            expression_sprites.append(sp)
        else:
            overlay_sprites.append(sp)

    def _emit(pipe, sp) -> None:
        layer_dir = out_root / sp.layer
        layer_dir.mkdir(parents=True, exist_ok=True)
        target = layer_dir / f"{sp.state}.png"
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

    # Pass 1: expression sprites with LoRA
    if expression_sprites:
        pipe_lora = get_pipeline(cfg.base_model, lora_safetensors=lora_path)
        for sp in expression_sprites:
            _emit(pipe_lora, sp)

    # Pass 2: overlay sprites with NO LoRA — base Qwen-Image only.
    # get_pipeline caches by (base_model, lora_path) tuple; passing
    # lora_safetensors=None forces a reload of the base pipeline.
    if overlay_sprites:
        pipe_base = get_pipeline(cfg.base_model, lora_safetensors=None)
        for sp in overlay_sprites:
            _emit(pipe_base, sp)

    return {
        "output_dir": str(out_root),
        "sprite_count": len(written),
        "sprites": written,
        "expression_pass_count": len(expression_sprites),
        "overlay_pass_count": len(overlay_sprites),
    }
