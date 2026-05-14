Product Requirements Document
AI-Hosted Live Commerce Platform
Status: Draft v1.0 Document type: Product spec (companion technical architecture document to follow) Last updated: May 2026


1. Vision and Goals
1.1 What we're building
A B2B SaaS that lets e-commerce brands and platforms run AI-hosted live commerce broadcasts without human hosts. Customers provide product page URLs and basic preferences; the system generates a fully scripted, AI-presented live broadcast that streams to the customer's chosen destination, with real-time AI-driven comment interaction during the broadcast.

The core value proposition: a brand can run a 60-minute live commerce broadcast for the cost of compute, scheduled at any time, with consistent quality, in any volume — without hiring, scheduling, or managing human hosts.
1.2 Why this is possible now
Three capability shifts in 2024–2026 make this viable:

Persona generation and consistency (Hunyuan Image 3.0, Imagen 4 Ultra, Nano Banana 2, Flux Kontext) now produce photorealistic Asian faces with reliable identity persistence across hundreds of generations.
Real-time talking-head models (MuseTalk 1.5, LivePortrait, EchoMimic v2) achieve broadcast-acceptable quality at near-real-time speeds on a single high-end GPU.
LLMs with strong Korean fluency and structured output (Claude, GPT) can generate live-commerce-grade scripts and triage live comments in production.

None of these alone is sufficient. The product is the orchestration of all three into a reliable broadcast pipeline that survives an hour or more of live operation.
1.3 Goals
Quality of broadcast output is the primary success metric. Viewers should not perceive the broadcast as "AI-generated" in a way that reduces engagement or trust. Quality > latency, quality > cost, quality > scope.
Hierarchical multi-tenancy from day one. The system must serve individual brand customers (e.g., a small fashion seller) and platform-scale customers (e.g., Musinsa, eBay) with seller sub-accounts, in the same product.
Configurability over opinion. Brand-tier customers expect to control tone, persona, script, pacing, and visual presentation. The product should expose configuration where reasonable and impose defaults only where uniformity protects quality.
End-to-end self-serve workflow. A brand seller should be able to log in, paste a product URL, and have a broadcast ready to launch within the system's pre-generation SLA — without sales involvement for routine broadcasts. Sales-assisted onboarding is acceptable for platform-tier contracts and persona customization.
Bilingual (Korean and English) from launch. Both the product UI and broadcast output must support Korean and English in v1. Other languages are deferred but architecturally accommodated.
1.4 Non-goals (explicitly out of scope for v1)
Generating output for distribution platforms — broadcast streams to customer-configured destinations; the company has its own service for distribution.
Producing pre-recorded video assets that are not live broadcasts (e.g., short product videos, ad creative).
Replacing all human hosts — the product is positioned as a complement and scaling lever, not a wholesale replacement.
Avatar customization beyond persona library + commissioned custom personas (no real-time customer "design your own avatar" UI in v1).


2. Users and Use Cases
2.1 Account types
The system has two account types reflecting hierarchical tenancy:

Brand accounts. Direct customers — typically a single brand, agency, or seller. They manage their own broadcasts, personas, scripts, and team members. Billed directly. Examples: a mid-sized fashion brand, a cosmetics startup, a kitchenware seller.

Platform accounts. Enterprise customers whose tenancy contains many seller sub-accounts. The platform pays at the tenancy level; sellers within the tenancy create and run broadcasts. Platform admins configure access controls, persona availability, broadcast approval workflows, and usage attribution for the sellers in their tenancy. Examples: Musinsa, eBay, Coupang.

A platform account behaves architecturally like a customer with N brand accounts under it, plus an admin layer.
2.2 User roles
Within both account types, the following roles exist (with platform admin being the only role unique to platform accounts):

Platform admin (platform accounts only): manages seller sub-accounts, persona allocation, broadcast approval policy, billing/usage views.
Account admin: top-level admin for a brand account or seller sub-account; manages users, broadcasts, integrations.
Broadcast author: creates, edits, and launches broadcasts; manages scripts and product selections.
Broadcast reviewer: reviews pre-generated broadcasts before launch; approves or rejects (typically a brand manager or compliance reviewer).
Viewer-only: can see broadcasts and analytics but cannot create or modify (e.g., executive dashboards).
2.3 Primary use cases
UC-1: Routine product broadcast. A brand seller wants to run a weekly 60-minute broadcast featuring 10 hero products from their seasonal catalog. They paste 10 PDP URLs, select hero products, choose a persona and tone, review the auto-generated script, and schedule the broadcast for a specific time.

UC-2: Catalog clearance broadcast. A seller has 800 products to move during end-of-season sale. They submit 800 PDP URLs, select 30 hero products to anchor the script narrative, and run a 2-hour broadcast. During broadcast, viewers asking about non-hero products receive AI responses powered by RAG over the full 800-product catalog.

