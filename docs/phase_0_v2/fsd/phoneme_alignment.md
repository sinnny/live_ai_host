# Function Spec — Phoneme alignment (Rhubarb)

| | |
|---|---|
| Status | Spec v1 (ready to execute) |
| Component | Converts TTS audio output into per-frame viseme timing for mouth animation |
| First instantiation | Daramzzi prototype clip |
| Future use | Same module in test_3 (just invoked per-utterance in streaming mode) |
| Source documents | [`../prototype_spec.md`](../prototype_spec.md) §5.2, [`../../prd.md`](../../prd.md) §4.3.4 |
| Last updated | 2026-05-13 |

---

## 1. Purpose and scope

### 1.1 What this FSD defines

The subsystem that takes a WAV audio file and emits a timeline of viseme states (`closed`, `aa`, `ih`, `ou`, `ee`, `oh`) with millisecond precision. The renderer consumes this to swap the mouth-overlay sprite at the right frames.

### 1.2 Out of scope

- Phoneme detection across speakers (single-speaker per clip).
- Multi-language phoneme models (we use Rhubarb's language-agnostic shape detection; no Korean-specific model needed).
- Real-time streaming alignment (deferred to test_3).

### 1.3 Success criterion

For a 1-3 minute Korean WAV:
1. Output viseme timeline aligns with audio to within ±50ms drift across the whole clip.
2. Processing time ≤ 10% of audio duration (i.e. 18 sec for a 3-min clip).
3. Output is valid JSON parseable by the renderer.
4. No crashes on Korean audio (Rhubarb is shape-based, not phoneme-model-based — language agnostic).

---

## 2. Technology stack (locked)

| Stage | Tool | License | Why |
|---|---|---|---|
| Alignment engine | **Rhubarb Lip Sync** | MIT | language-agnostic mouth-shape detector; CLI tool, no GPU needed; mature (multiple game engines depend on it) |
| Mapping | own Python | – | maps Rhubarb's A-H shape codes → our 6 viseme states |
| Audio I/O | Rhubarb handles internally | – | – |
| Infra | runs on CPU; same Docker container as TTS | – | – |

### 2.1 Why not phoneme-based (e.g. wav2vec / Whisper)?

A phoneme-based aligner needs a Korean acoustic model — that's what `phase_0_v1/stage4_oss_findings.md` proved is broken in 2026 OSS (EchoMimic's chinese-wav2vec2 doesn't generalize to Korean). Rhubarb sidesteps this by analyzing audio shape/formant properties directly without a language model.

The cost is less precision (Rhubarb's shape detection is coarser than phoneme prediction), but for a stylized 2.5D mascot mouth, "close enough" is what we want — too much precision over-emphasizes mouth movement artificially.

### 2.2 Fallback: amplitude envelope

If Rhubarb alignment quality is unacceptable on Korean:
- **Fallback strategy:** drop Rhubarb, switch to pure audio amplitude envelope (50ms attack / 100ms release) driving `closed ↔ aa` toggle. Less expressive but reliable.
- This is also the **production default** per PRD §4.3.4 if the test reveals Rhubarb instability.

---

## 3. Inputs

| Input | Source | Format |
|---|---|---|
| Audio file | output of `tts.py synthesize` | `audio.wav`, mono 16+ kHz |

---

## 4. Outputs

```
prototype_runs/<clip>/phonemes/
└── alignment.json
```

### 4.1 Output format

```json
{
  "schema_version": 1,
  "audio_file": "../tts/audio.wav",
  "audio_duration_ms": 87340,
  "alignment_engine": "rhubarb",
  "alignment_engine_version": "1.13.0",
  "frames": [
    { "start_ms": 0,     "end_ms": 120,   "viseme": "closed" },
    { "start_ms": 120,   "end_ms": 240,   "viseme": "aa" },
    { "start_ms": 240,   "end_ms": 380,   "viseme": "oh" },
    { "start_ms": 380,   "end_ms": 500,   "viseme": "closed" },
    ...
  ]
}
```

Adjacent frames with the same viseme are merged.

---

## 5. Pipeline

### 5.1 Stage

```
audio.wav → rhubarb → raw.json → mapper → alignment.json
```

### 5.2 Rhubarb invocation

```bash
rhubarb -o raw.json --exportFormat json \
        --extendedShapes GHX \
        --recognizer pocketSphinx \
        audio.wav
```

- `--recognizer pocketSphinx` is the default; works language-agnostically.
- `--extendedShapes GHX` enables 9-shape output (A-X) for finer mouth detail.

### 5.3 Shape-to-viseme mapping

Rhubarb emits shape codes (A through X). Map to our 6 visemes:

| Rhubarb shape | Our viseme | Korean phoneme association |
|---|---|---|
| X | closed | silence, lip-closed consonants |
| A | aa | 아 (open vowel) |
| B | aa | similar open vowel |
| C | ee | 에 / 애 (wide vowel) |
| D | aa | open vowel, leaning toward A |
| E | oh | 오 (rounded mid vowel) |
| F | ou | 우 (rounded close vowel) |
| G | ih | 이 (close front vowel) |
| H | ih | similar close vowel |

### 5.4 Smoothing

- Merge consecutive same-viseme frames.
- Skip transitions shorter than 60ms (avoid jitter from noisy detection); promote to the longer neighbor.

---

## 6. Execution

```bash
python phoneme_alignment.py \
  --audio prototype_runs/clip_01/tts/audio.wav \
  --output prototype_runs/clip_01/phonemes/alignment.json
```

---

## 7. Quality criteria

| Criterion | Method | Threshold |
|---|---|---|
| Audio-viseme sync | manual: play audio, watch viseme stream | ≤ 50ms drift on any sample |
| Processing speed | wall clock vs audio duration | ≤ 0.1× (i.e. 6 sec for 60 sec audio) |
| JSON validity | json.loads + schema check | valid |
| No empty timeline | sanity check | at least one non-closed viseme per spoken segment |

---

## 8. Failure modes

| Mode | Symptom | Response |
|---|---|---|
| Korean tonal/aspirate sounds get classified as closed | mouth doesn't open during speech | tune Rhubarb sensitivity flag; if persistent, switch to amplitude-envelope fallback (§2.2) |
| Excessive viseme jitter | rapid swapping at sub-100ms intervals | already smoothed (§5.4); if still too rapid, increase minimum-frame threshold to 80ms |
| Rhubarb hang on unusual audio | timeout | wrap in 5-min timeout; on timeout fall back to amplitude envelope |
| Mapper produces unsupported viseme | KeyError | unmapped shapes default to `closed` |

---

## 9. Cost and time

Pure CPU. Negligible cost (~$0.01/clip GPU rental amortized across other stages).

3-minute clip: ~15-20 sec wall clock for alignment.

---

## 10. Session continuity

- Pure function: same audio.wav → same alignment.json. Fully idempotent.
- No model state, no checkpoints to manage.
- Re-running is free.

---

## 11. References

- [`../prototype_spec.md`](../prototype_spec.md) §5.2
- [`../../prd.md`](../../prd.md) §4.3.4
- Rhubarb Lip Sync project (github.com/DanielSWolf/rhubarb-lip-sync)
- [`../../phase_0_v1/stage4_oss_findings.md`](../../phase_0_v1/stage4_oss_findings.md) — why phoneme-model approaches fail on Korean
