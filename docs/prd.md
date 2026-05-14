# Product Requirements Document

**AI-Hosted Live Commerce Platform — "Autonomous Meme-Host"**

| | |
|---|---|
| Status | Draft v2.1 |
| Document type | Product spec — source of truth |
| Supersedes | `phase_0_v1/prd_v1_photoreal_legacy.md` (May 2026, photoreal direction, deprecated by 2026-05-13 pivot) |
| Last updated | 2026-05-13 |
| v2.1 changes | Primary mascot locked to 다람찌 (§1.5, `docs/characters/daramzzi.md`). Mascot identity resolved in §8/§9. |

---

## 0. Pivot context

This document supersedes the May 2026 photoreal-direction PRD (preserved under `phase_0_v1/`). The product thesis shifted in two stages, both grounded in Phase 0 evidence:

**Pivot 1 (2026-05-13, mid-Phase 0):** photorealistic AI host → obviously-AI stylized character.

- `phase_0_v1/stage2_pulid_findings.md` — three RunPod sweeps proved PuLID identity-locks too hard for prompt-driven variation across every tested config.
- `phase_0_v1/stage4_oss_findings.md` — SOTA OSS talking-head (EchoMimic v3) fails Korean lip-sync across two sessions + five orthogonal tuning levers; the same gap applies to every OSS talking-head with public weights because `chinese-wav2vec2` has no Korean.
- Independent Korean market signal: VTuber commerce on Naver 쇼핑라이브, the 김햄찌-style mascot YouTube/TikTok ecosystem, and the 과일 불륜 TikTok genre all prove viewers are already primed to buy from non-human, obviously-synthetic personalities.

**Pivot 2 (this document, post-stack-review):** lightweight 3D rig → 2.5D sprite-puppet driven by automated asset pipeline.

- Even auto-rigged 3D (VRoid, Mixamo) requires founder hands-on time per mascot (2-4 hours minimum).
- The product premise is "no humans, AI all the way down" — that must extend to *asset creation*, not just *broadcast operation*.
- A scripted asset pipeline (`make_mascot`, `make_bg`, `make_broll`, `make_voice`) collapses asset creation to a one-command operation. The founder types a sentence; the system produces broadcast-ready assets.

Both pivots are reflected throughout this document. The old photoreal sections of v1 are not amended in place — this is a full rewrite.

---

## 1. Vision and goals

### 1.1 What we are building

A B2B SaaS that lets Korean e-commerce sellers run **fully autonomous AI-hosted live commerce broadcasts** featuring obviously-AI, entertainment-first character hosts. The seller provides product page URLs and basic preferences; the system schedules and runs the broadcast end-to-end with zero human operator and zero human performer, streaming to the seller's configured destination (YouTube Live, Naver 쇼핑라이브 from Sprint 5+, etc.).

**Core value proposition:** a seller can run a 60-120 minute live commerce broadcast for the cost of compute, scheduled at any time, in any volume, with consistent character personality and broadcast-acceptable production quality — without hiring, scheduling, or managing human hosts, riggers, illustrators, editors, or operators.

### 1.2 The "obviously AI" thesis

Photorealistic AI hosts are structurally broken in 2026: identity drift in image generators, uncanny-valley lip-sync in talking-head models, and audience distrust of "fake humans." Phase 0 evidence (`phase_0_v1/`) confirms each of these independently.

The product wins by *embracing* its AI nature instead of fighting it:

1. **Stylized character art** has no uncanny valley. A mascot whose mouth shape is one frame "wrong" is on-brand for a meme-aesthetic character, not repulsive.
2. **Identity drift becomes a non-problem.** A sprite-puppet with a fixed atlas literally cannot drift between frames.
3. **Korean entertainment commerce is already here.** VTuber commerce on Naver, the 김햄찌-style mascot economy, and 과일 불륜 TikTok all prove the audience is buying from non-human personalities. We are not asking viewers to suspend disbelief about a fake human; we are giving them a character to love.
4. **Failure modes become stylistic, not creepy.** A mistimed gesture on a hamster reads as personality; a mistimed micro-expression on a fake human face reads as wrong.

The v1 primary mascot — **다람찌**, see §1.5 — is the concrete instantiation of this thesis: a probationary squirrel show host whose cheek-stuff frames, mid-bite mumbles, and self-correcting fluster *are* the brand. Any visual or audio failure that would damage a photoreal host reads on her as character.

### 1.3 Goals

