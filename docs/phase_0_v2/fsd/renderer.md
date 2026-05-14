# Function Spec — Sprite-puppet renderer (three.js)

| | |
|---|---|
| Status | Spec v1 (ready to execute) |
| Component | Real-time 2.5D sprite-puppet rendering with layered composition |
| First instantiation | Daramzzi prototype offline render to MP4 |
| Future use | Live render in test_3 + production (same code, different I/O wiring) |
| Source documents | [`../prototype_spec.md`](../prototype_spec.md) §5.3, [`../../prd.md`](../../prd.md) §4.3.4 |
| Last updated | 2026-05-13 |

---

## 1. Purpose and scope

### 1.1 What this FSD defines

The renderer that consumes (atlas + script + audio + viseme alignment) and produces a frame-by-frame video stream. Layered sprite composition (expression / tail / ears / mouth) driven by script timing + audio-aligned viseme stream. Procedural idle motion for liveliness.

### 1.2 Out of scope

- The mouth-driving phoneme alignment itself (separate FSD: [`phoneme_alignment.md`](phoneme_alignment.md)).
- The encoder/muxer (handled by orchestrator + FFmpeg).
- The atlas generation pipeline (separate FSD: [`make_mascot.md`](make_mascot.md)).
- Live chat interaction (test_3 work).
- WebSocket interface for live driving — exists in the code but not exercised in prototype.

### 1.3 Success criterion

For the prototype:
1. 60 fps render with no frame drops over 1-3 minute clip.
2. Layered composition (expression + tail + ears + mouth) renders without visible misalignment.
3. Expression crossfade smooth at 300ms; viseme crossfade smooth at 50ms.
4. Procedural idle motion makes the character feel alive without being distracting.
5. Frame output captures correctly to image sequence OR pipes directly to FFmpeg.

---

## 2. Technology stack (locked)

| Stage | Tool | License | Why |
|---|---|---|---|
| Rendering engine | **three.js** | MIT | WebGL-based; mature; well-documented sprite/shader support |
| Browser runtime | **Playwright** + headless Chrome | Apache 2.0 / BSD | reliable headless rendering; deterministic frame capture |
| Frame capture | Chromium screencast API via Playwright | – | reads back GPU buffer to PNG/raw |
| Audio sync | Web Audio API + manual timeline | – | audio is the timing master |
| Sprite atlas loader | three.js TextureLoader + custom UV mapping | – | reads `atlas.png` + `config.json` from `make_mascot` output |
| Composition | custom GLSL fragment shader | – | z-ordered layer compositing with alpha + crossfade |
| Infra | runs in same Docker container as orchestrator; uses GPU via headless Chrome | – | same L40S as rest of pipeline |

### 2.1 Why not Pixi.js, Phaser, or Cocos?

- **Pixi.js** — fine alternative, similar feature set; three.js chosen for slightly more flexible shader control + larger community.
- **Phaser** — game-engine overhead unnecessary for our use case.
- **Cocos** — Chinese-origin commercial license caveats; skip.
- **Native (no browser)** — would need a windowing context (xvfb / Wayland headless); browser is simpler and gives us a built-in WebGL stack.

### 2.2 Why not just use ffmpeg filters directly?

Sprite layering with z-order and alpha crossfade is doable in ffmpeg's `overlay` filter, but the per-frame state machine (which sprite is currently shown, current crossfade progress) is awkward to express. JS in a renderer is much more natural.

---

## 3. Inputs

| Input | Source | Format |
|---|---|---|
| Sprite atlas | `make_mascot` output | `atlas.png` (single PNG) + `config.json` (sprite positions, anchors, layer rules) |
| Script | founder-written + validated | `<clip>.json` per `script_schema.json` |
| Audio | TTS output | `audio.wav` mono 24 kHz |
| Viseme alignment | Rhubarb output | `alignment.json` per `phoneme_alignment.md` §4 |
| Render config (optional) | `renderer_config.json` | resolution, fps, idle motion params, crossfade timings |

### 3.1 Default render config

