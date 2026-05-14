# Checklist — Host agent (Claude Sonnet 4.6)

| | |
|---|---|
| Purpose | Bring up the Host agent generating Daramzzi's spoken Korean lines |
| FSD | [`../../fsd/llm_host.md`](../../fsd/llm_host.md) |
| Phase | Phase 1 |
| Language | English source — KO at [`../ko/llm_host.md`](../ko/llm_host.md) |

---

## Tech stack (at a glance)

- **Claude Sonnet 4.6** (proprietary, paid) — LLM
- Streaming output via Anthropic SDK
- Prompt cache (15k+ tokens for persona + bible)
- **Redis** — event bus
- **Infra**: API calls from anywhere; no GPU

Full table: [`../../fsd/llm_host.md`](../../fsd/llm_host.md) §2

---

## Session resume

Per-broadcast Host instance. Cache survives 5-min TTL via extended caching. Restart triggers one cold call to warm cache.

---

## §1. Prerequisites

- [ ] [`../../fsd/llm_host.md`](../../fsd/llm_host.md) read
- [ ] `ANTHROPIC_API_KEY` set
- [ ] System prompt written (`prompts/host_sonnet.md`):
  - [ ] Full character bible §3 inlined
  - [ ] Bible §5 speech patterns
  - [ ] Bible §6.3 hard guardrails
  - [ ] RAG citation rules
  - [ ] Emotion tag schema with examples
  - [ ] 5-8 positive + 5-8 negative few-shot examples
- [ ] [`../../fsd/rag.md`](../../fsd/rag.md) operational

---

## §2. Solo persona-consistency eval

- [ ] Run 50 varied prompts through the Host
- [ ] Manually review:
  - [ ] Korean honorifics consistent
  - [ ] Persona stays in-character (no AI references, no breaking the squirrel frame)
  - [ ] Emotion tags emitted in every line
  - [ ] No hallucinated facts (when RAG provided, citations match)
- [ ] Target: ≤ 2% out-of-character / honorific issues

---

## §3. RAG integration test

- [ ] Provide test RAG with 3 mock products
- [ ] Ask 20 fact-grounded questions
- [ ] 100% of numeric claims correctly cite RAG product+field

---

## §4. Latency / TTFT

- [ ] Warm-up call to cache 15k+ tokens
- [ ] Measure TTFT on 30 calls; verify p95 ≤ 500ms

---

## §5. Serve

- [ ] Run: `python llm_host.py serve --redis-url redis://localhost:6379/0 --in-topic director.decision.<id> --out-topic host.draft.<id>`
- [ ] Verify token-stream output reaches Redis

---

## §6. Status board

| Step | Status | Notes |
|---|---|---|
| §1 Prerequisites | ⬜ Pending | – |
| §2 Persona eval | ⬜ Pending | ≤ 2% issues |
| §3 RAG integration | ⬜ Pending | 100% citation |
| §4 TTFT check | ⬜ Pending | p95 ≤ 500ms |
| §5 Serve | ⬜ Pending | – |

---

## §7. Troubleshooting

| Issue | Cause | Response |
|---|---|---|
| Hallucinates a price | RAG ignored or empty | strengthen system prompt: "ONLY cite RAG; if not present, say 확인 후 알려드릴게요" |
| Character breaks (refers to AI) | weak bible context | add explicit "you are NOT an AI, you are a squirrel intern" guardrail |
| Banmal in formal context | persona pattern unclear | reinforce honorific rules with explicit examples |
| Missing emotion tag | output format weak | add output schema check + retry on missing tag |