- **Autonomy is the primary success metric.** A broadcast must run start-to-finish with no human in the loop — no operator, no performer, no editor, no moderator. The founder's role during pilots is exception handling (an emergency-stop button), not operation.
- **Quality of broadcast output** is the second metric. Viewers should perceive the broadcast as *intentionally* AI-stylized, not *accidentally* bad. Quality target: charming, consistent, watchable for 60+ minutes.
- **Per-broadcast cost ≤ ₩30,000 (~$22 USD)** at MVP scale, excluding seller-side ad spend. This makes the offering viable for small Korean sellers, not just enterprise.
- **Hierarchical multi-tenancy from day one** — brand tier and platform tier, as in v1.
- **Korean-first.** v1 launches Korean-only. English/bilingual deferred to v2 (was launch in v1; pulled back to reduce scope).
- **End-to-end self-serve workflow.** A seller logs in, pastes product URLs, types a one-sentence mascot description (or picks from a library), and the system produces a broadcast-ready show within the pre-generation SLA.

### 1.4 Non-goals (v1)

- Operating a distribution platform — broadcasts push RTMP to seller-configured destinations.
- Producing non-broadcast video assets (ad creative, shorts).
- Replacing all human commerce hosts — the product is a complement and scaling lever for small/mid sellers, not a wholesale replacement of the Korean live-commerce host industry.
- Per-seller custom mascot in MVP. v1 ships with **다람찌 as the primary mascot** (see §1.5, full bible at `docs/characters/daramzzi.md`) plus a small library (~3-5 total) the seller can pick from once subsequent mascots are produced. Per-seller custom mascot is a v2 feature unlocked by the `make_mascot` pipeline.
- Photorealistic personas. Permanently out of scope; this is a strategic positioning choice, not a deferred capability.
- Real-time voice cloning of an existing human voice (legal/consent burden too high for MVP).
- Bilingual support (deferred to v2).

### 1.5 Primary mascot: 다람찌

The v1 broadcast launches with **다람찌** (Daramzzi) — formal on-air name **쇼호스트 김다람** — as the primary mascot and the first of the 3–5 mascot library. She anchors the food vertical (§2.4) and sets house style for subsequent mascots.

**One-line identity.** A chubby ground-squirrel show host on probation — earnest, anxious that she'll be cut after this shift, and physically incapable of pitching a food product without sampling it first. The probation anxiety is **internal** to her personality. There is no offscreen boss / 사장님 / PD character; that frame is explicitly out. She is a show host with quirks, not a sketch character.

**Why this character fits the v1 thesis.**
- **Cheek pouches are a renewable comedy engine for food products.** Every sample becomes a physical gag without scripted setup — critical for the 60–120 min broadcast format where script density inevitably drops.
- **Sprite-puppet rig friendly.** Round chibi silhouette, large expressive tail (its own rig layer), simple atlas of 8 expression states × 3 mouth shapes covers the live runtime.
- **Cannot fall into the uncanny valley.** A cartoon squirrel's mistimed mouth frame reads as personality — the §1.2 failure-mode-as-style thesis, instantiated.
- **Differentiated from 김햄찌** without leaving the rodent-cute lane Korean audiences already buy from.
- **Series-anchor.** Sets the "AI workforce of probationary misfits" house style; subsequent mascots in other verticals inherit the world.

**Visual brief (summary).** Warm chestnut (도토리색) fur, cream cheek/belly highlight, chipmunk dorsal stripes simplified to 1–2 dark lines for sprite legibility. Wardrobe: soft 쇼호스트 half-apron with one pocket, name tag reading **"쇼호스트 김다람 (수습)"** — the "(수습)" is visible on-air and is part of the joke. Signature prop: an 도토리 always somewhere in scene. Accent color: rust-orange / soft red for merch coherence.

**Voice brief (summary).** Standard Seoul Korean. Default 존댓말 (probationary register). Slightly higher than the speaker's neutral pitch but **not** pitched-up — anything processed kills the earnestness. Reference vibe: an earnest probationary host who really needs this gig to work out, without the K-drama-intern slapstick. A muffled "cheek-stuffed" delivery filter is a stretch goal pending Korean TTS provider validation in Phase 0 (§6); the show works with or without it — fallback strategies are specified in the bible §5.1.

**Hard guardrails (mirrored into runtime prompts).** From the bible §3.3 + §6.3:
- Never break the squirrel-host frame; no meta-commentary about being AI.
- Never reintroduce a named boss/사장님/PD character. The anxiety is internal.
- Never sassy, sarcastic, flirty, or sexualized — cute-coded, earnest, never coquettish.
- Never deliver claims beyond seller-provided product copy (also enforced by Moderator agent, §4.3.2 + §4.5).
- Never deliver legal/medical/financial advice — deflect with a flustered "그건 제가 답변드리기 어려운 부분이라…" and pivot back to the product.

