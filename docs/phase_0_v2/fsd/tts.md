# Function Spec — TTS service (CosyVoice 2)

| | |
|---|---|
| Status | Spec v1 (ready to execute) |
| Component | Korean Text-to-Speech for Daramzzi voice |
| First instantiation | Daramzzi prototype clip (offline, one-shot) |
| Future use | Streaming mode in test_3 + production (post-prototype) |
| Source documents | [`../prototype_spec.md`](../prototype_spec.md) §5.1, [`../../prd.md`](../../prd.md) §4.3.3 |
| Last updated | 2026-05-13 |

---

## 1. Purpose and scope

### 1.1 What this FSD defines

The Korean TTS subsystem that converts script segments into a single WAV file for the prototype clip, with persona-consistent voice (Daramzzi character), per-segment speed control, and optional SFX cues.

### 1.2 Out of scope (for prototype)

- Streaming TTS mode (deferred to test_3 — same model, different invocation pattern).
- Multi-speaker / multi-character voice switching (single Daramzzi voice for now).
- Real-time emotion injection (handled by sprite layer, not TTS, in prototype scope).
- English TTS (Korean only for v1; CosyVoice 2 supports English natively, can be enabled later).

### 1.3 Success criterion

For a 1-3 minute Korean script:
1. Audio output sounds natural Korean — no robotic artifacts, no English-language drift.
2. Voice is persona-appropriate per bible §5.1 (slightly higher than average register, energetic-anxious intern energy, no chipmunk pitch-up).
3. `speed_modifier` from the script correctly slows down cheek-stuffed segments.
4. Total wall clock ≤ 2 minutes for a 3-minute script.

---

## 2. Technology stack (locked)

| Stage | Tool | License | Why |
|---|---|---|---|
| TTS engine | **CosyVoice 2** | Apache 2.0 | Best Apache-2.0 multilingual TTS with KR support; zero-shot voice cloning; ~150 ms TTFA in streaming mode (not used for prototype) |
| Audio I/O | librosa + soundfile | ISC + MIT | WAV read/write, sample rate conversion |
| Audio mixing | numpy + scipy.signal | BSD | concatenation, silence insertion, SFX overlay |
| Infra | RunPod L40S | rental | same box as `make_mascot` |

### 2.1 Explicitly NOT used

- ElevenLabs / OpenAI TTS / Naver CLOVA Voice / Supertone — paid APIs, violates PRD §4.2.1 OSS lock
- XTTS v2 — CPML non-commercial license, trap for B2B SaaS
- Fish-Speech 1.5 — CC-BY-NC-SA, non-commercial
- GPT-SoVITS — fallback only if CosyVoice 2 fails

### 2.2 Voice reference

Daramzzi uses a **synthetic voice reference** generated one-time:
- Bootstrap: CosyVoice 2's default Korean female preset reads ~10 seconds of bible-derived sample text.
- Saved as `scripts/test_3/voice/daramzzi_ref.wav`.
- Reused across all clips. No recording of a real human voice — avoids consent/legal burden.

This is the "no outsourcing, no manual labor" constraint applied to voice acting.

---

## 3. Inputs

| Input | Source | Format | Notes |
|---|---|---|---|
| Script segments | parsed from `<clip>.json` | list of `{text, speed_modifier?, pause_after_ms?, sfx?}` | validated against `script_schema.json` |
| Voice reference | `scripts/test_3/voice/daramzzi_ref.wav` | WAV mono ≥ 16kHz | generated one-time, reused |
| SFX library (optional) | `scripts/test_3/sfx/` | per-cue WAV files | e.g. `bite.wav`, `hiccup.wav` |

---

## 4. Outputs

```
prototype_runs/<clip>/tts/
├── audio.wav              — full concatenated TTS output, mono 24 kHz
├── segments/
│   ├── seg_000.wav        — per-segment WAV (for debugging)
│   ├── seg_001.wav
│   └── ...
└── manifest.json          — per-segment: text, duration_ms, start_ms_in_full, voice_settings
```

### 4.1 Manifest format

