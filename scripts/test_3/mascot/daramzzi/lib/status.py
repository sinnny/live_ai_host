"""Pipeline status reporter — `python pipeline.py status` implementation.

Reports completion state of each stage by inspecting deterministic output paths.
"""

from __future__ import annotations

from pathlib import Path

from .config import Config


STAGES = [
    ("5.1 brief",         "01_brief/prompts.json"),
    ("5.2 seed",          "02_seed/seed.png"),
    ("5.3 lora-dataset",  "03_lora_dataset/"),
    ("5.4 lora-train",    "04_lora_train/checkpoints/final.safetensors"),
    ("5.5 sprites",       "05_raw_sprites/"),
    ("5.6 alpha",         "06_alpha/"),
    ("5.7 normalize",     "07_normalized/"),
    ("5.8 pack",          None),  # special: check final_atlas_dir
]


def report(cfg: Config) -> str:
    lines = [f"Pipeline status for {cfg.character_name}:"]
    expected_sprites = len(cfg.all_sprite_states())  # 24 for Daramzzi

    for stage, rel in STAGES:
        if stage == "5.8 pack":
            atlas_png = cfg.final_atlas_dir / "atlas.png"
            atlas_cfg = cfg.final_atlas_dir / "config.json"
            ok = atlas_png.exists() and atlas_cfg.exists()
            symbol = "✅" if ok else "⬜"
            detail = ""
            if ok:
                detail = f"  ({atlas_png.stat().st_size / 1024:.0f} KB)"
            lines.append(f"  {symbol} {stage}{detail}")
            continue

        path = cfg.output_dir / rel
        if path.is_file():
            ok = True
            detail = f"  ({path.stat().st_size / 1024:.0f} KB)"
        elif path.is_dir():
            sprite_pngs = list(path.rglob("*.png"))
            count = len(sprite_pngs)
            if stage.startswith("5.3"):
                # dataset stage — 8 augmentations expected
                ok = count >= cfg.lora_training.augmentation_count
                detail = f"  ({count} images)"
            elif stage.startswith(("5.5", "5.6", "5.7")):
                ok = count >= expected_sprites
                detail = f"  ({count}/{expected_sprites} sprites)"
            else:
                ok = count > 0
                detail = f"  ({count} files)"
        else:
            ok = False
            detail = ""
        symbol = "✅" if ok else "⬜"
        lines.append(f"  {symbol} {stage}{detail}")

    return "\n".join(lines)
