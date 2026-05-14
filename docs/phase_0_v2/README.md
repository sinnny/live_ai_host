# Phase 0 v2 — Sprite-puppet + Autonomous Runtime Validation

Active workspace for the post-pivot Phase 0. Replaces `phase_0_v1/`, which validated the photoreal direction deprecated by the 2026-05-13 pivot.

## Current focus: prototype before test_3

Scope was reduced after technical review: instead of going straight to a full live-runtime validation (`test_3`), we first run a smaller **visual-feasibility prototype** — a single 1-3 minute offline MP4 clip rendered from a founder-written Korean script. Cuts spend from ~$100 → ~$15 and wall-clock from ~1 week → ~1-2 days.

If the prototype passes the four pass-conditions in [`prototype_spec.md`](prototype_spec.md) §1.3 → proceed to test_3 (now in [`deferred/`](deferred/)). If it fails → post-mortem and replan before spending more.

## Folder structure

```
docs/phase_0_v2/
├── README.md                 ← this file
├── prototype_spec.md         ← CURRENT scope, pass criteria
│
├── fsd/                      ← 36 FSDs (English, technical source of truth)
│   ├── [Phase 0 v2 — current] make_mascot, tts, phoneme_alignment, renderer, orchestrator
│   ├── [Phase 1 — test_3]    chat_ingest, llm_moderator, llm_director, llm_host, rag,
│   │                          tts_streaming, renderer_live, compositor_obs,
│   │                          rtmp_output, broadcast_orchestrator
│   ├── [Phase 2 — MVP]       make_bg, make_broll, make_voice, compositor_gstreamer,
│   │                          operator_dashboard, data_model, multi_tenancy,
│   │                          audit_log, observability, storage,
│   │                          compliance_pre_check, pricing_billing
│   └── [Phase 3 — post-MVP]  make_mascot_v2, make_voice_v2, compliance_runbook,
│                              naver_platform, kakao_platform, coupang_platform,
│                              bilingual_extension, seller_onboarding, analytics_dashboard
│
├── checklist/
│   ├── en/                   ← 36 English source-of-truth checklists
│   └── ko/                   ← 36 Korean translations
│
└── deferred/
    └── test_3_spec.md        ← full live-runtime validation, resurrects after prototype passes
```

## FSD coverage by phase

| Phase | When written | FSD count |
|---|---|---|
| **Phase 0 v2** (current — prototype) | written 2026-05-13 | 5 |
| **Phase 1** (test_3 live-runtime) | written 2026-05-13 | 10 |
| **Phase 2** (MVP production) | written 2026-05-13 | 12 |
| **Phase 3** (post-MVP, speculative) | written 2026-05-13 as skeletons | 9 |
| **Total** | | **36** |

Each FSD has a paired English checklist + Korean translation, totaling **108 documents (36 × 3)**.

Phase 1+ FSDs were written in advance to support session continuity (a fresh Claude can read FSDs to understand future work). Phase 3 docs are skeletons noting open dependencies; they'll be fleshed out when their phase activates.

## Execution order (for the current prototype work)

1. **Atlas first** — follow [`checklist/en/make_mascot.md`](checklist/en/make_mascot.md) (or [`ko`](checklist/ko/make_mascot.md))
2. **Prototype clip** — drive via [`checklist/en/orchestrator.md`](checklist/en/orchestrator.md) (or [`ko`](checklist/ko/orchestrator.md))
3. **Pass/fail decision** — apply [`prototype_spec.md`](prototype_spec.md) §1.3 criteria

The four sub-component checklists (tts, phoneme_alignment, renderer, encode) are referenced by the orchestrator checklist; you don't usually run them in isolation.

## How to read this folder

- **Want to execute right now?** → start with `checklist/en/make_mascot.md` or `checklist/ko/make_mascot.md`.
- **Want to understand the tech stack of a component?** → read `fsd/<component>.md` §2.
- **Want to know what comes after the prototype?** → `deferred/test_3_spec.md` and the Phase 1 FSDs.
- **Want to know the whole product picture?** → `../prd.md` is the source of truth.
- **Session disconnected?** → every checklist has a "Session resume" section at the top. Open the relevant checklist, find the first unchecked `[ ]`, resume from there.

## Static artifacts (in `scripts/test_3/`, not docs)

- [`../../scripts/test_3/mascot/daramzzi/prompts.json`](../../scripts/test_3/mascot/daramzzi/prompts.json) — 24 hand-written sprite generation prompts. Replaces the Claude API call previously specified in `fsd/make_mascot.md` §5.1.
- [`../../scripts/test_3/script_schema.json`](../../scripts/test_3/script_schema.json) — JSON Schema for prototype clip scripts. IDE-validatable.

## Why we didn't just amend phase_0_v1

`phase_0_v1/` documents the photoreal direction whose failure motivated the pivot. Those findings are still load-bearing context (they are *why* this stack looks the way it does), so they are preserved in place rather than rewritten. Treat `phase_0_v1/` as read-only historical evidence; new work happens here.