```json
{
  "voice_ref": "voice/daramzzi_ref.wav",
  "voice_ref_sha": "sha256:...",
  "model": "CosyVoice2",
  "model_version": "...",
  "sample_rate": 24000,
  "total_duration_ms": 87340,
  "segments": [
    {
      "idx": 0,
      "text": "안녕하세요! 다람찌입니다.",
      "speed_modifier": 1.0,
      "duration_ms": 1820,
      "start_ms_in_full": 0,
      "pause_after_ms": 200,
      "sfx": null
    },
    ...
  ]
}
```

The manifest is consumed by the renderer to map script segments to audio timeline.

---

## 5. Pipeline

### 5.1 Stage layout

```
script.json → tts.py
  ├─→ load CosyVoice 2 + voice_ref
  ├─→ for each segment:
  │     ├─→ synthesize(text, lang=ko, speed=speed_modifier) → seg_NNN.wav
  │     └─→ write segment manifest entry
  ├─→ assemble:
  │     ├─→ concatenate segments with `pause_after_ms` silences
  │     └─→ overlay SFX clips if specified
  └─→ write audio.wav + manifest.json
```

### 5.2 Per-segment synthesis

```python
audio = cosyvoice.inference_zero_shot(
    tts_text=segment.text,
    prompt_text=voice_ref_text,        # transcription of voice_ref.wav
    prompt_speech=voice_ref_audio,
    speed=segment.speed_modifier or 1.0,
    stream=False,                       # prototype is offline batch
)
```

### 5.3 Concatenation + SFX mixing

- Silences inserted between segments per `pause_after_ms`.
- SFX cues mixed at segment end at -6 dB relative to TTS to avoid masking.
- Output normalized to -3 dBFS peak.

---

## 6. Execution

```bash
# Generate the voice reference (one-time)
python tts.py voice-ref \
  --bootstrap-voice cosyvoice2:default_kr_female \
  --output voice/daramzzi_ref.wav

# Synthesize a clip's audio
python tts.py synthesize \
  --script scripts/clip_01.json \
  --voice voice/daramzzi_ref.wav \
  --output-dir prototype_runs/clip_01/tts/
```

---

## 7. Quality criteria

| Criterion | Method | Threshold |
|---|---|---|
| Korean pronunciation natural | manual listen | no robotic / synthesizer-obvious artifacts on common words |
| Voice consistency across segments | manual listen | same voice timbre throughout |
| `speed_modifier` correctly applied | duration check | segment with 0.8 modifier is ~1.25× longer than 1.0 equivalent |
| Sample rate | header check | 24 kHz mono |
| Peak level | RMS check | -3 dBFS, no clipping |
| File integrity | ffprobe | valid WAV, frame count matches duration |

---

## 8. Failure modes

| Mode | Symptom | Response |
|---|---|---|
| Korean mispronunciation on a specific word | manual listen catches it | edit script: respell phonetically in Korean (e.g. `사장님` → `사장 니임` if elongation needed) |
| Voice drift across segments | timbre changes mid-clip | shorter segments + same voice ref enforces stability; if persists, regenerate voice ref |
| English-language drift | KR text spoken with English phonetics | explicit `language="ko"` flag, prompt text reinforcement |
| OOM on long input | crash | chunk into smaller segments (max 200 chars each) |
| `speed_modifier` rejected | model API error | check supported range [0.5, 1.5]; reject out-of-range in validator |

---

## 9. Cost and time

| Item | Estimate |
|---|---|
| Voice reference generation (one-time) | ~5 sec compute, $0.01 |
| Per-segment synthesis | ~2-5 sec compute per second of audio |
| 3-minute script (~25 segments) | ~2-3 min wall clock, $0.05-0.10 |

---

## 10. Session continuity

- Voice reference is reusable — once generated, never regenerated.
- Synthesis is idempotent: same input → same output (CosyVoice 2 has a deterministic mode with fixed seed).
- Each segment WAV is written before the next is synthesized; partial runs can be resumed by skipping segments whose WAV already exists.

---

## 11. References

- [`../prototype_spec.md`](../prototype_spec.md) §5.1 — TTS stage in the prototype pipeline
- [`../../prd.md`](../../prd.md) §4.3.3 — production TTS architecture (streaming mode)
- [`../../characters/daramzzi.md`](../../characters/daramzzi.md) §5 — voice and speech direction
- CosyVoice 2 paper / repo (Alibaba FunAudioLLM)
