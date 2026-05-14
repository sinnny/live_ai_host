"""Stage 5.4 — LoRA training via AI-Toolkit (Ostris).

Generates an AI-Toolkit config YAML for the Daramzzi dataset, then shells out
to the toolkit's training entry point. The final checkpoint is symlinked to
`final.safetensors` for downstream stage discovery.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import yaml

from .config import Config


def _build_config(cfg: Config, dataset_dir: Path, output_dir: Path) -> dict:
    """Construct AI-Toolkit train config (Qwen-Image LoRA, character-style preset)."""
    return {
        "job": "extension",
        "config": {
            "name": f"{cfg.character_name}_lora",
            "process": [
                {
                    "type": "sd_trainer",
                    "training_folder": str(output_dir),
                    "device": "cuda:0",
                    "trigger_word": cfg.character_name,
                    "network": {
                        "type": "lora",
                        "linear": cfg.lora_training.rank,
                        "linear_alpha": cfg.lora_training.rank,
                    },
                    "save": {
                        "dtype": "float16",
                        "save_every": 250,
                        "max_step_saves_to_keep": 4,
                    },
                    "datasets": [
                        {
                            "folder_path": str(dataset_dir),
                            "caption_ext": "txt",
                            "caption_dropout_rate": 0.05,
                            "shuffle_tokens": False,
                            "cache_latents_to_disk": True,
                            "resolution": [cfg.canvas.sprite_size],
                        }
                    ],
                    "train": {
                        "batch_size": cfg.lora_training.batch_size,
                        "steps": cfg.lora_training.steps,
                        "gradient_accumulation_steps": 1,
                        "train_unet": True,
                        "train_text_encoder": False,
                        "gradient_checkpointing": True,
                        "noise_scheduler": "flowmatch",
                        "optimizer": "adamw8bit",
                        "lr": cfg.lora_training.learning_rate,
                        "ema_config": {"use_ema": True, "ema_decay": 0.99},
                        "dtype": "bf16",
                    },
                    "model": {
                        "name_or_path": cfg.base_model,
                        "is_flux": False,
                        "quantize": True,
                    },
                    "sample": {
                        "sampler": "flowmatch",
                        "sample_every": 500,
                        "width": cfg.canvas.sprite_size,
                        "height": cfg.canvas.sprite_size,
                        "prompts": [
                            f"a chubby cartoon ground squirrel intern named {cfg.character_name}, "
                            "default presenter pose, neutral attentive expression"
                        ],
                        "neg": "hamster, photorealistic, dark, edgy, sexy, low quality",
                        "seed": cfg.seed,
                        "walk_seed": True,
                        "guidance_scale": 4,
                        "sample_steps": 25,
                    },
                }
            ],
        },
        "meta": {"name": cfg.character_name, "version": "1.0"},
    }


def _find_latest_checkpoint(output_dir: Path) -> Path | None:
    """AI-Toolkit writes `<name>_<step>.safetensors` files; return the highest-step one."""
    candidates = list(output_dir.rglob("*.safetensors"))
    if not candidates:
        return None
    def step_of(p: Path) -> int:
        # Heuristic: trailing _NNNNNN before .safetensors
        stem = p.stem
        for chunk in reversed(stem.split("_")):
            if chunk.isdigit():
                return int(chunk)
        return 0
    return max(candidates, key=step_of)


def run(cfg: Config, *, force: bool = False) -> dict:
    dataset_dir = cfg.stage_dir("03_lora_dataset")
    if not dataset_dir.exists() or not any(dataset_dir.glob("*.png")):
        raise FileNotFoundError(
            f"LoRA dataset missing at {dataset_dir}. Run stage `lora-dataset` first."
        )

    out_dir = cfg.stage_dir("04_lora_train")
    out_dir.mkdir(parents=True, exist_ok=True)
    final_link = out_dir / "checkpoints" / "final.safetensors"
    final_link.parent.mkdir(parents=True, exist_ok=True)

    if final_link.exists() and not force:
        return {"output": str(final_link), "skipped": True}

    config_path = out_dir / "ai_toolkit_config.yaml"
    with config_path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(_build_config(cfg, dataset_dir, out_dir), fh, sort_keys=False)

    # Resolve the toolkit entry point. AI-Toolkit ships `run.py` at repo root.
    toolkit_root = Path(os.environ.get("AI_TOOLKIT_ROOT", "/opt/ai-toolkit"))
    run_py = toolkit_root / "run.py"
    if not run_py.exists():
        raise FileNotFoundError(
            f"AI-Toolkit not installed at {toolkit_root}. "
            "Rebuild the container or set AI_TOOLKIT_ROOT."
        )

    cmd = ["python", str(run_py), str(config_path)]
    log_path = out_dir / "train.log"
    with log_path.open("w", encoding="utf-8") as logf:
        proc = subprocess.run(cmd, stdout=logf, stderr=subprocess.STDOUT, check=False)
    if proc.returncode != 0:
        raise RuntimeError(
            f"AI-Toolkit returned exit code {proc.returncode}. See {log_path}."
        )

    latest = _find_latest_checkpoint(out_dir)
    if latest is None:
        raise RuntimeError(
            f"Training completed but no .safetensors found under {out_dir}."
        )
    # Replace any stale final
    if final_link.is_symlink() or final_link.exists():
        final_link.unlink()
    try:
        final_link.symlink_to(latest.resolve())
    except OSError:
        shutil.copyfile(latest, final_link)

    return {
        "output": str(final_link),
        "latest_checkpoint": str(latest),
        "log": str(log_path),
    }
