# Function Spec — Host agent (Claude Sonnet 4.6)

| | |
|---|---|
| Status | Spec v1 (Phase 1 / test_3) |
| Phase | Phase 1 |
| Component | Generates the spoken Korean line — RAG-grounded, persona-consistent, emotion-tagged |
| Source documents | [`../../prd.md`](../../prd.md) §4.3.2 |
| Last updated | 2026-05-13 |

---

## 1. Purpose and scope

### 1.1 What this FSD defines

The Host agent, the LLM whose output literally becomes the broadcast's spoken Korean. Generates lines based on Director's decision, grounded in product RAG, tagged with `<emotion=...>` for the renderer.

### 1.2 Why Sonnet 4.6 (not Haiku)

The host's voice is the #1 perceived feature. Sonnet noticeably outperforms Haiku on:
- Korean honorific consistency under context drift
- Persona retention over long broadcasts
- RAG citation accuracy
- Subtle prosody control (when to switch between excited / pleading / panicked tones)

Per-stream cost difference (Sonnet vs Haiku) is ~$2-3 with caching. Worth it.

### 1.3 Out of scope

- Deciding when to speak (Director's job)
- Deciding what gets approved before TTS (Moderator's job)
- TTS synthesis (delegated to [`tts_streaming.md`](tts_streaming.md))

---

## 2. Technology stack (locked)

| Stage | Tool | License | Why |
|---|---|---|---|
| LLM | **Claude Sonnet 4.6** | proprietary, paid | best Korean prosody + persona consistency in the price tier; prompt caching covers persona+RAG |
| Streaming output | Anthropic SDK streaming | – | first token in <500ms with cache; tokens feed TTS as they arrive |
| Cache | Anthropic ephemeral cache | – | 90% discount on cached 15k+ token persona+context |
| Event bus | Redis | – | – |

---

## 3. Inputs

```json
{
  "schema_version": 1,
  "directive": {
    "action": "answer_comment",
    "comment_text": "이거 어디서 만들어진 거예요?",
    "emotion_tag": "warm",
    "duration_hint_ms": 8000
  },
  "current_product": {
    "product_id": "kimchi_01",
    "name": "할머니 김치",
    "price": "4500",
    "weight": "500g",
    "origin": "전라남도 광주"
  },
  "rag_excerpts": [
    {
      "product_id": "kimchi_01",
      "field": "manufacturing_process",
      "text": "전통 방식으로 발효 5일..."
    }
  ],
  "broadcast_context": {
    "elapsed_seconds": 832,
    "last_3_lines": ["...", "...", "..."]
  }
}
```

---

## 4. Outputs

Streaming text response with inline tags:

```
<emotion=warm>이거는 전라남도 광주에서 만들어진 할머니 김치예요! 발효를 5일이나 한다더라고요... <emotion=cheek_stuff>아 이거 진짜 한 봉지 다 못 참겠어요...</emotion>
```

Output spec:
- Korean only (Korean honorifics consistent per character bible §5)
- Inline `<emotion=...>` tags wrap segments
- Every numeric claim must cite a RAG product field
- Length matches `duration_hint_ms` roughly (~5 chars/sec speech rate)

---

## 5. Pipeline / prompt structure

### 5.1 System prompt (cached, ~15k tokens)

Heavy content:
- Role: "You are Daramzzi, the squirrel intern at a Korean home shopping channel."
- Full character bible §3 (persona) inline
- Speech patterns from bible §5
- Hard guardrails from bible §6.3
- RAG citation rules: "Quote prices/specs ONLY from the RAG provided per turn. If not in RAG, say '확인 후 알려드릴게요'."
- Emotion tag schema with examples
- Output format with positive + negative few-shot examples

### 5.2 Per-call dynamic input (~500 tokens uncached)

The directive + current product + RAG excerpts per §3.

### 5.3 API call

```python
with client.messages.stream(
    model="claude-sonnet-4-6",
    max_tokens=400,
    system=[
        {"type": "text", "text": SYSTEM_HOST_KO,
         "cache_control": {"type": "ephemeral"}}
    ],
    messages=[{"role": "user", "content": input_json}]
) as stream:
    for token in stream.text_stream:
        publish_to_tts(token)
```

---

## 6. Execution

```bash
python llm_host.py serve \
  --redis-url redis://localhost:6379/0 \
  --in-topic director.decision.<id> \
  --out-topic host.draft.<id>
```

Subscribes to Director decisions, generates lines, publishes drafts (Moderator audits before TTS).

---

## 7. Quality criteria

| Criterion | Method | Threshold |
|---|---|---|
| TTFT (time to first token) p95 | log | ≤ 500ms with cache hit |
| Korean honorific consistency | manual review | mid-line honorific switch ≤ 1 per hour |
| RAG citation correctness | check every numeric claim against RAG | 100% |
| Persona drift | manual review over 4-hr run | ≤ 2% out-of-character lines |
| Emotion tag presence | every output has at least one `<emotion=...>` | 100% |

---

## 8. Failure modes

| Mode | Symptom | Response |
|---|---|---|
| API error | call fails | retry with backoff; on persistent fail, Director sees missing host draft and switches to `silent_pause` |
| Hallucinated price | line states price not in RAG | Moderator catches it pre-TTS; Host regenerates with corrective hint |
| Persona break | line says something off-character | Moderator catches it; Host regenerates |
| Stream tokens too slow | TTFT > 500ms cache miss | likely first call of broadcast (warm-up); subsequent calls hit cache |
| Tag format error | inline tag malformed | parser strips invalid tags; renderer falls back to current emotion |

---

## 9. Cost and time

| Item | Estimate |
|---|---|
| Per-call (15k cached + 500 fresh in + 400 out) | ~$0.013 |
| Per 2-hr broadcast (~200 host calls) | ~$2.60 |
| TTFT | ≤ 500ms p95 (with cache) |

---

## 10. Session continuity

- Each broadcast has its own Host instance with own cache key.
- Cache survives 5-min TTL refreshes via extended caching.
- Restart: re-subscribe to same Redis topic; first call warms cache, subsequent are fast.
- No on-disk state.

---

## 11. References

- [`../../prd.md`](../../prd.md) §4.3.2
- [`../../characters/daramzzi.md`](../../characters/daramzzi.md) §3, §5, §6.3 — persona ground truth
- [`llm_director.md`](llm_director.md) — caller
- [`llm_moderator.md`](llm_moderator.md) — audit downstream
- [`rag.md`](rag.md) — RAG source
- [`tts_streaming.md`](tts_streaming.md) — TTS consumer
- Anthropic prompt caching + streaming docs
