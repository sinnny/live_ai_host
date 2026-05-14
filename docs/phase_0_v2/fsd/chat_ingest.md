# Function Spec — Chat ingest (YouTube Live)

| | |
|---|---|
| Status | Spec v1 (drafted for Phase 1 / test_3; pending implementation) |
| Phase | Phase 1 (test_3 — live runtime validation) |
| Component | Polls live chat from broadcast platform, emits structured comment events |
| Source documents | [`../../prd.md`](../../prd.md) §4.3.1, [`../deferred/test_3_spec.md`](../deferred/test_3_spec.md) |
| Last updated | 2026-05-13 |

---

## 1. Purpose and scope

### 1.1 What this FSD defines

The subsystem that ingests comments from the live broadcast platform's chat and emits structured events for downstream Moderator + Director consumption. Wraps platform-specific APIs in a uniform event interface.

### 1.2 Out of scope

- Comment authoring or reply (one-way ingest only)
- Cross-platform unification beyond schema (each platform has its own connector)
- Spam/abuse classification (handled by Moderator FSD, see [`llm_moderator.md`](llm_moderator.md))

### 1.3 Success criterion

For test_3 Gate G2 4-hour run on YouTube Live unlisted:
1. Zero comments missed (verified against YouTube Studio chat export).
2. Median ingest-to-emit latency ≤ 100ms.
3. Zero crashes over 4 hours.

---

## 2. Technology stack (locked)

| Stage | Tool | License | Why |
|---|---|---|---|
| YouTube Live chat polling | **pytchat** | MIT | mature, async-capable, handles auth + paging |
| Event bus | Redis Pub/Sub | RSALv2 / Valkey BSD-3 | low-latency in-process or distributed |
| Schema validation | jsonschema | MIT | event format guardrail |
| Infra | runs in same Docker container as `broadcast_orchestrator.md` | – | – |

### 2.1 Future platforms (deferred)

- **Naver 쇼핑라이브** — partnership-gated, separate FSD when access obtained
- **Kakao 쇼핑 라이브 / Coupang Live** — v2

---

## 3. Inputs

| Input | Source | Format |
|---|---|---|
| Broadcast platform credential | env vars (`YOUTUBE_API_KEY` or OAuth token) | string |
| Video/stream ID | from `broadcast_orchestrator` at start | string |
| Polling interval | config (default 1Hz) | seconds |

---

## 4. Outputs

Emits one event per comment to Redis topic `chat.comments.<broadcast_id>`:

```json
{
  "schema_version": 1,
  "broadcast_id": "bc_2026_05_13_001",
  "platform": "youtube",
  "comment_id": "ChQK...",
  "author": "viewer_xyz",
  "text": "이거 진짜 매워요?",
  "ts_platform": "2026-05-13T15:32:14.500Z",
  "ts_ingested": "2026-05-13T15:32:14.612Z"
}
```

---

## 5. Pipeline

```
broadcast_orchestrator → starts chat_ingest with video_id
chat_ingest:
  ├── pytchat.LiveChatAsync(video_id=...)
  ├── on each new chat item:
  │     ├── normalize to schema above
  │     ├── publish to Redis topic
  │     └── log ingest latency
  └── on disconnect: reconnect with backoff (1s, 2s, 4s, 8s, 30s cap)
```

---

## 6. Execution

```bash
python chat_ingest.py \
  --platform youtube \
  --broadcast-id bc_2026_05_13_001 \
  --video-id <yt_video_id> \
  --redis-url redis://localhost:6379/0
```

---

## 7. Quality criteria

| Criterion | Method | Threshold |
|---|---|---|
| Comment coverage | diff vs YouTube Studio export | 100% |
| Ingest latency | log timestamps | p95 ≤ 100ms |
| Reconnect resilience | kill network briefly during test | resume within 30s, no comments lost from buffer |
| Schema validity | every emitted event passes jsonschema | 100% |

---

## 8. Failure modes

| Mode | Symptom | Response |
|---|---|---|
| YouTube API rate limit | 403/429 errors | exponential backoff; if persistent, alert orchestrator (degraded state) |
| Stream offline / ended | pytchat returns end signal | emit `chat.lifecycle.ended` event, exit cleanly |
| Network blip | connection drop | reconnect with backoff |
| Comment with malformed Unicode | schema validation fail | log warning, drop comment, do not crash |

---

## 9. Cost and time

- pytchat: free (public API; OAuth quota usually generous for read)
- Compute: negligible (single thread, mostly I/O wait)
- Redis: negligible for this volume (~1 msg/sec peak)

---

## 10. Session continuity

- Stateless except for the last-ingested `comment_id` (de-duplication).
- On restart, polls from current platform position (does NOT replay history) — this is intentional; missed comments during a restart are accepted as a known limitation.
- All state derived from broadcast_id + Redis topic; no local files.

---

## 11. References

- [`../../prd.md`](../../prd.md) §4.3.1
- [`broadcast_orchestrator.md`](broadcast_orchestrator.md) — caller
- [`llm_moderator.md`](llm_moderator.md) — consumer
- pytchat repo (github.com/taizan-hokuto/pytchat)
