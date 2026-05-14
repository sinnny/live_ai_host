# Function Spec — `make_voice` (voice profile pipeline)

| | |
|---|---|
| Status | Spec v1 (Phase 2 / MVP production) |
| Phase | Phase 2 |
| Component | Per-character voice profile creation — replaces the inline bootstrap from `tts.md` §2.2 |
| Source documents | [`../../prd.md`](../../prd.md) §4.2.4 |
| Last updated | 2026-05-13 |

---

## 1. Purpose

For each new character, produce a reusable voice reference + metadata for CosyVoice 2 zero-shot cloning. Avoids recording any human voice in v1 (consent/legal burden); uses CosyVoice 2's built-in voice presets as bootstrap, then optionally refines.

---

## 2. Technology stack (locked)

| Stage | Tool | License |
|---|---|---|
| Brief expansion | Claude Sonnet 4.6 | proprietary, paid |
| Bootstrap voice gen | CosyVoice 2 with default presets | Apache 2.0 |
| (Optional) refinement | CosyVoice 2 with voice style transfer | Apache 2.0 |
| Audio I/O | librosa + soundfile | ISC + MIT |
| Infra | RunPod L40S | rental |

---

## 3. Inputs

CLI:
```bash
./make_voice --description "warm but slightly unhinged Korean female voice, late 20s" \
             --character daramzzi \
             --output-dir voices/daramzzi/
```

---

## 4. Outputs

```
voices/daramzzi/
├── ref.wav                — the ~10 sec reference audio
├── ref_text.txt           — exact transcript of ref.wav
├── samples/
│   ├── sample_01.wav ...  — test samples for review
└── manifest.yaml          — bootstrap preset used, generation seed, sha256
```

---

## 5. Pipeline

1. Claude reads description → emits 5 candidate "voice prompt + sample text" pairs.
2. CosyVoice 2 default presets generate 5 candidate ref clips.
3. Founder reviews + picks the best (or rerolls with new descriptions).
4. Selected ref + transcript written to `voices/<character>/`.

---

## 6. Quality criteria

| Criterion | Threshold |
|---|---|
| Sounds natural Korean | manual listen |
| Matches description | manual judgement |
| Sufficient length | ≥ 8 sec, ≤ 15 sec |
| Acceptable mono 24 kHz | format check |

---

## 7. Cost and time

- Per voice: ~$0.05, ~5 min wall clock (mostly review)

---

## 8. References

- [`../../prd.md`](../../prd.md) §4.2.4
- [`tts.md`](tts.md), [`tts_streaming.md`](tts_streaming.md) — consumers
- CosyVoice 2 voice cloning docs
