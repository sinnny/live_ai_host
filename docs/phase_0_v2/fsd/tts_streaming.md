# Function Spec — TTS streaming mode (CosyVoice 2)

| | |
|---|---|
| Status | Spec v1 (Phase 1 / test_3) |
| Phase | Phase 1 |
| Component | Streaming-mode extension of `tts.md` for live broadcasts |
| Extends | [`tts.md`](tts.md) (same model, different invocation pattern) |
| Source documents | [`../../prd.md`](../../prd.md) §4.3.3 |
| Last updated | 2026-05-13 |

---

## 1. Purpose and scope

### 1.1 What this FSD defines

CosyVoice 2 in **streaming mode** — first audio packet emitted ~150ms after first input text token, instead of waiting for full line. Required for live broadcast latency budget.

Inherits everything from [`tts.md`](tts.md) §2 (tech stack) and §10 (session continuity).

### 1.2 Delta from offline mode

| Aspect | Offline ([`tts.md`](tts.md)) | Streaming (this FSD) |
|---|---|---|
| Input pattern | full script JSON | text tokens arrive incrementally from Host |
| Output pattern | single WAV file | PCM stream chunks |
| Latency | not critical | first packet ≤ 150ms |
| Output destination | filesystem | Redis topic / WebSocket |
| Backpressure handling | n/a | required if downstream slow |

---

## 2. Technology stack (locked)

Same as [`tts.md`](tts.md) §2, plus:

| Stage | Tool | License | Why |
|---|---|---|---|
| Streaming I/O | CosyVoice 2 streaming API | Apache 2.0 | built-in streaming inference |
| Audio publish | Redis with binary payload | – | low-latency intra-process |
| (Alternative) WebSocket | `websockets` Python | BSD | direct to renderer |

---

## 3. Inputs

Streaming text tokens from Host:

```json
{
  "stream_id": "host_turn_123",
  "broadcast_id": "bc_2026_05_13_001",
  "token": "이거는",
  "is_final": false,
  "voice_ref_id": "daramzzi_voice_v1",
  "speed_modifier": 1.0
}
```

Plus inline emotion-tag-strip: input text may contain `<emotion=...>` tags; TTS streaming strips them before synthesis.

---

## 4. Outputs

PCM audio chunks published to Redis topic `tts.audio.<broadcast_id>`:

```json
{
  "stream_id": "host_turn_123",
  "chunk_idx": 0,
  "sample_rate": 24000,
  "pcm_data_b64": "...",
  "duration_ms": 50,
  "is_final": false,
  "phoneme_hints": [...] // if available from model
}
```

50ms chunks, mono, 24kHz S16LE.

---

## 5. Pipeline

```
host_token_stream → tts_streaming
  ├── strip emotion tags
  ├── accumulate text until punctuation/N chars
  ├── send to CosyVoice 2 streaming.synthesize(
  │     prompt=accumulated, voice_ref=..., stream=True)
  ├── for each output PCM chunk:
  │     publish to Redis topic
  └── on is_final from Host:
        flush remaining text, emit final chunk with is_final=true
```

---

## 6. Execution

```bash
python tts_streaming.py serve \
  --redis-url redis://localhost:6379/0 \
  --in-topic host.tokens.<id> \
  --out-topic tts.audio.<id> \
  --voice-ref voice/daramzzi_ref.wav
```

---

## 7. Quality criteria

| Criterion | Method | Threshold |
|---|---|---|
| First-packet latency | timestamp logs | ≤ 150ms from first text token |
| Audio continuity | listen for gaps/clicks | smooth playback |
| Korean prosody | manual listen | inherits [`tts.md`](tts.md) §7 quality |
| Backpressure handling | overload test | graceful degradation, no crashes |

---

## 8. Failure modes

| Mode | Symptom | Response |
|---|---|---|
| Model overload (too many concurrent streams) | latency spike | queue with timeout; reject if queue > N |
| Voice ref OOM | crash | preload voice ref at startup, never reload during stream |
| Text accumulator backed up | TTFA breach | flush more aggressively (lower text threshold) |
| Downstream (renderer) slow | Redis buffer growing | drop oldest chunks (audio glitch acceptable for live recovery) |

---

## 9. Cost and time

Same as [`tts.md`](tts.md) §9 but per-broadcast rather than per-clip:

| Item | Estimate |
|---|---|
| Per-broadcast (2 hr, ~10 min of actual speech) | ~$1.50 amortized GPU |

---

## 10. Session continuity

- Voice reference loaded once at startup, kept resident.
- No per-stream state beyond accumulator buffer.
- Restart: re-subscribe to in-topic, discard in-flight stream_id (renderer can re-request or accept gap).

---

## 11. References

- [`tts.md`](tts.md) — base FSD (offline mode)
- [`../../prd.md`](../../prd.md) §4.3.3
- [`llm_host.md`](llm_host.md) — upstream
- [`renderer_live.md`](renderer_live.md) — downstream
- CosyVoice 2 streaming API docs
