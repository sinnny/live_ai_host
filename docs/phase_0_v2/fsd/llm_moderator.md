# Function Spec — Moderator agent (Claude Haiku 4.5)

| | |
|---|---|
| Status | Spec v1 (Phase 1 / test_3) |
| Phase | Phase 1 |
| Component | Two-way LLM filter: classifies inbound comments + audits Host's drafted lines pre-TTS |
| Source documents | [`../../prd.md`](../../prd.md) §4.3.2, §4.5 |
| Last updated | 2026-05-13 |

---

## 1. Purpose and scope

### 1.1 What this FSD defines

The Moderator agent that operates as the autonomous-safety primitive in live broadcasts. Two filtering jobs:
1. **Comment classification** — for each inbound chat comment, decide: allow / hide / batch / flag (spam, abuse, off-topic).
2. **Host output audit** — for each Host-drafted line BEFORE TTS, decide: allow / reject. Rejection criteria include hallucinated price/spec, 표시광고법 ad-law violations, profanity, persona break.

### 1.2 Why this is critical

This is the safety net that replaces a human operator. If the Moderator silently lets violations through, viewer trust collapses and we accumulate ad-law liability. Therefore: **zero false-negative tolerance on the high-severity categories**.

### 1.3 Out of scope

- Generating replacement text (Host agent regenerates on rejection)
- Generating the comments or lines themselves (those are upstream)
- Long-term spam pattern tracking (per-broadcast scope only)

---

## 2. Technology stack (locked)

| Stage | Tool | License | Why |
|---|---|---|---|
| LLM | **Claude Haiku 4.5** | proprietary, paid | <100ms p95 with prompt caching; sufficient classification capability; Korean prosody understanding for honorific/ad-law checks |
| API client | `anthropic` Python SDK | MIT | official |
| Prompt cache | Anthropic prompt cache (5-min default TTL) | – | 90% discount on cached input |
| Event bus | Redis Pub/Sub | – | – |
| Schema | jsonschema | MIT | input/output validation |

---

## 3. Inputs

### 3.1 Comment classification request

```json
{
  "mode": "comment",
  "comment_id": "ChQK...",
  "text": "이거 진짜 매워요?",
  "author_history": { "prior_msg_count": 3, "flagged_count": 0 }
}
```

### 3.2 Host audit request

```json
{
  "mode": "host_audit",
  "draft_line": "이 김치 한 봉지에 5,000원입니다! 진짜 싸요!",
  "rag_citations": [
    { "product_id": "kimchi_01", "field": "price", "value": "5000", "unit": "KRW" }
  ],
  "current_product_id": "kimchi_01",
  "current_emotion_tag": "excited"
}
```

---

## 4. Outputs

### 4.1 Comment classification response

```json
{
  "verdict": "allow|hide|batch|flag",
  "reason": "...",
  "categories": [],
  "confidence": 0.95
}
```

### 4.2 Host audit response

```json
{
  "verdict": "allow|reject",
  "violations": [
    {
      "category": "hallucinated_price",
      "evidence": "Drafted price 5,000 not in RAG (RAG has 4,500)",
      "severity": "high"
    }
  ],
  "regeneration_hint": "Use the price from RAG: 4,500원"
}
```

---

## 5. Pipeline / prompt structure

### 5.1 System prompt (cached, ~5k tokens)

Static content — defines the agent's role, rule sets, output schemas, few-shot examples for both modes.

Contents:
- Role: "You are the Moderator for a Korean live commerce broadcast."
- Two modes (comment / host_audit) with examples
- Korean 표시광고법 rule summary (the actual rules; not just references)
- Hallucination check algorithm (compare claim → RAG citation)
- Persona break definition (specific to mascot in active broadcast)
- Output schema with examples

### 5.2 Per-call dynamic prompt (uncached, ~200 tokens)

Just the specific request payload (§3) wrapped in clarifying frame.

### 5.3 Call settings

```python
response = client.messages.create(
    model="claude-haiku-4-5",
    max_tokens=300,
    system=[
        {"type": "text", "text": SYSTEM_PROMPT_KO,
         "cache_control": {"type": "ephemeral"}}
    ],
    messages=[{"role": "user", "content": request_json}]
)
```

---

## 6. Execution

```bash
python llm_moderator.py serve \
  --redis-url redis://localhost:6379/0 \
  --in-topic chat.comments.<id>,host.draft.<id> \
  --out-topic moderator.verdict.<id>
```

Runs as a daemon, subscribes to both inbound topics, publishes verdicts.

---

## 7. Quality criteria

| Criterion | Method | Threshold |
|---|---|---|
| Latency p95 | log timestamps | ≤ 100ms |
| Classification accuracy on labeled test set | offline eval | ≥ 95% |
| Host-audit false-negative rate on violation test set | offline eval, manual review | **0** (zero tolerance) |
| Host-audit false-positive rate | offline eval | ≤ 10% (false rejection causes regen; not safety-critical) |
| Schema validity of every output | automated check | 100% |

---

## 8. Failure modes

| Mode | Symptom | Response |
|---|---|---|
| Anthropic API error / 429 | call fails | retry with exponential backoff (1s, 2s, 4s); on persistent failure default to `verdict: hide` for comments and `verdict: reject` for host audits (fail-safe) |
| Malformed LLM response (not JSON) | parse fail | retry once with stricter system prompt; on second fail, fail-safe per above |
| RAG citation missing for a numeric claim | host audit can't verify | auto-reject (Host must always cite) |
| Cache miss | latency spike | acceptable on first turn of broadcast; subsequent turns hit cache |

---

## 9. Cost and time

| Item | Estimate |
|---|---|
| Per-call (cached prompt + small payload) | ~$0.0008 (Haiku 4.5, mostly cached) |
| Per 2-hr broadcast (~400 comment classifications + ~200 host audits = 600 calls) | ~$0.50 |
| Latency budget | ≤ 100ms p95 |

---

## 10. Session continuity

- Each broadcast has its own Moderator instance (independent context).
- System prompt + few-shot examples are static — cache is consistent across restarts.
- No persistent state beyond the audit log (which goes to `audit_log.md`).
- Restart: subscribe to same Redis topic, continue processing new events.

---

## 11. References

- [`../../prd.md`](../../prd.md) §4.3.2, §4.5
- [`chat_ingest.md`](chat_ingest.md), [`llm_host.md`](llm_host.md) — input sources
- [`broadcast_orchestrator.md`](broadcast_orchestrator.md) — consumer of verdicts
- Anthropic prompt caching docs
- 표시광고법 — Korean ad law (to be summarized in prompt; legal consultation pending per `compliance_pre_check.md`)