UC-3: Platform-curated broadcast. Musinsa's editorial team curates 20 products from 8 different sellers and runs a "Musinsa Spring Picks" broadcast under the platform tenancy. Sellers' products appear with their attribution; sellers see analytics for their own products.

UC-4: Seller-initiated broadcast within platform. A small seller on Musinsa logs in via SSO from their seller dashboard, creates a broadcast for their own products under Musinsa's platform tenancy, with usage counted against Musinsa's contract.

UC-5: High-frequency broadcast operation. A brand runs 5 broadcasts per day across different product categories. Self-serve creation and scheduling are critical; sales-supported onboarding is unacceptable for routine operation.
2.4 Out-of-scope users for v1
End viewers of broadcasts — the broadcast itself is the product to viewers, not the SaaS platform.
Independent freelance live commerce hosts — not a target buyer.
Consumer creators (e.g., individual influencers) — pricing and feature set are not optimized for them in v1.


3. Scope: In and Out
3.1 In scope for v1
Hierarchical multi-tenancy with platform and brand account types.
Persona library (curated, shared across the system) and custom-commissioned personas (per-tenant exclusive).
PDP ingestion and product information extraction (existing capability — integrated, not built from scratch).
LLM-based script generation with hero product selection, tone control, and target duration.
Beat-level script editing, regeneration, and locking.
Pre-generation pipeline: script → TTS → talking-head video render → cached broadcast asset bundle.
Customer review interface: full preview of the pre-generated broadcast before launch.
Broadcast orchestration: state machine driving pre-rendered segments and real-time comment-response segments.
Real-time comment-response pipeline with RAG over full product catalog.
Multi-framing visual composition with motivated cuts (close-up, medium, wide, B-roll).
Idle loop assets per persona for transition coverage.
Stream output to customer-specified destination (RTMP push and integrations as configured).
Korean and English UI; Korean and English broadcast generation.
Audit logging and broadcast recording.
Basic analytics: viewer count over time, comment volume, comment-response logs, full broadcast recording playback.
3.2 Out of scope for v1
Real-time persona generation by customers (custom personas are commissioned via paid service with multi-day turnaround).
Multi-host broadcasts (single AI host per broadcast in v1; multi-host is v2+).
Languages beyond Korean and English.
Integration with specific external live commerce platforms beyond RTMP — assumed handled by company's existing distribution service.
Automated A/B testing of script variants.
Conversion tracking integrations (clicks, purchases) — exposed via webhook for customers to integrate themselves; we do not build attribution.
Mobile native apps for the SaaS console (responsive web is sufficient for v1).
Marketplace for third-party persona creators.
3.3 Deferred to v2 or later
Multi-host broadcasts (host + co-host, host + guest expert).
Live human takeover during broadcast (human can step in and override the AI mid-broadcast).
Scheduled recurring broadcasts (e.g., "every Tuesday at 8pm").
Persona emotion control (intensity sliders, mood presets).
Custom background scene generation per broadcast.
Customer-uploaded reference voices for cloning beyond the curated voice library.
Automated highlight clip generation post-broadcast.
Live polls, quizzes, viewer-driven branching segments.


4. Core Product Concepts
4.1 The hero product / full catalog separation
This is the architectural decision that lets the system handle 5 to 1,000+ products in a single broadcast.

Hero products are the small set (typically 5–50, customer-selected) that anchor the broadcast script. The script generator builds narrative around heroes — introductions, deep features, demonstrations, story beats. Heroes drive the visual flow of the broadcast.

Catalog products are the full set of products the customer has registered for the broadcast (up to 1,000+). Catalog products are not part of the script. They are indexed in a RAG store accessible to the comment-response pipeline. When a viewer asks "do you have this in red?" or "what about that other one?", the comment-response system retrieves relevant product context from the full catalog, not just heroes.

This means the broadcast feels like it covers the full catalog — viewers can ask about anything — but the script stays narratively coherent regardless of catalog size.

Customer experience: select all products for the broadcast, then mark some as heroes. Default heuristics (best-selling, highest-margin, customer-tagged) suggest hero candidates. Customer confirms or overrides.
4.2 The pre-render + real-time hybrid broadcast model
A live broadcast is not generated in real time end-to-end. It is composed of two segment types stitched at runtime:

Pre-rendered segments. All scripted content — product introductions, feature explanations, transitions between hero products, intro/outro — is rendered before the broadcast starts. These segments are generated using high-quality model settings (slower per frame, cleaner output) and cached as video files in object storage.

Real-time segments. Only comment-response improv is generated live during the broadcast. When a comment is selected for response, the real-time pipeline (TTS + talking-head model + composition) generates the response on demand, typically 10–30 seconds of output per response.