**Full character bible:** `docs/characters/daramzzi.md`. The bible is the source of truth for `make_mascot` art briefs, `make_voice` voice briefs, Host-agent runtime persona prompts (§4.3.2), and Director-agent behavioral triggers. Character-affecting decisions are made in the bible first and referenced here in summary.

---

## 2. Users and tenancy

### 2.1 Account types (unchanged from v1)

- **Brand accounts.** Direct customers — a single brand, agency, or seller. Manage their own broadcasts, mascot selection, scripts, team members. Billed directly. Examples: a mid-sized 식품 brand, a 스낵 startup, a 가공식품 seller.
- **Platform accounts.** Enterprise tenancies containing many seller sub-accounts. The platform pays at the tenancy level; sellers within create and run broadcasts. Platform admins configure access controls, mascot allocation, broadcast approval workflows, and usage attribution. Examples: Naver 쇼핑라이브 (partnership-gated, Sprint 5+), Kakao 쇼핑라이브 (v2), Coupang Live (v2).

A platform account behaves architecturally like a customer with N brand accounts under it, plus an admin layer.

### 2.2 User roles (unchanged from v1)

- **Platform admin** (platform tenancy only): manages seller sub-accounts, mascot allocation, broadcast approval policy, billing/usage.
- **Account admin**: top-level admin for a brand account or seller sub-account.
- **Broadcast author**: creates, edits, and launches broadcasts; manages product selections.
- **Broadcast reviewer**: optional approval gate before broadcast goes live (brand manager or compliance reviewer).
- **Viewer-only**: read-only access to broadcasts and analytics.

### 2.3 Primary use cases

- **UC-1: Routine product broadcast.** Brand seller runs a weekly 60-minute show with 10 hero products. Pastes 10 PDP URLs, picks a mascot, reviews the auto-generated script, schedules.
- **UC-2: Catalog clearance.** Seller has 800 products to move. Submits 800 PDP URLs, selects 30 hero anchors, runs a 2-hour broadcast. Viewers asking about non-hero products receive AI responses via RAG over the full 800-product catalog.
- **UC-3: Platform-curated.** Naver 쇼핑라이브 editorial curates 20 products from 8 sellers; runs a "이번 주 픽" broadcast under the platform tenancy.
- **UC-4: Seller-initiated within platform.** A small seller on Naver logs in via SSO, creates a broadcast for their own products under Naver's tenancy.
- **UC-5: High-frequency operation.** A brand runs 5 broadcasts/day across product categories. Self-serve creation and scheduling is mandatory; sales-supported onboarding is unacceptable for routine ops.

### 2.4 First vertical: food/snacks

