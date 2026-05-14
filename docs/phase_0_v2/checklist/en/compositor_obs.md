# Checklist — Compositor (OBS Studio)

| | |
|---|---|
| Purpose | Stand up OBS as the compositor for test_3 broadcasts |
| FSD | [`../../fsd/compositor_obs.md`](../../fsd/compositor_obs.md) |
| Phase | Phase 1 |
| Language | English source — KO at [`../ko/compositor_obs.md`](../ko/compositor_obs.md) |

---

## Tech stack (at a glance)

- **OBS Studio** (GPL) — compositor
- **obs-websocket** plugin (GPL) — JSON-RPC control
- **FFmpeg + NVENC** (LGPL) — encoder
- Browser source (CEF) — chat / product card overlays
- **Infra**: RunPod L40S with xvfb (headless X) — needed for OBS GUI

Full table: [`../../fsd/compositor_obs.md`](../../fsd/compositor_obs.md) §2

---

## Session resume

OBS profile is source of truth. Restart re-applies state. obs-websocket controller reconnects with backoff.

---

## §1. Prerequisites

- [ ] [`../../fsd/compositor_obs.md`](../../fsd/compositor_obs.md) read
- [ ] OBS Studio installed in Docker image (or on the L40S host)
- [ ] obs-websocket plugin installed and enabled
- [ ] xvfb installed: `apt install xvfb`
- [ ] OBS profile prepared: `daramzzi_broadcast.json` with 4 scenes (FULL_MASCOT, PIP, SCRIPTED_CLIP, EMERGENCY_LOOP)

---

## §2. Profile + scenes smoke

- [ ] Launch OBS once with GUI: `xvfb-run -a obs --profile daramzzi_broadcast`
- [ ] In a browser (e.g. via VNC on RunPod), verify each scene contains the right sources
- [ ] Adjust positions/sizes; save profile

---

## §3. obs-websocket connectivity

- [ ] OBS WebSocket settings: port 4455, password set
- [ ] Run: `python compositor_obs.py probe --obs-url ws://localhost:4455 --password <pw>`
- [ ] Confirm scene listing matches expected

---

## §4. Programmatic scene-switch test

- [ ] Run: `python compositor_obs.py scene-switch --to PIP`
- [ ] Verify scene switches within 200ms (measure via screen capture)

---

## §5. Encoder + RTMP test

- [ ] Configure OBS RTMP push to local nginx-rtmp (per [`rtmp_output.md`](rtmp_output.md))
- [ ] Start streaming from OBS
- [ ] Pull stream locally with ffplay; verify 1080p30 H.264/AAC

---

## §6. Serve as controller

- [ ] Run: `python compositor_obs.py serve --redis-url redis://localhost:6379/0 --in-topic broadcast.fsm.<id> --obs-url ws://localhost:4455`
- [ ] Trigger FSM state change from orchestrator; verify scene change

---

## §7. Status board

| Step | Status | Notes |
|---|---|---|
| §1 Prerequisites | ⬜ Pending | – |
| §2 Profile smoke | ⬜ Pending | – |
| §3 WS connectivity | ⬜ Pending | – |
| §4 Scene-switch | ⬜ Pending | ≤ 200ms |
| §5 Encoder + RTMP | ⬜ Pending | – |
| §6 Serve as controller | ⬜ Pending | – |

---

## §8. Troubleshooting

| Issue | Cause | Response |
|---|---|---|
| OBS crashes on start | xvfb missing / wrong display | `DISPLAY=:99 xvfb-run -a obs` |
| Scene switches not received | obs-websocket auth fail | check password in connector |
| NVENC unavailable | driver/license | fall back to libx264 in OBS encoder settings |
| Browser source blank | URL not reachable from container | use host networking or include browser source content as local file |