Both segment types use the same talking-head model (e.g., MuseTalk 1.5) with different speed/quality settings. This avoids identity drift between modes — the host looks like the same person whether pre-rendered or live.

The broadcast orchestrator stitches segments together using motivated visual cuts (see 4.4) and idle loops (see 4.5) so that transitions are imperceptible or read as intentional editing choices.
4.3 Beats as the unit of script and render
The script is structured as a sequence of beats. A beat is a self-contained unit of broadcast content:

~15–90 seconds of narrative content (product intro, feature highlight, transition, etc.)
Tagged with type (intro, hero-product-feature, transition, comment-response-window, outro, etc.)
Tagged with hero product reference (if applicable)
Tagged with visual hints (close-up, medium, wide, B-roll cutaway)
Renders to a self-contained video asset

Beats are the unit of:

Editing — customers edit text or regenerate at the beat level, not the whole script.
Locking — customers can lock a beat ("this is approved, don't change it") before regenerating others.
Rendering — each beat is an idempotent render job; re-rendering one beat does not require re-rendering the broadcast.
Playback — broadcast orchestrator plays beats in sequence, inserting comment-response segments between beats during interaction windows.
4.4 Multi-framing as glitch-defeat strategy
Rather than attempting seamless continuous-shot transitions between segments, the broadcast uses motivated visual cuts as part of its native visual grammar.

A single high-resolution source render (e.g., 1440p talking-head video) is the master content.
The broadcast composition layer dynamically crops different framings — close-up, medium, wide — from this single source.
Cuts between framings happen frequently throughout the broadcast, motivated by content (emphasis points, topic transitions, comment responses).
Because cuts are happening constantly anyway, the cut at a real segment boundary (pre-rendered → real-time, or beat → beat) is invisible — it is just another cut.

The script generator emits framing tags inline:

[medium] 안녕하세요 여러분, 오늘 정말 특별한 제품을 가져왔어요.

[cut: close-up, emphasis] 이게 진짜 인생템이에요.

[cut: medium] 자, 같이 보실까요?

[cut: B-roll, product] (product hero shot, host narration continues)

The composition layer reads these tags and executes the cuts.
4.5 Idle loops and the canonical pose
Each persona has a set of idle loop assets — short (3–5 second) seamlessly looping video clips of the host in a canonical neutral pose, with natural breathing and small movements.

Variants per persona include: neutral idle, listening (slight head tilt), reading (looking down), thinking (slight head movement), smiling (warm idle).

Idle loops cover:

The pause when a comment is being processed and the response is being generated.
Any unexpected delay in beat transitions.
Cover during compositional changes (e.g., switching scenes in OBS).
The visual default state when no scripted or real-time content is currently playing.

All beats begin and end with the host in the canonical pose, so transitions to/from idle loops are seamless.
4.6 Tone of voice as structured parameters
Tone is exposed to customers in two layers:

Preset tones — a curated set of named tones (e.g., 친근함, 전문가, 럭셔리, 활기, 차분함, 신뢰감) with predefined parameter values. Preset tones are the default and recommended path.
Free-text refinement — optional text input that nudges the preset. The system runs a tone-extraction LLM pass that converts free text into structured deltas applied to the preset parameters.

The intermediate structured representation (formality, warmth, humor, expertise signaling, energy, etc., on numeric scales) is what conditions script generation. Customers do not see the structured parameters directly, but they ensure consistency and reproducibility.
4.7 Personas as composed assets
A persona is not a single image. It is an asset bundle:

Hero portrait (canonical reference image, 4K)
Identity dataset (100–500 images of the persona at various angles, expressions, lighting)
Trained or fine-tuned talking-head model weights for this specific persona
Voice model (cloned voice or curated voice assigned to the persona)
Idle loop variants (5+ short looping clips)
Outfit variants (multiple outfit options, with consistent identity)
Background environments (compatible scenes for this persona)
Metadata (suggested tone affinity, language fluency, regional appearance, age band)

Persona creation is an internal pipeline, not a customer-facing real-time feature. Curated personas are built by the company. Custom personas are commissioned by enterprise customers and built by the same pipeline with brand input.


