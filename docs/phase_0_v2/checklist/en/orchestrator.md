# Checklist — Orchestrator (end-to-end pipeline)

| | |
|---|---|
| Purpose | Drive the 4-stage prototype pipeline end-to-end; produce final MP4 |
| FSD reference | [`../../fsd/orchestrator.md`](../../fsd/orchestrator.md) |
| Encompasses | [`make_mascot`](make_mascot.md) (one-time), then [`tts`](tts.md) → [`phoneme_alignment`](phoneme_alignment.md) → [`renderer`](renderer.md) → encode (per clip) |
| Language | English source — Korean translation at [`../ko/orchestrator.md`](../ko/orchestrator.md) |
| Last updated | 2026-05-13 |

---

## Tech stack (at a glance)

- **Click** (BSD-3) — Python CLI framework
- **jsonschema** (MIT) — script validation against `script_schema.json`
- **PyYAML** (MIT) — manifest emission
- **FFmpeg + libx264 + AAC** (LGPL) — encoder
- **Docker** (Apache 2.0) — reproducible env
- **Infra**: RunPod L40S
- Coordinates: TTS → phoneme_alignment → renderer → encoder, all on same box

Full table with rationale: [`../../fsd/orchestrator.md`](../../fsd/orchestrator.md) §2

---

## Session resume

Use `--resume` flag; orchestrator detects partial state and skips completed stages.

If unsure about state: `python orchestrator.py status --run-dir prototype_runs/<clip>/` dumps current progress.

---

## §1. Prerequisites

- [ ] [`../../fsd/orchestrator.md`](../../fsd/orchestrator.md) read (especially §5 pipeline flow + §6 execution)
- [ ] Atlas ready (per [`make_mascot.md`](make_mascot.md) checklist completed)
- [ ] Voice reference ready (per [`tts.md`](tts.md) §2 completed once)
- [ ] Script JSON written and validated (per [`tts.md`](tts.md) §3.1)
- [ ] RunPod L40S running, Docker image built

---

## §2. Dry-run validation

> Before the real run, validate inputs without executing stages.

- [ ] Run: `python orchestrator.py render --dry-run --script scripts/<clip>.json --atlas mascot/daramzzi/atlas/ --voice voice/daramzzi_ref.wav --output-dir prototype_runs/<clip>/`
- [ ] Expected output:
  - [ ] Schema validation: PASS
  - [ ] Atlas validation: PASS
  - [ ] Voice file readable: PASS
  - [ ] Plan summary printed: 4 stages will run
- [ ] Address any validation errors before proceeding to real run

---

## §3. Full pipeline run

### §3.1 Launch

- [ ] Run: `python orchestrator.py render --script scripts/<clip>.json --atlas mascot/daramzzi/atlas/ --voice voice/daramzzi_ref.wav --output-dir prototype_runs/<clip>/`
- [ ] Watch stage logs in real-time: `tail -f prototype_runs/<clip>/logs/*.log`

### §3.2 Per-stage monitoring

- [ ] **TTS** (per [`tts.md`](tts.md)) — wait for completion
  - [ ] `tts.log` ends with: `TTS_COMPLETE`
  - [ ] `tts/audio.wav` + `tts/manifest.json` present
- [ ] **Phoneme alignment** (per [`phoneme_alignment.md`](phoneme_alignment.md))
  - [ ] `phoneme.log` ends with: `ALIGNMENT_COMPLETE`
  - [ ] `phonemes/alignment.json` present
- [ ] **Render** (per [`renderer.md`](renderer.md))
  - [ ] `render.log` ends with: `RENDER_COMPLETE: N frames`
  - [ ] `frames/` contains expected frame count
- [ ] **Encode**
  - [ ] `encode.log` ends with: `ENCODE_COMPLETE`
  - [ ] `output.mp4` present and ≤ 50 MB

### §3.3 Final output

- [ ] `output.mp4` exists
- [ ] `manifest.yaml` exists with all 4 stages marked `status: success`
- [ ] Run `ffprobe output.mp4`:
  - [ ] Valid MP4 container
  - [ ] H.264 video stream
  - [ ] AAC audio stream
  - [ ] Duration matches script's total expected runtime (within 1 sec)

Total estimated: ~8-10 min for 1-3 min clip / Cost: ~$0.30

---

## §4. Resume after failure

If any stage fails:

- [ ] Inspect the failed stage's log under `logs/`
- [ ] Cross-reference the component's troubleshooting section (in its FSD §8)
- [ ] Fix root cause (script tweak, config tweak, atlas regen, etc.)
- [ ] Resume: `python orchestrator.py render --resume --script ... --output-dir prototype_runs/<clip>/`
- [ ] Resume skips completed stages, restarts at the failed stage

---

## §5. Watch the output

- [ ] Download MP4 to local Mac: `rsync runpod:/workspace/.../<clip>/output.mp4 ./`
- [ ] Play with VLC / QuickTime / ffplay
- [ ] **Apply prototype pass criteria** (see [`../../prototype_spec.md`](../../prototype_spec.md) §1.3 — the four yes/no questions)

---

## §6. Prototype pass/fail decision

Founder review against [`../../prototype_spec.md`](../../prototype_spec.md) §1.3:

- [ ] **Recognizable** — clearly Daramzzi from the bible, not a hamster, not generic anime
- [ ] **Watchable** — no painful uncanny moments, mouth roughly matches audio, expressions don't feel jarring
- [ ] **On-brand** — earnest, lovable, intern-energy; not sassy or flat
- [ ] **Worth iterating** — "I'd put effort into making this better"

If all 4 yes → green-light test_3 ([`../../deferred/test_3_spec.md`](../../deferred/test_3_spec.md)).
If any no → write `post_mortem_<n>.md` per `prototype_spec.md` §10, replan.

---

## §7. Status board

| Step | Status | Started | Completed | Cost | Notes |
|---|---|---|---|---|---|
| §1 Prerequisites | ⬜ Pending | – | – | – | – |
| §2 Dry-run validation | ⬜ Pending | – | – | $0 | – |
| §3.1 Launch | ⬜ Pending | – | – | – | – |
| §3.2 TTS stage | ⬜ Pending | – | – | – | – |
| §3.2 Phoneme stage | ⬜ Pending | – | – | – | – |
| §3.2 Render stage | ⬜ Pending | – | – | – | – |
| §3.2 Encode stage | ⬜ Pending | – | – | – | – |
| §3.3 Final output | ⬜ Pending | – | – | – | – |
| §5 Watch the output | ⬜ Pending | – | – | $0 | – |
| §6 Pass/fail decision | ⬜ Pending | – | – | – | – |

---

## §8. Troubleshooting

| Issue | Likely cause | Response |
|---|---|---|
| Schema validation fails | Script JSON malformed | Fix per the specific schema error message |
| TTS stage crash | See [`tts.md`](tts.md) §6 (troubleshooting) | Component-specific fix, then `--resume` |
| Phoneme alignment fails | Korean misalignment | Fall back to amplitude mode (`phoneme_alignment.md` §3.3), then `--resume` |
| Render crashes mid-clip | Headless Chrome OOM | `--resume` picks up at the failing frame |
| FFmpeg encode fails | Frame count vs. audio duration mismatch | Re-render frames; encode is cheap, just rerun |
| Disk full at frame stage | 1080p × 60 fps × 3 min ≈ 3-5 GB intermediate | Mount frames dir on bigger volume or use `--frame-format jpg` |
