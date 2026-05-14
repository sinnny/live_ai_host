"""Stage 5.8 — Atlas packing + config emission.

Per FSD §4.2: 6-column grid of 1024px sprites = 6144x4096 PNG. Layer states
laid out in canonical FSD order. Emits atlas.png, config.json, manifest.yaml,
and copies the trained LoRA next to the atlas for reproducibility.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from PIL import Image

from .config import Config
from .manifest import file_sha, write_manifest


LAYER_ORDER = ["expression", "mouth", "tail", "ears"]


# z_order + anchor canvas position (must match stage_normalize.ANCHORS)
LAYER_META = {
    "expression": {"z_order": 0, "anchor": {"x": 512, "y": 512}},
    "tail":       {"z_order": 1, "anchor": {"x": 200, "y": 700}},
    "ears":       {"z_order": 2, "anchor": {"x": 512, "y": 350}},
    "mouth":      {"z_order": 3, "anchor": {"x": 512, "y": 600}},
}


def _atlas_position(idx: int, columns: int) -> tuple[int, int]:
    """Return (col, row) for sprite index idx in a row-major grid."""
    return idx % columns, idx // columns


def run(cfg: Config, *, force: bool = False) -> dict:
    src_root = cfg.stage_dir("07_normalized")
    if not src_root.exists():
        raise FileNotFoundError(f"Normalized sprites missing at {src_root}. Run `normalize` first.")

    cfg.final_atlas_dir.mkdir(parents=True, exist_ok=True)
    atlas_png = cfg.final_atlas_dir / "atlas.png"
    atlas_cfg = cfg.final_atlas_dir / "config.json"
    manifest_yaml = cfg.final_atlas_dir / "manifest.yaml"
    lora_dst = cfg.final_atlas_dir / "lora.safetensors"

    if atlas_png.exists() and atlas_cfg.exists() and not force:
        return {"atlas": str(atlas_png), "config": str(atlas_cfg), "skipped": True}

    sprite_size = cfg.canvas.sprite_size
    cols = cfg.canvas.atlas_columns

    # Collect sprites in canonical order
    ordered: list[tuple[str, str, Path]] = []
    for layer in LAYER_ORDER:
        for state in cfg.sprite_layers[layer]["states"]:
            p = src_root / layer / f"{state}.png"
            if not p.exists():
                raise FileNotFoundError(f"Missing normalized sprite: {p}")
            ordered.append((layer, state, p))

    rows = (len(ordered) + cols - 1) // cols
    atlas = Image.new("RGBA", (cols * sprite_size, rows * sprite_size), (0, 0, 0, 0))

    config: dict = {
        "schema_version": 1,
        "character": cfg.character_name,
        "sprite_size": sprite_size,
        "atlas_image": "atlas.png",
        "atlas_columns": cols,
        "layers": {},
        "composition_order": ["expression", "tail", "ears", "mouth"],
        "default_state": {
            "expression": "neutral",
            "mouth": "closed",
            "tail": "relaxed",
            "ears": "up",
        },
    }

    for layer in LAYER_ORDER:
        config["layers"][layer] = {
            **LAYER_META[layer],
            "states": {},
        }

    for idx, (layer, state, src_path) in enumerate(ordered):
        col, row = _atlas_position(idx, cols)
        sprite = Image.open(src_path).convert("RGBA")
        if sprite.size != (sprite_size, sprite_size):
            sprite = sprite.resize((sprite_size, sprite_size), Image.LANCZOS)
        atlas.paste(sprite, (col * sprite_size, row * sprite_size), sprite)
        config["layers"][layer]["states"][state] = {"atlas_pos": [col, row]}

    atlas.save(atlas_png, format="PNG", optimize=True)
    atlas_cfg.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")

    # Copy LoRA next to atlas for reproducibility
    lora_src = cfg.stage_dir("04_lora_train") / "checkpoints" / "final.safetensors"
    if lora_src.exists():
        # Resolve symlink to its real file to avoid a dangling symlink in the atlas dir
        real = lora_src.resolve()
        shutil.copyfile(real, lora_dst)

    # Manifest
    write_manifest(
        config_path=Path(__file__).resolve().parent.parent / f"{cfg.character_name}_config.yaml",
        bible_path=cfg.bible_path,
        base_model=cfg.base_model,
        seed=cfg.seed,
        lora_metadata={
            "trained_for_steps": cfg.lora_training.steps,
            "rank": cfg.lora_training.rank,
            "dataset_size": cfg.lora_training.augmentation_count,
            "checkpoint_sha": file_sha(lora_dst) if lora_dst.exists() else "missing",
        },
        generation_metadata={
            "total_raw_sprites": len(ordered),
            "atlas_columns": cols,
            "atlas_rows": rows,
            "atlas_size_px": [cols * sprite_size, rows * sprite_size],
        },
        post_processing_metadata={
            "alpha_threshold": cfg.canvas.alpha_threshold,
            "anchor_method": "alpha-centroid (expression) / alpha-bbox-edge (overlays)",
            "atlas_packing_method": "layered_v1",
        },
        out_path=manifest_yaml,
    )

    return {
        "atlas": str(atlas_png),
        "config": str(atlas_cfg),
        "manifest": str(manifest_yaml),
        "lora": str(lora_dst) if lora_dst.exists() else None,
        "size_px": [cols * sprite_size, rows * sprite_size],
        "size_bytes": atlas_png.stat().st_size,
    }
