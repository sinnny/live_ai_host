# Checklist — Moderator agent (Claude Haiku 4.5)

| | |
|---|---|
| Purpose | Bring up the Moderator agent for two-way filtering during test_3 |
| FSD | [`../../fsd/llm_moderator.md`](../../fsd/llm_moderator.md) |
| Phase | Phase 1 |
| Language | English source — KO at [`../ko/llm_moderator.md`](../ko/llm_moderator.md) |

---

## Tech stack (at a glance)

- **Claude Haiku 4.5** (proprietary, paid) — LLM
- **anthropic** Python SDK (MIT)
- Anthropic prompt cache — 90% discount on cached system prompt
- **Redis** — event bus
- **Infra**: API calls from anywhere; no GPU needed

Full table: [`../../fsd/llm_moderator.md`](../../fsd/llm_moderator.md) §2

---

## Session resume

Each broadcast has its own Moderator instance. Restart re-subscribes to Redis topic. System prompt cache is rebuilt on first call after restart (~1 cold call).

---

## §1. Prerequisites

- [ ] [`../../fsd/llm_moderator.md`](../../fsd/llm_moderator.md) read
- [ ] `ANTHROPIC_API_KEY` set in env
- [ ] System prompt written and reviewed (`prompts/moderator_haiku.md`)
- [ ] Test sets prepared:
  - [ ] 30 comments labeled (spam/abuse/off-topic/clean)
  - [ ] 20 host lines labeled (hallucinated price/spec, ad-law violation, profanity, honorific break, character break, clean)
- [ ] Redis running

---

## §2. Prompt + few-shot offline eval

- [ ] Run offline eval: `python llm_moderator.py eval --test-set test_sets/moderator/`
- [ ] **Comment classification**: accuracy ≥ 95% on labeled set
- [ ] **Host audit (most important)**: **zero false negatives** on the 20-violation set
- [ ] **Host audit false positive rate**: ≤ 10%
- [ ] If false-negative > 0: iterate prompt with more violation few-shots, re-eval

---

## §3. Latency check

- [ ] Warm-up call (caches the system prompt): one dummy call
- [ ] Run 100 calls back-to-back with varied inputs
- [ ] Verify p95 latency ≤ 100ms

---

## §4. Serve

- [ ] Run: `python llm_moderator.py serve --redis-url redis://localhost:6379/0 --in-topic chat.comments.<id>,host.draft.<id> --out-topic moderator.verdict.<id>`
- [ ] Tail logs: `tail -f logs/moderator.log`
- [ ] Verify first verdict arrives in Redis

---

## §5. Status board

| Step | Status | Notes |
|---|---|---|
| §1 Prerequisites | ⬜ Pending | – |
| §2 Offline eval | ⬜ Pending | FN must be 0 |
| §3 Latency check | ⬜ Pending | p95 ≤ 100ms |
| §4 Serve | ⬜ Pending | – |

---

## §6. Troubleshooting

| Issue | Cause | Response |
|---|---|---|
| FN > 0 on host audit | weak prompt | add more violation few-shots, re-eval |
| Latency spikes | cache miss | warm up cache, monitor cache hit rate |
| Malformed JSON output | LLM creativity | tighten output schema in prompt, retry once on fail |
| Anthropic 429 | rate limit | exponential backoff (built-in) |