```json
{
  "resolution": [1920, 1080],
  "fps": 60,
  "background_color": "#F8F1E6",
  "character_position": { "x": 960, "y": 540 },
  "character_scale": 1.0,
  "idle_motion": {
    "y_sine_amplitude_px": 6,
    "y_sine_period_ms": 2400,
    "x_jitter_amplitude_px": 1,
    "blink_period_ms_min": 4000,
    "blink_period_ms_max": 7000
  },
  "crossfade": {
    "expression_ms": 300,
    "tail_ms": 300,
    "ears_ms": 200,
    "mouth_ms": 50
  }
}
```

---

## 4. Outputs

Two output modes, selected by orchestrator:

### 4.1 Image sequence mode (default for prototype)

```
prototype_runs/<clip>/frames/
├── frame_00000.png
├── frame_00001.png
└── ... (60 fps × clip duration in seconds frames)
```

Then orchestrator runs FFmpeg to mux frames + audio into MP4.

### 4.2 Live stream mode (used in test_3, optional for prototype)

Frames piped directly to FFmpeg via virtual webcam (v4l2loopback) or named pipe. Faster end-to-end, no intermediate PNG dump.

For the prototype we use mode 4.1 for simpler debugging.

---

## 5. Architecture

### 5.1 Module layout

```
scripts/test_3/renderer/
├── index.html            — boots the renderer in headless Chrome
├── main.js               — orchestrates the render loop
├── atlas_loader.js       — loads atlas.png + parses config.json
├── timeline.js           — script + alignment → per-frame state machine
├── sprite_layer.js       — single layer renderer (handles crossfade)
├── puppet.js             — composes 4 layers (expression, tail, ears, mouth)
├── idle_motion.js        — procedural Y-sine + X-jitter + blink
├── audio_sync.js         — Web Audio playback for timing master
├── capture.js            — frame capture via Playwright API
└── shaders/
    ├── sprite.vert.glsl
    └── composite.frag.glsl
```

### 5.2 Frame rendering pipeline (per frame at 60 fps)

```
1. timeline.tick(t_audio_ms)
     → returns desired states: { expression, tail, ears, mouth }
        plus per-layer crossfade alpha if mid-transition

2. idle_motion.tick(t_audio_ms)
     → returns: { offset_y_px, offset_x_px, blink_alpha }

3. puppet.render(states, offsets):
     ├─ expression layer at z=0 (with crossfade if active)
     ├─ tail layer at z=1
     ├─ ears layer at z=2
     ├─ mouth layer at z=3
     └─ composited via fragment shader

4. capture.snapshot(frame_idx) → frame_NNNNN.png
```

### 5.3 Timeline state machine

The script provides per-segment expression/tail/ears states (or defaults).
The alignment provides per-frame mouth viseme.
At time `t_audio_ms`:
- Find the current segment via TTS manifest's `start_ms_in_full` + segment duration.
- Read expression/tail/ears from current segment (or default if not specified).
- Read mouth from the alignment frame covering `t_audio_ms`.
- If a layer's desired state changed since the previous frame, start a crossfade (alpha ramps from 0 to 1 over the layer's `crossfade_ms`).

### 5.4 Layered composition (GLSL)

Fragment shader:
```glsl
// pseudocode
vec4 expr_curr = sample(atlas, expression_uv_curr);
vec4 expr_prev = sample(atlas, expression_uv_prev);
vec4 expr = mix(expr_prev, expr_curr, expression_crossfade_alpha);

// similar for tail, ears, mouth

vec4 base = vec4(background_color, 1.0);
vec4 over = blend_alpha(base, expr);          // z=0
over = blend_alpha(over, tail);                // z=1
over = blend_alpha(over, ears);                // z=2
over = blend_alpha(over, mouth);               // z=3

gl_FragColor = over;
```

Crossfade is a linear alpha ramp; can be switched to a smoothstep curve if linear feels too mechanical.

### 5.5 Procedural idle motion

Position offset per frame:
```
offset_y = sin(2π · t / period_y) · amplitude_y
offset_x = noise(t · 0.001) · amplitude_x
```

