# Function Spec — RTMP output

| | |
|---|---|
| Status | Spec v1 (Phase 1 / test_3) |
| Phase | Phase 1 |
| Component | Pushes encoded H.264/AAC stream to platform RTMP endpoint |
| Source documents | [`../../prd.md`](../../prd.md) §4.3.6 |
| Last updated | 2026-05-13 |

---

## 1. Purpose and scope

### 1.1 What this FSD defines

RTMP push from the compositor to the broadcast platform. Includes local nginx-rtmp for test_3 Gate 1 (private latency measurement) and direct push to YouTube Live for Gate 2.

### 1.2 Out of scope

- Naver / Kakao / Coupang RTMP endpoints (Phase 3, separate FSDs)
- HLS / DASH delivery (platforms handle this themselves)
- Multi-bitrate transcoding (single 1080p30 stream for MVP)

---

## 2. Technology stack (locked)

| Stage | Tool | License | Why |
|---|---|---|---|
| Local RTMP receiver (test) | **nginx-rtmp-module** | BSD-2 | well-supported, low-overhead local server |
| Push library | FFmpeg's `flv` muxer (called by OBS) | LGPL | standard |
| Encryption | RTMPS for production | – | YouTube supports |

---

## 3. Inputs

| Input | Source |
|---|---|
| H.264/AAC stream | from [`compositor_obs.md`](compositor_obs.md) |
| Destination URL | env var `RTMP_DEST_URL` (e.g. `rtmps://a.rtmp.youtube.com/live2/<key>`) |

---

## 4. Outputs

The stream lands at the destination — for test_3:
- Gate 1: local nginx-rtmp at `rtmp://localhost:1935/live/test`
- Gate 2: YouTube Live unlisted broadcast

---

## 5. Configuration

### 5.1 Local nginx-rtmp (test_3 Gate 1)

```nginx
# /etc/nginx/nginx.conf
rtmp {
    server {
        listen 1935;
        chunk_size 4096;
        application live {
            live on;
            record off;
        }
    }
}
```

### 5.2 OBS push settings (Gate 2 to YouTube)

- Service: Custom
- Server: `rtmps://a.rtmp.youtube.com/live2`
- Stream key: `<YT_STREAM_KEY>` (from env)
- Video bitrate: 5000 Kbps
- Audio bitrate: 128 Kbps
- Keyframe interval: 2 sec

---

## 6. Execution

```bash
# Local nginx-rtmp (Gate 1)
sudo systemctl start nginx
# Verify: rtmp://localhost:1935/live

# Pull stream locally for review
ffplay rtmp://localhost:1935/live/test

# OBS pushes via its UI/config; nothing else to do
```

---

## 7. Quality criteria

| Criterion | Method | Threshold |
|---|---|---|
| Stream stays connected 4 hr | log RTMP keepalives | 0 disconnects |
| Bitrate stable | nginx log / YouTube Studio | within 10% of 5 Mbps target |
| End-to-end latency (compositor encode → playable on platform) | manual timing | ≤ 8s (platform-side delay dominates) |

---

## 8. Failure modes

| Mode | Symptom | Response |
|---|---|---|
| Local nginx-rtmp not running | OBS push fails | systemd auto-restart |
| YouTube rejects stream key | OBS push fails | re-fetch stream key, restart |
| Network jitter / packet loss | bitrate drops | OBS adapts via `rate_control=cbr`; if too bad, alert |
| TLS handshake fail (RTMPS) | initial connect fails | check certificates, fall back to plain RTMP if local only |

---

## 9. Cost and time

| Item | Estimate |
|---|---|
| Bandwidth (5 Mbps × 2 hr) | ~4.5 GB egress; ~$0.45 at typical cloud rates |
| nginx-rtmp | free |

---

## 10. Session continuity

- RTMP is single-shot per broadcast — restart starts a new stream key.
- For test_3, we restart from scratch on each gate run.

---

## 11. References

- [`../../prd.md`](../../prd.md) §4.3.6
- [`compositor_obs.md`](compositor_obs.md) — upstream
- nginx-rtmp-module repo
- YouTube Live streaming docs
