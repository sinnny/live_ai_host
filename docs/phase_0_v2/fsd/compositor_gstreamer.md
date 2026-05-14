# Function Spec — Compositor (GStreamer, production)

| | |
|---|---|
| Status | Spec v1 (Phase 2 / MVP production) |
| Phase | Phase 2 |
| Component | Production compositor replacing OBS in [`compositor_obs.md`](compositor_obs.md) |
| Source documents | [`../../prd.md`](../../prd.md) §4.3.5 |
| Predecessor | [`compositor_obs.md`](compositor_obs.md) |
| Last updated | 2026-05-13 |

---

## 1. Purpose

Lower-latency, more programmable compositor than OBS for production. Same composition responsibilities (background + character + product card + chat overlay → encoded RTMP), but expressed as a GStreamer pipeline driven by API rather than a GUI tool.

---

## 2. Technology stack (locked)

| Stage | Tool | License |
|---|---|---|
| Pipeline framework | **GStreamer** | LGPL |
| Compositor element | `compositor` / `videomixer` | LGPL |
| Encoder | `nvh264enc` (NVENC) | LGPL |
| Audio mixer | `audiomixer` | LGPL |
| RTMP sink | `rtmpsink` | LGPL |
| Python binding | `gst-python` | LGPL |
| Infra | RunPod L40S, GPU NVENC | rental |

---

## 3. Pipeline (GStreamer graph)

```
v4l2src device=/dev/video10 (renderer) ─┐
filesrc location=bg.mp4 (background) ──┼→ compositor → nvh264enc → flvmux → rtmpsink
appsrc (product_card_overlay HTML)  ───┘
                                       │
appsrc (TTS audio PCM) → audiomixer ───┴→
```

---

## 4. Compared to OBS

| Aspect | OBS | GStreamer |
|---|---|---|
| Latency from input to encoder | ~100-200ms | ~30-50ms |
| Programmatic scene-switch latency | ~200ms | ~20ms |
| GUI debugging | yes | no |
| Plugin ecosystem | rich (browser src, plugins) | smaller |
| Per-stream resource | full OBS process | lightweight pipeline |

---

## 5. Migration plan

- OBS remains the dev/debugging compositor.
- GStreamer rolls in for production once test_3 latency Gate 1 reveals OBS as the dominant stage in the budget.
- Same FSM input semantics (scene-switch commands from `broadcast_orchestrator.md`).

---

## 6. Quality criteria

| Criterion | Threshold |
|---|---|
| Pipeline stability over 4 hr | 0 errors |
| Scene-switch latency | ≤ 30ms |
| Encoder bitrate stability | within 10% of target |

---

## 7. References

- [`compositor_obs.md`](compositor_obs.md) — predecessor
- [`../../prd.md`](../../prd.md) §4.3.5
- GStreamer docs (gstreamer.freedesktop.org)
