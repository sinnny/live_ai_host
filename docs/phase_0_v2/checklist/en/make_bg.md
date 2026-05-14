# Checklist — `make_bg` (background generation)

| | |
|---|---|
| Purpose | Generate 20 backgrounds (stills + animated loops) for a vibe |
| FSD | [`../../fsd/make_bg.md`](../../fsd/make_bg.md) |
| Phase | Phase 2 |
| Language | English source — KO at [`../ko/make_bg.md`](../ko/make_bg.md) |

---

## Tech stack (at a glance)

- **Claude Sonnet 4.6** — vibe → 20 prompts
- **Qwen-Image** (Apache 2.0) — stills
- **AnimateDiff + SDXL** (Apache 2.0 / OpenRAIL-M) — animated loops
- **FFmpeg** (LGPL) — seamless-loop pass + muxing
- **Infra**: RunPod L40S overnight batch

Full table: [`../../fsd/make_bg.md`](../../fsd/make_bg.md) §2

---

## §1. Prerequisites

- [ ] [`../../fsd/make_bg.md`](../../fsd/make_bg.md) read
- [ ] L40S running, Qwen-Image + AnimateDiff weights loaded
- [ ] Vibe descriptor decided

## §2. Run batch

- [ ] Run: `./make_bg --count 20 --vibe "..." --animated-fraction 0.3 --output-dir backgrounds/<vibe>/`
- [ ] Wait overnight (~2 hr)

## §3. Review

- [ ] Stills: visual cohesion across batch
- [ ] Loops: seamless boundaries (no visible cut)
- [ ] Manifest valid

## §4. Status board

| Step | Status | Cost |
|---|---|---|
| §1 Prerequisites | ⬜ | – |
| §2 Run batch | ⬜ | ~$3-5 |
| §3 Review | ⬜ | – |

## §5. Troubleshooting

| Issue | Response |
|---|---|
| Loop has visible pop at boundary | re-run with crossfade pass in FFmpeg |
| Stills look unrelated | strengthen vibe prompt; rerun the off-brand subset |
| OOM on AnimateDiff | reduce batch size, run sequentially |
