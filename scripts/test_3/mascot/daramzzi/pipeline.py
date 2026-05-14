"""make_mascot pipeline CLI — Daramzzi atlas generation.

Source of truth: docs/phase_0_v2/fsd/make_mascot.md (§5 stages, §6 commands).
Stages are idempotent: re-running with the same inputs and no `--force` skips
work already done.
"""

from __future__ import annotations

import json
import sys
import time
import traceback
from pathlib import Path

import click

from lib import (
    config as cfg_mod,
    stage_alpha,
    stage_brief,
    stage_lora_dataset,
    stage_lora_train,
    stage_normalize,
    stage_pack,
    stage_seed,
    stage_sprites,
    status as status_mod,
)


def _emit(payload: dict, started: float) -> None:
    payload = {**payload, "wall_clock_seconds": round(time.time() - started, 2)}
    click.echo(json.dumps(payload, ensure_ascii=False, indent=2, default=str))


def _load(config_path: str):
    return cfg_mod.load_config(config_path)


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
def cli() -> None:
    """make_mascot pipeline. See docs/phase_0_v2/fsd/make_mascot.md."""


@cli.command()
@click.option(
    "--output", "out",
    default="daramzzi_config.yaml",
    show_default=True,
    type=click.Path(dir_okay=False),
)
@click.option("--force/--no-force", default=False)
def init(out: str, force: bool) -> None:
    """Emit the FSD §3.2 default config to `daramzzi_config.yaml`."""
    target = Path(out)
    if target.exists() and not force:
        click.echo(f"{target} already exists. Pass --force to overwrite.", err=True)
        sys.exit(1)
    target.write_text(cfg_mod.DEFAULT_CONFIG_YAML, encoding="utf-8")
    click.echo(f"Wrote {target}")


@cli.command()
@click.option("--config", "config_path", default="daramzzi_config.yaml", show_default=True)
def status(config_path: str) -> None:
    """Show which stages have produced their outputs."""
    cfg = _load(config_path)
    click.echo(status_mod.report(cfg))


def _run_stage(name: str, fn) -> None:
    started = time.time()
    try:
        result = fn()
    except Exception as exc:  # noqa: BLE001 — orchestration boundary
        traceback.print_exc()
        click.echo(json.dumps({"stage": name, "status": "error", "error": str(exc)}, indent=2), err=True)
        sys.exit(1)
    _emit({"stage": name, "status": "success", "result": result}, started)


@cli.command()
@click.option("--config", "config_path", default="daramzzi_config.yaml", show_default=True)
def brief(config_path: str) -> None:
    """Stage 5.1 — copy static prompts.json into work dir (no Claude API call)."""
    cfg = _load(config_path)
    _run_stage("5.1 brief", lambda: stage_brief.run(cfg))


@cli.command()
@click.option("--config", "config_path", default="daramzzi_config.yaml", show_default=True)
@click.option("--new-seed", type=int, default=None, help="Override config seed for this attempt.")
@click.option("--force/--no-force", default=False)
def seed(config_path: str, new_seed: int | None, force: bool) -> None:
    """Stage 5.2 — generate the canonical seed sprite (founder approval gate)."""
    cfg = _load(config_path)
    _run_stage("5.2 seed", lambda: stage_seed.run(cfg, new_seed=new_seed, force=force))


@cli.command("lora-dataset")
@click.option("--config", "config_path", default="daramzzi_config.yaml", show_default=True)
@click.option("--force/--no-force", default=False)
def lora_dataset_cmd(config_path: str, force: bool) -> None:
    """Stage 5.3 — generate `augmentation_count` LoRA training images."""
    cfg = _load(config_path)
    _run_stage("5.3 lora-dataset", lambda: stage_lora_dataset.run(cfg, force=force))


@cli.command("lora-train")
@click.option("--config", "config_path", default="daramzzi_config.yaml", show_default=True)
@click.option("--force/--no-force", default=False)
def lora_train_cmd(config_path: str, force: bool) -> None:
    """Stage 5.4 — train Daramzzi LoRA via AI-Toolkit."""
    cfg = _load(config_path)
    _run_stage("5.4 lora-train", lambda: stage_lora_train.run(cfg, force=force))


