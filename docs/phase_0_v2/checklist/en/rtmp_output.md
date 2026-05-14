# Checklist — RTMP output

| | |
|---|---|
| Purpose | Configure RTMP push (local nginx-rtmp for Gate 1, YouTube Live for Gate 2) |
| FSD | [`../../fsd/rtmp_output.md`](../../fsd/rtmp_output.md) |
| Phase | Phase 1 |
| Language | English source — KO at [`../ko/rtmp_output.md`](../ko/rtmp_output.md) |

---

## Tech stack (at a glance)

- **nginx-rtmp-module** (BSD-2) — local RTMP receiver
- **FFmpeg flv muxer** (LGPL) — called by OBS, standard
- **RTMPS** — for YouTube production push
- **Infra**: nginx on the L40S host (Gate 1) + YouTube Live (Gate 2)

Full table: [`../../fsd/rtmp_output.md`](../../fsd/rtmp_output.md) §2

---

## Session resume

Single-shot per broadcast. Re-running starts a new stream.

---

## §1. Prerequisites (Gate 1 — local)

- [ ] [`../../fsd/rtmp_output.md`](../../fsd/rtmp_output.md) read
- [ ] nginx with rtmp module installed: `apt install libnginx-mod-rtmp` (or compile)
- [ ] nginx config has rtmp block (per FSD §5.1)
- [ ] Port 1935 reachable on the L40S

---

## §2. Local nginx-rtmp dry run

- [ ] Start nginx: `sudo systemctl start nginx`
- [ ] Verify port: `sudo ss -tlnp | grep 1935`
- [ ] Push from OBS to `rtmp://localhost:1935/live/test`
- [ ] Pull with ffplay: `ffplay rtmp://localhost:1935/live/test` — verify video plays

---

## §3. Prerequisites (Gate 2 — YouTube)

- [ ] Create unlisted broadcast in YouTube Studio
- [ ] Copy RTMPS URL + stream key
- [ ] Set env: `RTMP_DEST_URL=rtmps://a.rtmp.youtube.com/live2/<key>`

---

## §4. YouTube push test

- [ ] Configure OBS Stream settings with YouTube RTMPS URL + key
- [ ] Start streaming from OBS
- [ ] Verify YouTube Studio shows "Receiving stream" within 30s
- [ ] Click "Go Live"; verify the unlisted broadcast plays end-to-end

---

## §5. Stability check (during Gate 2 4-hr run)

- [ ] Monitor RTMP connection: nginx log shows keepalives every 10s
- [ ] Watch for disconnects in OBS log
- [ ] Verify bitrate stays within 10% of 5 Mbps target

---

## §6. Status board

| Step | Status | Notes |
|---|---|---|
| §1 Local prerequisites | ⬜ Pending | – |
| §2 Local dry run | ⬜ Pending | – |
| §3 YouTube prerequisites | ⬜ Pending | – |
| §4 YouTube push test | ⬜ Pending | – |
| §5 Stability check | ⬜ Pending | for Gate 2 |

---

## §7. Troubleshooting

| Issue | Cause | Response |
|---|---|---|
| nginx port 1935 blocked | firewall | open port locally, or use loopback only |
| YouTube rejects stream key | expired key | refresh in Studio, update env |
| TLS handshake fails | RTMPS issue | ensure OBS supports RTMPS; check certs |
| Bitrate adapting downward | network jitter | OBS rate_control=cbr; check uplink |