5. User Flows
5.1 Onboarding (brand account)
Customer signs up via website or sales-routed invite.
Account admin completes profile: brand info, language preference, default tone, default destination for broadcasts.
Account admin selects which curated personas the team will use (subset of the full library).
(Optional) Account admin commissions a custom persona — this routes to a sales/production workflow with multi-day turnaround.
Account admin invites team members and assigns roles.
Customer reaches the broadcast creation interface. A guided first-broadcast tutorial is available.
5.2 Onboarding (platform account, e.g., Musinsa)
Sales-led contract and provisioning.
Platform admin configures: total quota, persona allocation across sellers, broadcast approval policy, SSO integration with platform's existing seller authentication.
Platform admin invites or imports seller sub-accounts (typically via API or bulk CSV).
Sellers within the platform log in via the platform's SSO; from their perspective, the experience matches a brand account, scoped to the platform's policies.
Platform admin has a separate dashboard for cross-seller analytics, quota usage, and broadcast moderation.
5.3 Broadcast creation (the core flow)
Initiate. User clicks "Create Broadcast" in the console.
Product input. User pastes one or many PDP URLs (single field accepts multiple URLs separated by newlines or commas). The system begins async PDP extraction immediately upon paste.
Hero selection. As products are extracted, they appear in a list. The system suggests heroes (based on heuristics or customer history). User confirms or modifies hero selection.
Broadcast parameters. User specifies:
Target duration (free-text or preset: ~30 min, ~1 hr, ~2 hr, etc.).
Persona (from available library plus any custom personas).
Tone (preset, optionally with free-text refinement).
Additional emphasis prompt (free text — "highlight the limited-edition nature", "we're targeting 30s women", etc.).
Output destination (default from account, overridable per broadcast).
Pre-generation kickoff. User clicks "Generate." The system queues the pre-generation job. User receives an estimated completion time based on broadcast length and current queue.
Pre-generation progress. User can leave the page; receives notification when ready (in-app + email).
Review. User opens the pre-generated broadcast preview:
Full timeline view showing all beats in sequence.
Inline preview of each beat (video plus text).
Per-beat actions: edit text, regenerate beat, lock beat, delete beat.
Full broadcast preview: watch the entire generated broadcast end-to-end.
Edit cycle (optional).
User edits beat text → triggers re-generation of that beat only.
User regenerates a beat with different parameters → re-render that beat only.
User locks beats they're satisfied with.
User regenerates the script (entire or unlocked portions only).
Each edit is fast because it's beat-scoped, not broadcast-scoped.
Approve. User approves the broadcast for launch.
Schedule or launch. User chooses immediate launch or scheduled time.
5.4 Live broadcast operation
Pre-broadcast staging. N minutes before scheduled launch (or immediately if launching now), the broadcast engine allocates GPU resources, loads persona assets, primes the RAG index over the full catalog, and prepares the streaming output.
Broadcast start. Stream goes live to configured destination. Idle loop plays briefly, then the first beat begins.
Beat playback loop.
Current beat plays from pre-rendered cache.
Comment listener polls comment source on the configured cadence (default 2–3 sec).
Comment triage LLM classifies incoming comments (ignore / acknowledge in batch / answer in detail / flag for human review).
Interaction windows. At designated points (between beats, or at scripted "comment break" beats), the orchestrator selects 1–2 high-value comments for response.
Real-time response.
Cut to close-up framing on host (signaling direct viewer engagement).
Real-time pipeline kicks off: response LLM generates reply text → TTS streams audio → talking-head model renders video → composition layer streams to output.
If generation is slow, idle loop variant ("reading" or "thinking") covers.
Resume scripted content. Cut back to medium framing, next beat begins.
Broadcast end. Outro beat plays. Stream closes. Broadcast recording finalized in object storage.
Post-broadcast. User receives notification with link to recording, transcript, comment log, and analytics dashboard.
5.5 Broadcast review and operations dashboard
After a broadcast ends, the user can access:

Full recording playback.
Beat-by-beat transcript with timestamps.
Comment log with which comments received responses, what was responded, latency per response.
Viewer engagement timeline (viewer count over time, comment volume over time).
Any moderation events (flagged content, human-review-required comments).
Webhook delivery log if customer has configured outbound webhooks for analytics integration.


6. Functional Requirements
6.1 Account and identity management
Account creation supports both self-serve (brand) and sales-provisioned (platform) flows.
Platform accounts support unlimited seller sub-accounts.
SSO integration for platform accounts (SAML, OIDC; specific protocols negotiated per platform contract).
Role-based access control with the roles defined in 2.2.
Audit log for all configuration changes, broadcast creations, and approvals (retained for ≥1 year, exportable).
6.2 Persona management
Curated persona library is browsable by all tenants (subject to platform admin restrictions, if applicable).
Custom personas are scoped to the commissioning tenant and are not visible to other tenants.
Each persona exposes: preview thumbnail, sample voice clip, available outfits, available background scenes, recommended tone affinities, language fluency.
Persona usage is loggable per-broadcast for billing attribution.
Customers cannot upload their own face/voice in v1; custom persona is a commissioned service.
6.3 PDP ingestion and product management
Customer pastes one or more PDP URLs; system extracts product information using the existing PDP extraction service.
Extracted information includes (where available): product name, price, options (sizes, colors, variants), description text, descriptive images, key features, stock status, shipping info, regulatory info (where applicable).
Customer can manually edit any extracted field before broadcast generation.
Customer can manually upload product information for products without an accessible PDP.
Up to 1,000+ products per broadcast supported; system tested to perform at 1,000 products with no degradation in script quality.
Hero product selection: customer marks 5–50 products as heroes; the rest are catalog-only.
All products (heroes + catalog) are indexed in the broadcast's RAG store.
6.4 Script generation
Generated based on: hero products, target duration, persona, tone, additional emphasis prompt, language.

