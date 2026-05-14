# Prototype spec — Daramzzi 1-3 minute clip

| | |
|---|---|
| Status | Spec v1 (ready to execute) |
| Document type | Prototype spec — visual-feasibility proof of concept |
| Purpose | "Can we render Daramzzi speaking Korean and have it look good?" go/no-go check, BEFORE committing to MVP build |
| Supersedes for now | [`deferred/test_3_spec.md`](deferred/test_3_spec.md) — the full live-runtime validation, postponed until after this prototype passes |
| Source documents | [`make_mascot_fsd.md`](make_mascot_fsd.md) (atlas pipeline), [`../characters/daramzzi.md`](../characters/daramzzi.md) (character bible), [`../prd.md`](../prd.md) (overall product context) |
| Last updated | 2026-05-13 |

---

## 1. What this is and is not

### 1.1 This is

A **smallest test of the riskiest assumption**: that a 2.5D sprite-puppet driven by Korean TTS + audio-driven mouth + sprite-swap expressions actually produces a watchable, on-brand Daramzzi clip. Single 1-3 minute MP4 file, scripted by the founder, rendered offline.

### 1.2 This is NOT

- A live broadcast. No RTMP. No real-time anything.
- An autonomous broadcast. No LLM in the runtime path; the founder writes the script.
- A latency or stability test. That's `deferred/test_3_spec.md`, run later if and only if the prototype passes.
- A multi-tenant test. Single-tenant flat namespace.
- A test of Claude agents. Director / Moderator / Host are all out of scope for this round.
- A polished demo for customers. It's an internal go/no-go gut check.

### 1.3 Pass condition (qualitative, founder judgement)

After watching the rendered MP4, the founder answers yes to all four:

1. **Recognizable.** This is clearly Daramzzi from the bible (not a hamster, not generic anime girl, not off-brand).
2. **Watchable.** No painful uncanny moments. Mouth motion roughly matches audio. Expression swaps don't feel jarring.
3. **On-brand.** The character reads as earnest, lovable, intern-energy. Not sassy, not flat.
4. **Worth iterating.** "I would put effort into making this better" — not "this is a dead end."

If yes to all four → green-light to plan test_3.
If no on any → stop, write a post-mortem, replan.

---

## 2. Tech stack (subset of locked PRD §4.2)

All OSS, all on the rented RunPod L40S, **no paid APIs at runtime**.

| Stage | Tool | License | Notes |
|---|---|---|---|
| Image generation | Qwen-Image | Apache 2.0 | unchanged from `make_mascot_fsd.md` §2 |
| LoRA training | AI-Toolkit | MIT | unchanged |
| Background removal | BiRefNet | MIT | unchanged |
| Anchor alignment | MediaPipe | Apache 2.0 | unchanged |
| Atlas packing | Pillow + Python | – | unchanged |
| **TTS** | **CosyVoice 2** | **Apache 2.0** | one-shot batch mode (not streaming), Korean |
| **Phoneme alignment** | **Rhubarb Lip Sync** | MIT | offline batch on the WAV |
| **Renderer** | **three.js** + sprite-swap | MIT | offline render to image sequence (or live to ffmpeg via virtual webcam) |
| **Encoder** | **FFmpeg + libx264** | LGPL | software encode is fine; offline doesn't need NVENC |
| **Orchestrator** | Python 3.11 | – | single CLI, runs in same Docker container as `make_mascot` |

**Explicitly NOT in this prototype:**
- Claude API (Sonnet / Haiku) — founder writes the script, no live LLM
- nginx-rtmp / OBS / RTMP push — offline render, not a live stream
- vLLM / Qdrant / RAG — no LLM, no retrieval
- pytchat / YouTube Live chat — no chat, scripted only
- Director FSM, Moderator agent, Host agent — not needed for a scripted clip

---

## 3. Inputs

| Input | Source | Format | Notes |
|---|---|---|---|
| Daramzzi atlas | output of `make_mascot` pipeline | `atlas/atlas.png` + `atlas/config.json` + `atlas/lora.safetensors` | Generated once, reused for all prototype clips |
| Korean script | founder writes | `scripts/test_3/scripts/<clip_name>.json` | Validated against [`scripts/test_3/script_schema.json`](../../scripts/test_3/script_schema.json) |
| Voice reference | one-time generated | `scripts/test_3/voice/daramzzi_ref.wav` | ~10s reference for CosyVoice 2 zero-shot clone. Bootstrap with CosyVoice 2's default female KR voice reading a sample line; can be re-recorded later. |
| Background image (optional) | static | PNG | If omitted, plain solid color from bible §4.2 (warm autumn cream) |

