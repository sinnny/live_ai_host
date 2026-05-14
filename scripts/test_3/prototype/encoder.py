"""FFmpeg encoder — PNG frames + audio.wav → MP4.

Per FSD orchestrator.md §2.1.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import click


def _ffmpeg() -> str:
    bin_ = shutil.which("ffmpeg")
    if not bin_:
        raise FileNotFoundError("ffmpeg not found on PATH")
    return bin_


def encode(
    *,
    frames_dir: Path,
    audio_path: Path,
    out_path: Path,
    fps: int,
    preset: str,
) -> dict:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    preset_args = {
        "slow": ["-preset", "slow", "-crf", "18"],
        "fast": ["-preset", "veryfast", "-crf", "23", "-tune", "zerolatency"],
    }[preset]
    cmd = [
        _ffmpeg(),
        "-y",
        "-framerate", str(fps),
        "-i", str(frames_dir / "frame_%05d.png"),
        "-i", str(audio_path),
        "-c:v", "libx264",
        *preset_args,
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",
        "-movflags", "+faststart",
        str(out_path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg exit={proc.returncode}\n{proc.stderr[-1500:]}")
    return {
        "output": str(out_path),
        "size_bytes": out_path.stat().st_size,
        "preset": preset,
        "fps": fps,
    }


@click.command()
@click.option("--frames-dir", required=True, type=click.Path(file_okay=False, exists=True))
@click.option("--audio", "audio_path", required=True, type=click.Path(exists=True, dir_okay=False))
@click.option("--output", "out_path", required=True, type=click.Path(dir_okay=False))
@click.option("--fps", type=int, default=60, show_default=True)
@click.option("--preset", type=click.Choice(["fast", "slow"]), default="slow", show_default=True)
def main(frames_dir, audio_path, out_path, fps, preset):
    result = encode(
        frames_dir=Path(frames_dir),
        audio_path=Path(audio_path),
        out_path=Path(out_path),
        fps=fps,
        preset=preset,
    )
    click.echo(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