Output is a structured script with beats (see 4.3), framing tags (see 4.4), and TTS-ready text.

Length calibration: TTS audio length is estimated from generated text; system iterates if estimated runtime deviates from target by more than ±10%.

Compliance pass: an LLM compliance check reviews the script for obvious violations of advertising/consumer-protection requirements (claims unsupported by product data, prohibited terms, etc.). Flags issues to the customer with suggested rewrites; does not block on its own.

Script is delivered to the customer for review before any rendering begins; rendering does not start until customer approves the script.

(Note: this is a refinement of the flow in 5.3 — script approval gates rendering. Customers see the text first, approve, then renders begin. This keeps GPU work from being wasted on scripts the customer will reject.)
6.5 Beat-level operations
Edit text: customer modifies text; on save, system re-runs TTS for that beat only and re-renders the beat's video.
Regenerate beat: customer requests a new version of the beat with optional new parameters (e.g., different tone, different emphasis); script generator produces a new beat, customer reviews, accepts or regenerates again.
Lock beat: customer marks a beat as approved; subsequent script regenerations leave locked beats untouched.
Delete beat: customer removes a beat; script generator may auto-suggest a replacement transition or leave a gap.
All beat operations are idempotent and incremental — re-rendering one beat does not affect any other beat.
6.6 Pre-render pipeline
Triggered on customer approval of script.
Renders each beat in parallel where capacity allows.
Each beat render produces: video file (1440p source, 1080p delivery crop), audio file, subtitle/transcript file, metadata.
Stored in tenant-scoped object storage with a stable beat ID; cached for the lifetime of the broadcast plus retention period.
Resumable: if rendering fails for a beat, only that beat is retried.
Customer can preview each beat as it completes; full broadcast preview is available when all beats complete.
6.7 Broadcast orchestrator (live runtime)
State machine driving beat playback, interaction windows, real-time response handling, error recovery.
Stream output to configured destination via the company's existing distribution service.
Comment polling: configurable cadence per broadcast (default 2–3 sec).
Triage LLM: classifies each comment; configurable per-broadcast triage rules.
Interaction windows: configurable per broadcast — between every beat, every N beats, or only at designated comment-break beats.
Response selection: ranks queued comments by priority signals (question vs. statement, repeat askers, sentiment, product-relevance) and selects top 1–2 per window.
Real-time response generation: LLM generates response → TTS → talking-head render → composition. Target end-to-end latency <2 sec from comment selection to first frame of response.
Failure recovery: if real-time generation fails or exceeds timeout, falls back to a pre-recorded "we'll come back to that" idle clip and moves on.
6.8 Visual composition
Multi-framing crops from single 1440p source: close-up, medium, wide.
Cuts driven by framing tags from script generator.
Idle loop insertion: between segments, during real-time generation wait, during long pauses.
B-roll insertion: when script tags request product imagery, the composition layer overlays product images or short product video clips (provided by customer or extracted from PDP).
Color grading: uniform LUT applied to all generated content for visual consistency.
Output encoding: 1080p30, H.264, suitable for RTMP delivery.
6.9 Real-time comment interaction
RAG index: built per-broadcast over the full catalog of products at pre-render time.
Retrieval: comment text → embedding → top-K product context retrieval → composed prompt for response LLM.
Response LLM: generates response in persona's voice/tone, constrained to truthful product information from RAG context.
Hallucination guardrails: response LLM is instructed to refuse or defer if RAG context does not contain relevant information ("I'm not sure about that one — let me check and follow up").
Logged: every selected comment, the retrieved context, the generated response, the resulting audio/video, and timing.
6.10 Analytics and reporting
Real-time during broadcast: viewer count, comment volume, current beat, interaction window status.
Post-broadcast: full recording, transcript, comment log, response log, viewer engagement timeline, moderation events.
Cross-broadcast: aggregate analytics over time per persona, per product, per tone.
Webhook delivery: customer-configurable webhooks fire on broadcast events (start, end, comment received, response sent, error) for customer's own analytics integration.
Export: CSV/JSON export of all analytics data.
6.11 Compliance and moderation
Pre-broadcast: script compliance check (see 6.4).
Live: comment moderation filters profanity, spam, prohibited content before triage LLM sees them.
Live: response moderation re-checks generated responses before delivery to broadcast.
Configurable per-tenant: word lists, sensitivity levels, escalation rules.
Audit: every moderation decision logged.
6.12 Internationalization
UI: Korean and English, switchable per user.
Broadcast generation: Korean and English, selectable per broadcast.
Persona voice models support both languages where the persona is marked as bilingual.
Script generator and response LLM operate in the broadcast's target language.


