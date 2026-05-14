# Function Spec — Orchestrator (Python CLI + FFmpeg encoder)

| | |
|---|---|
| Status | Spec v1 (ready to execute) |
| Component | End-to-end pipeline driver — wires TTS → phoneme → renderer → encoder for one clip |
| First instantiation | Daramzzi prototype |
| Future use | Generalized to broadcast orchestrator in test_3 + production (per PRD §4) |
| Source documents | [`../prototype_spec.md`](../prototype_spec.md) §5, [`../../prd.md`](../../prd.md) §4.4 |
| Last updated | 2026-05-13 |

---

## 1. Purpose and scope

### 1.1 What this FSD defines

The Python CLI tool that takes a script + atlas + voice reference and drives the four pipeline stages (TTS, phoneme alignment, render, encode) in sequence, producing a final MP4 output plus a complete provenance manifest.

### 1.2 Out of scope (for prototype)

- Live broadcast orchestration (FSM, scene switching, RTMP push) — test_3 work, separate FSD will be written then.
- Multi-tenancy (job queues, per-tenant isolation) — MVP-production work.
- Multi-clip batch rendering (one clip at a time for prototype).
- Job retry / circuit-breaker logic (single-shot for prototype; manual rerun on failure).

### 1.3 Success criterion

For one script invocation:
1. All four pipeline stages run in correct order.
2. Stage failures halt the pipeline and log the cause clearly.
3. Final output is a single MP4 file passing [`../prototype_spec.md`](../prototype_spec.md) §8 quality checks.
4. A complete manifest is produced documenting all inputs, intermediate artifacts, and timings.
5. Total wall clock for a 1-3 min clip ≤ 15 minutes.

---

## 2. Technology stack (locked)

| Stage | Tool | License | Why |
|---|---|---|---|
| CLI framework | **Click** | BSD-3 | mature, ergonomic, low-overhead |
| Schema validation | **jsonschema** | MIT | validate scripts against `script_schema.json` |
| Subprocess orchestration | Python `subprocess` | – | for FFmpeg, Rhubarb, Playwright invocations |
| Manifest emission | **PyYAML** | MIT | YAML for human-readable provenance |
| Encoder | **FFmpeg + libx264 + AAC** | LGPL | software encoder; offline doesn't need NVENC |
| Container | Docker | Apache 2.0 | reproducible env on RunPod |
| Infra | RunPod L40S (same box as other stages) | rental | – |

### 2.1 Encoder settings

FFmpeg invocation (default for prototype):

```bash
ffmpeg -framerate 60 -i frames/frame_%05d.png \
       -i tts/audio.wav \
       -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p \
       -c:a aac -b:a 128k \
       -shortest -movflags +faststart \
       output.mp4
```

- `-preset slow -crf 18` — high quality, slow encode. Acceptable for offline prototype (~1 min for 3-min clip).
- `-pix_fmt yuv420p` — required for widest playback compatibility.
- `-movflags +faststart` — moov atom at file start so browsers can stream during download.

For production / live use (test_3+), swap to `libx264 -preset veryfast -crf 23 -tune zerolatency` and NVENC if available.

---

## 3. Inputs

CLI args parsed by Click:

| Arg | Required | Description |
|---|---|---|
| `--script PATH` | yes | path to script JSON, validated against `script_schema.json` |
| `--atlas DIR` | yes | path to atlas folder containing `atlas.png`, `config.json`, `manifest.yaml` |
| `--voice WAV` | yes | voice reference WAV (output of `make_voice` or one-time bootstrap) |
| `--output-dir DIR` | yes | output directory; created if missing |
| `--render-config PATH` | no | renderer config JSON; defaults to built-in |
| `--encoder-preset {fast,slow}` | no | default `slow` |
| `--resume` | flag | skip stages whose output already exists |
| `--dry-run` | flag | validate inputs, print plan, exit without running stages |

---

## 4. Outputs

