# Function Spec — `make_bg` (background generation pipeline)

| | |
|---|---|
| Status | Spec v1 (Phase 2 / MVP production) |
| Phase | Phase 2 |
| Component | Offline pipeline producing the library of broadcast backgrounds (static stills + ambient looping animations) |
| Source documents | [`../../prd.md`](../../prd.md) §4.2 |
| Last updated | 2026-05-13 |

---

## 1. Purpose

Generate a library of backgrounds for the compositor to cycle through. A "vibe" descriptor produces N variations: stills for shorter shots, animated loops (4-8 sec) for longer holds.

---

## 2. Technology stack (locked)

| Stage | Tool | License |
|---|---|---|
| Brief expansion | Claude Sonnet 4.6 (1 call per batch) | proprietary, paid |
| Static gen | Qwen-Image (or Z-Image-Turbo for faster) | Apache 2.0 |
| Animated loop gen | AnimateDiff on SDXL with motion LoRAs | Apache 2.0 / OpenRAIL-M |
| Looper / muxer | FFmpeg with seamless-loop filter | LGPL |
| Infra | RunPod L40S (offline batch, overnight runs OK) | rental |

---

## 3. Inputs

CLI:
```bash
./make_bg --count 20 --vibe "warm kitchen, golden-hour sunset, lived-in" \
          --animated-fraction 0.3 \
          --output-dir backgrounds/<vibe-name>/
```

---

## 4. Outputs

```
backgrounds/<vibe-name>/
├── stills/
│   ├── 001.png ... 014.png
├── loops/
│   ├── 015.mp4 ... 020.mp4  (4-8s loops, H.264)
└── manifest.yaml
```

---

## 5. Pipeline

1. Claude expands vibe into 20 specific prompts.
2. Qwen-Image batch-generates stills at 1920×1080.
3. For animated fraction: feed still + motion LoRA prompt into AnimateDiff → 4-8 sec loop.
4. FFmpeg ensures seamless loop boundary (slight crossfade if needed).
5. Emit manifest with prompt, seed, generation timestamp per asset.

---

## 6. Quality criteria

| Criterion | Threshold |
|---|---|
| Visual cohesion across batch | manual review: 90%+ feel like same vibe |
| Loop seamlessness | no visible cut/pop at loop boundary |
| Resolution | 1920×1080 |
| File sizes | stills ≤ 2 MB, loops ≤ 20 MB |

---

## 7. Cost and time

- Batch of 20: ~$3-5, ~2 hours unattended (mostly AnimateDiff time).
- Run overnight; manual review next morning.

---

## 8. References

- [`make_mascot.md`](make_mascot.md) — sibling pipeline (similar pattern)
- [`compositor_obs.md`](compositor_obs.md) — consumer (uses backgrounds as OBS Media Sources)
- AnimateDiff repo
