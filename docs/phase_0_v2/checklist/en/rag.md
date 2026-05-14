# Checklist — RAG (Qdrant + KURE + BGE-M3)

| | |
|---|---|
| Purpose | Build + serve product RAG for a test_3 broadcast |
| FSD | [`../../fsd/rag.md`](../../fsd/rag.md) |
| Phase | Phase 1 |
| Language | English source — KO at [`../ko/rag.md`](../ko/rag.md) |

---

## Tech stack (at a glance)

- **Qdrant** (Apache 2.0) — vector DB
- **KURE** — Korean retrieval embedding (primary)
- **BGE-M3** (MIT) — multilingual fallback
- **qdrant-client** Python (Apache 2.0)
- **Infra**: Qdrant container + L40S for embedding (build-time only)

Full table: [`../../fsd/rag.md`](../../fsd/rag.md) §2

---

## Session resume

Per-broadcast Qdrant collection survives restarts. Rebuild only triggered on explicit version bump.

---

## §1. Prerequisites

- [ ] [`../../fsd/rag.md`](../../fsd/rag.md) read
- [ ] Qdrant running: `docker run -p 6333:6333 qdrant/qdrant`
- [ ] KURE + BGE-M3 weights downloaded
- [ ] Product list prepared for the test broadcast (`broadcasts/<id>/products.json`, 3 mock food products for test_3)

---

## §2. Build per-broadcast collection

- [ ] Run: `python rag.py build --broadcast-id <id> --products-file broadcasts/<id>/products.json --qdrant-url http://localhost:6333`
- [ ] Verify collection exists: `curl http://localhost:6333/collections/broadcast_<id>_products`
- [ ] Expected vector count: ~30 (3 products × ~10 fields)

---

## §3. Retrieval smoke test

- [ ] Run 5 known-good queries: `python rag.py query --broadcast-id <id> --query "할머니 김치 가격" --top-k 3`
- [ ] Verify top hit has correct `product_id` + `field`
- [ ] Latency p95 ≤ 50ms

---

## §4. Eval on labeled set

- [ ] Prepare 30 hand-labeled (query → expected hit) pairs
- [ ] Run: `python rag.py eval --test-set test_sets/rag/`
- [ ] Verify recall@3 ≥ 90%, top-1 accuracy ≥ 85%

---

## §5. Mixed-language fallback test

- [ ] Run KR+EN mixed query (e.g. "kimchi 가격 in won")
- [ ] Verify BGE-M3 fallback engages and returns relevant hits

---

## §6. Status board

| Step | Status | Notes |
|---|---|---|
| §1 Prerequisites | ⬜ Pending | – |
| §2 Build collection | ⬜ Pending | – |
| §3 Smoke test | ⬜ Pending | latency p95 ≤ 50ms |
| §4 Eval on labeled set | ⬜ Pending | recall@3 ≥ 90% |
| §5 Mixed-language fallback | ⬜ Pending | – |

---

## §7. Troubleshooting

| Issue | Cause | Response |
|---|---|---|
| Low recall on KR queries | KURE not loaded | check model path; rebuild collection |
| Top hit wrong product | semantic ambiguity | rerank with hybrid (dense + sparse for product names) |
| Qdrant connection refused | container not up | restart Qdrant; check port |
| OOM during embedding build | batch too large | reduce batch size in build script |