```
prototype_runs/<clip>/
├── input_script.json              — copy of input script (provenance)
├── tts/                            — TTS stage output
│   ├── audio.wav
│   ├── segments/
│   └── manifest.json
├── phonemes/                       — phoneme alignment output
│   └── alignment.json
├── frames/                         — renderer output (deleted after encode unless --keep-frames)
│   └── frame_*.png
├── output.mp4                      — final encoded clip
├── manifest.yaml                   — orchestrator-level provenance (see §4.1)
└── logs/                           — per-stage stdout/stderr
    ├── tts.log
    ├── phoneme.log
    ├── render.log
    └── encode.log
```

### 4.1 Master manifest format

```yaml
schema_version: 1
clip_name: clip_01
generated_at: 2026-05-13T15:30:00+09:00
total_duration_seconds: 87.3
total_wall_clock_seconds: 412

inputs:
  script:
    path: scripts/clip_01.json
    sha256: ...
    schema_version: 1
    segments: 23
  atlas:
    path: mascot/daramzzi/atlas/
    atlas_png_sha256: ...
    config_sha256: ...
    lora_sha256: ...
    character: daramzzi
  voice:
    path: voice/daramzzi_ref.wav
    sha256: ...

stages:
  tts:
    status: success
    started_at: 2026-05-13T15:30:00+09:00
    ended_at: 2026-05-13T15:32:15+09:00
    duration_seconds: 135
    output: tts/audio.wav
    cost_usd: 0.07
  phonemes:
    status: success
    started_at: 2026-05-13T15:32:15+09:00
    ended_at: 2026-05-13T15:32:35+09:00
    duration_seconds: 20
    output: phonemes/alignment.json
    cost_usd: 0.01
  render:
    status: success
    started_at: 2026-05-13T15:32:35+09:00
    ended_at: 2026-05-13T15:39:00+09:00
    duration_seconds: 385
    output: frames/ (5240 frames)
    cost_usd: 0.20
  encode:
    status: success
    started_at: 2026-05-13T15:39:00+09:00
    ended_at: 2026-05-13T15:39:52+09:00
    duration_seconds: 52
    output: output.mp4 (28.4 MB)
    cost_usd: 0.005

totals:
  cost_usd: 0.285
  wall_clock_seconds: 412
```

---

## 5. Pipeline flow

```
1. Validate inputs
   ├─ load script, validate against script_schema.json
   ├─ load atlas/config.json, validate schema
   ├─ check voice WAV exists and readable
   └─ check output_dir is writable, empty (or --resume mode)

2. Copy input_script.json to output_dir (provenance)

3. Stage: TTS
   ├─ subprocess: python tts.py synthesize --script ... --voice ... --output-dir <output>/tts/
   ├─ check exit code; on non-zero, log + halt
   └─ verify output: audio.wav exists, manifest.json valid

4. Stage: Phoneme alignment
   ├─ subprocess: python phoneme_alignment.py --audio <output>/tts/audio.wav --output <output>/phonemes/alignment.json
   ├─ check exit code
   └─ verify output: alignment.json valid

5. Stage: Render
   ├─ subprocess: python renderer_cli.py render --atlas ... --script ... --audio ... --alignment ... --output-dir <output>/frames/
   ├─ check exit code
   └─ verify output: frame count matches expected (audio_duration_sec * fps)

6. Stage: Encode
   ├─ subprocess: ffmpeg -framerate 60 -i ... -i audio.wav -c:v libx264 ... output.mp4
   ├─ check exit code
   └─ verify output: ffprobe shows valid MP4 with audio + video streams

7. Write master manifest.yaml

8. Cleanup (unless --keep-frames):
   └─ rm -rf <output>/frames/
```

### 5.1 Resume semantics

With `--resume`, each stage is skipped if its output artifact already exists and passes basic validation:
- TTS skipped if `tts/manifest.json` exists and segment WAVs are present.
- Phoneme skipped if `phonemes/alignment.json` exists and is valid JSON.
- Render skipped if expected frame count is present in `frames/`.
- Encode is *always* re-run on resume (cheap, deterministic).

This handles the common case "the renderer crashed at frame 4000, fix bug, resume" — orchestrator skips TTS+phoneme, redoes only the render+encode.

---

## 6. Execution

