# Checklist — Renderer live mode (three.js)

| | |
|---|---|
| Purpose | Run the renderer live for a broadcast: WebSocket state, streamed audio, virtual webcam out |
| FSD | [`../../fsd/renderer_live.md`](../../fsd/renderer_live.md) |
| Extends | [`renderer.md`](renderer.md) (offline base) |
| Phase | Phase 1 |
| Language | English source — KO at [`../ko/renderer_live.md`](../ko/renderer_live.md) |

---

## Tech stack (at a glance)

Same as [`renderer.md`](renderer.md) plus:

- **websockets** Python (BSD) — state-change channel
- Inline live viseme classifier (amplitude or streaming Rhubarb)
- **v4l2loopback** (GPL, Linux) — virtual webcam output
- **Infra**: RunPod L40S with v4l2 module

Full table: [`../../fsd/renderer_live.md`](../../fsd/renderer_live.md) §2

---

## Session resume

Bound to broadcast. Restart picks up state from orchestrator on WS reconnect.

---

## §1. Prerequisites

- [ ] [`../../fsd/renderer.md`](../../fsd/renderer.md) offline mode validated
- [ ] [`../../fsd/renderer_live.md`](../../fsd/renderer_live.md) read
- [ ] Atlas built (per [`make_mascot.md`](make_mascot.md) checklist)
- [ ] v4l2loopback kernel module loaded: `lsmod | grep v4l2loopback`
- [ ] Virtual webcam device created: `ls -la /dev/video10`

---

## §2. Static + composition smoke (re-use offline checklist)

- [ ] [`renderer.md`](renderer.md) §2.1 + §2.2 smoke tests pass

---

## §3. WebSocket state-change test

- [ ] Start live renderer: `python renderer_cli.py live --atlas mascot/daramzzi/atlas/ --websocket-port 8765 --output /dev/video10`
- [ ] Connect a test client to ws://localhost:8765
- [ ] Send state-change events; verify renderer crossfades within 50ms
- [ ] Read /dev/video10 with `ffplay /dev/video10` to confirm frames flow

---

## §4. Audio chunk integration test

- [ ] Pipe pre-recorded PCM chunks via Redis to in-topic
- [ ] Verify mouth opens during speech, closes during silence
- [ ] Audio-viseme latency ≤ 50ms

---

## §5. 4-hour stability

- [ ] Run renderer for 4 hours with synthetic 1 msg/min state changes + continuous audio
- [ ] Monitor GPU memory: ≤ 100 MB drift over 4 hr
- [ ] Verify 60 fps sustained

---

## §6. Status board

| Step | Status | Notes |
|---|---|---|
| §1 Prerequisites | ⬜ Pending | – |
| §2 Static smoke | ⬜ Pending | – |
| §3 WS state test | ⬜ Pending | – |
| §4 Audio integration | ⬜ Pending | – |
| §5 4-hr stability | ⬜ Pending | for Gate 2 |

---

## §7. Troubleshooting

| Issue | Cause | Response |
|---|---|---|
| WS disconnects mid-run | network blip | renderer keeps last state; reconnect with backoff |
| Audio chunks not arriving | TTS not publishing | check tts_streaming logs |
| Browser OOM mid-stream | per-frame leak | restart renderer; orchestrator resends state |
| /dev/video10 missing | v4l2loopback not loaded | `sudo modprobe v4l2loopback` |
