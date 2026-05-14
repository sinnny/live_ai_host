# Checklist — Chat ingest (YouTube Live)

| | |
|---|---|
| Purpose | Stand up pytchat-based chat ingestion for a test_3 broadcast |
| FSD | [`../../fsd/chat_ingest.md`](../../fsd/chat_ingest.md) |
| Phase | Phase 1 |
| Language | English source — KO at [`../ko/chat_ingest.md`](../ko/chat_ingest.md) |

---

## Tech stack (at a glance)

- **pytchat** (MIT) — YouTube Live chat polling
- **Redis** Pub/Sub (Valkey BSD-3 / RSALv2) — event bus
- **jsonschema** (MIT) — event validation
- **Infra**: same Docker container as broadcast_orchestrator

Full table: [`../../fsd/chat_ingest.md`](../../fsd/chat_ingest.md) §2

---

## Session resume

Stateless ingest. Last-seen `comment_id` is in Redis. Restart resumes from current platform position.

---

## §1. Prerequisites

- [ ] [`../../fsd/chat_ingest.md`](../../fsd/chat_ingest.md) read
- [ ] YouTube Live unlisted broadcast created
- [ ] Video ID copied from YouTube Studio
- [ ] Optional: YouTube Data API key (`YOUTUBE_API_KEY`) if hitting rate limits
- [ ] Redis running and reachable

---

## §2. Install + smoke test

- [ ] `pip install pytchat` in Docker image
- [ ] `python -c "import pytchat; print(pytchat.__version__)"` succeeds
- [ ] Smoke test on a public live stream: `python chat_ingest.py --video-id <public_live> --dry-run` — prints comments to stdout

---

## §3. Connect to your test broadcast

- [ ] Launch the unlisted broadcast on YouTube (go live in Studio)
- [ ] Run: `python chat_ingest.py --platform youtube --broadcast-id <id> --video-id <yt_video_id> --redis-url redis://localhost:6379/0`
- [ ] Verify first comment from a test post arrives in Redis: `redis-cli SUBSCRIBE chat.comments.<id>`

---

## §4. Resilience checks

- [ ] Briefly drop network (`sudo ifdown eth0; sleep 5; sudo ifup eth0`) — ingest reconnects, no crash
- [ ] Restart the ingest process mid-broadcast — resumes from current position (older comments NOT replayed; documented limitation)

---

## §5. Status board

| Step | Status | Notes |
|---|---|---|
| §1 Prerequisites | ⬜ Pending | – |
| §2 Install + smoke | ⬜ Pending | – |
| §3 Connect to broadcast | ⬜ Pending | – |
| §4 Resilience checks | ⬜ Pending | – |

---

## §6. Troubleshooting

| Issue | Likely cause | Response |
|---|---|---|
| 403/429 from YouTube | rate limit | exponential backoff (built in); add API key if persistent |
| `LiveChatAsync` returns end signal immediately | broadcast not live yet | wait for Studio to show "live" status |
| Unicode warning on comment | malformed emoji | drop comment, continue |
| Reconnect storm | flapping network | cap backoff at 30s (built in) |
