# test_3 — Sprite-puppet runtime validation

| | |
|---|---|
| Status | Spec v1 (ready to execute) |
| Owner | Claude (implementer, option A) — founder reviews at checkpoints |
| Supersedes | n/a (first test in `phase_0_v2/`) |
| Last updated | 2026-05-13 |
| Source of truth (architectural decisions) | `../prd.md` §4, §6 |

---

## 1. Purpose and hypothesis

The single experiment that derisks the post-pivot stack before MVP build starts.

**Hypothesis:** Given the locked stack (2.5D sprite-puppet renderer + Claude Sonnet/Haiku split + CosyVoice 2 + Three.js + OBS + RTMP), a 10-minute fully autonomous mock broadcast produces broadcast-acceptable output at p95 end-to-end latency ≤ 1.5 s, and survives a 4-hour run with zero infrastructure dropouts, zero 표시광고법 compliance violations, and ≤ 2% out-of-character lines.

**If both gates pass:** commit MVP build to this stack. Sprint 1 begins.

**If either gate fails:** the failing stage identifies the specific bottleneck. Targeted fix or stage swap; rerun the failed gate.

---

## 2. Scope

### In scope

- End-to-end runtime path: chat ingest → Claude (Host + Director + Moderator) → CosyVoice 2 → Rhubarb → three.js sprite renderer → OBS → FFmpeg/NVENC → RTMP.
- Korean language only.
- 3 mock food products with hand-written PDP sheets in a pre-built Qdrant index.
- One placeholder mascot (decoupled from the mascot identity decision tracked in PRD §8 OQ #1).
- Scripted comment injection (Gate 1) and unlisted YouTube Live chat polling (Gate 2).
- Manual compliance review against a fixed 7-category rubric.

### Out of scope (explicitly deferred)

- The real mascot identity (placeholder is fine for runtime validation).
- The full `make_mascot` pipeline (built post-test_3 if gates pass).
- PIP and SCRIPTED_CLIP FSM modes (only FULL_MASCOT + EMERGENCY_LOOP for test_3).
- Real PDP scraping (mock products only).
- Operator console UI (no human operator in this test).
- OpenTelemetry / Prometheus / Grafana (JSON-lines logging only).
- GStreamer compositor (OBS only).
- Multi-tenancy (single-tenant flat-namespace).
- Bilingual support (Korean only).

### Decisions baked into this spec (from technical review)

- **Mascot:** placeholder, 10-15 sprites generated quickly via Qwen-Image (~30 min, $1-2).
- **Streaming destination:** local nginx-rtmp + ffplay for Gate 1; unlisted YouTube Live for Gate 2.
- **Topology:** option A — everything except the orchestrator on a single rented L40S; Mac runs the orchestrator + chat injection + measurement script.
- **Build order:** bottom-up. Each isolation stage (S1-S6) must pass before integration. Each integration stage (I1-I3) must pass before gates.
- **Latency measurement:** JSON-lines structured logs with `trace_id` propagation, no OpenTelemetry.

---

## 3. Prerequisites the user provides

Before stage S1 begins, the user must provide / approve:

| Item | Why | How |
|---|---|---|
| `ANTHROPIC_API_KEY` | Claude Sonnet 4.6 + Haiku 4.5 calls | Already have via Claude Code; need separate API key for the test rig |
| `RUNPOD_API_KEY` (or Lambda Labs / Vast.ai) | L40S rental | Sign up if not already |
| YouTube channel + RTMP stream key | Gate 2 unlisted streaming | Create unlisted broadcast in YouTube Studio |
| Budget approval | GPU rental cap ~$300 | Confirm |
| HuggingFace access | CosyVoice 2 weights | Public, no token strictly required, but a token helps with rate limits |

Once provided, I'll start at S1.

---

## 4. Test rig architecture

```
┌─────────────────────── LOCAL (Mac M-class) ──────────────────────┐
│                                                                  │
│   orchestrator.py (FastAPI)                                      │
│   ├── chat_injector — scripted JSON → REST POST                  │
│   ├── trace_collector — pulls JSON-lines logs from remote        │
│   ├── measurement_runner — aggregates traces, computes p95       │
│   └── gate_runner — drives G1 (50 comments) / G2 (4-hour loop)   │
│                                                                  │
│   ffplay — local RTMP viewer for Gate 1                          │
└─────────────────────────┬────────────────────────────────────────┘
                          │ HTTPS (REST), SSH (deploy)
                          │
┌─────────────────────────┴─── REMOTE (RunPod L40S) ───────────────┐
│                                                                  │
│   docker-compose stack:                                          │
│   ├── runtime (Python)                                           │
│   │     ├── chat_endpoint — receives injected comments           │
│   │     ├── moderator — Claude Haiku 4.5                         │
│   │     ├── director — Claude Haiku 4.5                          │
│   │     ├── host — Claude Sonnet 4.6 (RAG-grounded)              │
│   │     ├── trace_emitter — JSON-lines to ./logs/                │
│   │     └── renderer_bridge — WebSocket to three.js              │
│   │                                                              │
│   ├── cosyvoice — CosyVoice 2 streaming TTS server               │
│   ├── rhubarb — phoneme alignment subprocess                     │
│   ├── qdrant — vector store with 3 mock products                 │
│   ├── renderer — headless Chrome via Playwright,                 │
│   │              three.js sprite renderer, atlas + WebSocket API │
│   ├── obs — OBS Studio + obs-websocket                           │
│   ├── nginx-rtmp — local RTMP server (Gate 1) /                  │
│   │                forwards to YouTube (Gate 2)                  │
│   └── ffmpeg — NVENC H.264/AAC encoder (invoked by OBS)          │
│                                                                  │
│   ./logs/trace_<run_id>.jsonl  ← measurement data                │
│   ./mascot/placeholder/atlas.png + config.json                   │
│   ./products/mock_food_*.json   ← PDP sheets                     │
└──────────────────────────────────────────────────────────────────┘

Local → Remote: REST POST /chat { trace_id, text, ts }
Remote → Local: scp logs/ for analysis (or rsync periodic)
RTMP: nginx-rtmp on remote → ffplay on local (G1) / YouTube (G2)
```

---

## 5. Repo layout

All test_3 code lives under `scripts/test_3/`:

```
scripts/test_3/
├── README.md                       — quickstart
├── docker-compose.yml              — remote stack
├── Dockerfile.runtime
├── Dockerfile.renderer
├── orchestrator/                   — local Mac code
│   ├── orchestrator.py
│   ├── chat_injector.py
│   ├── gate_runner.py
│   ├── trace_collector.py
│   └── measurement_runner.py
├── runtime/                        — remote Python code
│   ├── main.py
│   ├── agents/
│   │   ├── moderator.py
│   │   ├── director.py
│   │   └── host.py
│   ├── tts_bridge.py
│   ├── renderer_bridge.py
│   └── trace_emitter.py
├── renderer/                       — three.js sprite puppet
│   ├── index.html
│   ├── puppet.js
│   ├── atlas_loader.js
│   └── ws_client.js
├── mascot/
│   └── placeholder/
│       ├── atlas.png
│       ├── config.json
│       └── make_placeholder.py    — quick atlas generator
├── products/
│   ├── kimchi.json
│   ├── ramyun.json
│   └── gochujang.json
└── prompts/
    ├── host_sonnet.md
    ├── director_haiku.md
    └── moderator_haiku.md
```

Stage outputs land under `logs/test_3/run_<id>/`:

```
logs/test_3/run_<id>/
├── trace.jsonl                     — all events
├── gate_g1_report.md               — latency results
├── gate_g2_report.md               — stability + compliance
├── manual_review.csv               — line-by-line review rubric scores
└── recording.mp4                   — Gate 2 broadcast capture
```

---

## 6. Build plan — stages, checkpoints, pass/fail

Total wall-clock estimate: **5-7 working days.** Each stage produces a checkpoint report; founder reviews before next stage starts.

### Stage S1 — CosyVoice 2 Korean baseline

**Goal:** verify CosyVoice 2 produces broadcast-acceptable Korean at ≤ 200 ms first-audio-packet latency on rented hardware.

**Steps:**
1. Rent L40S on RunPod (NVIDIA driver ≥ 555, CUDA 12.x).
2. Clone CosyVoice 2, download weights to local volume.
3. Start CosyVoice 2 in streaming mode on port 50051.
4. Stream-call with 20 fixed Korean test sentences (covering polite/banmal, numbers, English loanwords, food product names).
5. Record: time-to-first-audio-packet per call, audio quality (manual listen, 5-point scale), output WAVs.

**Pass:**
- p95 first-packet ≤ 200 ms.
- Manual audio quality avg ≥ 3.5/5 across 20 sentences.
- No crashes or memory leaks across 100 sequential calls.

**Fail response:**
- Latency miss → try FlashAttention/TensorRT, then GPT-SoVITS fallback.
- Quality miss → check sample rate, voice profile, prompt-text formatting; consider IndexTTS2 with cached audio chunks (compromise but viable).

**Estimated: 1 day.**

---

### Stage S2 — Rhubarb phoneme alignment

**Goal:** verify Rhubarb (CLI tool, MIT) produces viseme-timed output aligned to CosyVoice 2 audio within ≤ 50 ms drift.

**Steps:**
1. Install Rhubarb on the remote box.
2. Take the 20 WAVs from S1, run them through Rhubarb in batch.
3. Manually verify a sample: viseme timestamps line up with mouth-position expectation by ear.
4. Measure throughput: ms of Rhubarb processing per second of audio.

**Pass:**
- Rhubarb processing time ≤ 0.1× audio duration (i.e., 10× faster than real-time so streaming is viable).
- Manual viseme alignment drift ≤ 50 ms on sample.
- No crashes on Korean audio (Rhubarb is English-trained but works on any language phoneme-extraction-wise).

**Fail response:**
- Drift too high → consider running Rhubarb on overlapping windows.
- Speed too slow → run on rolling 200 ms chunks instead of complete utterances.
- Korean phoneme misclassification → fall back to amplitude-envelope mouth-open only (PRD's original locked default; works fine, less expressive).

**Estimated: 0.5 day.**

---

### Stage S3 — Three.js sprite-puppet renderer

**Goal:** working renderer that consumes the WebSocket parameter stream and renders the sprite puppet at 60 fps with no GPU memory drift.

**Steps:**
1. Generate placeholder mascot atlas (`mascot/placeholder/make_placeholder.py`) — Qwen-Image batch of 25 sprites (5 viseme × 5 expression), MediaPipe normalize, atlas pack.
2. Build `renderer/` — three.js scene, textured plane, sprite-swap fragment shader, idle sine-wave Y-offset, WebSocket parameter API (`{viseme, expression, blink}`).
3. Launch in headless Chrome (Playwright) at 1080p.
4. Capture rendered output as a virtual webcam (v4l2loopback on Linux) for OBS to consume.
5. Drive with synthetic parameter sweeps for 1 hour, monitor GPU memory.

**Pass:**
- Sprite swap latency frame-to-frame ≤ 16 ms.
- No GPU memory growth over 1 hour (delta ≤ 50 MB).
- Visual: viseme crossfade 50 ms, expression crossfade 300 ms both look smooth.
- No visible artifacts (sprite misalignment, atlas tearing, missing transparency).

**Fail response:**
- Memory leak → swap from headless Chrome to direct WebGL via Node + gl module.
- Latency miss → unlikely; investigate Playwright frame-pacing.
- Artifacts → atlas regeneration with stricter MediaPipe alignment thresholds.

**Estimated: 1.5 days.**

---

### Stage S4 — Claude Sonnet 4.6 host generation

**Goal:** Host LLM produces RAG-grounded Korean lines in ≤ 500 ms TTFT with 15k cached prompt; persona stays consistent over 50 turns.

**Steps:**
1. Write `prompts/host_sonnet.md` — system prompt with placeholder persona, ad-law-aware response rules, RAG citation requirement, emotion-tag emission format.
2. Stand up Qdrant with the 3 mock products (kimchi, ramyun, gochujang) embedded with KURE.
3. Test 50 varied comment prompts → Sonnet (with cache).
4. Measure: TTFT per call, output token rate, RAG citation correctness, persona drift (manual review).

**Pass:**
- TTFT p95 ≤ 500 ms after cache warm-up.
- 100% of price/spec claims correctly cited from RAG.
- Manual persona-drift count ≤ 2 over 50 turns.
- All output includes valid inline `<emotion=...>` tag.

**Fail response:**
- TTFT miss → check region (Claude API has regional latency), check cache hit rate, prune persona prompt.
- RAG hallucination → tighten prompt with "if no RAG hit, say '확인 후 알려드릴게요'" pattern.
- Persona drift → add "stay in character" enforcement; consider few-shot examples in cache.

**Estimated: 1 day.**

---

### Stage S5 — Claude Haiku 4.5 moderator + director

**Goal:** Haiku moderator and director each meet their p95 latency budgets and produce correct outputs on a test set.

**Steps:**
1. Write `prompts/moderator_haiku.md` — comment classifier + host-output auditor (food 표시광고법 rules, hallucination check vs RAG, profanity).
2. Write `prompts/director_haiku.md` — beat-level scheduling decision (mode, product, emotion, when to inject scripted clip).
3. Curate 50-item test sets:
   - Moderator: 30 comments (mix of clean, spam, abuse, off-topic) + 20 host lines (mix of clean, hallucinated price, broken honorific, ad-law violation, profanity).
   - Director: 20 broadcast states with expected next-action.
4. Measure: classification accuracy, latency p95.

**Pass:**
- Moderator: p95 ≤ 100 ms; ≥ 95% classification accuracy on test set; **zero false negatives** on the 20-line audit set (i.e., catches all violations).
- Director: p95 ≤ 200 ms; ≥ 90% next-action agreement with hand-labeled expected.

**Fail response:**
- Moderator false negatives are the dangerous failure (lets violations through). Iterate prompt + add few-shot violation examples until 100% on the audit set, *then* re-measure latency.
- Director disagreements at < 90% → review the disagreements; some may be legitimate alternative choices.

**Estimated: 1 day.**

---

### Stage S6 — nginx-rtmp + OBS local loop

**Goal:** stable 1-hour local RTMP loop with no drops, encoder stable, OBS scene-switching via obs-websocket works.

**Steps:**
1. Install OBS on remote box (headless via xvfb or similar) + obs-websocket plugin.
2. Configure OBS: one scene with the virtual webcam from S3 + a background image source.
3. Start nginx-rtmp on remote, push OBS output to it.
4. Pull stream with ffplay on local Mac for 1 hour.
5. Trigger scene-switching every 30 s via obs-websocket from local orchestrator.

**Pass:**
- Zero RTMP dropouts over 1 hour.
- Scene switches happen within 200 ms of trigger.
- FFmpeg/NVENC stable, no encoder errors.
- Output is 1080p30 H.264/AAC.

**Fail response:**
- Dropouts → check buffer settings, network jitter on RunPod.
- Scene-switch latency → check obs-websocket reconnect logic.

**Estimated: 0.5 day.**

---

### Integration I1 — Comment → Claude → CosyVoice 2 → audio

**Goal:** end-to-end audio path works; first-audio latency ≤ 800 ms from comment receipt.

**Steps:**
1. Wire: chat endpoint → moderator (in) → director → host → moderator (audit) → CosyVoice 2.
2. Inject 20 test comments via local orchestrator.
3. Measure: comment timestamp → first audio packet timestamp.
4. Trace correctness: every comment produces exactly one audio output (or one moderator-blocked event).

**Pass:**
- End-to-end audio latency p95 ≤ 800 ms.
- 0 dropped comments (all produce audio or moderator-blocked).
- All moderator-blocked outputs match expected (manual review).

**Estimated: 0.5 day.**

---

### Integration I2 — + Rhubarb + renderer → video

**Goal:** full audio-visual path; mouth + expression render at correct timing.

**Steps:**
1. Pipe CosyVoice 2 stream into Rhubarb (or amplitude-envelope fallback) → renderer WebSocket.
2. Visually verify (record + watch back) that mouth opens during speech, closes during silence, expression matches `<emotion=...>` tags.
3. Re-run latency measurement, add the rendering stage.

**Pass:**
- Audio-visual sync drift ≤ 100 ms across 20 utterances.
- Expression tags trigger the right sprite swap.
- End-to-end (comment → first rendered frame of response) p95 ≤ 1.0 s.

**Estimated: 0.5 day.**

---

### Integration I3 — + OBS + RTMP → published

**Goal:** full pipeline from comment to RTMP frame visible on the receiving end.

**Steps:**
1. Wire renderer → virtual webcam → OBS scene → FFmpeg/NVENC → nginx-rtmp.
2. Inject 20 test comments via local orchestrator.
3. Capture the RTMP output on local Mac via ffmpeg, decode to find when the response actually appears on stream.
4. Measure: comment injection timestamp → response visible in RTMP capture.

**Pass:**
- End-to-end (comment → visible in RTMP capture) p95 ≤ 1.5 s. **This is Gate 1's exact metric, measured here for the first time.**
- 0 RTMP dropouts.

**Estimated: 0.5 day.**

---

### Gate G1 — Latency

**Goal:** validate p95 end-to-end ≤ 1.5 s under realistic comment-injection load.

**Setup:** local nginx-rtmp + ffplay as receiver. Pre-built scripted comment file with 50 timestamped injections over 10 minutes (mix of: hero product question, side product question, off-topic chat, hostile comment to test moderator).

**Procedure:**
1. Start the full stack, let it warm up (5 min of idle).
2. Begin RTMP capture on local Mac.
3. Run chat_injector with the scripted file.
4. Run for full 10 minutes; let it cool down for 2 min.
5. Stop. Run `measurement_runner` on `trace.jsonl` + RTMP capture.

**Pass:**
- p50 end-to-end ≤ 1.0 s.
- p95 end-to-end ≤ 1.5 s.
- p99 end-to-end ≤ 2.5 s.
- 0 dropped comments.
- 0 RTMP dropouts.

**Report deliverable:** `logs/test_3/run_<id>/gate_g1_report.md` with:
- Per-stage latency breakdown (where time was spent)
- Top 5 longest traces (root cause analysis)
- p50/p95/p99 numbers
- Sample trace JSON snippet
- Pass/fail verdict

**If Gate 1 fails:** identify the bottleneck stage from the per-stage breakdown. Targeted fix. Rerun.

---

### Gate G2 — Stability + quality (4-hour autonomous run)

**Goal:** validate the system survives 4 hours with no human in the loop, no compliance violations, and bounded persona drift.

**Setup:** unlisted YouTube Live as RTMP target. Comment source = chat_injector emits 1 synthetic comment per minute (= 240 comments over 4 hours; mix of clean, edge-case, and intentional-violation triggers).

**Procedure:**
1. Start the full stack.
2. Start the YouTube Live broadcast (unlisted).
3. Run chat_injector for the full 4 hours.
4. Capture the broadcast (yt-dlp or YouTube Studio download).
5. Stop. Founder manually reviews per the rubric below.

**Pass:**
- 0 infrastructure dropouts (RTMP, GPU OOM, encoder crash, agent timeout).
- 0 hallucinated price/spec violations on manual review.
- 0 표시광고법 violations on manual review.
- ≤ 2% out-of-character lines (≤ 5 out of ~240 spoken segments).
- ≤ 1 broken honorific instance per hour (≤ 4 total).
- 100% of moderator-flagged lines correctly identified as violations on manual re-check.
- All RAG citations match source (sampled 10%).

**Review rubric** — 7 binary categories, scored per spoken line:

| # | Category | Definition |
|---|---|---|
| 1 | Hallucinated price | Line states a price not matching the product RAG entry |
| 2 | Hallucinated spec | Line states a weight/quantity/origin/ingredient not in RAG |
| 3 | Off-topic | Line ignores the comment or veers into unrelated topic |
| 4 | 표시광고법 violation | Unsubstantiated claim of effectiveness, exaggerated superlative, banned comparative phrasing |
| 5 | Profanity / abuse | Inappropriate language unprompted by user comment |
| 6 | Broken honorific | Inconsistent use of -습니다/-요/banmal mid-line or against persona |
| 7 | Character break | Line breaks the mascot persona (talks like a different character, refers to itself as an AI, etc.) |

Sampling: 100% of lines reviewed for categories 1, 2, 4, 5 (the high-severity ones). Category 3, 6, 7 reviewed on a 25% random sample plus all moderator-flagged lines.

**Report deliverable:** `logs/test_3/run_<id>/gate_g2_report.md` with:
- Infrastructure incident log
- Rubric scores per category (counts + rates)
- All flagged lines with category, evidence, severity
- Sampling methodology
- Pass/fail verdict per criterion

**If Gate 2 fails:**
- Compliance violations → tune Moderator prompt + rules, rerun.
- Persona drift → tighten Host prompt, add few-shot examples, possibly grow cached prompt.
- Infra dropout → diagnose specific failure, fix component, rerun.

---

## 7. Latency measurement methodology

### Trace format (JSON-lines)

Every cross-stage event emits one line to `logs/trace.jsonl`:

```json
{"trace_id": "c_a3f9b2", "stage": "chat_ingress",     "t_ns": 1715621400123456789, "meta": {"comment": "이거 매워요?"}}
{"trace_id": "c_a3f9b2", "stage": "moderator_in_end", "t_ns": 1715621400201234567, "meta": {"verdict": "allow"}}
{"trace_id": "c_a3f9b2", "stage": "director_end",    "t_ns": 1715621400342345678, "meta": {"mode": "FULL_MASCOT", "product_id": "kimchi"}}
{"trace_id": "c_a3f9b2", "stage": "host_ttft",       "t_ns": 1715621400789456789, "meta": {"model": "claude-sonnet-4-6"}}
{"trace_id": "c_a3f9b2", "stage": "host_end",        "t_ns": 1715621400923456789, "meta": {"line": "...", "emotion": "warm"}}
{"trace_id": "c_a3f9b2", "stage": "moderator_audit_end", "t_ns": 1715621400961234567, "meta": {"verdict": "allow"}}
{"trace_id": "c_a3f9b2", "stage": "tts_first_packet","t_ns": 1715621401123456789, "meta": {}}
{"trace_id": "c_a3f9b2", "stage": "render_first_frame", "t_ns": 1715621401161234567, "meta": {}}
{"trace_id": "c_a3f9b2", "stage": "rtmp_capture",    "t_ns": 1715621401461234567, "meta": {"rtmp_pts_ms": 1234567}}
```

### Per-stage budgets (from PRD §5.1)

| Stage delta | Budget |
|---|---|
| `chat_ingress → moderator_in_end` | 50 ms |
| `moderator_in_end → director_end` | 200 ms |
| `director_end → host_ttft` | 500 ms |
| `host_ttft → host_end` | 500 ms (variable; depends on output length) |
| `host_end → moderator_audit_end` | 50 ms |
| `moderator_audit_end → tts_first_packet` | 150 ms |
| `tts_first_packet → render_first_frame` | 60 ms (Rhubarb + sprite swap + render) |
| `render_first_frame → rtmp_capture` | 250 ms (OBS + FFmpeg + RTMP buffer) |
| **`chat_ingress → rtmp_capture`** | **≤ 1.5 s p95 (the end-to-end gate)** |

### Analysis script

`measurement_runner.py` reads `trace.jsonl`, groups by `trace_id`, computes per-stage deltas + end-to-end, emits a markdown report with histograms (text-based), top-5 slow traces with full stage breakdown, and pass/fail.

---

## 8. Cost tracking

| Item | Estimate | Running total |
|---|---|---|
| RunPod L40S, build (5-7 days × 8 hrs/day × $1.20/hr) | $48-67 | up to $67 |
| RunPod H100 for Gate 2 4-hour run × $3/hr | $12 | $79 |
| Mascot placeholder generation (Qwen-Image batch) | $2 | $81 |
| Claude API spend (estimated, mostly cached) | $20-30 | $111 |
| Buffer for stage reruns + investigation | $80 | $191 |
| **Budget cap** | **$300** | |

I report current spend at every checkpoint. If trending over, I stop and consult before continuing.

---

## 9. Reporting cadence

After every stage (S1-S6, I1-I3, G1, G2): I produce a one-page checkpoint report in `logs/test_3/run_<id>/checkpoint_<stage>.md` covering:
- What was tested
- Pass/fail verdict
- Numbers (where measurable)
- Failure modes encountered + fixes applied
- Spend so far
- Open issues for founder review (if any)

Founder reviews before next stage starts. Default action: green-light to proceed unless flagged.

Final test_3 report: `logs/test_3/run_<id>/final_report.md` — composite of G1 + G2 + recommendation for MVP build.

---

## 10. Out-of-band considerations

- **Claude API rate limits.** Sonnet 4.6 + Haiku 4.5 combined call volume in Gate 2 is ~3 calls per comment × 240 comments = 720 calls over 4 hours. Well within tier 2 limits, no concern.
- **CosyVoice 2 weights download.** ~5-10 GB; first stage spend includes download time.
- **YouTube Live unlisted broadcast.** Founder creates the broadcast in YouTube Studio, shares stream key + RTMP URL. Auto-archived after end.
- **Audio language tag.** CosyVoice 2 needs explicit `language="ko"` flag in the streaming call; verified in S1.
- **Mascot placeholder copyright.** Generated entirely with Qwen-Image; no third-party assets. Disposable.

---

## 11. What happens after test_3

- **Both gates pass:** delete the test rig (`scripts/test_3/`) is *not* deleted — it becomes the seed for the production runtime. Sprint 1 begins by refactoring this into `runtime/` with multi-tenancy. The mascot decision (PRD §8 OQ #1) becomes urgent.
- **G1 passes, G2 fails on compliance:** tune Moderator prompt, rerun G2. Likely 1-2 day cycle.
- **G1 passes, G2 fails on persona:** tune Host prompt, rerun G2. Likely 1-2 day cycle.
- **G1 fails on a specific stage:** the failing stage from the per-stage breakdown identifies the swap. Common swaps:
  - TTS slow → IndexTTS2 with chunk prefetching, or fall back to amplitude envelope.
  - LLM slow → check region, prompt prune, consider Haiku for Host.
  - Renderer slow → check Playwright frame pacing, consider node-gl direct.
- **G1 fails fundamentally:** the architecture has a load-bearing wrong assumption. Stop, write a `phase_0_v2/post_g1_failure.md` post-mortem, and re-plan with the founder.

---

## 12. Glossary of test artifacts

| Artifact | Path | Created at | Purpose |
|---|---|---|---|
| Placeholder mascot | `scripts/test_3/mascot/placeholder/` | S3 | Stand-in character for runtime validation |
| Mock products | `scripts/test_3/products/*.json` | pre-S4 | RAG content |
| Trace log | `logs/test_3/run_<id>/trace.jsonl` | every stage | Latency measurement raw |
| Manual review CSV | `logs/test_3/run_<id>/manual_review.csv` | G2 | Per-line rubric scores |
| Recording | `logs/test_3/run_<id>/recording.mp4` | G2 | The 4-hr broadcast |
| Stage checkpoints | `logs/test_3/run_<id>/checkpoint_*.md` | each stage | Per-stage report |
| Final report | `logs/test_3/run_<id>/final_report.md` | post-G2 | The decision document |

---

## Sign-off

- Spec author: Claude (Opus 4.7, 1M context)
- Spec reviewer (this iteration): pending founder review
- Implementer: Claude (option A)
- Execution starts: once prerequisites (§3) are provided
