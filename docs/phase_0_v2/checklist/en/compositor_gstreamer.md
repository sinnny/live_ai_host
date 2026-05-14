# Checklist — Compositor (GStreamer, production)

| | |
|---|---|
| Purpose | Replace OBS with a GStreamer pipeline for lower-latency production |
| FSD | [`../../fsd/compositor_gstreamer.md`](../../fsd/compositor_gstreamer.md) |
| Predecessor | [`compositor_obs.md`](compositor_obs.md) |
| Phase | Phase 2 |
| Language | English source — KO at [`../ko/compositor_gstreamer.md`](../ko/compositor_gstreamer.md) |

---

## Tech stack (at a glance)

- **GStreamer** (LGPL) — pipeline framework
- `nvh264enc` (LGPL) — NVENC H.264
- `gst-python` (LGPL) — Python binding
- **Infra**: RunPod L40S with NVENC

Full table: [`../../fsd/compositor_gstreamer.md`](../../fsd/compositor_gstreamer.md) §2

---

## §1. Prerequisites

- [ ] [`../../fsd/compositor_gstreamer.md`](../../fsd/compositor_gstreamer.md) read
- [ ] GStreamer + plugins installed
- [ ] OBS compositor still operational (rollback path)

## §2. Build pipeline

- [ ] Implement pipeline graph per FSD §3
- [ ] Test with static inputs (image + audio file)
- [ ] Verify output: RTMP push works

## §3. Side-by-side benchmark

- [ ] Run OBS and GStreamer on same content; measure latency
- [ ] Verify GStreamer wins by ≥ 100ms

## §4. Production switch

- [ ] Update `broadcast_orchestrator` to point at GStreamer
- [ ] Keep OBS as fallback for 2 sprints
- [ ] Monitor for regressions

## §5. Status board

| Step | Status |
|---|---|
| §1 Prerequisites | ⬜ |
| §2 Build pipeline | ⬜ |
| §3 Benchmark | ⬜ |
| §4 Production switch | ⬜ |

## §6. Troubleshooting

| Issue | Response |
|---|---|
| Pipeline errors silently | enable GST_DEBUG=3 |
| NVENC unavailable | fallback to `x264enc` (CPU); latency hit acceptable temporarily |
| Audio sync drift | check timestamp propagation across elements |
