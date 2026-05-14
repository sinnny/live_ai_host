# Function Spec — Compositor (OBS Studio)

| | |
|---|---|
| Status | Spec v1 (Phase 1 / test_3 — MVP compositor) |
| Phase | Phase 1 |
| Component | Composes character + background + overlays into final 1080p H.264 stream |
| Source documents | [`../../prd.md`](../../prd.md) §4.3.5 |
| Successor | [`compositor_gstreamer.md`](compositor_gstreamer.md) (Phase 2 production version) |
| Last updated | 2026-05-13 |

---

## 1. Purpose and scope

### 1.1 What this FSD defines

OBS Studio configured as our compositor for test_3 and early MVP. Layers (background, character, product card, chat overlay) merged programmatically via obs-websocket. Output encoded with FFmpeg/NVENC → RTMP.

### 1.2 Why OBS for MVP (not GStreamer)

- GUI lets us debug visually
- Mature plugin ecosystem (browser source, virtual cam, audio mixing)
- obs-websocket gives programmatic scene control
- Production-grade encoding via FFmpeg

Lower latency than GStreamer would give us, but ~100-200ms is fine inside the 1.5s budget. GStreamer swap happens in Phase 2 when we need to push under 1s.

### 1.3 Out of scope

- Programmatic scene authoring beyond switching (scenes are pre-configured in OBS GUI)
- Multi-stream tenancy (one OBS instance per broadcast for now)

---

## 2. Technology stack (locked)

| Stage | Tool | License | Why |
|---|---|---|---|
| Compositor | **OBS Studio** | GPL | mature, well-documented, FFmpeg-backed |
| Remote control | **obs-websocket** plugin | GPL | JSON-RPC over WebSocket |
| Browser source | OBS built-in CEF | – | for chat overlay HTML |
| Window/V4L source | OBS built-in | – | captures renderer's virtual webcam |
| Audio mixing | OBS built-in | – | mixes Daramzzi voice + SFX + background music |
| Encoder | FFmpeg + NVENC | LGPL | hardware-accelerated H.264 |

---

## 3. Inputs

| Input | Source |
|---|---|
| Character feed | virtual webcam from [`renderer_live.md`](renderer_live.md) |
| Audio feed | virtual audio device or local file from [`tts_streaming.md`](tts_streaming.md) |
| Background | static image or animated MP4 loop (from `make_bg.md`) |
| Product card | HTML browser source, content driven by orchestrator |
| Chat overlay | HTML browser source (optional) |
| Scene-switch commands | obs-websocket from `broadcast_orchestrator.md` |

---

## 4. Outputs

H.264/AAC encoded video stream to nginx-rtmp (local) or RTMP destination (live).

---

## 5. Scenes (pre-configured in OBS profile)

| Scene | Used in mode | Sources visible |
|---|---|---|
| `FULL_MASCOT` | default mascot mode | background + character + product card |
| `PIP` | mascot small-corner, B-roll fullscreen | B-roll layer + character (small overlay) |
| `SCRIPTED_CLIP` | pre-rendered B-roll fullscreen | B-roll only |
| `EMERGENCY_LOOP` | technical difficulties | static "잠시만 기다려 주세요" image + soft music |

Saved as `daramzzi_broadcast.json` OBS profile.

---

## 6. Execution

```bash
# Start OBS headless (Linux server with virtual X session)
xvfb-run -a obs --startvirtualcam --profile daramzzi_broadcast \
                --scene FULL_MASCOT --minimize-to-tray &

# Connect obs-websocket controller
python compositor_obs.py serve \
  --redis-url redis://localhost:6379/0 \
  --in-topic broadcast.fsm.<id> \
  --obs-url ws://localhost:4455
```

---

## 7. Quality criteria

| Criterion | Method | Threshold |
|---|---|---|
| Scene-switch latency (FSM cmd → visible) | log + capture | ≤ 200ms |
| Encoder stability over 4 hr | monitor encoder bitrate | no encoder errors |
| Output bitrate consistent | check stream | 4-6 Mbps target |
| A/V sync drift | check final stream | ≤ 100ms |

---

## 8. Failure modes

| Mode | Symptom | Response |
|---|---|---|
| OBS crash | output stops | systemd auto-restart; compositor reconnects |
| obs-websocket disconnect | scene switches don't apply | reconnect with backoff |
| NVENC unavailable | encoder error | fall back to libx264 software encode (higher CPU) |
| Virtual webcam stalls | character frozen on stream | renderer is the issue ([`renderer_live.md`](renderer_live.md) §8) |
| Audio device clock drift | A/V drift | OBS handles internally; alert if drift > 100ms |

---

## 9. Cost and time

| Item | Estimate |
|---|---|
| OBS + encoder GPU usage during live | ~5-10% of L40S |
| Per 2-hr broadcast amortized | ~$0.50 |

---

## 10. Session continuity

- OBS profile is the source of truth; live changes via obs-websocket are not persisted (compositor reapplies state on reconnect).
- Active scene + source visibilities published to Redis on every change for observability.

---

## 11. References

- [`../../prd.md`](../../prd.md) §4.3.5
- [`renderer_live.md`](renderer_live.md) — input source
- [`tts_streaming.md`](tts_streaming.md) — audio source
- [`rtmp_output.md`](rtmp_output.md) — encoder destination
- [`broadcast_orchestrator.md`](broadcast_orchestrator.md) — scene-switch controller
- OBS Studio + obs-websocket docs
