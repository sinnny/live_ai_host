# Checklist (KO) — RAG (Qdrant + KURE + BGE-M3)

| | |
|---|---|
| 목적 | test_3 방송용 제품 RAG 구축 + 서비스 |
| FSD | [`../../fsd/rag.md`](../../fsd/rag.md) |
| Phase | Phase 1 |
| 언어 정보 | 영어 원본 [`../en/rag.md`](../en/rag.md) — 이 문서는 한국어 번역 |

---

## 기술 스택 (한눈에 보기)

- **Qdrant** (Apache 2.0) — 벡터 DB
- **KURE** — 한국어 retrieval embedding (primary)
- **BGE-M3** (MIT) — 다국어 폴백
- **qdrant-client** Python (Apache 2.0)
- **인프라**: Qdrant 컨테이너 + L40S (build 시에만 임베딩)

상세: [`../../fsd/rag.md`](../../fsd/rag.md) §2

---

## 세션 재개

방송별 Qdrant 컬렉션은 재시작에도 유지. 버전 명시적 변경 시에만 재구축.

---

## §1. 사전 준비

- [ ] [`../../fsd/rag.md`](../../fsd/rag.md) 읽기
- [ ] Qdrant 실행: `docker run -p 6333:6333 qdrant/qdrant`
- [ ] KURE + BGE-M3 가중치 다운로드
- [ ] 테스트 방송용 제품 리스트 준비 (`broadcasts/<id>/products.json`, test_3 용 모의 식품 3개)

---

## §2. 방송별 컬렉션 빌드

- [ ] 실행: `python rag.py build --broadcast-id <id> --products-file broadcasts/<id>/products.json --qdrant-url http://localhost:6333`
- [ ] 컬렉션 존재 확인: `curl http://localhost:6333/collections/broadcast_<id>_products`
- [ ] 예상 벡터 수: ~30 (3 제품 × ~10 필드)

---

## §3. 검색 스모크 테스트

- [ ] 알려진 정답 쿼리 5개 실행: `python rag.py query --broadcast-id <id> --query "할머니 김치 가격" --top-k 3`
- [ ] top 1 가 올바른 `product_id` + `field` 인지 확인
- [ ] 지연 p95 ≤ 50ms

---

## §4. 라벨된 셋 평가

- [ ] 30개 hand-label (쿼리 → 예상 hit) 페어 준비
- [ ] 실행: `python rag.py eval --test-set test_sets/rag/`
- [ ] recall@3 ≥ 90%, top-1 정확도 ≥ 85% 확인

---

## §5. 혼합 언어 폴백 테스트

- [ ] KR+EN 혼합 쿼리 (예: "kimchi 가격 in won") 실행
- [ ] BGE-M3 폴백 동작, 관련 hit 반환 확인

---

## §6. 진행 상태 보드

| 단계 | 상태 | 비고 |
|---|---|---|
| §1 사전 준비 | ⬜ 대기 | – |
| §2 컬렉션 빌드 | ⬜ 대기 | – |
| §3 스모크 테스트 | ⬜ 대기 | 지연 p95 ≤ 50ms |
| §4 라벨 셋 평가 | ⬜ 대기 | recall@3 ≥ 90% |
| §5 혼합 언어 폴백 | ⬜ 대기 | – |

---

## §7. 트러블슈팅

| 이슈 | 원인 | 대응 |
|---|---|---|
| KR 쿼리에서 낮은 recall | KURE 로드 안됨 | 모델 경로 확인; 컬렉션 재구축 |
| top hit 잘못된 제품 | 의미적 모호 | hybrid (dense + sparse for product names) 로 rerank |
| Qdrant connection refused | 컨테이너 다운 | Qdrant 재시작; 포트 확인 |
| 임베딩 빌드 중 OOM | 배치 너무 큼 | build 스크립트의 배치 사이즈 축소 |