7. Non-Functional Requirements
7.1 Quality
Persona visual quality: indistinguishable from real human in viewer-perception studies at the broadcast's intended resolution and framing.
Lip-sync accuracy: viewer-perception passing rate ≥95% (no perceptible mismatch in casual viewing).
Identity consistency: a persona looks like the same person across all beats, all framings, and all broadcasts indefinitely.
Voice naturalness: passes naïve-listener "is this AI?" test at ≥80% in target languages.
7.2 Reliability
Broadcast uptime: a launched broadcast completes successfully ≥99% of the time, accepting up to 2 brief recoverable interruptions per hour.
Pre-generation success: ≥99% of submitted scripts complete pre-generation without manual intervention.
Real-time response success: ≥98% of selected comments receive a response within target latency; remaining ≤2% gracefully fall back without dead air.
7.3 Latency
Pre-generation target: ≤1.5x broadcast runtime (e.g., 60 min broadcast pre-renders within 90 min).
Real-time comment-response: ≤2 sec from selection to first frame of response, ≤4 sec for tail (longer responses).
Beat re-render: ≤3 min for a typical beat.
UI responsiveness: all interactive operations <500ms server response, <2 sec for any operation that does work.
7.4 Scalability
Concurrent broadcasts per tenant: not limited (capacity-bound, not architecturally bound).
System-wide concurrent broadcasts: scales horizontally with GPU capacity.
Pre-generation queue: scales horizontally; queue priority based on tenant tier and scheduled launch time.
Per-broadcast catalog size: 1,000+ products tested as primary scale point; no architectural ceiling.
7.5 Security and isolation
Tenant data isolation: each tenant's broadcasts, scripts, custom personas, and analytics are inaccessible to other tenants.
Platform-tenancy: sellers within a platform are isolated from each other; platform admins have visibility per their configured policies.
Persona asset protection: custom personas cannot be exfiltrated or used outside their commissioning tenant.
API authentication: per-tenant API keys, scoped tokens, audit logging.
Data retention: configurable per tenant, with default 1 year for broadcast recordings and analytics.
Compliance: SOC 2-aligned controls; data residency options for regional regulatory requirements.
7.6 Observability
Per-broadcast traces from script generation through stream output.
GPU utilization, queue depth, pipeline latency dashboards for ops.
Alerting on broadcast failures, latency excursions, capacity thresholds.


8. System Architecture (Overview)
The detailed architecture lives in the companion technical document. This section provides the conceptual model.
8.1 Major subsystems
Tenancy and identity service. Manages account types, sub-accounts, users, roles, SSO, audit logs.

Persona service. Stores and serves persona asset bundles. Coordinates persona creation pipeline (internal-only operation for commissioning).

Product ingestion service. Wraps the existing PDP extraction capability; normalizes product data into the system's canonical product schema; manages per-broadcast product sets.

Script service. Orchestrates LLM-based script generation, beat structuring, framing tagging, length calibration, compliance pre-check. Owns beat-level edit operations.

Render farm. GPU-backed worker pool that consumes beat render jobs. Each job is idempotent. Output is cached in object storage. Workers are stateless and replaceable; the queue is the source of truth for rendering work.

Broadcast engine. The runtime that drives a live broadcast. State machine; allocates GPU pod for real-time pipeline; manages beat playback, interaction windows, comment-response generation, stream output. One broadcast engine instance per active broadcast.

RAG service. Per-broadcast vector index over the full product catalog. Used by the comment-response pipeline at broadcast runtime.

Comment ingestion and triage service. Polls customer-configured comment sources; runs triage LLM; queues high-value comments for response by the broadcast engine.

Analytics and reporting service. Captures all broadcast events, viewer telemetry, comment logs, response logs. Serves dashboards and webhook delivery.

Customer console (web app). The user interface for everything brand and platform users do. Bilingual.
8.2 Core data model (conceptual)
Tenant (brand or platform; platforms contain sub-tenants which are sellers).
User (belongs to a tenant; has a role).
Persona (curated or custom; scoped to system or to a tenant).
Product (belongs to a tenant; can be referenced in many broadcasts).
Broadcast (the top-level entity for a single broadcast event).
Script (belongs to a broadcast; contains beats).
Beat (belongs to a script; rendered into video assets).
Render asset (the actual video/audio files for a beat; stored in object storage).
Broadcast run (an instance of running a broadcast — there may be re-runs of the same broadcast with the same script).
Comment, Response (events during a broadcast run).
Analytics event (anything telemetry-worthy during a broadcast).
8.3 Tenancy model
Hierarchical: Tenant → (optional Sub-tenant) → Resources.