### 3.1 Script format (JSON, validated by schema)

Example minimal script:

```json
{
  "schema_version": 1,
  "title": "Daramzzi 인사 클립",
  "language": "ko",
  "default_state": { "expression": "neutral", "tail": "relaxed", "ears": "up" },
  "segments": [
    { "text": "안녕하세요! 다람찌입니다.", "expression": "neutral", "pause_after_ms": 200 },
    { "text": "음... 이거 진짜 맛있어요...", "expression": "cheek_stuff", "ears": "flat", "speed_modifier": 0.8 },
    { "text": "아 사장님이 보면 안 되는데!", "expression": "panic", "tail": "puffed" }
  ]
}
```

Mouth state is NOT in the script — it's amplitude/phoneme-driven from the audio at render time.

---

## 4. Outputs

```
scripts/test_3/prototype_runs/<clip_name>/
├── input_script.json                  — copy of the input script for provenance
├── tts/
│   ├── audio.wav                       — full TTS output, mono 24kHz
│   └── segments/                       — per-segment WAV (for debugging)
├── phonemes/
│   └── alignment.json                  — Rhubarb output, viseme + timing
├── frames/                             — optional, only if rendering to image sequence
│   └── frame_*.png
├── output.mp4                          — the final clip, 1080p H.264/AAC
└── manifest.yaml                       — full provenance: atlas version, script hash, LoRA sha, timestamps
```

---

## 5. Pipeline stages

Four stages. End-to-end ~30 minutes after atlas is ready.

### Stage 5.1 — TTS

**Input:** `<clip_name>.json` script
**Output:** `tts/audio.wav` + `tts/segments/*.wav`

**Process:**
1. Load CosyVoice 2 + Daramzzi voice reference.
2. For each segment in the script:
   - Call CosyVoice 2 with `text=segment.text`, `language="ko"`, `speed=segment.speed_modifier ?? 1.0`, voice reference.
   - Save segment WAV.
3. Concatenate segment WAVs with `pause_after_ms` silences between.
4. Apply SFX cues if any (mix in a short SFX clip at segment end).
5. Output single `audio.wav`.

**Wall clock:** ~2 min for 1-3 min script
**Cost:** ~$0.05 in GPU time
**Failure modes:** CosyVoice 2 mispronounces a Korean word → tweak phonetic spelling in script; rerun.

### Stage 5.2 — Phoneme alignment

**Input:** `tts/audio.wav`
**Output:** `phonemes/alignment.json`

**Process:**
1. Run Rhubarb on the WAV: `rhubarb -o alignment.json --exportFormat json audio.wav`.
2. Rhubarb emits a list of `{start_ms, end_ms, viseme}` entries.
3. Map Rhubarb's mouth-shape codes (A-H) to our atlas viseme states (closed, aa, ih, ou, ee, oh).

**Wall clock:** ~30 sec
**Cost:** ~$0.01 (CPU mostly)
**Failure modes:** Rhubarb misaligned on Korean → fallback to amplitude-envelope mouth-open (no phoneme, just `closed ↔ aa` toggled by audio amplitude).

### Stage 5.3 — Render

**Input:** atlas, script, audio.wav, alignment.json
**Output:** image sequence OR direct video stream to ffmpeg

**Process:**
1. Boot headless Chrome via Playwright pointed at `scripts/test_3/renderer/index.html`.
2. Pass atlas + script + alignment via WebSocket bootstrap.
3. Renderer plays the audio.wav as the timing master.
4. Per frame (60 fps target):
   - Determine current segment from script timeline → set expression / tail / ears layers.
   - Determine current viseme from alignment.json → set mouth layer.
   - Apply procedural idle motion (sine-wave Y-offset + slight X-jitter, sub-pixel scale).
   - Composite layers in z-order: expression → tail → ears → mouth.
