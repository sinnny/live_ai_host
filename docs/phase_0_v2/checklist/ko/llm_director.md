# Checklist (KO) — Director agent (Claude Haiku 4.5)

| | |
|---|---|
| 목적 | 비트 레벨 FSM 결정용 Director agent 구동 |
| FSD | [`../../fsd/llm_director.md`](../../fsd/llm_director.md) |
| Phase | Phase 1 |
| 언어 정보 | 영어 원본 [`../en/llm_director.md`](../en/llm_director.md) — 이 문서는 한국어 번역 |

---

## 기술 스택 (한눈에 보기)

- **Claude Haiku 4.5** (proprietary, paid) — LLM
- **anthropic** Python SDK (MIT)
- Anthropic prompt cache — 페르소나+바이블 컨텍스트 90% 할인
- **Redis** — 이벤트 버스
- **인프라**: 어디서든 API 호출; GPU 불필요

상세: [`../../fsd/llm_director.md`](../../fsd/llm_director.md) §2

---

## 세션 재개

호출당 stateless — 매 tick 마다 방송 상태 전체 전달. 재시작 시 Redis 토픽 재구독.

---

## §1. 사전 준비

- [ ] [`../../fsd/llm_director.md`](../../fsd/llm_director.md) 읽기
- [ ] `ANTHROPIC_API_KEY` 설정
- [ ] 시스템 프롬프트 작성 (`prompts/director_haiku.md`):
  - [ ] 바이블 §6 페이싱 룰 (cheek-stuff 사이클, 사장님 언급, hoarding gag)
  - [ ] FSM 전환 룰
  - [ ] 결정 예제 few-shot
- [ ] 20개 hand-label 된 방송 상태 + 예상 다음 액션 테스트셋

---

## §2. 오프라인 평가

- [ ] 실행: `python llm_director.py eval --test-set test_sets/director/`
- [ ] hand-label 예상과 ≥ 90% 일치 확인
- [ ] 불일치 검토 — 일부는 정당한 대안일 수 있음; 지속 불일치는 프롬프트 반복 필요

---

## §3. 지연 시간 체크

- [ ] 워밍업 호출
- [ ] 50회 호출; p95 ≤ 200ms 확인

---

## §4. Serve

- [ ] 실행: `python llm_director.py serve --redis-url redis://localhost:6379/0 --in-topic broadcast.tick.<id> --out-topic director.decision.<id>`
- [ ] 첫 결정 Redis 도착 확인

---

## §5. 페이싱 검토 (test_3 4시간 운행 중)

- [ ] 결정 30분 샘플링; 바이블 §6 사이클이 대략 준수되는지 확인 (cheek-stuff 빈도 등 ±20%)

---

## §6. 진행 상태 보드

| 단계 | 상태 | 비고 |
|---|---|---|
| §1 사전 준비 | ⬜ 대기 | – |
| §2 오프라인 평가 | ⬜ 대기 | ≥ 90% 일치 |
| §3 지연 체크 | ⬜ 대기 | p95 ≤ 200ms |
| §4 Serve | ⬜ 대기 | – |
| §5 페이싱 검토 | ⬜ 대기 | G2 이후 |

---

## §7. 트러블슈팅

| 이슈 | 원인 | 대응 |
|---|---|---|
| 상태 바뀌었는데 같은 액션 반복 | 프롬프트가 상태 인식 약함 | 유사 상태에서 다른 best action 의 예제 강화 |
| 위반될 액션 제안 | OK — Moderator 가 잡음 | Director 의 책임 아님 |
| 지연 시간 초과 | 캐시 콜드 | 먼저 워밍업 |
| Tick 이벤트 미수신 | orchestrator 가 미발행 | broadcast_orchestrator 로그 확인 |
