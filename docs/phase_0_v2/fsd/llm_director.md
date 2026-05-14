# Function Spec — Director agent (Claude Haiku 4.5)

| | |
|---|---|
| Status | Spec v1 (Phase 1 / test_3) |
| Phase | Phase 1 |
| Component | Beat-level scheduling FSM — decides what happens next at each broadcast moment |
| Source documents | [`../../prd.md`](../../prd.md) §4.3.2 |
| Last updated | 2026-05-13 |

---

## 1. Purpose and scope

### 1.1 What this FSD defines

The Director agent that makes beat-level decisions during a live broadcast: which comment to answer, when to switch products, what emotion tag to apply, which scripted clip to play, when to trigger giveaway/quiz segments.

Replaces a human operator's "what's next" judgment.

### 1.2 Out of scope

- Generating the actual spoken line (delegated to Host — see [`llm_host.md`](llm_host.md))
- Filtering / safety (delegated to Moderator — see [`llm_moderator.md`](llm_moderator.md))
- Rendering / TTS (delegated to downstream)
- Persistent stream-level state (managed by `broadcast_orchestrator.md`)

### 1.3 Success criterion

For test_3 Gate G2:
1. Director decisions match founder-labeled "expected next action" on a 20-item test set in ≥ 90% of cases.
2. Latency p95 ≤ 200ms.
3. No decision deadlocks (i.e. doesn't issue same action repeatedly when state changed).

---

## 2. Technology stack (locked)

| Stage | Tool | License | Why |
|---|---|---|---|
| LLM | **Claude Haiku 4.5** | proprietary, paid | fast enough for beat decisions; cached prompt amortizes the persona+context |
| API client | `anthropic` Python SDK | MIT | – |
| Prompt cache | Anthropic ephemeral cache | – | 90% discount on cached input |
| Event bus | Redis | – | – |

---

## 3. Inputs

```json
{
  "schema_version": 1,
  "broadcast_state": {
    "elapsed_seconds": 832,
    "current_product_id": "kimchi_01",
    "current_mode": "FULL_MASCOT",
    "products_remaining": ["ramyun_01", "gochujang_01"],
    "last_n_spoken_lines": ["...", "...", "..."],
    "sales_state": "slow",
    "scripted_beats_remaining": ["sale_announcement", "closing"]
  },
  "pending_comments": [
    { "id": "c1", "text": "이거 어디서 만들어진 거예요?", "verdict": "allow" },
    { "id": "c2", "text": "다음 제품 뭐예요?", "verdict": "allow" }
  ]
}
```

---

## 4. Outputs

```json
{
  "schema_version": 1,
  "decision": {
    "action": "answer_comment|advance_product|play_scripted|emergency_loop|silent_pause",
    "comment_id": "c1",
    "product_id": null,
    "scripted_beat_id": null,
    "emotion_tag": "warm",
    "duration_hint_ms": 8000
  },
  "reasoning": "Comment c1 directly asks origin info, RAG can answer; answering it keeps engagement during slow sales. c2 about next product is on the upcoming script beat — defer."
}
```

---

## 5. Pipeline / prompt structure

### 5.1 System prompt (cached, ~10k tokens)

- Role: "You are the Director for Daramzzi's live broadcast. You decide what happens next at each beat."
- Mascot bible summary (key persona traits relevant to pacing)
- Decision rules:
  - Hot comments (engagement-driving) take priority
  - Sales-slow → schedule sales-pivot beats (pleading, victory if any conversion)
  - Cheek-stuff cooldowns (no two cheek-stuff beats within 5 min)
  - 사장님 references every ~10 min
  - Hoarding gag every ~15-20 min
- FSM rules: which mode transitions are allowed when
- Few-shot examples of good decisions vs. bad
- Output schema with examples

### 5.2 Per-call dynamic input (uncached, ~500 tokens)

Just the broadcast state + pending comments.

---

## 6. Execution

```bash
python llm_director.py serve \
  --redis-url redis://localhost:6379/0 \
  --in-topic broadcast.tick.<id> \
  --out-topic director.decision.<id>
```

Triggered by tick events from `broadcast_orchestrator.md` (every 5-10 sec or on new high-priority event).

---

## 7. Quality criteria

| Criterion | Method | Threshold |
|---|---|---|
| Latency p95 | log timestamps | ≤ 200ms |
| Decision agreement with hand-labeled expected | offline eval | ≥ 90% |
| No deadlock | check over 4-hr run | 0 repeated identical decisions when state changed |
| Persona-pacing rules respected | manual review of 30-min sample | bibles §6.2 cycles followed ±20% |

---

## 8. Failure modes

| Mode | Symptom | Response |
|---|---|---|
| API error / 429 | call fails | retry with exponential backoff; on persistent fail, default to `silent_pause` (safe default) |
| Malformed response | parse fail | retry once; on second fail, default `silent_pause` |
| Director picks invalid action | parse OK, action not in enum | reject, retry with stricter system prompt |
| Director suggests action that violates Moderator (e.g. hallucinated price product) | Moderator catches downstream | not Director's job to validate |

---

## 9. Cost and time

| Item | Estimate |
|---|---|
| Per-call | ~$0.001 (Haiku 4.5, mostly cached) |
| Per 2-hr broadcast (~120 ticks) | ~$0.12 |
| Latency p95 | ≤ 200ms |

---

## 10. Session continuity

- Director receives a snapshot of broadcast state per call — no internal state between calls.
- Stream-level state lives in `broadcast_orchestrator.md`.
- Cache stays warm as long as system prompt unchanged across calls within the broadcast.

---

## 11. References

- [`../../prd.md`](../../prd.md) §4.3.2
- [`broadcast_orchestrator.md`](broadcast_orchestrator.md) — caller / state-keeper
- [`llm_host.md`](llm_host.md), [`llm_moderator.md`](llm_moderator.md) — siblings
- [`../../characters/daramzzi.md`](../../characters/daramzzi.md) §6 — pacing rules
