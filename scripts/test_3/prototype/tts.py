"""TTS service — CosyVoice 2 zero-shot Korean synthesis.

Per FSD docs/phase_0_v2/fsd/tts.md. Two subcommands:
  - voice-ref:  bootstrap a Daramzzi reference WAV from CosyVoice 2's default KR voice
  - synthesize: render a script to audio.wav + per-segment WAVs + manifest.json
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import click
import numpy as np
import soundfile as sf

from lib.schema import load_script


SAMPLE_RATE = 24000
DEFAULT_REF_TEXT = (
    "안녕하세요, 쇼호스트 김다람입니다. 오늘도 잘 부탁드려요. "
    "저는 다람찌예요. 만나서 반갑습니다."
)


def _file_sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return f"sha256:{h.hexdigest()}"


def _load_cosyvoice():
    """Lazy import — CosyVoice 2 is heavy and not present locally on Mac."""
    try:
        from cosyvoice.cli.cosyvoice import CosyVoice2
    except Exception as exc:  # pragma: no cover — local dev fallback
        raise RuntimeError(
            "CosyVoice2 module not importable. Confirm /opt/cosyvoice is on "
            "PYTHONPATH and the model weights are reachable (HuggingFace cache). "
            f"Underlying error: {exc!r}"
        )
    # CosyVoice loads weights via ModelScope's snapshot_download, NOT HuggingFace.
    # The canonical ModelScope ID is `iic/CosyVoice2-0.5B` (per CosyVoice's
    # GitHub README). HuggingFace-style IDs (e.g. "FunAudioLLM/CosyVoice2-0.5B")
    # error with "The request model does not exist!".
    # Defaults: load_jit=True, load_trt=False, load_vllm=False, fp16=True.
    # We don't have TensorRT installed (filtered out of setup_runpod.sh), so
    # the default load_trt=False is what we want.
    return CosyVoice2("iic/CosyVoice2-0.5B")


@click.group()
def cli() -> None:
    """CosyVoice 2 TTS wrapper for the Daramzzi prototype."""


CROSS_LINGUAL_PROMPT = Path("/opt/cosyvoice/asset/cross_lingual_prompt.wav")
ZERO_SHOT_PROMPT = Path("/opt/cosyvoice/asset/zero_shot_prompt.wav")


@cli.command("voice-ref")
@click.option("--output", "out", required=True, type=click.Path(dir_okay=False))
@click.option("--text", default=DEFAULT_REF_TEXT, show_default=False,
              help="Korean text the reference voice will read (~10s).")
@click.option("--reference-wav", default=str(CROSS_LINGUAL_PROMPT), show_default=True,
              type=click.Path(),
              help="Reference voice WAV (bundled with CosyVoice 2). Used as the voice "
                   "timbre for cross-lingual Korean generation.")
def voice_ref(out: str, text: str, reference_wav: str) -> None:
    """One-time bootstrap: render `text` as Korean speech using CosyVoice 2's
    cross-lingual path with a bundled reference WAV as the voice timbre source.

    CosyVoice 2-0.5B has zero SFT speakers — it's purely zero-shot/cross-lingual.
    `inference_cross_lingual` takes a reference WAV (any language) and generates
    the requested text (in our case Korean) using that voice's timbre.
    """
    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    ref_path = Path(reference_wav)
    if not ref_path.exists():
        raise click.ClickException(
            f"Reference WAV not found: {ref_path}. CosyVoice 2 ships two: "
            f"{CROSS_LINGUAL_PROMPT} and {ZERO_SHOT_PROMPT}."
        )

    # Load reference at 16 kHz (what CosyVoice 2's frontend expects).
    from cosyvoice.utils.file_utils import load_wav
    prompt_speech_16k = load_wav(str(ref_path), 16000)

    model = _load_cosyvoice()
    samples = []
    for chunk in model.inference_cross_lingual(text, prompt_speech_16k, stream=False):
        samples.append(chunk["tts_speech"].cpu().numpy().flatten())
    audio = np.concatenate(samples) if samples else np.zeros(0, dtype=np.float32)

    # Normalize peak to -3 dBFS
    peak = np.max(np.abs(audio)) if audio.size else 1.0
    if peak > 0:
        audio = audio * (10 ** (-3 / 20)) / peak

    sf.write(str(out_path), audio.astype(np.float32), SAMPLE_RATE)
    sidecar = out_path.with_suffix(".txt")
    sidecar.write_text(text, encoding="utf-8")
    click.echo(json.dumps({
        "output": str(out_path),
        "duration_sec": len(audio) / SAMPLE_RATE,
        "transcript": str(sidecar),
        "reference_wav": str(ref_path),
        "inference_mode": "cross_lingual",
    }, ensure_ascii=False, indent=2))


@cli.command("synthesize")
@click.option("--script", "script_path", required=True, type=click.Path(exists=True, dir_okay=False))
@click.option("--voice", "voice_path", required=True, type=click.Path(exists=True, dir_okay=False))
@click.option("--output-dir", "out_dir", required=True, type=click.Path(file_okay=False))
@click.option("--resume/--no-resume", default=False)
def synthesize(script_path: str, voice_path: str, out_dir: str, resume: bool) -> None:
    """Render a full script to audio.wav + per-segment WAVs + manifest.json."""
    script = load_script(script_path)
    out = Path(out_dir)
    seg_dir = out / "segments"
    out.mkdir(parents=True, exist_ok=True)
    seg_dir.mkdir(parents=True, exist_ok=True)

    voice_path_p = Path(voice_path)
    sidecar = voice_path_p.with_suffix(".txt")
    prompt_text = sidecar.read_text(encoding="utf-8") if sidecar.exists() else DEFAULT_REF_TEXT

    model = _load_cosyvoice()
    # Read voice reference into model-expected format
    import torchaudio
    ref_audio, ref_sr = torchaudio.load(str(voice_path_p))
    if ref_sr != 16000:
        resampler = torchaudio.transforms.Resample(ref_sr, 16000)
        ref_audio = resampler(ref_audio)

    segments_meta = []
    full_audio: list[np.ndarray] = []
    cursor_ms = 0

    for idx, seg in enumerate(script["segments"]):
        seg_wav = seg_dir / f"seg_{idx:03d}.wav"
        speed = seg.get("speed_modifier", 1.0)

        if resume and seg_wav.exists():
            audio = sf.read(str(seg_wav))[0]
        else:
            chunks = []
            for out_chunk in model.inference_zero_shot(
                tts_text=seg["text"],
                prompt_text=prompt_text,
                prompt_speech_16k=ref_audio,
                stream=False,
                speed=speed,
            ):
                chunks.append(out_chunk["tts_speech"].cpu().numpy().flatten())
            audio = np.concatenate(chunks) if chunks else np.zeros(0, dtype=np.float32)
            sf.write(str(seg_wav), audio.astype(np.float32), SAMPLE_RATE)

        duration_ms = int(round((len(audio) / SAMPLE_RATE) * 1000))
        pause_ms = int(seg.get("pause_after_ms", 0))

        segments_meta.append({
            "idx": idx,
            "text": seg["text"],
            "speed_modifier": speed,
            "duration_ms": duration_ms,
            "start_ms_in_full": cursor_ms,
            "pause_after_ms": pause_ms,
            "sfx": seg.get("sfx"),
        })
        full_audio.append(audio.astype(np.float32))
        cursor_ms += duration_ms
        if pause_ms > 0:
            silence_samples = int(SAMPLE_RATE * pause_ms / 1000)
            full_audio.append(np.zeros(silence_samples, dtype=np.float32))
            cursor_ms += pause_ms

    combined = np.concatenate(full_audio) if full_audio else np.zeros(0, dtype=np.float32)
    peak = float(np.max(np.abs(combined))) if combined.size else 1.0
    if peak > 0:
        combined = combined * (10 ** (-3 / 20)) / peak

    audio_path = out / "audio.wav"
    sf.write(str(audio_path), combined, SAMPLE_RATE)

    manifest = {
        "voice_ref": str(voice_path_p),
        "voice_ref_sha": _file_sha(voice_path_p),
        "model": "CosyVoice2",
        "model_version": "iic/CosyVoice2-0.5B",
        "sample_rate": SAMPLE_RATE,
        "total_duration_ms": cursor_ms,
        "segments": segments_meta,
    }
    (out / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    click.echo(json.dumps({
        "audio": str(audio_path),
        "manifest": str(out / "manifest.json"),
        "segment_count": len(segments_meta),
        "total_duration_ms": cursor_ms,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    cli()