5. Capture frame: either dump to PNG sequence OR pipe to ffmpeg via virtual webcam.

**Wall clock:** ~5 min for 1-3 min clip
**Cost:** ~$0.20 in GPU time
**Failure modes:**
- Sprite layers misaligned → atlas issue, re-pack from `make_mascot`.
- Viseme swap is too rapid/jittery → smooth with 50ms crossfade or 100ms hysteresis.
- Procedural idle motion looks robotic → tune sine parameters or add subtle scale modulation.

### Stage 5.4 — Encode

**Input:** image sequence OR live render
**Output:** `output.mp4`

**Process:**
1. ffmpeg: `-r 60 -i frame_%05d.png -i audio.wav -c:v libx264 -preset slow -crf 18 -c:a aac -b:a 128k output.mp4`.
2. Embed audio + video, mux to MP4 container.

**Wall clock:** ~1 min
**Cost:** negligible
**Failure modes:** A/V drift → check render timestamps vs audio length, adjust frame count.

---

## 6. Execution commands

```bash
# Once atlas is ready (per make_mascot pipeline):
cd /workspace/live_ai_host/scripts/test_3

# Generate a voice reference (one time)
docker run --rm --gpus all -v $(pwd):/work prototype-pipeline \
  python prototype.py voice-ref --output voice/daramzzi_ref.wav

# Write your script (manually): scripts/clip_01.json
# Validate it
docker run --rm -v $(pwd):/work prototype-pipeline \
  python prototype.py validate --script scripts/clip_01.json

# Run the full prototype pipeline for one script
docker run --rm --gpus all -v $(pwd):/work prototype-pipeline \
  python prototype.py render \
    --script scripts/clip_01.json \
    --atlas mascot/daramzzi/atlas/ \
    --voice voice/daramzzi_ref.wav \
    --output-dir prototype_runs/clip_01/

# Preview locally (rsync mp4 down from RunPod, play with ffplay or VLC)
rsync runpod:/workspace/.../clip_01/output.mp4 ./
open output.mp4
```

---

## 7. Cost (real numbers, not padded)

| Item | Cost |
|---|---|
| `make_mascot` (one-time for Daramzzi, then reused) | $5-7 |
| Voice reference generation | $0.05 |
| Per-clip TTS + render + encode | $0.30 |
| **First prototype clip total** | **~$6-8** |
| **Each additional clip after** | **~$0.30** |

Hard cap: $15 for the full prototype phase including 3-5 iterations on script + render parameters. If we exceed $15, halt and consult.

---

## 8. Quality criteria

Mostly qualitative. The pass condition is §1.3 above. Quantitatively we also check:

- A/V sync drift ≤ 100ms across the whole clip
- 60 fps render with no frame drops
- Output MP4 ≤ 50 MB for 1-3 min at 1080p
- No transparent pixels in the final output (background fully filled)

---

## 9. If the prototype passes

We commit to test_3 (the full live runtime validation, currently in `deferred/`). Estimated cost for that next phase: ~$70-100, ~1 week.

## 10. If the prototype fails

We do not proceed with the current stack as-is. Write a post-mortem under `phase_0_v2/post_mortem_<n>.md` covering:
- Which of §1.3's four pass conditions failed
- Root cause (TTS quality? sprite art? sync? composition?)
- Options: tune (cheap), swap a component (medium), full pivot (expensive)
- Recommendation

Then we plan v2 of the prototype with the relevant change, or pivot the product direction.

---

## 11. What about the bigger questions?

Several open product/strategy questions are deliberately deferred until after this prototype:

- Mascot identity lock (PRD §8 OQ #1) — Daramzzi is provisional. If the prototype validates the visual + voice combination, we commit. If it doesn't, we may pick a different character.
- Korean ad-law compliance approach — irrelevant to a scripted, non-live prototype.
- Multi-tenancy data model — irrelevant.
- Per-stream economics at scale — irrelevant for one offline clip.

These all come back when test_3 starts.

---

## 12. Sign-off

- Spec author: Claude (Opus 4.7, 1M context)
- Spec reviewer: founder (pending)
- Implementer: Claude (per `deferred/test_3_spec.md` option A, same model applies here)
- Prerequisites to start: atlas ready (from `make_mascot`), founder-written script, RunPod access
