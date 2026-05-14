# Checklist — `make_voice` (voice profile pipeline)

| | |
|---|---|
| Purpose | Generate a CosyVoice 2 voice reference for a new character |
| FSD | [`../../fsd/make_voice.md`](../../fsd/make_voice.md) |
| Phase | Phase 2 |
| Language | English source — KO at [`../ko/make_voice.md`](../ko/make_voice.md) |

---

## Tech stack (at a glance)

- **Claude Sonnet 4.6** — description → voice prompt candidates
- **CosyVoice 2** (Apache 2.0) — synthesizes candidate refs from built-in Korean female presets
- **Infra**: RunPod L40S

Full table: [`../../fsd/make_voice.md`](../../fsd/make_voice.md) §2

---

## §1. Prerequisites

- [ ] [`../../fsd/make_voice.md`](../../fsd/make_voice.md) read
- [ ] CosyVoice 2 weights loaded
- [ ] Voice description ready

## §2. Generate candidates

- [ ] Run: `./make_voice --description "..." --character <name> --output-dir voices/<name>/`
- [ ] 5 candidate refs produced

## §3. Listen + pick

- [ ] Founder listens to all 5
- [ ] Pick best; saved as `ref.wav`
- [ ] Re-roll if none acceptable (different description / presets)

## §4. Status board

| Step | Status | Cost |
|---|---|---|
| §1 Prerequisites | ⬜ | – |
| §2 Generate | ⬜ | $0.05 |
| §3 Listen + pick | ⬜ | – |

## §5. Troubleshooting

| Issue | Response |
|---|---|
| All 5 too similar | broaden description; re-roll with different prompt structure |
| Sounds too mature/childish | tune age descriptor |
| Korean unnatural | check preset; some presets are KR-trained, some aren't |
