# Checklist (KO) — Host agent (Claude Sonnet 4.6)

| | |
|---|---|
| 목적 | 다람찌의 한국어 발화 라인을 생성하는 Host agent 구동 |
| FSD | [`../../fsd/llm_host.md`](../../fsd/llm_host.md) |
| Phase | Phase 1 |
| 언어 정보 | 영어 원본 [`../en/llm_host.md`](../en/llm_host.md) — 이 문서는 한국어 번역 |

---

## 기술 스택 (한눈에 보기)

- **Claude Sonnet 4.6** (proprietary, paid) — LLM
- Anthropic SDK 의 스트리밍 출력
- 프롬프트 캐시 (페르소나+바이블 15k+ 토큰)
- **Redis** — 이벤트 버스
- **인프라**: 어디서든 API 호출; GPU 없음

상세: [`../../fsd/llm_host.md`](../../fsd/llm_host.md) §2

---

## 세션 재개

방송별 Host 인스턴스. 캐시는 extended caching 으로 5분 TTL 갱신. 재시작 시 1회 콜드 호출로 캐시 워밍.

---

## §1. 사전 준비

- [ ] [`../../fsd/llm_host.md`](../../fsd/llm_host.md) 읽기
- [ ] `ANTHROPIC_API_KEY` 설정
- [ ] 시스템 프롬프트 작성 (`prompts/host_sonnet.md`):
  - [ ] 캐릭터 바이블 §3 inline 포함
  - [ ] 바이블 §5 화법 패턴
  - [ ] 바이블 §6.3 하드 가드레일
  - [ ] RAG citation 룰
  - [ ] 감정 태그 스키마 + 예제
  - [ ] positive 5-8 + negative 5-8 few-shot 예제
- [ ] [`../../fsd/rag.md`](../../fsd/rag.md) 운영 중

---

## §2. 단독 페르소나 일관성 평가

- [ ] 다양한 프롬프트 50개를 Host 에 실행
- [ ] 수동 검토:
  - [ ] 한국어 존댓말 일관성
  - [ ] 페르소나 in-character 유지 (AI 언급 없음, 다람쥐 프레임 깨지지 않음)
  - [ ] 모든 라인에 감정 태그 출력
  - [ ] 환각 사실 없음 (RAG 제공 시 인용 일치)
- [ ] 목표: out-of-character / 존댓말 이슈 ≤ 2%

---

## §3. RAG 통합 테스트

- [ ] 모의 제품 3개로 테스트 RAG 제공
- [ ] 사실 기반 질문 20개
- [ ] 모든 numeric claim 이 RAG product+field 인용 100%

---

## §4. 지연 시간 / TTFT

- [ ] 15k+ 토큰 캐싱 워밍업 호출
- [ ] 30회 호출에서 TTFT 측정; p95 ≤ 500ms 확인

---

## §5. Serve

- [ ] 실행: `python llm_host.py serve --redis-url redis://localhost:6379/0 --in-topic director.decision.<id> --out-topic host.draft.<id>`
- [ ] 토큰 스트림 출력이 Redis 에 도착하는지 확인

---

## §6. 진행 상태 보드

| 단계 | 상태 | 비고 |
|---|---|---|
| §1 사전 준비 | ⬜ 대기 | – |
| §2 페르소나 평가 | ⬜ 대기 | ≤ 2% 이슈 |
| §3 RAG 통합 | ⬜ 대기 | citation 100% |
| §4 TTFT 체크 | ⬜ 대기 | p95 ≤ 500ms |
| §5 Serve | ⬜ 대기 | – |

---

## §7. 트러블슈팅

| 이슈 | 원인 | 대응 |
|---|---|---|
| 가격 환각 | RAG 무시 또는 비어있음 | 시스템 프롬프트 강화: "RAG 만 인용; 없으면 확인 후 알려드릴게요" |
| 캐릭터 breaking (AI 언급) | 바이블 컨텍스트 약함 | 명시적 "당신은 AI 가 아니라 다람쥐 인턴" 가드레일 추가 |
| 정식 맥락에서 banmal | 페르소나 패턴 불명 | 존댓말 룰 + 명시 예제로 강화 |
| 감정 태그 누락 | 출력 포맷 약함 | 출력 스키마 체크 + 누락 시 재시도 |