@cli.command()
@click.option("--config", "config_path", default="daramzzi_config.yaml", show_default=True)
@click.option("--only", multiple=True, help="layer/state to regenerate; repeatable.")
@click.option("--force/--no-force", default=False)
def sprites(config_path: str, only: tuple[str, ...], force: bool) -> None:
    """Stage 5.5 — generate the 24 layered sprites (with LoRA)."""
    cfg = _load(config_path)
    _run_stage("5.5 sprites", lambda: stage_sprites.run(cfg, only=list(only) or None, force=force))


@cli.command()
@click.option("--config", "config_path", default="daramzzi_config.yaml", show_default=True)
@click.option("--force/--no-force", default=False)
def alpha(config_path: str, force: bool) -> None:
    """Stage 5.6 — BiRefNet background removal on all 24 sprites."""
    cfg = _load(config_path)
    _run_stage("5.6 alpha", lambda: stage_alpha.run(cfg, force=force))


@cli.command()
@click.option("--config", "config_path", default="daramzzi_config.yaml", show_default=True)
@click.option("--force/--no-force", default=False)
def normalize(config_path: str, force: bool) -> None:
    """Stage 5.7 — anchor-align sprites to canonical canvas positions."""
    cfg = _load(config_path)
    _run_stage("5.7 normalize", lambda: stage_normalize.run(cfg, force=force))


@cli.command()
@click.option("--config", "config_path", default="daramzzi_config.yaml", show_default=True)
@click.option("--force/--no-force", default=False)
def pack(config_path: str, force: bool) -> None:
    """Stage 5.8 — pack atlas.png, emit config.json + manifest.yaml + lora copy."""
    cfg = _load(config_path)
    _run_stage("5.8 pack", lambda: stage_pack.run(cfg, force=force))


_ALL_STAGES = [
    ("5.1 brief", "brief"),
    ("5.2 seed", "seed"),
    ("5.3 lora-dataset", "lora-dataset"),
    ("5.4 lora-train", "lora-train"),
    ("5.5 sprites", "sprites"),
    ("5.6 alpha", "alpha"),
    ("5.7 normalize", "normalize"),
    ("5.8 pack", "pack"),
]


@cli.command("run-all")
@click.option("--config", "config_path", default="daramzzi_config.yaml", show_default=True)
@click.option(
    "--start",
    type=click.Choice([name for _, name in _ALL_STAGES]),
    default="brief",
    show_default=True,
    help="Stage to start from (later stages always run).",
)
@click.option("--force/--no-force", default=False)
def run_all(config_path: str, start: str, force: bool) -> None:
    """Run every stage in order starting at --start.

    Note: Stage 5.2 (seed) is a founder-approval gate. Re-run after manual
    review with `--start=lora-dataset` to continue.
    """
    cfg = _load(config_path)

    stage_fns = {
        "brief":        lambda: stage_brief.run(cfg),
        "seed":         lambda: stage_seed.run(cfg, force=force),
        "lora-dataset": lambda: stage_lora_dataset.run(cfg, force=force),
        "lora-train":   lambda: stage_lora_train.run(cfg, force=force),
        "sprites":      lambda: stage_sprites.run(cfg, force=force),
        "alpha":        lambda: stage_alpha.run(cfg, force=force),
        "normalize":    lambda: stage_normalize.run(cfg, force=force),
        "pack":         lambda: stage_pack.run(cfg, force=force),
    }

    started_idx = next(i for i, (_, n) in enumerate(_ALL_STAGES) if n == start)
    for display_name, key in _ALL_STAGES[started_idx:]:
        click.echo(f"\n=== {display_name} ===", err=True)
        _run_stage(display_name, stage_fns[key])


@cli.command()
@click.option("--config", "config_path", default="daramzzi_config.yaml", show_default=True)
@click.option("--stage", required=True, help="e.g. 05_raw_sprites")
@click.option("--layer", required=True, type=click.Choice(["expression", "mouth", "tail", "ears"]))
@click.option("--state", required=True)
def view(config_path: str, stage: str, layer: str, state: str) -> None:
    """Print the absolute path to a stage's sprite for quick inspection."""
    cfg = _load(config_path)
    target = cfg.stage_dir(stage) / layer / f"{state}.png"
    if not target.exists():
        click.echo(f"Not found: {target}", err=True)
        sys.exit(1)
    click.echo(str(target))


if __name__ == "__main__":
    cli()
