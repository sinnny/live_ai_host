# Function Spec — RAG (Qdrant + KURE + BGE-M3)

| | |
|---|---|
| Status | Spec v1 (Phase 1 / test_3) |
| Phase | Phase 1 |
| Component | Product knowledge retrieval — feeds Host with verified facts for citation |
| Source documents | [`../../prd.md`](../../prd.md) §4.4 |
| Last updated | 2026-05-13 |

---

## 1. Purpose and scope

### 1.1 What this FSD defines

Product knowledge retrieval that grounds Host outputs. For every Host turn that may quote a price, spec, ingredient, origin, etc., the Host retrieves the top-k product facts and is required to cite them. Moderator independently re-validates retrieved facts against source.

### 1.2 Out of scope

- General-purpose knowledge retrieval (only product DB)
- Cross-broadcast / cross-tenant retrieval (per-broadcast collection)
- Web retrieval

---

## 2. Technology stack (locked)

| Stage | Tool | License | Why |
|---|---|---|---|
| Vector DB | **Qdrant** | Apache 2.0 | mature; supports per-collection isolation; fast HNSW |
| Primary embedding (KR) | **KURE** | (verify; MIT-leaning) | Korean retrieval embedding model; outperforms multilingual on KR product copy |
| Fallback embedding | **BGE-M3** | MIT | multilingual; handles mixed KR+EN copy |
| Hybrid search | Qdrant native | – | combines dense + sparse for product names |
| API client | `qdrant-client` Python | Apache 2.0 | – |

---

## 3. Inputs

### 3.1 Build-time (pre-broadcast)

Product list per broadcast (~10 hero + up to 800 long-tail), each:

```json
{
  "product_id": "kimchi_01",
  "name": "할머니 김치",
  "name_en": "Grandmother's Kimchi",
  "category": "fermented_food",
  "price": 4500,
  "currency": "KRW",
  "weight_g": 500,
  "origin": "전라남도 광주",
  "ingredients": ["배추", "고춧가루", ...],
  "manufacturing_process": "전통 방식으로 발효 5일...",
  "shelf_life_days": 60,
  "is_hero": true,
  "image_urls": [...]
}
```

### 3.2 Query-time

```json
{
  "broadcast_id": "bc_2026_05_13_001",
  "query": "할머니 김치 원산지",
  "top_k": 5,
  "filter": { "is_hero": true }
}
```

---

## 4. Outputs

### 4.1 Build-time output

Qdrant collection per broadcast: `broadcast_<id>_products`.

### 4.2 Query-time output

```json
{
  "results": [
    {
      "product_id": "kimchi_01",
      "field": "origin",
      "value": "전라남도 광주",
      "score": 0.91,
      "source": {"collection": "...", "vector_id": "..."}
    },
    ...
  ]
}
```

---

## 5. Pipeline

### 5.1 Indexing (pre-broadcast)

```
for each product:
  for each field (name, origin, ingredients, manufacturing_process, ...):
    text = f"{field_name}: {field_value}"
    vec_kure = KURE.embed(text)
    vec_bge = BGE-M3.embed(text)
    upsert to Qdrant with both vectors + payload
```

### 5.2 Retrieval

```
1. Detect query language (heuristic: presence of Hangul vs Latin)
2. Use KURE if KR-dominant, BGE-M3 if mixed/EN
3. Qdrant search top_k with optional filter
4. Return field-level hits (not whole-product hits) — Host cites specific fields
```

### 5.3 Citation contract

Host MUST include `product_id + field` in its line for any numeric claim. Moderator re-validates by re-running the field-level query.

---

## 6. Execution

```bash
# Build collection per broadcast
python rag.py build \
  --broadcast-id bc_2026_05_13_001 \
  --products-file broadcasts/bc_.../products.json \
  --qdrant-url http://localhost:6333

# Query
python rag.py query \
  --broadcast-id bc_2026_05_13_001 \
  --query "할머니 김치 가격" \
  --top-k 3
```

---

## 7. Quality criteria

| Criterion | Method | Threshold |
|---|---|---|
| Retrieval recall on labeled KR queries | offline eval | ≥ 90% top-3 |
| Latency p95 | log | ≤ 50ms per query |
| Hit accuracy (top-1 field matches expected) | manual review on 50 queries | ≥ 85% |
| Mixed-language fallback works | test KR+EN mixed query | hits relevant product |

---

## 8. Failure modes

| Mode | Symptom | Response |
|---|---|---|
| Qdrant unavailable | query fails | retry; on persistent fail, Host blocks any numeric claim |
| No hits above threshold | empty results | Host says "확인 후 알려드릴게요" instead of guessing |
| KURE OOM on large product set | batch fail | chunk indexing batches |
| Embedding drift across model versions | retrieval quality degradation | pin model versions in collection metadata; rebuild on version bump |

---

## 9. Cost and time

| Item | Estimate |
|---|---|
| Index build (per broadcast, ~30 products × ~10 fields = 300 vectors) | ~$0.10 GPU |
| Per-query | ~$0.0001 (CPU-only retrieval after index) |
| Qdrant hosting | ~$5/month at MVP scale (single tenant) |

---

## 10. Session continuity

- Per-broadcast collection is the unit of work; survives orchestrator restarts.
- Embedding model versions pinned per collection — re-indexing only triggered on explicit version bump.
- No mid-broadcast state.

---

## 11. References

- [`../../prd.md`](../../prd.md) §4.4
- [`llm_host.md`](llm_host.md) — primary caller
- [`llm_moderator.md`](llm_moderator.md) — re-validates host citations
- Qdrant docs, KURE paper, BGE-M3 paper