```bash
# Full pipeline run
python orchestrator.py render \
  --script scripts/clip_01.json \
  --atlas mascot/daramzzi/atlas/ \
  --voice voice/daramzzi_ref.wav \
  --output-dir prototype_runs/clip_01/

# Dry-run validation
python orchestrator.py render --dry-run \
  --script scripts/clip_01.json \
  --atlas mascot/daramzzi/atlas/ \
  --voice voice/daramzzi_ref.wav \
  --output-dir prototype_runs/clip_01/

# Resume after partial failure
python orchestrator.py render --resume \
  --script scripts/clip_01.json \
  --atlas mascot/daramzzi/atlas/ \
  --voice voice/daramzzi_ref.wav \
  --output-dir prototype_runs/clip_01/

# Validate a script only (no execution)
python orchestrator.py validate --script scripts/clip_01.json

# Show status of an in-progress or completed run
python orchestrator.py status --run-dir prototype_runs/clip_01/
```

---

## 7. Quality criteria

| Criterion | Method | Threshold |
|---|---|---|
| All four stages complete | manifest check | every stage `status: success` |
| Final MP4 validity | ffprobe | valid container, AAC audio, H.264 video, correct duration |
| A/V sync drift | manual playback inspection | ≤ 100 ms across full clip |
| Manifest completeness | schema check | every field populated |
| Logs preserved | filesystem | per-stage `.log` files present, non-empty |

---

## 8. Failure modes

| Mode | Symptom | Response |
|---|---|---|
| Input script schema invalid | exit at stage 1 | print specific schema violation, suggest fix |
| Atlas config malformed | exit at stage 1 | re-run `make_mascot` Stage 5.8 |
| TTS stage crash | exit at stage 3 | inspect `logs/tts.log`; see [`tts.md`](tts.md) §8 |
| Phoneme stage failure | exit at stage 4 | fall back to amplitude envelope per [`phoneme_alignment.md`](phoneme_alignment.md) §2.2 |
| Renderer crash mid-frame | partial `frames/` | resume with `--resume` after fixing root cause |
| FFmpeg encode failure | exit at stage 6 | check `logs/encode.log`; typical: frame-count/audio-duration mismatch (re-render frames) |
| Out of disk space (PNG frames) | render aborts | `--keep-frames=false` (default) + temp-mount frames dir on a larger volume |

---

## 9. Cost and time

| Item | Estimate |
|---|---|
| TTS stage | ~$0.07 |
| Phoneme stage | ~$0.01 |
| Render stage | ~$0.20 |
| Encode stage | ~$0.005 |
| **Total per clip** | **~$0.30** |
| Wall clock | ~6-8 min for 1-3 min clip |

---

## 10. Session continuity

- Each stage writes its output to a deterministic path.
- Manifest is updated incrementally — partial runs leave a `manifest.yaml` with completed-stage entries.
- `--resume` automatically picks up where the previous run halted.
- All inputs are referenced by path + SHA256 in the manifest; re-running with the same inputs produces byte-identical TTS, phoneme, and render output (subject to model determinism).

---

## 11. Evolution to live broadcast (test_3+)

The orchestrator is purposely structured to extend, not be replaced, when we move to live broadcast:

- Today: sequential stage execution → MP4 file
- test_3: stages become parallel (Director runs ahead of TTS, TTS streams to renderer, renderer streams to RTMP) → live stream
- The pipeline definition becomes a graph instead of a list; same `manifest.yaml` schema captures it.

This FSD will be superseded by `broadcast_orchestrator.md` (TBD) when test_3 activates.

---

## 12. References

- [`../prototype_spec.md`](../prototype_spec.md) §6 — execution commands
- [`../../prd.md`](../../prd.md) §4.4 — production broadcast orchestrator (eventual evolution)
- [`tts.md`](tts.md), [`phoneme_alignment.md`](phoneme_alignment.md), [`renderer.md`](renderer.md), [`make_mascot.md`](make_mascot.md) — sibling FSDs
- Click documentation (click.palletsprojects.com)
- FFmpeg documentation (ffmpeg.org)
