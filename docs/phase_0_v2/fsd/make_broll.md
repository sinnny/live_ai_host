# Function Spec — `make_broll` (product B-roll pipeline)

| | |
|---|---|
| Status | Spec v1 (Phase 2 / MVP production) |
| Phase | Phase 2 |
| Component | Per-product B-roll generation: takes seller-uploaded product photos + spec sheet, produces 30-60 sec demo clips |
| Source documents | [`../../prd.md`](../../prd.md) §4.2.3, §3.3 |
| Last updated | 2026-05-13 |

---

## 1. Purpose

Per-product, produce a polished 30-60 sec B-roll that the Director can play in SCRIPTED_CLIP mode (PRD §3.1). Fully automated — Claude writes the shotlist, Wan 2.2 renders shots, FFmpeg stitches.

---

## 2. Technology stack (locked)

| Stage | Tool | License |
|---|---|---|
| Shotlist generation | Claude Sonnet 4.6 (per product) | proprietary, paid |
| Image-to-video shot | Wan 2.2 I2V | Apache 2.0 |
| Editing template | FFmpeg with predefined transitions | LGPL |
| Captions (optional) | FFmpeg `drawtext` | LGPL |
| Infra | RunPod L40S, batch overnight per broadcast | rental |

---

## 3. Inputs

```json
{
  "product_id": "kimchi_01",
  "name": "할머니 김치",
  "photos": ["...01.jpg", "...02.jpg", "...03.jpg"],
  "specs": {...},
  "persona": "daramzzi",
  "duration_target_sec": 45
}
```

---

## 4. Outputs

```
broadcasts/<id>/broll/<product_id>/
├── shotlist.json          — Claude's plan
├── shots/
│   ├── shot_01.mp4 ... shot_NN.mp4  (each 2-5 sec, Wan 2.2)
├── final.mp4              — stitched, 1080p H.264/AAC
└── manifest.yaml
```

---

## 5. Pipeline

1. Claude reads product info → emits shotlist JSON (6-12 shots, each with photo idx + motion prompt + duration).
2. For each shot: select photo → Wan 2.2 I2V with the motion prompt → 2-5 sec MP4.
3. FFmpeg concatenates shots with template transitions (fades, slight zoom-ins per shot).
4. Optional caption track from product spec highlights.
5. Mux to final MP4.

---

## 6. Quality criteria

| Criterion | Threshold |
|---|---|
| Total duration | within 10% of target |
| Shot count | 6-12 |
| Motion quality | no obvious distortion / artifact on the product |
| Transitions | smooth, on-brand |

---

## 7. Cost and time

- Per product: ~$2-3, ~20 min unattended.
- Per broadcast (5-10 products): ~$10-30, overnight.

---

## 8. References

- [`../../prd.md`](../../prd.md) §3.3, §4.2.3
- [`make_mascot.md`](make_mascot.md), [`make_bg.md`](make_bg.md) — siblings
- Wan 2.2 (Alibaba) repo / docs
