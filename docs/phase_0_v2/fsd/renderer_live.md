# Function Spec — Renderer live mode (three.js)

| | |
|---|---|
| Status | Spec v1 (Phase 1 / test_3) |
| Phase | Phase 1 |
| Component | Live-driven extensions to renderer (WebSocket parameter API, audio streaming, real-time emotion swap) |
| Extends | [`renderer.md`](renderer.md) (same code, different I/O pattern) |
| Source documents | [`../../prd.md`](../../prd.md) §4.3.4 |
| Last updated | 2026-05-13 |

---

## 1. Purpose and scope

### 1.1 What this FSD defines

Live-runtime delta from the offline renderer ([`renderer.md`](renderer.md)). Same three.js + Playwright stack, same atlas + composition rules — but inputs arrive incrementally and frames stream out continuously instead of being captured to PNG.

### 1.2 Delta from offline mode

| Aspect | Offline ([`renderer.md`](renderer.md)) | Live (this FSD) |
|---|---|---|
| Audio input | full WAV file | PCM chunk stream from Redis |
| Viseme input | full alignment.json | live viseme classification (or amplitude envelope) per chunk |
| Expression/tail/ears input | parsed from script | live WebSocket from `broadcast_orchestrator` (driven by Director emotion tags) |
| Frame output | PNG sequence to disk | live virtual webcam / named pipe to compositor |
| Audio timing | playback from WAV | external (compositor handles audio mux) |

---

## 2. Technology stack (locked)

Same as [`renderer.md`](renderer.md) §2, plus:

| Stage | Tool | License | Why |
|---|---|---|---|
| WebSocket server | `websockets` Python | BSD | drives parameters from FSM |
| Live viseme classifier | inline (amplitude envelope or streaming Rhubarb adaptation) | MIT | per-chunk |
| Virtual webcam | v4l2loopback (Linux) | GPL | renderer output → OBS input |

---

## 3. Inputs

### 3.1 Static (at startup)

- Atlas + config (same as offline)
- Renderer config (same as offline)

### 3.2 Live (per WebSocket message)

Expression / tail / ears state change:
```json
{ "type": "state_change", "layer": "expression", "to": "panic", "crossfade_ms": 300 }
```

Audio chunk arrival (from `tts_streaming.md`):
```json
{ "type": "audio_chunk", "stream_id": "...", "pcm_b64": "...", "is_final": false }
```

---

## 4. Outputs

Frames continuously rendered to the virtual webcam at 60 fps.

No on-disk output; compositor captures the virtual webcam.

---

## 5. Pipeline

```
WebSocket: receives state-change events
  ├── update target state, start crossfade timer
Audio thread: receives PCM chunks
  ├── feed amplitude envelope (or streaming viseme detector)
  ├── compute current viseme
Render loop @ 60 fps:
  ├── interpolate crossfades using current time
  ├── compose layers (same as offline)
  ├── write frame to virtual webcam
```

---

## 6. Execution

```bash
# Start virtual webcam device (Linux, once at boot)
sudo modprobe v4l2loopback devices=1 video_nr=10 card_label="Daramzzi"

# Start the live renderer
python renderer_cli.py live \
  --atlas mascot/daramzzi/atlas/ \
  --websocket-port 8765 \
  --audio-redis-topic tts.audio.<id> \
  --output /dev/video10
```

---

## 7. Quality criteria

| Criterion | Method | Threshold |
|---|---|---|
| Frame rate stability under live load | log timestamps over 4-hr run | 60 fps ± 0.5 fps |
| Audio-viseme latency | log: chunk arrival → frame with new mouth | ≤ 50ms |
| State-change responsiveness | log: WS message → first frame with new state | ≤ 50ms (crossfade starts) |
| GPU memory drift | monitor every 30 min | ≤ 100 MB growth over 4 hr |

---

## 8. Failure modes

| Mode | Symptom | Response |
|---|---|---|
| WebSocket disconnect | state changes stop | renderer keeps last state, auto-reconnect with backoff |
| Audio chunks stop | mouth stays closed | OK, accurate behavior |
| Browser OOM mid-stream | renderer freezes | watchdog restarts the renderer, accepts ~5s gap |
| v4l2loopback dropped frames | compositor sees skips | log; investigate if frequent |

---

## 9. Cost and time

| Item | Estimate |
|---|---|
| Renderer GPU usage during live broadcast | ~5% of one L40S |
| Amortized per 2-hr broadcast | ~$1 |

---

## 10. Session continuity

- Live renderer instance bound to a broadcast.
- Restart picks up at current state from orchestrator (orchestrator re-sends last state on renderer reconnect).
- No persistent renderer-local state.

---

## 11. References

- [`renderer.md`](renderer.md) — base FSD
- [`tts_streaming.md`](tts_streaming.md) — audio source
- [`broadcast_orchestrator.md`](broadcast_orchestrator.md) — state-change source
- [`compositor_obs.md`](compositor_obs.md) — downstream (consumes virtual webcam)
- v4l2loopback docs
