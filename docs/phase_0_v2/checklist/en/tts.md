# Checklist — TTS (CosyVoice 2)

| | |
|---|---|
| Purpose | Synthesize Korean audio from a script JSON, using the Daramzzi voice |
| FSD reference | [`../../fsd/tts.md`](../../fsd/tts.md) |
| Depends on | [`make_mascot.md`](make_mascot.md) (no atlas needed — voice is independent), but typically run after `make_mascot` |
| Language | English source — Korean translation at [`../ko/tts.md`](../ko/tts.md) |
| Last updated | 2026-05-13 |

---

## Tech stack (at a glance)

- **CosyVoice 2** (Apache 2.0) — Korean TTS, zero-shot voice clone
- **librosa + soundfile** (ISC + MIT) — audio I/O
- **numpy + scipy.signal** (BSD) — concatenation + SFX mixing
- **Infra**: RunPod L40S (same box as `make_mascot`)
- No paid TTS APIs

Full table with rationale: [`../../fsd/tts.md`](../../fsd/tts.md) §2

---

## Session resume

If picking up after disconnect: find the first unchecked `[ ]` below. All stages are idempotent — voice reference is reused; per-segment WAVs are skipped if already on disk.

---

## §1. Prerequisites

- [ ] [`../../fsd/tts.md`](../../fsd/tts.md) read (especially §3 inputs, §5 pipeline)
- [ ] RunPod L40S still running (same box as `make_mascot`)
- [ ] CosyVoice 2 weights downloaded (~5 GB) — first run will auto-fetch from Hugging Face
- [ ] `daramzzi-pipeline` Docker image built (same as `make_mascot`)

---

## §2. One-time: voice reference

> Done ONCE per character. Then reused for every clip.

- [ ] Bootstrap voice reference with CosyVoice 2 default Korean female preset reading a bible-derived ~10-sec sample
- [ ] Run: `python tts.py voice-ref --bootstrap-voice cosyvoice2:default_kr_female --output voice/daramzzi_ref.wav`
- [ ] Listen to `voice/daramzzi_ref.wav` — verify:
  - [ ] Natural Korean prosody, no robotic artifacts
  - [ ] Female voice, slightly higher than average register (bible §5.1)
  - [ ] Energetic-anxious-intern tone (not too mature, not too childish)
- [ ] If unsatisfied: rerun with different bootstrap sample text until acceptable
- [ ] Verify SHA256 logged: `sha256sum voice/daramzzi_ref.wav >> voice/voices.log`
- Estimated: 5 min / Cost: ~$0.01

---

## §3. Per-clip TTS synthesis

> Run for each prototype clip. Each clip has its own script JSON.

### §3.1 Script preparation

- [ ] Script file exists at `scripts/test_3/scripts/<clip_name>.json`
- [ ] Validates against schema: `python orchestrator.py validate --script scripts/<clip_name>.json` → passes
- [ ] Sanity-check segment count: matches expected clip duration (rough: 25-40 segments per 3 min)

### §3.2 Run TTS

- [ ] Run: `python tts.py synthesize --script scripts/<clip_name>.json --voice voice/daramzzi_ref.wav --output-dir prototype_runs/<clip_name>/tts/`
- [ ] Verify outputs:
  - [ ] `tts/audio.wav` exists, valid WAV (mono 24 kHz)
  - [ ] `tts/segments/seg_*.wav` — one per script segment
  - [ ] `tts/manifest.json` — schema valid, all segments listed with durations

### §3.3 Audio quality review (manual)

- [ ] Listen to `tts/audio.wav` end-to-end
- [ ] Verify:
  - [ ] Natural Korean pronunciation on all words (no robotic synthesizer-obvious moments)
  - [ ] Voice timbre consistent throughout — no drift mid-clip
  - [ ] `speed_modifier` correctly applied (cheek-stuffed segments noticeably slower)
  - [ ] Pauses between segments natural-feeling, not too long or too short
  - [ ] Peak level no clipping (check on quiet system or with audio meter)
- Estimated: ~3 min per 3-min clip / Cost: ~$0.05-0.10

### §3.4 Iteration on script

If pronunciation issues are caught in review:
- [ ] Edit specific segment text in script (phonetic respelling, add filler, etc.)
- [ ] Re-run only that segment: `python tts.py synthesize --segment-idx N` (or delete that segment's WAV and re-run full synthesize — idempotent skip)
- [ ] Re-review

---

## §4. Quality validation

- [ ] Peak level: `ffmpeg -i audio.wav -af "volumedetect" -f null - 2>&1 | grep max_volume` shows ≤ -3 dB
- [ ] Total duration matches sum of segment durations + pauses (within 100 ms)
- [ ] Per-segment manifest entries all have non-zero duration

---

## §5. Handoff to phoneme alignment

- [ ] `tts/audio.wav` is ready
- [ ] Proceed to [`phoneme_alignment.md`](phoneme_alignment.md)

---

## §6. Status board

| Step | Status | Started | Completed | Notes |
|---|---|---|---|---|
| §1 Prerequisites | ⬜ Pending | – | – | – |
| §2 Voice reference (one-time) | ⬜ Pending | – | – | – |
| §3.1 Script preparation | ⬜ Pending | – | – | – |
| §3.2 Run TTS | ⬜ Pending | – | – | – |
| §3.3 Audio quality review | ⬜ Pending | – | – | – |
| §4 Quality validation | ⬜ Pending | – | – | – |

---

## §7. Troubleshooting

| Issue | Likely cause | Response |
|---|---|---|
| English-language drift on Korean text | Missing `language="ko"` flag or KR phrases too short | Explicit lang flag; pad short utterances |
| Robotic on one specific word | Out-of-vocabulary or unusual phonetic | Respell phonetically in script |
| Voice timbre drifts mid-clip | Segments too long (model loses prosodic context) | Split long segments to ≤ 200 chars each |
| OOM on long input | Single segment > model limit | Chunk into smaller segments |
| `speed_modifier` rejected | Out of [0.5, 1.5] range | Validator should catch; otherwise fix script |