Eye blink: at random intervals in `[blink_period_ms_min, blink_period_ms_max]`, swap to a "blink" expression variant (or apply alpha mask to eye region) for 100-150ms.

For prototype, blink is *optional* — if we don't have blink sprites, the procedural blink is skipped. The bible §4.4 minimum atlas doesn't include blink; we can add it as expansion later.

---

## 6. Execution

```bash
# Render a clip (orchestrator calls this; rarely invoked directly)
python renderer_cli.py render \
  --atlas mascot/daramzzi/atlas/ \
  --script scripts/clip_01.json \
  --audio prototype_runs/clip_01/tts/audio.wav \
  --alignment prototype_runs/clip_01/phonemes/alignment.json \
  --output-dir prototype_runs/clip_01/frames/ \
  --render-config renderer_config.json
```

`renderer_cli.py` internally launches Playwright + headless Chrome, loads `index.html`, posts inputs via `page.evaluate(...)`, waits for `RENDER_COMPLETE` event, dumps frames.

---

## 7. Quality criteria

| Criterion | Method | Threshold |
|---|---|---|
| Frame rate stability | log frame timestamps | 60 fps ± 0.5 fps over full clip |
| Frame count matches audio | `frames.length / fps = audio.duration` | within ±0.5 seconds |
| Layered composition alignment | overlay-check on a still | mouth/tail/ears anchor to expected canvas position |
| Crossfade smoothness | visual review | no popping / sudden swap on layer changes |
| Idle motion natural | visual review | character doesn't look frozen; doesn't feel hyperactive |
| No transparency holes | per-pixel check | every frame is fully opaque (alpha = 1 everywhere) |
| File size | filesystem | each PNG frame ≤ 500 KB at 1080p |

---

## 8. Failure modes

| Mode | Symptom | Response |
|---|---|---|
| Atlas misaligned across sprites | mouth jumps position when state changes | regenerate atlas with stricter `make_mascot` Stage 5.7 normalization |
| Viseme swap too rapid (visible jitter) | mouth flickers | increase `crossfade.mouth_ms` from 50→80; or increase phoneme smoothing in `phoneme_alignment.md` §5.4 |
| Expression crossfade feels mechanical | linear ramp visible | switch crossfade from linear to smoothstep |
| Background bleed at sprite edges | colored halo around character | regenerate atlas with stricter BiRefNet alpha threshold |
| Idle motion feels seasick | too much amplitude | reduce `idle_motion.y_sine_amplitude_px` from 6→3 |
| Playwright frame drop | missing PNGs | retry that frame; on persistent failure, drop to 30 fps and continue |
| Headless Chrome OOM on long clips | crash mid-render | chunk into 30-second segments, render each, concatenate frames |

---

## 9. Cost and time

| Item | Estimate |
|---|---|
| Renderer startup (headless Chrome + atlas load) | ~5-10 sec |
| Per-second of clip render | ~1.5-2 sec wall clock at 60 fps (real-time-ish) |
| 3-minute clip total | ~5-6 minutes wall clock |
| GPU cost (L40S amortized) | ~$0.20/clip |
| Disk: 1080p PNG sequence at 60 fps for 3 min | ~3-5 GB (cleaned up post-encode) |

---

## 10. Session continuity

- Renderer is deterministic given the same inputs (same atlas, script, audio, alignment, config). Re-rendering is free and produces identical output.
- Frame output is written incrementally; partial runs can be resumed by skipping existing frame indices.
- Manifest is written after render completes; presence of manifest = success indicator.

---

## 11. References

- [`../prototype_spec.md`](../prototype_spec.md) §5.3
- [`../../prd.md`](../../prd.md) §4.3.4
- [`make_mascot.md`](make_mascot.md) §4.2 — atlas config schema this renderer consumes
- [`phoneme_alignment.md`](phoneme_alignment.md) §4 — alignment format this renderer consumes
- three.js documentation (threejs.org)
- Playwright docs for headless Chrome (playwright.dev)