For brand accounts, Tenant → Resources directly.

For platform accounts, Tenant (platform) → Sub-tenant (seller) → Resources. Platform admin policies determine what sub-tenants can do (broadcast freely, require approval, restricted persona access, etc.).

Resource access is always scoped via the user's tenant + sub-tenant context.
8.4 Bilingual implementation
All user-facing strings are externalized for translation. UI defaults from user preference; can be overridden per session. Broadcast generation language is per-broadcast and independent of UI language. Models (TTS, talking-head, LLM) are selected based on the broadcast's target language; not all personas are bilingual, and persona selection in the UI filters by available languages.


9. Open Questions
These are decisions deferred or not yet made; each needs an owner and resolution before the affected component is built.

Pricing model. Per-broadcast, per-minute, per-hour-of-output, monthly subscription with quotas, or hybrid. Affects metering architecture. Owner: TBD.
Persona library size and composition for launch. Number of curated personas, demographic spread, language coverage. Owner: TBD.
Custom persona commissioning workflow. SLA for delivery, pricing, what's included (number of outfits, voice variants, etc.). Owner: TBD.
Korean regulatory disclosure. Specific labeling requirements for AI hosts under 표시광고법 and adjacent regulations; whether disclosure must be on-screen or in metadata. Owner: legal/compliance, TBD.
Platform tenancy contract terms. What's negotiable per platform: SLA tiers, white-labeling depth, data residency, audit access. Owner: enterprise sales, TBD.
Comment moderation defaults. Default sensitivity levels, default word lists, escalation rules for system-wide vs. per-tenant. Owner: TBD.
Webhook event taxonomy. Exact list of events fired and their schemas. Owner: engineering, TBD.
Approval policy for platform-tenant sellers. Default for new platform contracts: auto-approve, require platform-admin approval, configurable. Owner: product + enterprise sales, TBD.
Custom persona IP and licensing. Who owns the persona — the commissioning tenant, the company, joint? Affects contracts. Owner: legal, TBD.
Data retention defaults and legal floors. Particularly for broadcast recordings (potentially containing user comments) and audit logs. Owner: legal, TBD.


10. Risks
10.1 Product risks
Quality drift over long broadcasts. Personas may exhibit subtle artifacts or identity drift after many beats. Mitigation: investing heavily in persona pipeline reliability, fine-tuning per-persona, idle loop coverage of edge cases.
Comment interaction feels robotic. If comment selection or response timing feels off, viewers perceive the host as a chatbot rather than a host. Mitigation: careful interaction-window pacing, response variety, idle "thinking" loops, RAG-grounded responses to avoid generic content.
Hero/catalog separation confuses customers. If customers don't understand why some products get script time and others don't, they'll perceive missing coverage. Mitigation: clear UI explanation, default heuristics that pick reasonable heroes, visible indication of "covered in script" vs "available in chat."
Customer review fatigue at scale. Reviewing a 2-hour script for 1,000-product broadcast is impractical. Mitigation: section/category-level review summaries, highlighted-changes view on regeneration, locked-beat workflows.
10.2 Technical risks
Real-time pipeline latency. Hitting <2 sec response generation reliably is hard, especially on shared GPU infrastructure. Mitigation: dedicated GPU allocation per broadcast, model warm-up, streaming TTS, parallelized rendering.
Identity drift between pre-render and real-time modes. Even with the same model, different speed settings can shift output. Mitigation: extensive same-model testing, per-persona fine-tuning that fixes identity hard.
Visual cut motivation feels arbitrary. Cuts driven by mechanical timing rather than content emphasis feel wrong. Mitigation: cut-scheduling logic tied to script's emphasis tags, audio energy, and structural boundaries.
PDP extraction edge cases. Unusual product page structures, dynamic content, blocked scrapers. Mitigation: existing PDP extraction service is mature; manual override path is exposed for failures.
10.3 Business and regulatory risks
Korean regulatory action on AI-hosted commerce. Disclosure requirements may tighten; specific product categories (cosmetics, food, supplements, financial products) may face restrictions. Mitigation: configurable disclosure system, category-specific compliance review, ongoing legal monitoring.
Platform partner policy changes. A major platform partner could change AI-host policies after contract. Mitigation: contractual protections, fallback distribution capabilities, customer-driven multi-platform output.
Competitive entry. Hyperscalers or established live commerce platforms could build competing capabilities. Mitigation: depth of Korean-market specialization, persona quality, customer relationships, hierarchical-tenancy fit for platform-tier customers.
Public perception backlash. A high-profile failure ("AI host said something wrong about a product") could damage trust. Mitigation: aggressive moderation, RAG grounding, clear escalation and correction paths.
10.4 Operational risks
GPU capacity volatility. GPU pricing and availability fluctuate; sustained access at scale may require contracts. Mitigation: hybrid cloud + colo strategy, capacity planning ahead of customer demand.
Customer concentration. Early platform-tier contracts may represent large revenue concentration. Mitigation: actively pursue multiple platforms and brand customers in parallel.
Persona refresh and aging. Personas may need refreshing over time (style changes, fashion drift). Mitigation: persona versioning, customer-visible refresh notifications, gradual rollout of refreshed personas.


