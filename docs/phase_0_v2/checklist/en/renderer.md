# Checklist — Sprite-puppet renderer (three.js)

| | |
|---|---|
| Purpose | Render 60 fps frames from atlas + script + audio + viseme alignment |
| FSD reference | [`../../fsd/renderer.md`](../../fsd/renderer.md) |
| Depends on | [`make_mascot.md`](make_mascot.md), [`tts.md`](tts.md), [`phoneme_alignment.md`](phoneme_alignment.md) |
| Language | English source — Korean translation at [`../ko/renderer.md`](../ko/renderer.md) |
| Last updated | 2026-05-13 |

---

## Tech stack (at a glance)

- **three.js** (MIT) — WebGL rendering engine
- **Playwright** + headless Chrome (Apache 2.0 / BSD) — browser runtime
- Custom GLSL fragment shader — layered composition with alpha crossfade
- Web Audio API — audio playback as timing master
- **Infra**: RunPod L40S (Chrome uses GPU for WebGL)

Full table with rationale: [`../../fsd/renderer.md`](../../fsd/renderer.md) §2

---

## Session resume

Find the first unchecked `[ ]`. Frame output is incremental — if the renderer crashed at frame N, restart skips frames 0..N-1 automatically.

---

## §1. Prerequisites

- [ ] [`../../fsd/renderer.md`](../../fsd/renderer.md) read (especially §5 architecture)
- [ ] All upstream outputs exist:
  - [ ] `mascot/daramzzi/atlas/atlas.png` + `config.json` (from `make_mascot`)
  - [ ] `prototype_runs/<clip>/tts/audio.wav` + `manifest.json` (from `tts`)
  - [ ] `prototype_runs/<clip>/phonemes/alignment.json` (from `phoneme_alignment`)
- [ ] Renderer code present at `scripts/test_3/renderer/`
- [ ] Playwright + Chromium installed in Docker image: `playwright --version`
- [ ] `renderer_config.json` exists (or use built-in defaults per FSD §3.1)

---

## §2. Pre-flight check

### §2.1 Atlas dry-run

- [ ] Launch renderer in static-preview mode (no audio): `python renderer_cli.py preview --atlas mascot/daramzzi/atlas/ --output /tmp/preview.png`
- [ ] Open `/tmp/preview.png` and verify:
  - [ ] Daramzzi visible, centered, on background color
  - [ ] No transparent holes
  - [ ] Sprite layers composited correctly (mouth on top, expression as base)

### §2.2 Composition smoke test

- [ ] Loop through all expression states with `python renderer_cli.py preview --state-cycle`
- [ ] Verify every expression renders, every tail state renders, every ear state renders, every mouth viseme renders

---

## §3. Run full render

- [ ] Run: `python renderer_cli.py render --atlas mascot/daramzzi/atlas/ --script scripts/<clip>.json --audio prototype_runs/<clip>/tts/audio.wav --alignment prototype_runs/<clip>/phonemes/alignment.json --output-dir prototype_runs/<clip>/frames/ --render-config renderer_config.json`
- [ ] Monitor: frames written incrementally to `frames/frame_NNNNN.png`
- [ ] Wait for completion log: `RENDER_COMPLETE: <N> frames written`
- [ ] Verify frame count: expected = `audio_duration_sec * fps` (e.g. 3 min × 60 fps = 10800 frames)

Estimated: ~1.5-2× audio duration in wall clock (5-6 min for 3-min clip) / Cost: ~$0.20

---

## §4. Quality validation

### §4.1 Frame-rate stability

- [ ] Inspect renderer log: per-frame timing
- [ ] Verify: 60 fps ± 0.5 fps sustained; no significant frame drops

### §4.2 Visual review (spot check)

- [ ] Open `frames/frame_00000.png` — verify opening pose matches script segment 0
- [ ] Open frame at midpoint — verify visible expression/tail/ear states match the segment timeline
- [ ] Open last frame — verify ending pose

### §4.3 Composition correctness (manual sampling)

- [ ] Pick 5 random frames from middle of clip
- [ ] For each: verify mouth overlay aligns to face, tail aligns to body, no visible misalignment
- [ ] No transparent holes anywhere in frame

### §4.4 Crossfade smoothness

- [ ] Find a frame at expected expression-transition boundary (from script timeline)
- [ ] Inspect ±300 ms of frames around the boundary (18 frames @ 60 fps)
- [ ] Verify smooth alpha ramp, no abrupt swap

---

## §5. Cleanup decision

- [ ] If frames will be encoded immediately: proceed to encoder; frames will be deleted post-encode (default)
- [ ] If frames need to be preserved (debugging, comparison): re-run with `--keep-frames` flag

---

## §6. Handoff to encoder

- [ ] `frames/frame_*.png` is ready
- [ ] Proceed to [`orchestrator.md`](orchestrator.md) §3 (encode stage)

---

## §7. Status board

| Step | Status | Started | Completed | Frames written | Notes |
|---|---|---|---|---|---|
| §1 Prerequisites | ⬜ Pending | – | – | – | – |
| §2.1 Static preview | ⬜ Pending | – | – | – | – |
| §2.2 Composition cycle | ⬜ Pending | – | – | – | – |
| §3 Full render | ⬜ Pending | – | – | 0/expected | – |
| §4 Quality validation | ⬜ Pending | – | – | – | – |

---

## §8. Troubleshooting

| Issue | Likely cause | Response |
|---|---|---|
| Atlas layers misaligned | `make_mascot` Stage 5.7 normalization weak | Regenerate atlas with stricter MediaPipe anchor check |
| Mouth flickering / visible jitter | Viseme swap too rapid | Increase `crossfade.mouth_ms` 50→80 in renderer_config |
| Crossfade looks mechanical | Linear alpha ramp visible | Switch to smoothstep in FSD §5.4 |
| Sprite halos / background bleed | Atlas alpha matte loose | Regenerate atlas with stricter BiRefNet threshold |
| Idle motion feels seasick | Amplitude too high | Reduce `idle_motion.y_sine_amplitude_px` 6→3 |
| Playwright frame missing | Headless Chrome glitch | Auto-retry; on persistent failure drop to 30 fps |
| Headless Chrome OOM on long clip | Memory accumulating per frame | Render in 30-sec chunks, concatenate frame folders |