MVP launches with the food/snacks vertical:
- Lowest regulatory risk under Korean 표시광고법 and 식품위생법.
- Easiest auto-generated product B-roll (food on a plate doesn't require complex pose/handling shots).
- Matches the 과일 불륜 / mascot-drama aesthetic the audience already engages with.

Cosmetics is the second vertical (Sprint 8+), gated on cosmetics-specific ad-law tuning of the Moderator agent.

---

## 3. Broadcast experience

### 3.1 What a viewer sees

A 60-120 minute live show where a stylized 2.5D character mascot (the "host") talks through a product lineup, reacts to chat in real time, and runs commerce beats (price reveal, coupon drop, giveaway, "buy now" calls-to-action). The audio is the host's TTS voice; visually the host is composited over an animated background with product cards, captions, and overlays.

The show alternates between two modes:

- **Mascot mode.** The mascot is the focal element. Host talks, reacts to chat, points at on-screen product cards. Most of the show runtime.
- **Scripted-clip mode.** A pre-rendered product B-roll plays (the mascot's voiceover continues or pauses depending on the beat). Used for product reveals, transitions, "as seen in 30 seconds" segments.

The Director agent decides mode transitions in real time.

### 3.2 What a seller sees (operator console)

- Read-only stream preview.
- Live moderation flags (when Moderator catches an ad-law issue or hallucinated claim — counter only; the system handles it autonomously).
- Current scene / product / mode.
- Latency telemetry.
- **One button: EMERGENCY_LOOP.** Interrupts the show, plays a "잠시만 기다려 주세요" interstitial, halts RTMP. Used only on regression.

### 3.3 Broadcast lifecycle

1. **Author** — seller adds products, optional manual script tweaks, selects mascot + background style.
2. **Pre-generate** — system generates the script with Claude Sonnet 4.6, produces B-roll clips with Wan 2.2, embeds product RAG into Qdrant. Pre-gen SLA: ≤ 30 min for a 60-min broadcast with ≤ 20 products.
3. **Review (optional)** — broadcast-reviewer role approves; required for platform tenancy, optional for brand.
4. **Schedule + live** — broadcast starts on schedule, runs autonomously, ends on schedule or on `END_OF_SCRIPT` event.
5. **Post-broadcast** — recording archived to object storage, analytics piped to ClickHouse, usage attributed to tenancy/seller.

---

## 4. Technical architecture

### 4.1 System shape

```
                  ┌──────── OFFLINE PIPELINE (per asset, automated) ─────────┐
                  │                                                          │
                  │  make_mascot  →  Qwen-Image + LoRA training              │
                  │  make_bg      →  Qwen-Image + AnimateDiff                │
                  │  make_broll   →  Claude script + Wan 2.2 I2V             │
                  │  make_voice   →  CosyVoice 2 zero-shot clone             │
                  │                                                          │
                  └──────────────────────────┬───────────────────────────────┘
                                             │ assets
 ┌──────────────────── BROADCAST PREP (per broadcast) ─────────────────────┐
 │                                                                          │
 │  PDP ingest  →  Claude Sonnet 4.6 script generation                     │
 │              →  Beat structure + Performance Planner tags               │
 │              →  Compliance pre-check (Claude with 표시광고법 rules)      │
 │              →  Qdrant per-broadcast index (KURE + BGE-M3 embeddings)   │
 │                                                                          │
 └──────────────────────────────────┬───────────────────────────────────────┘
                                    │
 ┌──────────────── LIVE RUNTIME (per concurrent stream) ────────────────────┐
 │                                                                          │
 │   YouTube chat  →  Moderator (Haiku 4.5) →  Director (Haiku 4.5)        │
 │                                                       │                  │
 │                                                       ▼                  │
 │                                            ┌──────────────────┐         │
 │                                            │ Decides:         │         │
 │                                            │  - speak/silent  │         │
 │                                            │  - product       │         │
 │                                            │  - mode          │         │
 │                                            │  - emotion tag   │         │
 │                                            └────────┬─────────┘         │
 │                                                     │                    │
 │                  ┌──────────────────────────────────┼───────────────┐    │
 │                  ▼                                  ▼               ▼    │
 │       Host (Sonnet 4.6)  →  Moderator filter  →  CosyVoice 2    MP4    │
 │       RAG-grounded        (output pre-TTS)        streaming TTS  clip  │
 │                                                       │                 │
 │                                                       ▼                 │
 │                                          Rhubarb Lip Sync → phonemes    │
 │                                                       │                 │
 │                                                       ▼                 │
 │                                          three.js sprite-puppet         │
 │                                          (atlas-swap mouth + expression)│
 │                                                       │                 │
 │                                                       ▼                 │
 │                                          OBS compositor → FFmpeg/NVENC  │
 │                                                       │                 │
 │                                                       ▼                 │
 │                                                  RTMP push              │
 └──────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Offline asset pipeline

Each script is a one-command operation. The founder (or eventually a seller, post-MVP) types a brief; the script produces broadcast-ready assets.

#### 4.2.1 `make_mascot`

```
./make_mascot "depressed avocado with a cigarette, 80s anime aesthetic, 
               lives in a chaotic kitchen"
```

Pipeline:
1. **Brief expansion.** Claude Sonnet 4.6 takes the one-sentence input and produces a structured character bible: visual descriptors, personality, voice descriptor, motion descriptor, color palette, 25 specific image prompts.
2. **Seed generation.** Qwen-Image generates the canonical "neutral pose, neutral expression" sprite at 1024×1024.
3. **LoRA training.** AI-Toolkit (Ostris) trains a character-identity LoRA on the seed image and 5-10 augmentations. ~30-60 min on a rented H100.
4. **Sprite atlas generation.** Qwen-Image + LoRA batch-generates 24 more sprites covering 5 visemes × 5 expressions (with a few extras for transitions).
5. **Normalization.** MediaPipe detects face landmarks, auto-crops/aligns each sprite to a consistent frame, alpha-mattes the background out.
6. **Atlas packing.** Python packs all 25 sprites into a single texture atlas with UV metadata.
7. **Renderer config emission.** Outputs `mascots/<name>.json` — readable by the three.js sprite renderer.

**Founder input:** one sentence. **Wall-clock time:** ~45 min unattended. **Cost:** $5-15 in rented GPU time per mascot.

#### 4.2.2 `make_bg`

```
./make_bg --count 20 --vibe "warm kitchen, golden-hour sunset, lived-in"
```

Pipeline:
1. Claude expands the vibe into 20 specific background prompts.
2. Qwen-Image batch-generates 20 stills at 1920×1080.
3. AnimateDiff produces 4-8 second seamless loops for the subset tagged "animated."
4. Outputs `backgrounds/<vibe-name>/<n>.mp4|.png`.

**Wall-clock:** overnight batch.

#### 4.2.3 `make_broll`

Per product, run during broadcast pre-generation:

1. Seller uploads product photos to PDP or directly to asset uploader.
2. Claude Sonnet 4.6 writes a 30-60 second shot-list per product based on PDP data + persona.
3. Wan 2.2 I2V generates each clip from the product photo + shot description.
4. FFmpeg with a fixed editing template stitches transitions, adds captions.
5. Outputs `broadcasts/<id>/broll/<product>.mp4`.

**Wall-clock:** ~20 min/product unattended.

#### 4.2.4 `make_voice`

```
./make_voice "warm but slightly unhinged Korean female voice, late 20s"
```

Pipeline:
1. Claude writes a 20-second sample text in Korean.
2. Bootstrap: generate a reference audio via an existing TTS preset (CosyVoice 2 default Korean voice) reading the sample.
3. CosyVoice 2 zero-shot cloning uses the bootstrap audio as the reference voice for all future TTS in this persona.
4. Outputs `voices/<name>/ref.wav` + voice ID metadata.

**Wall-clock:** ~5 min. **Note:** v1 uses synthetic reference voices to avoid consent/legal burden of cloning real humans.

### 4.3 Live runtime architecture

#### 4.3.1 Inputs

- **Chat ingest** — pytchat (MIT) polls YouTube Live Chat API at 1 Hz; emits comment events.
- **Schedule trigger** — broadcast orchestrator (Temporal at scale, Celery at MVP) fires `BROADCAST_START`, drives the FSM through pre-rendered beats, listens for chat events for real-time interactions.

#### 4.3.2 The three LLM agents

| Agent | Model | Purpose | Latency target | Caching |
|---|---|---|---|---|
| **Moderator** | Claude Haiku 4.5 | Two-way filter: (1) classify incoming comments (spam, abuse, off-topic), (2) audit Host's drafted lines for 표시광고법 violations, hallucinated price/specs, profanity. Runs *before* TTS commits. | <100 ms p95 | 5k cached |
| **Director** | Claude Haiku 4.5 | Beat-level scheduling: which comment to answer, when to switch mode, when to fire next product, which emotion tag, when to trigger a giveaway. Reads chat-state, broadcast-state, last-N spoken lines. | <200 ms p95 | 10k cached |
| **Host** | Claude Sonnet 4.6 | Generates the spoken Korean line. RAG-grounded — quotes only specs/prices retrieved from product DB, never invents. Emits inline `<emotion=...>` tags consumed by the renderer. Persona is locked to the active mascot bible (for v1: `docs/characters/daramzzi.md` — §3 persona, §5 voice/speech, §6.3 hard guardrails are embedded directly in the system prompt). | <500 ms TTFT p95 | 15k+ cached (persona + product context) |

Why Claude over OSS LLMs for live: Korean prosody quality, prompt-cache economics (90% discount on repeated persona/context per turn), persona consistency under long context, single API ecosystem with the offline script generation.

#### 4.3.3 Korean TTS — CosyVoice 2

- **Apache 2.0**, ~150 ms first-audio-packet latency in streaming mode.
- Supports Korean natively; voice cloned per mascot via `make_voice`.
- Self-hosted on the runtime GPU. One CosyVoice 2 instance per concurrent stream.
- Fallback: GPT-SoVITS (MIT) if CosyVoice 2 degrades on a specific voice profile.
- Pre-rendered (non-real-time) narration uses IndexTTS2 for higher prosody quality where latency doesn't matter.

#### 4.3.4 Sprite-puppet renderer

The visual host. Replaces the rigged 3D character path from earlier drafts.

- **Format:** PNG texture atlas (5 viseme × 5 expression sprites + transition extras) + JSON metadata describing sprite layout, anchor points, expected idle motion.
- **Runtime:** three.js (MIT) running in headless Chrome via Playwright. Single textured plane with a sprite-swap fragment shader.
- **Mouth animation:** Rhubarb Lip Sync (MIT) consumes the TTS audio stream, emits phoneme timestamps; renderer swaps to the matching viseme sprite. Crossfade between sprites is 50 ms.
- **Expression:** Host LLM emits inline `<emotion=excited>` tags; renderer crossfades to the matching expression sprite with 300 ms blend.
- **Idle motion:** procedural — sine-wave Y-offset (gentle floating) + small random X-jitter + occasional eye-blink sprite swap. No authored animation files needed.
- **Compute:** ~50 MB GPU memory, ~5% of one GPU at 60 fps.

#### 4.3.5 Compositor

- **MVP:** OBS Studio (GPL) with obs-websocket plugin. Scene-switched by the FSM. The three.js renderer is captured via Window Capture; backgrounds are Media Sources; product cards are Browser Sources fed by the broadcast orchestrator.
- **Production (Sprint 6+):** GStreamer (LGPL) pipeline replacing OBS for lower latency and programmatic control. OBS preserved as a development/debugging environment.
- **Encoder:** FFmpeg + NVENC, 1080p30 H.264/AAC.

#### 4.3.6 Stream output

- **RTMP push** to seller-configured destination.
- v1 supports YouTube Live (open RTMP + Live Streaming API for chat).
- Sprint 5+: Naver 쇼핑라이브 (partnership-gated).
- v2: Kakao 쇼핑라이브, Coupang Live (closed APIs, business-development work).

### 4.4 RAG: Qdrant + KURE + BGE-M3

- **Embeddings (KR primary):** KURE (Korean retrieval embedding model). Used for the hero retrieval path on Korean product copy.
- **Embeddings (multilingual fallback):** BGE-M3 (MIT). Used when product copy contains substantial English or for mixed-language seller catalogs.
- **Vector store:** Qdrant (Apache 2.0). One collection per broadcast. Auto-rebuilt at pre-gen. Includes both hero products and the full long-tail catalog for chat-time retrieval.
- **Retrieval strategy:** Host LLM is required to cite RAG hit IDs in any line containing a price or spec. The Moderator independently re-validates these citations against the source before allowing the line to TTS.

### 4.5 Compliance and safety

**Korean 표시광고법 + 식품위생법 compliance** is non-negotiable for the food vertical.

- **Pre-broadcast compliance check.** The full script passes through a Claude Sonnet 4.6 call with the relevant Korean ad-law rules in the prompt. Flagged segments require seller revision before approval.
- **Live moderation (Moderator agent).** Every Host-drafted line is filtered before TTS. Violations trigger regeneration with a corrective prompt; persistent failures escalate to `EMERGENCY_LOOP`.
- **Hallucination defense.** Host is RAG-grounded; Moderator independently re-validates retrieved facts. Numeric claims (price, weight, calorie count) must match the product DB to within a configured tolerance, or the line is rejected.
- **Audit log.** Every comment, Director decision, Host draft, Moderator verdict, TTS output, and frame-rendered timestamp is written to ClickHouse for post-hoc review. The system can replay any broadcast slice exactly.

---

## 5. Cross-cutting concerns

### 5.1 Latency budget

End-to-end: **comment received → first visible-on-stream response.**

| Stage | Budget | Notes |
|---|---|---|
| Chat poll + ingest | 100 ms | pytchat 1 Hz tail |
| Moderator (in-comment classification) | 50 ms | Haiku, cached prompt |
| Director decision | 200 ms | Haiku, cached prompt |
| Host generation (TTFT) | 500 ms | Sonnet, large cache hit |
| Moderator (host output audit) | 50 ms | Haiku, parallel with first TTS chunk |
| CosyVoice 2 first audio | 150 ms | streaming mode |
| Rhubarb phoneme alignment | <16 ms | per audio chunk |
| three.js sprite swap | <16 ms | per frame |
| OBS compositor + encode | 100 ms | NVENC H.264 |
| RTMP buffering (platform-side) | 200 ms | not ours to fight |
| **Total** | **~1.4 s** | inside 1.5 s p95 target |

### 5.2 Per-stream economics (target, 2-hour broadcast)

| Cost line | Estimate |
|---|---|
| Real-time LLM (Claude Sonnet 4.6 Host + Haiku 4.5 Director/Moderator, with caching) | ~$3-4 |
| Script generation LLM (Sonnet 4.6, pre-gen) | ~$1-2 |
| CosyVoice 2 TTS (self-hosted, GPU amortized) | ~$2 |
| Renderer + compositor GPU (L40S or 4090, 2 hr) | ~$4-8 |
| B-roll generation (Wan 2.2, batch, amortized) | ~$2-3 |
| Storage + bandwidth | ~$1 |
| **Per-stream total** | **~$13-20** |

Target retail price per broadcast: ₩30,000-50,000 (~$22-37 USD). Gross margin 30-60% at MVP scale; improves as renderer GPU is shared across concurrent streams (each renderer thread uses ~5% of a GPU).

### 5.3 Observability

- **Prometheus + Grafana + OpenTelemetry** for runtime metrics (latency p50/p95/p99 per stage, GPU/CPU/memory, RTMP health, FSM state distribution).
- **ClickHouse** for high-cardinality event logging (comments, LLM calls, Moderator verdicts, audio packets).
- **Sentry or self-hosted equivalent** for application errors.
- **Per-broadcast trace** retrievable via broadcast ID for post-hoc debugging.

### 5.4 Data model (high level)

- **`tenant`** — brand or platform tenancy.
- **`account`** — user accounts under a tenancy; roles per §2.2.
- **`mascot`** — sprite atlas + voice profile + persona; owned by tenant or system.
- **`broadcast`** — scheduled show; references products, mascot, script.
- **`broadcast_beat`** — script unit (mascot mode block or scripted-clip block).
- **`product`** — PDP-derived product record; per-tenant.
- **`broadcast_event`** — high-volume log of every comment, LLM call, decision, audio packet (ClickHouse).
- **`audit_decision`** — Moderator's verdict on a Host line, with reasoning.

Primary DB: Postgres. Cache + queues: Redis (or Valkey). Object storage: S3-compatible (MinIO self-host or Cloudflare R2).

---

## 6. Phase 0 v2 — validation plan

The single experiment that derisks the entire post-pivot stack.

### 6.1 Hypothesis

> Given the locked stack (sprite-puppet + Claude split + CosyVoice 2 + three.js + OBS + RTMP), a 10-minute fully autonomous mock broadcast on rented infrastructure produces broadcast-acceptable output at p95 latency ≤ 1.5 s with zero compliance violations and zero persona-consistency failures across the run.

### 6.2 Setup (1 week build)

1. **Build `make_mascot` pipeline** — Claude brief expander, Qwen-Image generation, AI-Toolkit LoRA training, MediaPipe normalization, atlas packer, renderer config emitter.
2. **Build three.js sprite-puppet renderer** — ~200 lines, atlas + config in, parameterized mouth/expression/idle out, exposes WebSocket API.
3. **Wire the live runtime** — chat ingest (scripted comment injection for the test) → Haiku moderator → Haiku director → Sonnet host (RAG over 3 fake food products) → moderator audit → CosyVoice 2 streaming → Rhubarb → three.js → OBS → local RTMP server.
4. **Run on rented infra** — one H100 or L40S, $2-4/hr.

### 6.3 Two validation gates

- **Gate 1 — Latency.** 50 scripted comments injected over 10 minutes. Measure p50/p95/p99 of end-to-end latency. **Pass:** p95 ≤ 1.5 s.
- **Gate 2 — Stability + quality.** A 4-hour mock broadcast with one synthetic comment per minute. Measure:
  - Persona consistency: manual review of all spoken lines, count "out of character" instances (target: ≤ 2% of lines). For v1: alignment with `docs/characters/daramzzi.md` §3 + §5.
  - Ad-law violations: manual review of all spoken lines against 식품 표시광고법, count violations (target: 0).
  - GPU memory drift, RTMP dropouts, FSM deadlocks (target: 0 over 4 hrs).
  - Mascot visual coherence: no rendering glitches, no atlas misalignment, no missing visemes (target: 0).
  - **TTS feasibility (다람찌 cheek-stuff filter).** Verify Korean TTS provider can render the muffled/cheek-stuffed delivery natively, OR validate one of the two fallback paths from `docs/characters/daramzzi.md` §5.1 (pre-rendered interjection library, or visual-only cheek frames with no audio filter). Pass: at least one of the three paths works in production.

### 6.4 Cost + duration

- 1 week of build (Claude implementer + founder review)
- ~$200-400 in GPU rental (build + measurement runs)
- 1 day of measurement + analysis

### 6.5 Outcomes

- **Both gates pass** → commit to MVP build on this stack. Sprint 1 begins.
- **Gate 1 fails** → the failing stage identifies the specific bottleneck (TTS first-packet too slow, LLM TTFT too high, etc.). Targeted fix or stage swap; rerun gate.
- **Gate 2 fails on persona** → tune Host prompts and RAG; consider increasing model size temporarily.
- **Gate 2 fails on compliance** → tune Moderator prompts and rule set; this is a tunable, not a fundamental.
- **Gate 2 fails on visual coherence** → swap MediaPipe normalization or atlas packing approach; isolated to one pipeline stage.

The full plan is tracked in `phase_0_v2/` (test_3 spec to follow).

---

## 7. Post-validation roadmap

| Sprint | Window | Deliverables |
|---|---|---|
| 0 | Phase 0 v2 (1 wk) | Validation test_3 passes both gates |
| 1 | Wk 2-3 | Full asset pipeline (`make_mascot`, `make_bg`, `make_broll`, `make_voice`) productionized + tested with 3 mascot variants |
| 2 | Wk 4-5 | Broadcast orchestrator + Director FSM hardened. Seller-facing console MVP (Next.js + FastAPI). |
| 3 | Wk 6-7 | First mascot art locked + first 5-product test broadcast end-to-end on YouTube Live |
| 4 | Wk 8-9 | Compliance hardening (식품 ad-law rules, hallucination defense, audit log). First closed beta with 1-2 food sellers. |
| 5 | Wk 10-12 | Naver 쇼핑라이브 partnership integration (gated on partnership negotiation). Multi-tenant data isolation hardened. |
| 6 | Wk 13-14 | Cosmetics ad-law tuning. Second vertical ready. |
| 7 | Wk 15-16 | GStreamer compositor swap-in (production latency improvement). Kubernetes + NVIDIA GPU Operator (multi-stream scale). |
| 8+ | post-MVP | Per-seller custom mascot via `make_mascot` self-service. Per-seller voice via `make_voice`. Kakao 쇼핑라이브, Coupang Live integrations. Bilingual (Korean + English). |

---

## 8. Open questions

1. **Mascot identity — RESOLVED.** v1 primary mascot locked: **다람찌** (ground squirrel show host on probation, see §1.5 and `docs/characters/daramzzi.md`). The next 2–3 mascots in the 3–5 library — covering adjacent verticals — are deferred to post-Phase-0 spec.
2. **Multi-tenancy isolation depth.** Per-tenant separate Qdrant collections (decided) but separate Postgres schemas vs row-level isolation TBD.
3. **Operator console authentication.** SSO with Naver/Kakao required for platform tenancy; brand-tier email+password sufficient for MVP.
4. **Recording retention policy.** Default 90 days hot, 1 year cold? Per-tenant configurable? Compliance review needed.
5. **Pricing model.** Per-broadcast flat fee, per-broadcast + per-comment-handled, per-minute-streamed, or per-month subscription. Customer development needed in Sprint 4.
6. **Naver 쇼핑라이브 partnership terms.** RTMP push allowed? Comment API access terms? Required ad-law disclosures? Business development workstream from Sprint 3.
7. **Korean copyright on AI-generated mascots.** Defensive registration of mascot identity as a trademark recommended before public launch; legal review needed.

---

## 9. What this PRD does not promise

This is v2 draft. Things explicitly *not* committed yet:

- The v1 primary mascot is locked: 다람찌 (§1.5, `docs/characters/daramzzi.md`). Specific TTS provider and the feasibility of the cheek-stuff delivery filter are pending Phase 0 validation (§6.3 Gate 2). Subsequent mascots in the 3–5 library are not yet specified.
- Specific UI of seller console (wireframes are Sprint 2 work).
- Final pricing.
- Exact list of compliance rules in the Moderator prompt (Sprint 4 with Korean ad-law specialist).
- Multi-language support (deferred to v2 product release).

---

## 10. References

### Phase 0 v1 (deprecated, photoreal direction)

- `phase_0_v1/prd_v1_photoreal_legacy.md` — original PRD that this document supersedes.
- `phase_0_v1/Phase0 execution plan final.md` — locked Phase 0 v1 plan; outcomes captured below.
- `phase_0_v1/stage2_pulid_findings.md` — PuLID identity-lock evidence (three RunPod sweeps).
- `phase_0_v1/stage4_oss_findings.md` — EchoMimic v3 Korean lip-sync failures (two sessions + five tuning levers).
- `phase_0_v1/runpod_phase0_plan.md` — Phase 0 v1 infrastructure plan.
- `phase_0_v1/Phase0 checklist.md` / `Phase0 checklist_ko.md` — Phase 0 v1 checklists (English/Korean).

### Phase 0 v2 (current)

- `phase_0_v2/` — to be populated. test_3 spec coming next.

### Character bibles

- `characters/daramzzi.md` — 다람찌 (v1 primary mascot). Source of truth for art, voice, runtime persona, and behavioral guardrails. See §1.5 for the in-PRD summary.

### Memory pointers

- `~/.claude/projects/-Users-shinheehwang-Desktop-projects-00-live-ai-host/memory/project_live_ai_host.md` — locked architecture and pivot context.
- `~/.claude/projects/-Users-shinheehwang-Desktop-projects-00-live-ai-host/memory/project_pulid_flux_findings.md` — Phase 0 v1 evidence summary.
- `~/.claude/projects/-Users-shinheehwang-Desktop-projects-00-live-ai-host/memory/project_echomimic_v3_findings.md` — Phase 0 v1 evidence summary.