11. Phases (logical, not time-boxed)
These are logical sequences, not estimates. Each phase has clear entry and exit criteria; dependencies between phases are real but not linear.
Phase 0: Foundations
Tenancy service (hierarchical, with platform support).
Persona pipeline tooling (internal use, for building the curated library).
One end-to-end persona (for testing).
PDP extraction integrated.
Object storage for persona assets and render outputs.

Exit: internal users can create a tenant, store one persona, ingest products, and access the system.
Phase 1: Script and pre-render
Script generator (LLM with beat structuring, framing tags).
Beat-level data model and edit operations.
Render farm (single GPU class, single talking-head model).
Customer review interface (script preview, beat editing, video preview).
Compliance pre-check.

Exit: an internal user can create a tenant, paste PDP URLs, see a generated script, edit it, and trigger a full pre-render that produces a watchable broadcast.
Phase 2: Live broadcast and real-time interaction
Broadcast engine state machine.
RAG service (per-broadcast indexing).
Comment ingestion and triage.
Real-time response pipeline (TTS → talking-head → composition → stream).
Visual composition layer (multi-framing cuts, idle loops, B-roll).
Stream output to configured destination.

Exit: a complete pre-rendered broadcast can be launched live, comments are received and responded to during interaction windows, and the broadcast streams to a destination.
Phase 3: Multi-tenant productization
Customer console (UI, account management, billing integration).
Platform tenancy support (sub-accounts, SSO, platform admin views).
Bilingual UI and broadcast generation.
Analytics dashboards and webhooks.
Audit logging across all surfaces.
Persona library expansion (multiple personas, multiple voices, outfits, backgrounds).

Exit: an external customer can self-serve onboard, create a broadcast, run it live, and review analytics — entirely without engineering or sales involvement for the routine flow.
Phase 4: Production hardening and platform launch
Reliability investments to hit the SLOs in Section 7.
Capacity planning and elasticity.
Compliance hardening.
First platform-tier customer integration and launch.
Custom persona commissioning operationalized.

Exit: product is at the quality and reliability bar for a paying enterprise customer to run their actual live commerce operation on it.
Beyond v1
Multi-host broadcasts, scheduled recurrences, more languages, mobile apps, automated highlight generation, deeper conversion attribution, marketplace features.


12. Glossary
Beat. A discrete unit of script and rendered video — typically 15–90 seconds — that is the atomic unit of editing, locking, and rendering.
Broadcast. The top-level entity representing a single live commerce event: products, script, schedule, output destination.
Broadcast run. An instance of executing a broadcast (same broadcast can be re-run).
Catalog product. A product included in a broadcast for RAG/comment-response purposes but not featured in the script.
Custom persona. A persona commissioned for a specific tenant, exclusive to that tenant.
Curated persona. A persona built by the company for general use across the system, available to all tenants (subject to platform admin restrictions).
Hero product. A product featured in the broadcast script, with dedicated narrative time.
Idle loop. A short, seamlessly-looping video clip of the host in the canonical pose; used to cover transitions and waiting periods.
Interaction window. A scheduled time during the broadcast when comment responses are inserted.
Multi-framing. The visual pattern of cutting between close-up, medium, and wide framings, dynamically cropped from a single high-resolution source render.
Persona. The complete asset bundle representing an AI host: hero portrait, identity dataset, model weights, voice, idle loops, outfits, backgrounds, metadata.
Platform account. A tenant containing many seller sub-accounts (e.g., Musinsa, eBay).
Pre-render. The phase before broadcast where scripted segments are generated and cached.
RAG (Retrieval-Augmented Generation). The system that retrieves product context from the full catalog to answer viewer comments.
Real-time segment. A segment generated during the live broadcast in response to a comment or other live trigger.
Tone (preset / refinement). The structured parameters governing how the persona speaks; preset is a named bundle, refinement is free-text adjustment.



End of PRD.