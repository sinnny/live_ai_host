"""Phoneme alignment via Rhubarb Lip Sync.

Per FSD docs/phase_0_v2/fsd/phoneme_alignment.md.
Output schema matches §4.1.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import click
import soundfile as sf

from lib.viseme_map import map_shape


RHUBARB_BIN = shutil.which("rhubarb") or "/opt/rhubarb/rhubarb"


def _run_rhubarb(audio: Path, raw_out: Path) -> None:
    if not Path(RHUBARB_BIN).exists():
        raise FileNotFoundError(
            f"Rhubarb binary not found at {RHUBARB_BIN}. "
            "Re-run inside the prototype-pipeline Docker image."
        )
    cmd = [
        RHUBARB_BIN,
        "-o", str(raw_out),
        "--exportFormat", "json",
        "--extendedShapes", "GHX",
        "--recognizer", "pocketSphinx",
        str(audio),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if proc.returncode != 0:
        raise RuntimeError(
            f"Rhubarb failed (exit={proc.returncode}). stderr={proc.stderr[-500:]}"
        )


def _convert(raw: dict, audio_path: Path, audio_duration_ms: int) -> dict:
    raw_cues = raw.get("mouthCues", [])
    frames = []
    for cue in raw_cues:
        start_ms = int(round(float(cue["start"]) * 1000))
        end_ms = int(round(float(cue["end"]) * 1000))
        viseme = map_shape(cue["value"])
        frames.append({"start_ms": start_ms, "end_ms": end_ms, "viseme": viseme})

    # Merge consecutive same-viseme frames + skip transitions <60ms
    merged: list[dict] = []
    for f in frames:
        if merged and merged[-1]["viseme"] == f["viseme"]:
            merged[-1]["end_ms"] = f["end_ms"]
            continue
        if merged and (f["end_ms"] - f["start_ms"]) < 60:
            # Promote: extend previous
            merged[-1]["end_ms"] = f["end_ms"]
            continue
        merged.append(dict(f))

    return {
        "schema_version": 1,
        "audio_file": str(audio_path),
        "audio_duration_ms": audio_duration_ms,
        "alignment_engine": "rhubarb",
        "alignment_engine_version": "1.13.0",
        "frames": merged,
    }


def _amplitude_fallback(audio_path: Path) -> dict:
    """Cheap amplitude-envelope fallback per FSD §2.2."""
    audio, sr = sf.read(str(audio_path))
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    audio_duration_ms = int(round(1000 * len(audio) / sr))

    # 50ms windows, threshold-driven open/close
    win = int(sr * 0.05)
    frames: list[dict] = []
    cursor_ms = 0
    last_open = None
    for i in range(0, len(audio), win):
        chunk = audio[i:i + win]
        rms = float((chunk ** 2).mean() ** 0.5) if chunk.size else 0.0
        open_ = rms > 0.02
        viseme = "aa" if open_ else "closed"
        if frames and frames[-1]["viseme"] == viseme:
            frames[-1]["end_ms"] = cursor_ms + int(round(1000 * win / sr))
        else:
            frames.append({
                "start_ms": cursor_ms,
                "end_ms": cursor_ms + int(round(1000 * win / sr)),
                "viseme": viseme,
            })
        cursor_ms += int(round(1000 * win / sr))
    return {
        "schema_version": 1,
        "audio_file": str(audio_path),
        "audio_duration_ms": audio_duration_ms,
        "alignment_engine": "amplitude-envelope",
        "alignment_engine_version": "fallback",
        "frames": frames,
    }


@click.command()
@click.option("--audio", "audio_path", required=True, type=click.Path(exists=True, dir_okay=False))
@click.option("--output", "out_path", required=True, type=click.Path(dir_okay=False))
@click.option("--engine", type=click.Choice(["rhubarb", "amplitude"]), default="rhubarb")
def main(audio_path: str, out_path: str, engine: str) -> None:
    audio = Path(audio_path)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    samples, sr = sf.read(str(audio))
    audio_duration_ms = int(round(1000 * len(samples) / sr))

    if engine == "amplitude":
        result = _amplitude_fallback(audio)
    else:
        raw_path = out.with_suffix(".rhubarb_raw.json")
        try:
            _run_rhubarb(audio, raw_path)
            raw = json.loads(raw_path.read_text(encoding="utf-8"))
            result = _convert(raw, audio, audio_duration_ms)
        except Exception as exc:  # noqa: BLE001
            click.echo(f"[phoneme_alignment] Rhubarb failed → amplitude fallback: {exc}", err=True)
            result = _amplitude_fallback(audio)

    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    click.echo(json.dumps({
        "output": str(out),
        "frame_count": len(result["frames"]),
        "engine": result["alignment_engine"],
        "duration_ms": result["audio_duration_ms"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
