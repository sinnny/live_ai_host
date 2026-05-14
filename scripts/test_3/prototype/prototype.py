"""Prototype orchestrator — wires TTS → phoneme → renderer → encode for one clip.

Per FSD docs/phase_0_v2/fsd/orchestrator.md. CLI:
  prototype.py render     — full pipeline
  prototype.py validate   — schema-check a script (no execution)
  prototype.py voice-ref  — delegate to tts.py voice-ref
  prototype.py status     — show stage completion for an output dir
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

import click
import yaml

from lib.schema import load_script, validate as validate_script


HERE = Path(__file__).resolve().parent
DEFAULT_RENDERER_CONFIG = HERE.parent / "renderer" / "renderer_config.json"


def _sha(path: Path) -> str:
    if not path.exists():
        return "missing"
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return f"sha256:{h.hexdigest()}"


def _run(args: list[str], log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as logf:
        proc = subprocess.run(args, stdout=logf, stderr=subprocess.STDOUT)
    if proc.returncode != 0:
        raise RuntimeError(
            f"Stage failed (exit={proc.returncode}). See {log_path}."
        )


def _stage_done(check: bool) -> str:
    return "success" if check else "skipped"


@click.group()
def cli() -> None:
    """Prototype orchestrator. See docs/phase_0_v2/fsd/orchestrator.md."""


@cli.command()
@click.option("--script", "script_path", required=True, type=click.Path(exists=True, dir_okay=False))
def validate(script_path: str) -> None:
    """Validate a script JSON against script_schema.json."""
    data = load_script(script_path)
    click.echo(json.dumps({
        "valid": True,
        "title": data.get("title"),
        "language": data.get("language"),
        "segment_count": len(data.get("segments", [])),
    }, ensure_ascii=False, indent=2))


@cli.command("voice-ref")
@click.option("--output", "out", required=True, type=click.Path(dir_okay=False))
@click.option("--text", default=None, help="Korean reference text; default in tts.py")
def voice_ref(out: str, text: str | None) -> None:
    """Delegate to tts.py voice-ref."""
    args = [sys.executable, str(HERE / "tts.py"), "voice-ref", "--output", out]
    if text:
        args += ["--text", text]
    proc = subprocess.run(args)
    sys.exit(proc.returncode)


@cli.command()
@click.option("--script", "script_path", required=True, type=click.Path(exists=True, dir_okay=False))
@click.option("--atlas", "atlas_dir", required=True, type=click.Path(file_okay=False))
@click.option("--voice", "voice_path", required=True, type=click.Path(exists=True, dir_okay=False))
@click.option("--output-dir", "out_dir", required=True, type=click.Path(file_okay=False))
@click.option("--renderer-config", default=str(DEFAULT_RENDERER_CONFIG), show_default=True,
              type=click.Path(exists=True, dir_okay=False))
@click.option("--encoder-preset", type=click.Choice(["fast", "slow"]), default="slow", show_default=True)
@click.option("--fps", type=int, default=60, show_default=True)
@click.option("--resume/--no-resume", default=False, help="Skip stages with existing output.")
@click.option("--dry-run/--no-dry-run", default=False)
@click.option("--keep-frames/--no-keep-frames", default=False,
              help="Preserve PNG frame sequence after encode (debugging).")
def render(script_path, atlas_dir, voice_path, out_dir, renderer_config,
           encoder_preset, fps, resume, dry_run, keep_frames):
    """Run the full TTS → phoneme → render → encode pipeline."""
    script_p = Path(script_path).resolve()
    atlas_p = Path(atlas_dir).resolve()
    voice_p = Path(voice_path).resolve()
    out = Path(out_dir).resolve()
    renderer_cfg = Path(renderer_config).resolve()

    # Stage 1: validate
    validate_script(load_script(script_p))
    atlas_png = atlas_p / "atlas.png"
    atlas_config = atlas_p / "config.json"
    if not atlas_png.exists() or not atlas_config.exists():
        raise click.ClickException(f"Atlas directory missing required files: {atlas_p}")

    plan = {
        "clip_name": out.name,
        "script": str(script_p),
        "atlas": str(atlas_p),
        "voice": str(voice_p),
        "output_dir": str(out),
        "renderer_config": str(renderer_cfg),
        "encoder_preset": encoder_preset,
        "fps": fps,
        "resume": resume,
    }
    if dry_run:
        click.echo(json.dumps({"dry_run": True, "plan": plan}, ensure_ascii=False, indent=2))
        return

    out.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(script_p, out / "input_script.json")
    (out / "logs").mkdir(exist_ok=True)

    started_at = dt.datetime.now(dt.timezone.utc).isoformat()
    overall_start = time.time()

    manifest = {
        "schema_version": 1,
        "clip_name": out.name,
        "generated_at": started_at,
        "inputs": {
            "script": {"path": str(script_p), "sha256": _sha(script_p)},
            "atlas": {
                "path": str(atlas_p),
                "atlas_png_sha256": _sha(atlas_png),
                "config_sha256": _sha(atlas_config),
            },
            "voice": {"path": str(voice_p), "sha256": _sha(voice_p)},
            "renderer_config": {"path": str(renderer_cfg), "sha256": _sha(renderer_cfg)},
        },
        "stages": {},
    }

    # Stage 3: TTS
    tts_dir = out / "tts"
    tts_manifest = tts_dir / "manifest.json"
    started = time.time()
    if resume and tts_manifest.exists() and (tts_dir / "audio.wav").exists():
        status = "skipped"
    else:
        _run([
            sys.executable, str(HERE / "tts.py"), "synthesize",
            "--script", str(script_p),
            "--voice", str(voice_p),
            "--output-dir", str(tts_dir),
            *(["--resume"] if resume else []),
        ], out / "logs" / "tts.log")
        status = "success"
    manifest["stages"]["tts"] = {
        "status": status,
        "duration_seconds": round(time.time() - started, 2),
        "output": str(tts_dir / "audio.wav"),
    }

    # Stage 4: Phoneme alignment
    phoneme_dir = out / "phonemes"
    alignment_json = phoneme_dir / "alignment.json"
    started = time.time()
    if resume and alignment_json.exists():
        status = "skipped"
    else:
        _run([
            sys.executable, str(HERE / "phoneme_alignment.py"),
            "--audio", str(tts_dir / "audio.wav"),
            "--output", str(alignment_json),
        ], out / "logs" / "phoneme.log")
        status = "success"
    manifest["stages"]["phonemes"] = {
        "status": status,
        "duration_seconds": round(time.time() - started, 2),
        "output": str(alignment_json),
    }

    # Stage 5: Render
    frames_dir = out / "frames"
    started = time.time()
    expected_frames = None
    if alignment_json.exists():
        align = json.loads(alignment_json.read_text(encoding="utf-8"))
        expected_frames = int(round(align["audio_duration_ms"] * fps / 1000))
    actual_frames = len(list(frames_dir.glob("frame_*.png"))) if frames_dir.exists() else 0
    if resume and expected_frames and actual_frames >= expected_frames:
        status = "skipped"
    else:
        _run([
            sys.executable, str(HERE / "renderer_cli.py"),
            "--atlas-dir", str(atlas_p),
            "--script", str(script_p),
            "--audio", str(tts_dir / "audio.wav"),
            "--alignment", str(alignment_json),
            "--tts-manifest", str(tts_manifest),
            "--frames-dir", str(frames_dir),
            "--renderer-config", str(renderer_cfg),
            "--fps", str(fps),
        ], out / "logs" / "render.log")
        actual_frames = len(list(frames_dir.glob("frame_*.png")))
        status = "success"
    manifest["stages"]["render"] = {
        "status": status,
        "duration_seconds": round(time.time() - started, 2),
        "frame_count": actual_frames,
        "output": str(frames_dir),
    }

    # Stage 6: Encode
    output_mp4 = out / "output.mp4"
    started = time.time()
    _run([
        sys.executable, str(HERE / "encoder.py"),
        "--frames-dir", str(frames_dir),
        "--audio", str(tts_dir / "audio.wav"),
        "--output", str(output_mp4),
        "--fps", str(fps),
        "--preset", encoder_preset,
    ], out / "logs" / "encode.log")
    manifest["stages"]["encode"] = {
        "status": "success",
        "duration_seconds": round(time.time() - started, 2),
        "output": str(output_mp4),
        "size_bytes": output_mp4.stat().st_size,
    }

    manifest["totals"] = {
        "wall_clock_seconds": round(time.time() - overall_start, 2),
    }
    (out / "manifest.yaml").write_text(
        yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )

    if not keep_frames:
        shutil.rmtree(frames_dir, ignore_errors=True)

    click.echo(json.dumps({
        "output_mp4": str(output_mp4),
        "manifest": str(out / "manifest.yaml"),
        "wall_clock_seconds": manifest["totals"]["wall_clock_seconds"],
    }, ensure_ascii=False, indent=2))


@cli.command()
@click.option("--run-dir", required=True, type=click.Path(file_okay=False))
def status(run_dir: str) -> None:
    """Show stage completion for a prototype run directory."""
    p = Path(run_dir)
    rows = []
    checks = [
        ("input_script.json", p / "input_script.json"),
        ("tts/audio.wav", p / "tts" / "audio.wav"),
        ("tts/manifest.json", p / "tts" / "manifest.json"),
        ("phonemes/alignment.json", p / "phonemes" / "alignment.json"),
        ("output.mp4", p / "output.mp4"),
        ("manifest.yaml", p / "manifest.yaml"),
    ]
    for name, path in checks:
        rows.append({"path": name, "exists": path.exists()})
    click.echo(json.dumps({"run_dir": str(p), "checks": rows}, indent=2))


if __name__ == "__main__":
    cli()
