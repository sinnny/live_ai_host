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
    "안녕하세요! 람찌람찌, 다람찌예요! "
    "다람찌가 오늘 가져온 제품은… 두둥! 호두과자예요!"
)
# Natural-language instruction passed to inference_instruct2. CosyVoice 2 was
# trained primarily on Chinese instructions, so this is in Chinese. Translates
# roughly to "speak with a lively, cute, high-pitched young girl's voice."
# Override via --instruct on the CLI.
DEFAULT_INSTRUCT = "用一个活泼、可爱、年轻的高音女孩声音说"
# librosa.effects.trim threshold (dB below peak); higher = more aggressive.
SILENCE_TRIM_DB = 30


def _file_sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return f"sha256:{h.hexdigest()}"


def _patch_cosyvoice_load_wav() -> None:
    """Workaround for a CosyVoice frontend bug.

    Trace (per README usage, tensor-input flow):
      inference_cross_lingual(text, prompt_speech_16k)   # tensor
        → frontend.frontend_cross_lingual(text, prompt_wav, ...)
        → frontend.frontend_zero_shot(text, '', prompt_wav, ...)
        → frontend._extract_speech_feat(prompt_wav)
        → file_utils.load_wav(prompt_wav, 24000)        # expects PATH

    `load_wav` then calls `torchaudio.load(wav, ...)` and dies because the
    arg is a tensor, not a path. The README's example does pass a tensor —
    this is an internal-API mismatch in the cloned version. Patch `load_wav`
    in both modules where it's referenced (the module-level import in
    cosyvoice.cli.frontend binds at import time and won't update otherwise).
    """
    import torch as _torch
    import torchaudio as _torchaudio
    import cosyvoice.utils.file_utils as _cv_file_utils
    import cosyvoice.cli.frontend as _cv_frontend

    if getattr(_cv_file_utils, "_TENSOR_LOAD_WAV_PATCHED", False):
        return

    _original = _cv_file_utils.load_wav

    def _patched(wav, target_sample_rate):
        if isinstance(wav, _torch.Tensor):
            speech = wav if wav.dim() == 2 else wav.unsqueeze(0)
            # Our voice_ref / synthesize paths always pre-load tensors at
            # 16 kHz; CosyVoice's internal callers ask for 24 kHz output.
            if target_sample_rate != 16000:
                speech = _torchaudio.transforms.Resample(16000, target_sample_rate)(speech)
            return speech
        return _original(wav, target_sample_rate)

    _cv_file_utils.load_wav = _patched
    _cv_frontend.load_wav = _patched
    _cv_file_utils._TENSOR_LOAD_WAV_PATCHED = True


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
    _patch_cosyvoice_load_wav()
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
@click.option("--reference-wav", default=str(ZERO_SHOT_PROMPT), show_default=True,
              type=click.Path(),
              help="Reference voice WAV (bundled with CosyVoice 2). instruct2 mode "
                   "pairs with zero_shot_prompt.wav per the README.")
@click.option("--instruct", default=DEFAULT_INSTRUCT, show_default=False,
              help="Natural-language instruction for the voice style "
                   "(Chinese works best — CosyVoice 2 was trained on CN instructions).")
@click.option("--mode", type=click.Choice(["instruct2", "cross_lingual"]),
              default="instruct2", show_default=True,
              help="instruct2 = natural-language voice control (better tone match); "
                   "cross_lingual = pure timbre-copy from --reference-wav.")
@click.option("--trim-silence/--no-trim-silence", default=True, show_default=True,
              help="Strip trailing silence from CosyVoice's output.")
def voice_ref(out: str, text: str, reference_wav: str, instruct: str,
              mode: str, trim_silence: bool) -> None:
    """One-time bootstrap: render `text` as Korean speech via CosyVoice 2.

    Two synthesis modes:
      - instruct2 (default): natural-language voice control. The --instruct
        text tells the model HOW to speak (e.g. high-pitched, cute, lively).
        Better fit when we want a specific voice character.
      - cross_lingual: pure timbre-copy from --reference-wav, no style
        instruction. Earlier default; sounded androgynous for our use.
    """
    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    ref_path = Path(reference_wav)
    if not ref_path.exists():
        raise click.ClickException(
            f"Reference WAV not found: {ref_path}. CosyVoice 2 ships two: "
            f"{CROSS_LINGUAL_PROMPT} and {ZERO_SHOT_PROMPT}."
        )

    from cosyvoice.utils.file_utils import load_wav
    prompt_speech_16k = load_wav(str(ref_path), 16000)

    model = _load_cosyvoice()
    samples = []
    if mode == "instruct2":
        for chunk in model.inference_instruct2(text, instruct, prompt_speech_16k, stream=False):
            samples.append(chunk["tts_speech"].cpu().numpy().flatten())
    else:
        for chunk in model.inference_cross_lingual(text, prompt_speech_16k, stream=False):
            samples.append(chunk["tts_speech"].cpu().numpy().flatten())
    audio = np.concatenate(samples) if samples else np.zeros(0, dtype=np.float32)

    # Trim trailing (and leading) silence — CosyVoice 2 routinely emits
    # several seconds of dead air at the end of synthesis.
    if trim_silence and audio.size:
        import librosa
        audio, _ = librosa.effects.trim(audio, top_db=SILENCE_TRIM_DB)

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
        "inference_mode": mode,
        "instruct": instruct if mode == "instruct2" else None,
        "silence_trimmed": trim_silence,
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
            # CosyVoice 2 README invokes inference_zero_shot positionally,
            # not with kwargs — the parent CosyVoice class's signature uses
            # different parameter names than the docstrings suggest. Positional
            # call matches the README example verbatim:
            #   cosyvoice.inference_zero_shot(tts_text, prompt_text, prompt_speech_16k, stream=False)
            for out_chunk in model.inference_zero_shot(
                seg["text"],
                prompt_text,
                ref_audio,
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
