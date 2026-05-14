# Checklist — `make_broll` (product B-roll pipeline)

| | |
|---|---|
| Purpose | Generate 30-60 sec B-roll for one product |
| FSD | [`../../fsd/make_broll.md`](../../fsd/make_broll.md) |
| Phase | Phase 2 |
| Language | English source — KO at [`../ko/make_broll.md`](../ko/make_broll.md) |

---

## Tech stack (at a glance)

- **Claude Sonnet 4.6** — shotlist generation
- **Wan 2.2 I2V** (Apache 2.0) — image-to-video shots
- **FFmpeg** (LGPL) — stitching + transitions
- **Infra**: RunPod L40S, overnight batch per broadcast

Full table: [`../../fsd/make_broll.md`](../../fsd/make_broll.md) §2

---

## §1. Prerequisites

- [ ] [`../../fsd/make_broll.md`](../../fsd/make_broll.md) read
- [ ] Wan 2.2 weights loaded
- [ ] Product info available: photos + specs JSON

## §2. Generate shotlist

- [ ] Run: `python make_broll.py shotlist --product-id <id> --output shotlist.json`
- [ ] Quick review of shotlist (6-12 shots, sensible motion prompts)

## §3. Render shots

- [ ] Run: `python make_broll.py render --shotlist shotlist.json`
- [ ] Wait ~20 min/product
- [ ] Verify each shot MP4 valid

## §4. Stitch

- [ ] Run: `python make_broll.py stitch --product-id <id>`
- [ ] Verify `final.mp4` ≈ target duration (±10%)

## §5. Status board

| Step | Status | Cost |
|---|---|---|
| §1 Prerequisites | ⬜ | – |
| §2 Shotlist | ⬜ | $0.05 |
| §3 Render | ⬜ | $2-3 |
| §4 Stitch | ⬜ | negligible |

## §6. Troubleshooting

| Issue | Response |
|---|---|
| Wan distorts product | use cleaner reference photo; tighter motion prompt |
| Total duration off-target | Claude shotlist refinement |
| Transition feels abrupt | adjust template fade duration |
