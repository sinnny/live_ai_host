# Checklist — Phoneme alignment (Rhubarb)

| | |
|---|---|
| Purpose | Convert TTS audio into viseme timeline for renderer's mouth animation |
| FSD reference | [`../../fsd/phoneme_alignment.md`](../../fsd/phoneme_alignment.md) |
| Depends on | [`tts.md`](tts.md) — needs `audio.wav` |
| Language | English source — Korean translation at [`../ko/phoneme_alignment.md`](../ko/phoneme_alignment.md) |
| Last updated | 2026-05-13 |

---

## Tech stack (at a glance)

- **Rhubarb Lip Sync** (MIT) — language-agnostic mouth-shape detector
- Custom Python — viseme code mapping
- **Infra**: CPU only (runs in shared Docker container)
- Fallback: amplitude envelope mode if Korean alignment quality is poor

Full table with rationale: [`../../fsd/phoneme_alignment.md`](../../fsd/phoneme_alignment.md) §2

---

## Session resume

Pure stateless stage. Idempotent. Re-running is free. Find the first unchecked `[ ]`.

---

## §1. Prerequisites

- [ ] [`../../fsd/phoneme_alignment.md`](../../fsd/phoneme_alignment.md) read
- [ ] Rhubarb installed in Docker image: `which rhubarb` returns path
- [ ] Previous stage complete: `prototype_runs/<clip>/tts/audio.wav` exists

---

## §2. Run alignment

- [ ] Run: `python phoneme_alignment.py --audio prototype_runs/<clip>/tts/audio.wav --output prototype_runs/<clip>/phonemes/alignment.json`
- [ ] Verify output: `alignment.json` exists, valid JSON, matches FSD §4 schema
- [ ] Sanity check: viseme timeline length ≈ audio duration (in `frames` array length / fps equivalent)
- [ ] Sanity check: at least some non-`closed` visemes are present during speech segments

Estimated: ~20 sec for 3-min clip / Cost: ~$0.01

---

## §3. Quality validation

### §3.1 Audio-viseme sync (manual)

- [ ] Play audio in one window, scroll through alignment.json timestamps in another
- [ ] At 5 random sample points, verify viseme matches the mouth shape the audio would suggest
- [ ] Drift on any sample: ≤ 50 ms

### §3.2 Viseme distribution (auto)

- [ ] Run: `python phoneme_alignment.py stats --alignment alignment.json`
- [ ] Expected output: histogram showing reasonable spread across viseme states (not all `closed`, not all `aa`)

### §3.3 If Korean alignment quality is poor

- [ ] Fall back to amplitude-envelope mode per FSD §2.2:
  - [ ] `python phoneme_alignment.py --audio audio.wav --mode amplitude --output alignment.json`
  - [ ] Output schema is the same; renderer doesn't know the difference

---

## §4. Handoff to renderer

- [ ] `phonemes/alignment.json` is ready
- [ ] Proceed to [`renderer.md`](renderer.md)

---

## §5. Status board

| Step | Status | Started | Completed | Mode | Notes |
|---|---|---|---|---|---|
| §1 Prerequisites | ⬜ Pending | – | – | – | – |
| §2 Run alignment | ⬜ Pending | – | – | rhubarb / amplitude | – |
| §3 Quality validation | ⬜ Pending | – | – | – | – |

---

## §6. Troubleshooting

| Issue | Likely cause | Response |
|---|---|---|
| Mouth never opens during speech | Korean aspirate/tonal sounds misclassified as silence | Tune Rhubarb sensitivity flag; if persistent, fall back to amplitude mode (§3.3) |
| Excessive viseme jitter (rapid swapping) | Noisy detection at sub-100ms intervals | Increase smoothing threshold in FSD §5.4 from 60 ms to 80 ms |
| Rhubarb hangs on unusual audio | Edge case in shape detector | 5-min timeout in wrapper; fall back to amplitude mode |
| Unmapped Rhubarb shape | Shape outside A-X range | Wrapper defaults to `closed`; no action needed |
