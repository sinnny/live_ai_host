# Checklist — TTS streaming mode

| | |
|---|---|
| Purpose | Bring up CosyVoice 2 streaming TTS for live broadcasts |
| FSD | [`../../fsd/tts_streaming.md`](../../fsd/tts_streaming.md) |
| Extends | [`tts.md`](tts.md) (offline base) |
| Phase | Phase 1 |
| Language | English source — KO at [`../ko/tts_streaming.md`](../ko/tts_streaming.md) |

---

## Tech stack (at a glance)

Same as [`tts.md`](tts.md) plus:

- **CosyVoice 2 streaming API** (Apache 2.0)
- **Redis** binary publish (50ms PCM chunks)
- (Alternative) **websockets** Python (BSD) — direct to renderer
- **Infra**: RunPod L40S (same box as offline TTS)

Full table: [`../../fsd/tts_streaming.md`](../../fsd/tts_streaming.md) §2

---

## Session resume

Voice ref loaded once at startup, stays resident. No per-stream state beyond accumulator buffer. Restart re-subscribes to Redis in-topic.

---

## §1. Prerequisites

- [ ] [`../../fsd/tts.md`](../../fsd/tts.md) offline mode validated (its checklist done)
- [ ] [`../../fsd/tts_streaming.md`](../../fsd/tts_streaming.md) read
- [ ] Voice reference present: `voice/daramzzi_ref.wav`
- [ ] Redis running

---

## §2. Streaming-mode dry run

- [ ] Feed a fixed Korean sentence as a single payload to streaming API
- [ ] Verify first PCM packet arrives ≤ 150ms after request
- [ ] Verify final packet has `is_final=true`

---

## §3. Latency p95 check

- [ ] Run 30 streaming synth calls with varied lengths
- [ ] Verify TTFA p95 ≤ 150ms
- [ ] Audio continuity: stitched playback is smooth (no gaps)

---

## §4. Backpressure test

- [ ] Artificially slow the downstream consumer
- [ ] Verify oldest chunks are dropped gracefully (no crash)
- [ ] Audio glitches OK during overload; recovery should be automatic

---

## §5. Serve

- [ ] Run: `python tts_streaming.py serve --redis-url redis://localhost:6379/0 --in-topic host.tokens.<id> --out-topic tts.audio.<id> --voice-ref voice/daramzzi_ref.wav`
- [ ] Verify chunks flow from Host → TTS → renderer

---

## §6. Status board

| Step | Status | Notes |
|---|---|---|
| §1 Prerequisites | ⬜ Pending | offline TTS must work first |
| §2 Streaming dry run | ⬜ Pending | TTFA ≤ 150ms |
| §3 Latency p95 | ⬜ Pending | – |
| §4 Backpressure | ⬜ Pending | – |
| §5 Serve | ⬜ Pending | – |

---

## §7. Troubleshooting

| Issue | Cause | Response |
|---|---|---|
| TTFA > 150ms | text accumulator threshold too high | lower min-chars-before-synth |
| Audio gaps mid-stream | downstream slow | check backpressure handling |
| Voice ref OOM on load | model + voice ref too big for VRAM | preload only at startup; keep resident |
| Emotion tags in audio | tag stripper failed | check regex / inline tag handler |
